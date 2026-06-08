from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Depends, Request, Response
from typing import Optional
import uuid
from datetime import datetime
import logging
import json

from schemas.medical_schemas import AgentState
from api.auth_routes import require_privacy_policy, get_current_user

diagnosis_router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_workflow_info(graph, config: dict, state: dict) -> dict:
    snapshot = await graph.aget_state(config)
    next_nodes = list(snapshot.next) if snapshot and snapshot.next else []

    if not next_nodes:
        return {
            "workflow_complete": True,
            "next_endpoint": None,
            "needs_user_input": None,
            "next_step_description": "Medical analysis workflow complete",
            "show_next_button": False,
            "medical_report_available": bool(state.get("medical_report")),
        }

    node_map = {
        "generate_followup_questions": ("/patient/followup_questions", "followup_questions", "Follow-up questions needed"),
        "process_followup_responses": ("/patient/followup_questions", "followup_questions", "Answer follow-up questions"),
        "overall_analysis": ("/patient/overall_analysis", None, "Ready for comprehensive analysis"),
        "medical_report": ("/patient/medical_report", None, "Generating medical report"),
    }
    endpoint, user_input, description = node_map.get(next_nodes[0], (None, None, "Unknown next step"))

    return {
        "workflow_complete": False,
        "next_endpoint": endpoint,
        "needs_user_input": user_input,
        "next_step_description": description,
        "show_next_button": True,
        "confidence_score": state.get("average_confidence", 0.0),
    }


@diagnosis_router.post("/patient/textual_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_textual_analysis(
    request: Request,
    user_symptoms: str = Form(..., description="Patient symptoms"),
    session_id: Optional[str] = Form(None),
):
    session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        initial_state: AgentState = {
            "session_id": session_id,
            "latest_user_message": user_symptoms,
            "userInput_symptoms": user_symptoms,
            "current_workflow_stage": "initializing",
        }
        result = await graph.ainvoke(initial_state, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/followup_questions", dependencies=[Depends(require_privacy_policy)])
async def run_followup_questions(
    request: Request,
    session_id: str = Form(...),
    followup_responses: Optional[str] = Form(None),
):
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        if followup_responses:
            responses = json.loads(followup_responses)
            await graph.aupdate_state(config, {
                "followup_response": responses,
                "requires_user_input": False,
            })
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/overall_analysis", dependencies=[Depends(require_privacy_policy)])
async def run_overall_analysis(request: Request, session_id: str = Form(...)):
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/medical_report", dependencies=[Depends(require_privacy_policy)])
async def run_medical_report(
    request: Request,
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
):
    config = {"configurable": {"thread_id": session_id}}
    graph = request.app.state.patient_graph

    try:
        result = await graph.ainvoke(None, config)
        workflow_info = await _get_workflow_info(graph, config, result)
        return {"success": True, "session_id": session_id, "result": result, "workflow_info": workflow_info}
    except Exception as e:
        logger.error(f"Medical report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.post("/patient/export_report")
async def export_report_file(
    request: Request,
    session_id: str = Form(...),
    format: str = Form(...),
    include_details: bool = Form(True),
    report_data: str = Form(...),
):
    try:
        graph = request.app.state.patient_graph
        config = {"configurable": {"thread_id": session_id}}
        snapshot = await graph.aget_state(config)
        session_state = snapshot.values if snapshot and snapshot.values else json.loads(report_data)

        from nodes.medical_report_node import MedicalReportNode
        report_node = MedicalReportNode()
        file_content = await report_node.generate_export_file(
            state=session_state, format=format, include_details=include_details
        )

        if format == "pdf":
            media_type = "application/pdf"
            filename = f"medical-report-{session_id}.pdf"
        elif format == "word":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"medical-report-{session_id}.docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use pdf or word.")

        return Response(
            content=file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.get("/debug/routes")
async def debug_routes():
    return {"message": "Routes working", "endpoints": [
        "/patient/textual_analysis", "/patient/followup_questions",
        "/patient/overall_analysis", "/patient/medical_report",
        "/patient/export_report", "/health",
    ]}


@diagnosis_router.get("/health")
async def health_check():
    from config import settings
    return {
        "status": "healthy",
        "service": "AI Medical Diagnosis API",
        "version": "2.0.0",
        "llm_model": settings.LLM_MODEL,
        "timestamp": datetime.now().isoformat(),
    }
