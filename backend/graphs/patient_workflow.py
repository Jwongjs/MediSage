from langgraph.graph import StateGraph, END
from schemas.medical_schemas import AgentState
import asyncio
import os
from adapters.local_model_adapter import LocalModelAdapter
from adapters.skinlesion_efficientNet_adapter import EfficientNetAdapter
from adapters.embedder_adapter import EmbedderAdapter
from nodes import LLMDiagnosisNode, ImageClassificationNode, FollowUpInteractionNode, OverallAnalysisNode, HealthcareRecommendationNode, MedicalReportNode 


#Pydantic schemas
# from models.ai_schema import (
#     SymptomInput,
#     SymptomAnalysis,
#     SelfCareAdvice,
#     SpecialistRecommendation,
#     MedicalReport,
#     SessionEndCheck
# )

multipurpose_model_path = "ai_models/Llama-3.1-8B-UltraMedical.Q8_0.gguf" 
#huggingface_model_path = r"C:\Users\user\Desktop\Langgraph+Pydantic_Test\ai_models\BioMistral-7B_Q4_K_M" # "BioMistral/BioMistral-7B" 
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2" 

print("Initializing Local Model Adapter through llama.cpp...")
local_adapter = LocalModelAdapter(
    llm_path=multipurpose_model_path,
)

print("Initializing EfficientNet-b0 model (skin lesion classifier) Adapter...")
efficientnet_adapter = EfficientNetAdapter(
    model_path="ai_models/skin_lesion_efficientnetb0.pth",
)

print("Initializing embedding model adapter...")
embedder_adapter = EmbedderAdapter(
    model_name=embedding_model_name,
)

print("Adapters initialized.")

#Initialize all callable node instances
llm_diagnosis_node = LLMDiagnosisNode(adapter=local_adapter)
followup_interaction_node = FollowUpInteractionNode(adapter=local_adapter)
image_classification_node = ImageClassificationNode(adapter=efficientnet_adapter)
overall_analysis_node = OverallAnalysisNode(adapter=local_adapter)
healthcare_recommendation_node = HealthcareRecommendationNode(
    adapter=local_adapter,
    google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY")
)
medical_report_node = MedicalReportNode(adapter=local_adapter) 

#State graph creation
workflow = StateGraph(AgentState)

#Add callable nodes
workflow.add_node("llm_diagnosis", llm_diagnosis_node)
workflow.add_node("followup_interaction", followup_interaction_node)
workflow.add_node("image_analysis", image_classification_node)
workflow.add_node("overall_analysis_step", overall_analysis_node)
workflow.add_node("healthcare_recommendation_step", healthcare_recommendation_node)
workflow.add_node("generate_report", medical_report_node)

# Set entry point
workflow.set_entry_point("llm_diagnosis")

# Update routing functions to include healthcare recommendation
def route_after_llm_diagnosis(state: AgentState) -> str:
    """Route after initial LLM diagnosis - simplified routing logic"""
    textual_analysis = state.get("textual_analysis", [])
    image_required = state.get("image_required", False)
    
    CONFIDENCE_THRESHOLD = 0.6
    # Calculate average confidence from all diagnoses
    if textual_analysis and isinstance(textual_analysis, list):
        confidence_scores = [
            diagnosis.get("diagnosis_confidence", 0.0) 
            for diagnosis in textual_analysis
        ]
        average_confidence = sum(confidence_scores) / len(confidence_scores)
    else:
        average_confidence = 0.0
    
    state["average_confidence"] = average_confidence  # Store for later use
    state["workflow_path"] = [] #Track workflow path for overall analysis 
    
    print(f"🔍 Average confidence: {average_confidence:.2f} (from {len(textual_analysis)} diagnoses)")
    
    # Priority 1: Check if confidence is low -> need follow-up questions
    if average_confidence < CONFIDENCE_THRESHOLD:
        state["workflow_path"] = ["textual_to_followup"]
        print(f"📝 Low confidence ({average_confidence:.2f} < {CONFIDENCE_THRESHOLD}) - generating follow-up questions")
        return "followup_interaction"
    
    # Priority 2: Check if image is required
    if image_required:
        state["workflow_path"] = ["textual_to_image"]
        print("📸 Image required - routing to image analysis")
        return "image_analysis"
        
    # Priority 3: Go directly to overall analysis for high-confidence text-only cases
    state["workflow_path"] = ["textual_only"]
    print("📋 High confidence - routing to overall analysis")
    return "overall_analysis_step"

def route_after_followup_interaction(state: AgentState) -> str:
    """Route after follow-up interaction - simplified routing logic"""
    followup_response = state.get("followup_response", {})
    
    if state.get("requires_user_input", False) and not followup_response:
        # First time - waiting for input
        print("⏸️ Waiting for user input - pausing workflow")
        return END
    elif followup_response and state.get("requires_user_input", False):
        # We have responses - continue to process them
        print("🔄 Processing user responses")
        return "followup_interaction"  # Call the node again for processing responses

    # Check if image is required after follow-up
    image_required = state.get("image_required", False)
    workflow_path = state.get("workflow_path", [])
    
    if image_required:
        # **WORKFLOW INSTANCE 4: Textual -> Follow-up -> Image**
        workflow_path.append("followup_to_image")
        state["workflow_path"] = workflow_path
        print("📸 Follow-up completed - routing to image analysis")
        return "image_analysis"
    else:
        # **WORKFLOW INSTANCE 3: Textual -> Follow-up Only**
        workflow_path.append("followup_only")
        state["workflow_path"] = workflow_path
        print("📋 Follow-up completed - routing to overall analysis")
        return "overall_analysis_step"

# Update workflow routing
workflow.add_conditional_edges(
    "llm_diagnosis",
    route_after_llm_diagnosis,
    {
        "followup_interaction": "followup_interaction",
        "image_analysis": "image_analysis", 
        "overall_analysis_step": "overall_analysis_step",  
    }
)

workflow.add_conditional_edges(
    "followup_interaction",
    route_after_followup_interaction,
    {
        "followup_interaction": "followup_interaction",  # Loop back for processing responses
        "image_analysis": "image_analysis",
        "overall_analysis_step": "overall_analysis_step",  
        END: END
    }
)

workflow.add_edge("image_analysis", "overall_analysis_step")
workflow.add_edge("overall_analysis_step", "healthcare_recommendation_step")
workflow.add_edge("healthcare_recommendation_step", "generate_report")
workflow.add_edge("generate_report", END) 

# Compile the workflow
patient_app = workflow.compile()

print("Patient workflow graph compiled successfully!")