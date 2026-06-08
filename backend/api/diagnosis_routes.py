from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import Response
from typing import Optional, Dict
import uuid
import base64
from datetime import datetime
import logging
import json

import os
from nodes import LLMDiagnosisNode, ImageClassificationNode, FollowUpInteractionNode, OverallAnalysisNode, MedicalReportNode 
from schemas.medical_schemas import AgentState
from managers.websocket_manager import ConnectionManager
from managers.workflow_state_manager import workflow_state_manager
from managers.model_manager import model_manager
from adapters.skinlesion_efficientNet_adapter import EfficientNetAdapter

# Create router
diagnosis_router = APIRouter()
manager = ConnectionManager()

# Configure logger
logger = logging.getLogger(__name__)

#Global node instances
llm_diagnosis_node: LLMDiagnosisNode | None = None
followup_interaction_node: FollowUpInteractionNode | None = None
image_classification_node: ImageClassificationNode | None = None
overall_analysis_node: OverallAnalysisNode | None = None
# healthcare_recommendation_node: HealthcareRecommendationNode | None = None
medical_report_node: MedicalReportNode | None = None

print("✅ All nodes initialized for API routes!")

session_states: Dict[str, AgentState] = {}

def get_or_create_session_state(session_id: str, initial_state: Optional[AgentState] = None) -> AgentState:
    """Get existing session state or create new one"""
    if session_id not in session_states:
        if initial_state:
            session_states[session_id] = initial_state
        else:
            session_states[session_id] = AgentState(
                session_id=session_id,
                latest_user_message="",
                image_required=False
            )
    return session_states[session_id]

def update_session_state(session_id: str, updated_state: AgentState) -> None:
    """Update session state in storage"""
    session_states[session_id] = updated_state
    
def initialize_nodes_once():
    """Initialize all nodes ONCE with pre-loaded models"""
    global llm_diagnosis_node, followup_interaction_node, image_classification_node
    global overall_analysis_node, medical_report_node
    
    if not model_manager.is_loaded():
        raise RuntimeError("Models not loaded. Cannot initialize nodes.")
    
    print("🔧 Initializing nodes with loaded models...")
    
    # Get local adapter (always available)
    local_adapter = model_manager.get_local_adapter()
    
    if local_adapter is None:
        raise RuntimeError("Local adapter is None. Models may not have loaded properly.")
    
    llm_diagnosis_node = LLMDiagnosisNode(adapter=local_adapter)
    followup_interaction_node = FollowUpInteractionNode(adapter=local_adapter)
    overall_analysis_node = OverallAnalysisNode(adapter=local_adapter)
    medical_report_node = MedicalReportNode(adapter=local_adapter)

    #Image classification node set to none as it will be loaded on demand
    image_classification_node = None
    print("✅ All nodes initialized with loaded models!")
    
def ensure_nodes_initialized():
    """check if models are loaded"""
    if not model_manager.is_loaded():
        raise HTTPException(status_code=503, detail="Models not loaded yet. Please wait for startup to complete.")
    
    # 🔧 FIX: Nodes should already be initialized at startup
    if llm_diagnosis_node is None:
        raise HTTPException(status_code=500, detail="Nodes not initialized. Internal server error.")

async def get_image_classification_node():
    "create image classification node separately for on-demand model loading"
    global image_classification_node
    
    if image_classification_node is None:
        try:
            efficientnet_adapter = await model_manager.get_efficientnet_adapter()
            
            if efficientnet_adapter is None:
                raise RuntimeError("Failed to load EfficientNet adapter")
            
            # Create the image classification node
            image_classification_node = ImageClassificationNode(adapter=efficientnet_adapter)
            print("✅ Image classification node created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create image classification node: {e}")
            raise
    
    return image_classification_node

#NODE 1: Textual Analysis Endpoint
@diagnosis_router.post("/patient/textual_analysis")
async def run_textual_analysis(
    user_symptoms: str = Form(..., description="Patient symptoms"),
    session_id: Optional[str] = Form(None, description="Session ID"),
):
    """Run LLM textual analysis on symptoms"""
    
    # Ensure nodes are initialized with loaded models
    ensure_nodes_initialized()
    
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    try:
        #Create or get session state
        state = get_or_create_session_state(session_id, AgentState(
            session_id=session_id,
            latest_user_message=user_symptoms,
            userInput_symptoms=user_symptoms,
            image_required=False,
            current_workflow_stage="initializing"  # Start with initializing
        ))
                
        # Send progress update
        await manager.send_message(session_id, {
            "type": "node_started",
            "node": "textual_analysis",
            "message": "Analyzing symptoms with AI...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Run the LLM diagnosis node
        result = await llm_diagnosis_node(state)
        
        #workflow state manager to set completion stage and determine next step
        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "textual_analysis"
        )

        print(f"🔍 After WorkflowStateManager - stage: {result.get('current_workflow_stage')}")
        print(f"📊 Workflow info: {workflow_info}")
        
        update_session_state(session_id, result)

        # Send completion update
        await manager.send_message(session_id, {
            "type": "node_completed", 
            "node": "textual_analysis",
            "result": result,
            "workflow_info": workflow_info,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info #Frontend will use this to determine next step
        }
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "node_error",
            "node": "textual_analysis", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))

#NODE 2: Follow-up Questions Endpoint
@diagnosis_router.post("/patient/followup_questions")
async def run_followup_questions(
    session_id: str = Form(..., description="Session ID"),
    previous_state: str = Form(..., description="JSON of previous AgentState"),
    followup_responses: str | None = Form(None, description="JSON of user responses")
):
    """Generate follow-up questions OR process responses"""
    
    # Ensure nodes are initialized with loaded models
    ensure_nodes_initialized()
    
    try:
        ### Solution 1: Try deleting the followup_response here instead 
        
        import json
        state = json.loads(previous_state)
        
        print("check followup_responses:", followup_responses)
        
        # Add follow-up responses if provided
        if not followup_responses:
            state["requires_user_input"] = True
        else: 
            state["followup_response"] = json.loads(followup_responses)
            state["requires_user_input"] = False
        
        await manager.send_message(session_id, {
            "type": "node_started",
            "node": "followup_questions",
            "message": "Processing follow-up interaction...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Run the follow-up interaction node
        result = await followup_interaction_node(state)
        
        # Normal processing - use workflow state manager
        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "followup_interaction"
        )

        update_session_state(session_id, result)
        
        await manager.send_message(session_id, {
            "type": "node_completed",
            "node": "followup_questions", 
            "result": result,
            "workflow_info": workflow_info,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "node_error",
            "node": "followup_questions",
            "error": str(e), 
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))

#NODE 3: Image Analysis Endpoint  
@diagnosis_router.post("/patient/image_analysis")
async def run_image_analysis(
    session_id: str = Form(...),
    previous_state: str = Form(..., description="JSON of previous AgentState"),
    image_file: UploadFile | None = File(None, description="Medical image")
):
    """Run image classification analysis"""
    
    # Ensure nodes are initialized with loaded models
    ensure_nodes_initialized()
    
    try:
        import json
        state = json.loads(previous_state)
        
        # Handle new image upload
        if image_file:
            image_bytes = await image_file.read()
            state["image_input"] = base64.b64encode(image_bytes).decode('utf-8')
        
        await manager.send_message(session_id, {
            "type": "node_started",
            "node": "image_analysis",
            "message": "Analyzing medical image...",
            "timestamp": datetime.now().isoformat()
        })
        
        #Get image classification node with on-demand loading
        image_node = await get_image_classification_node()
        
        await manager.send_message(session_id, {
            "type": "node_progress",
            "node": "image_analysis", 
            "message": "Analyzing medical image...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Run the image classification node
        result = await image_node(state)
        
        #workflow state manager to set completion stage and determine next step
        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "image_analysis"
        )

        print(f"🔍 After WorkflowStateManager - stage: {result.get('current_workflow_stage')}")
        print(f"📊 Workflow info: {workflow_info}")
        
        update_session_state(session_id, result)
        
        await manager.send_message(session_id, {
            "type": "node_completed",
            "node": "image_analysis",
            "result": result, 
            "workflow_info": workflow_info,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "node_error",
            "node": "image_analysis",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))

#NODE 4: Overall Analysis Endpoint
@diagnosis_router.post("/patient/overall_analysis")
async def run_overall_analysis(
    session_id: str = Form(...),
    previous_state: str = Form(..., description="JSON of previous AgentState")
):
    """Run comprehensive overall analysis"""
    
    # Ensure nodes are initialized with loaded models
    ensure_nodes_initialized()
    
    try:
        import json
        state = json.loads(previous_state)
        
        await manager.send_message(session_id, {
            "type": "node_started",
            "node": "overall_analysis",
            "message": "Performing comprehensive analysis...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Run the overall analysis node
        result = await overall_analysis_node(state)
        
        #workflow state manager to set completion stage and determine next step
        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "overall_analysis"
        )

        print(f"🔍 After WorkflowStateManager - stage: {result.get('current_workflow_stage')}")
        print(f"📊 Workflow info: {workflow_info}")
        
        update_session_state(session_id, result)
        
        await manager.send_message(session_id, {
            "type": "node_completed",
            "node": "overall_analysis",
            "result": result,
            "workflow_info": workflow_info,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "node_error",
            "node": "overall_analysis",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))

# #NODE 5: Healthcare Recommendations Endpoint
# @diagnosis_router.post("/patient/healthcare_recommendations")
# async def run_healthcare_recommendations(
#     session_id: str = Form(...),
#     previous_state: str = Form(..., description="JSON of previous AgentState")
# ):
#     """Generate healthcare recommendations"""
    
#     # Ensure nodes are initialized with loaded models
#     ensure_nodes_initialized()
    
#     try:
#         import json
#         state = json.loads(previous_state)
        
#         await manager.send_message(session_id, {
#             "type": "node_started",
#             "node": "healthcare_recommendations",
#             "message": "Finding healthcare recommendations...",
#             "timestamp": datetime.now().isoformat()
#         })
        
#         # Run the healthcare recommendation node
#         result = await healthcare_recommendation_node(state)
        
#         #workflow state manager to set completion stage and determine next step
#         workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
#             result, "healthcare_recommendation"
#         )

#         print(f"🔍 After WorkflowStateManager - stage: {result.get('current_workflow_stage')}")
#         print(f"📊 Workflow info: {workflow_info}")
        
#         update_session_state(session_id, result)
        
#         await manager.send_message(session_id, {
#             "type": "node_completed",
#             "node": "healthcare_recommendations",
#             "result": result,
#             "workflow_info": workflow_info,
#             "timestamp": datetime.now().isoformat()
#         })
        
#         return {
#             "success": True,
#             "session_id": session_id,
#             "result": result,
#             "workflow_info": workflow_info,
#         }
        
#     except Exception as e:
#         await manager.send_message(session_id, {
#             "type": "node_error",
#             "node": "healthcare_recommendations",
#             "error": str(e),
#             "timestamp": datetime.now().isoformat()
#         })
#         raise HTTPException(status_code=500, detail=str(e))

@diagnosis_router.post("/patient/medical_report")
async def export_medical_report(
    session_id: str = Form(...),
    previous_state: str = Form(..., description="JSON of previous AgentState")
):
    """Generate and export medical report in PDF or Word format"""
    ensure_nodes_initialized()
    
    try:
        state = json.loads(previous_state)

        await manager.send_message(session_id, {
            "type": "node_started",
            "node": "medical_report",
            "message": "Generating comprehensive medical report...",
            "timestamp": datetime.now().isoformat()
        })
        
        result = await medical_report_node(state)
        
        # Update workflow stage
        workflow_info = workflow_state_manager.update_workflow_stage_and_determine_next(
            result, "generate_report"
        )

        print(f"🔍 After WorkflowStateManager - stage: {result.get('current_workflow_stage')}")
        print(f"📊 Workflow info: {workflow_info}")
        
        update_session_state(session_id, result)
        
        await manager.send_message(session_id, {
            "type": "node_completed",
            "node": "medical_report",
            "result": result,
            "workflow_info": workflow_info,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "workflow_info": workflow_info,
        }
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@diagnosis_router.post("/patient/export_report")
async def export_medical_report(
    session_id: str = Form(...),
    format: str = Form(...),  # 'pdf' or 'word'
    include_details: bool = Form(True),
    report_data: str = Form(...)  # JSON string
):
    """Generate and export medical report in PDF or Word format (EXPORT ONLY)"""
    
    try:
        import json
        data = json.loads(report_data)
        
        # Get session state for complete report data
        session_state = session_states.get(session_id)
        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")
            session_state = data
        
        # Use medical report node for export generation
        if not medical_report_node:
            raise HTTPException(status_code=500, detail="Medical report node not initialized")
        
        # Call export method with correct arguments
        file_content = await medical_report_node.generate_export_file(
            state=session_state,
            format=format,
            include_details=include_details
        )
        
        if format == 'pdf':
            media_type = 'application/pdf'
            filename = f"medical-report-{session_id}.pdf"
        elif format == 'word':
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f"medical-report-{session_id}.docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@diagnosis_router.get("/debug/routes")
async def debug_routes():
    return {
        "message": "Routes are working!",
        "available_endpoints": [
            "/patient/textual_analysis",
            "/patient/followup_questions", 
            "/patient/image_analysis",
            "/patient/overall_analysis",
            "/patient/healthcare_recommendations",
            "/patient/medical_report",
            "/health"
        ]
    }

# **Unused - Enhanced diagnostic endpoint with WebSocket integration
@diagnosis_router.post("/patient/diagnose_patient_realtime")
async def diagnose_patient_realtime(
    user_symptoms: str = Form(..., description="Symptoms provided by the patient"),
    session_id: Optional[str] = Form(None, description="Session ID for WebSocket connection"),
    user_lat: Optional[float] = Form(None, description="User latitude for location services"),
    user_lng: Optional[float] = Form(None, description="User longitude for location services"),
    image_file: Optional[UploadFile] = File(None, description="Medical image file")
):
    """Enhanced diagnosis with real-time WebSocket updates"""
    
    # Ensure nodes are initialized with loaded models
    ensure_nodes_initialized()
    
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    try:
        # Initialize workflow state
        initial_state = AgentState(
            session_id=session_id,
            latest_user_message=user_symptoms,
            userInput_symptoms=user_symptoms,
            workflow_path=[],
            image_required=False,
            user_location={"lat": user_lat, "lng": user_lng} if user_lat and user_lng else None,
            image_input=None
        )
        
        # Handle image upload
        if image_file:
            try:
                if not image_file.content_type.startswith('image/'):
                    raise HTTPException(status_code=400, detail="File must be an image")
                
                image_bytes = await image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                initial_state["image_input"] = image_base64
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
            finally:
                await image_file.close()
        
        # Store session in connection manager
        manager.session_workflows[session_id] = {
            "status": "started",
            "current_stage": "initializing",
            "progress": 0,
            "started_at": datetime.now().isoformat()
        }
        
        # Send workflow started notification
        await manager.send_message(session_id, {
            "type": "workflow_started",
            "session_id": session_id,
            "initial_symptoms": user_symptoms,
            "timestamp": datetime.now().isoformat()
        })
        
        # Run workflow with real-time updates
        result = await run_workflow_with_updates(initial_state, session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "result": result,
            "message": "Diagnosis completed successfully"
        }
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "workflow_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@diagnosis_router.get("/health")
async def health_check():
    """System health check with WebSocket connection info"""
    return {
        "status": "healthy",
        "service": "AI Medical Diagnosis API", 
        "version": "2.0.0",
        "features": {
            "llm_analysis": True,
            "image_classification": True,
            "location_services": True,
            "medical_reporting": True,
            "realtime_websocket": True,
            "active_connections": len(manager.active_connections)
        },
        "websocket_endpoint": "/ws/{session_id}",
        "timestamp": datetime.now().isoformat()
    }

# Workflow execution with real-time updates
async def run_workflow_with_updates(state: AgentState, session_id: str):
    """Run the LangGraph workflow with real-time WebSocket updates"""
    
    workflow_stages = [
        ("llm_diagnosis", "Analyzing symptoms with AI", 20),
        ("followup_interaction", "Generating follow-up questions", 40), 
        ("image_analysis", "Processing medical images", 60),
        ("overall_analysis_step", "Comprehensive medical analysis", 80), 
        ("healthcare_recommendation_step", "Finding healthcare recommendations", 90),  
        ("generate_report", "Generating medical report", 100)
    ]
    current_progress = 0
    
    # Create a custom callback for workflow updates
    async def workflow_callback(node_name: str, node_result: dict):
        nonlocal current_progress
        
        # Find current stage info
        stage_info = next((s for s in workflow_stages if s[0] == node_name), None)
        if stage_info:
            stage_name, description, progress = stage_info
            current_progress = progress
            
            # Update session workflow data
            manager.session_workflows[session_id].update({
                "status": "running",
                "current_stage": stage_name,
                "stage_description": description,
                "progress": progress,
                "last_updated": datetime.now().isoformat()
            })
            
            # Send real-time update
            await manager.send_message(session_id, {
                "type": "workflow_progress",
                "stage": stage_name,
                "description": description,
                "progress": progress,
                "node_result": node_result,
                "timestamp": datetime.now().isoformat()
            })
            
            # Special handling for follow-up questions
            if node_name == "followup_interaction" and node_result.get("requires_user_input"):
                await manager.send_message(session_id, {
                    "type": "user_input_required",
                    "questions": node_result.get("followup_questions", []),
                    "message": "Please answer the following questions to improve diagnosis accuracy",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Execute workflow with custom monitoring
    try:
        # Execute the workflow
        result = await execute_workflow_with_monitoring(state, workflow_callback)
        
        # Final completion message
        manager.session_workflows[session_id].update({
            "status": "completed",
            "progress": 100,
            "completed_at": datetime.now().isoformat()
        })
        
        await manager.send_message(session_id, {
            "type": "workflow_completed",
            "final_result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
        
    except Exception as e:
        manager.session_workflows[session_id].update({
            "status": "error",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })
        
        await manager.send_message(session_id, {
            "type": "workflow_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise e

async def execute_workflow_with_monitoring(state: AgentState, callback):
    """Execute the LangGraph workflow with monitoring callbacks"""
    
    # This is a wrapper around your existing patient_app workflow
    # We'll add monitoring by intercepting node execution
    
    from graphs.patient_workflow import patient_app
    
    # Execute the workflow
    result = await patient_app.ainvoke(state)
    
    return result

# Session management endpoints
@diagnosis_router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current status of a diagnosis session"""
    if session_id not in manager.session_workflows:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "workflow_status": manager.session_workflows[session_id],
        "websocket_connected": session_id in manager.active_connections,
        "timestamp": datetime.now().isoformat()
    }

@diagnosis_router.delete("/session/{session_id}")
async def terminate_session(session_id: str):
    """Terminate a diagnosis session"""
    if session_id in manager.session_workflows:
        del manager.session_workflows[session_id]
    
    if session_id in manager.active_connections:
        await manager.send_message(session_id, {
            "type": "session_terminated",
            "message": "Session has been terminated",
            "timestamp": datetime.now().isoformat()
        })
        manager.disconnect(session_id)
    
    return {
        "success": True,
        "message": f"Session {session_id} terminated",
        "timestamp": datetime.now().isoformat()
    }

# System monitoring endpoints
@diagnosis_router.get("/admin/connections")
async def list_active_connections():
    """List all active WebSocket connections (admin endpoint)"""
    return {
        "active_connections": list(manager.active_connections.keys()),
        "active_workflows": list(manager.session_workflows.keys()),
        "total_connections": len(manager.active_connections),
        "total_workflows": len(manager.session_workflows),
        "timestamp": datetime.now().isoformat()
    }