from typing_extensions import TypedDict, Literal
from typing import Optional, List, Dict, Union, Any

# Workflow stage enum for type safety
WorkflowStage = Literal[
    # Initial stages
    "initial",
    "textual_analysis", 
    "textual_analysis_complete",
    
    # Follow-up flow
    "generating_followup_questions",
    "awaiting_followup_responses", 
    "processing_followup_responses",
    "followup_analysis_complete",
    
    # Image flow
    "awaiting_image_upload",
    "analyzing_image",
    "image_analysis_complete",
    
    # Analysis flow
    "performing_overall_analysis",
    "overall_analysis_complete",
    
    # Final stages
    "generating_healthcare_recommendations",
    "healthcare_recommendation_complete",
    "generating_medical_report",
    "workflow_complete"
]

# Workflow action types
WorkflowAction = Literal[
    "none",                    # No action needed
    "user_input_required",     # Need user input (questions/image)
    "auto_continue",          # Automatically continue to next step
    "workflow_complete"       # Workflow finished
]

WorkflowPathType = Literal[
    "textual_only",           # Instance 1: Direct textual analysis
    "textual_to_image",       # Instance 2: Textual -> Image
    "textual_to_skin_screening",   # Instance 2: Textual -> Skin Cancer Screening -> Image
    "skin_to_image_analysis",  # Instance 2: Skin screening -> Image analysis
    "textual_to_followup",    # Instance 3 & 4: Textual -> Follow-up (start)
    "followup_only",          # Instance 3: Follow-up -> Overall analysis
    "skin_to_standard_followup" # Instance 3: Skin screening -> Standard follow-up (negative assessment on skin cancer)
]

class WorkflowInfo(TypedDict, total=False):
    current_stage: WorkflowStage
    ui_component: str  # Backend tells frontend which component to render
    next_endpoint: str | None
    needs_user_input: Literal["followup_questions", "image_upload"] | None
    auto_continue: bool
    show_continue_button: bool
    progress_percentage: int
    stage_description: str
    workflow_complete: bool

#Minimal schema on purpose during early stages to enable lazy loading for performance(without reasoning/severity)
class TextualSymptomAnalysisResult(TypedDict):
    text_diagnosis: str
    diagnosis_confidence: float
    
class SkinLesionImageAnalysisResult(TypedDict):
    image_diagnosis: str | None
    confidence_score: Union[dict[str, float]] | None
    
class OverallAnalysisResult(TypedDict):
    final_diagnosis: str
    final_confidence: float
    final_severity: str                     # mild/moderate/severe/critical/emergency

    user_explanation: str           # Simple explanation for patients (low health literacy)
    clinical_reasoning: str         # Technical LLM justification with factors
    
    specialist_recommendation: str
    
# class HealthcareRecommendationResult(TypedDict):
#     recommendation_type: str              
#     self_care_advice: Optional[List[str]]
#     specialist_type: Optional[str] 
#     nearby_facilities: Optional[List[Dict[str, Any]]]  
#     facility_search_radius: Optional[str]  
#     emergency_contacts: Optional[List[Dict[str, str]]]  
#     appointment_urgency: Optional[str]     
#     insurance_guidance: Optional[List[str]] 
#     rag_evidence: Optional[List[str]]
#     telemedicine_options: Optional[List[Dict[str, Any]]] 
#     cost_estimates: Optional[Dict[str, str]]

class AgentState(TypedDict, total=False):
    session_id: str #Unique ID for session
    workflow: WorkflowInfo #Unified worfklow info- single source of truth
    current_workflow_stage: str | None
    
    #Data tracking
    image_required: bool
    requires_skin_cancer_screening: bool | None  # Flag for skin cancer screening
    workflow_path: list[WorkflowPathType] | None
    average_confidence: float | None # Average confidence score across all diagnoses for textual analysis and follow-up diagnosis

    
    #STAGE 1: Textual Symptom Analysis 
    userInput_symptoms: str | None #Used to store user input of their symptoms to be used as a value with textual_analysis for overall analysis
    textual_analysis: list[TextualSymptomAnalysisResult] | None 

    #Follow-up stage (if required based on confidence)
    followup_type: Literal["standard", "skin_cancer_screening"] | None
    requires_user_input: bool | None # Indicates if user input is required for follow-up questions
    followup_questions: list[str] | None
    followup_response: dict[str, str] | None # Follow-up responses from user
    followup_qna_overall: str | None # Combined Q&A pairs from follow-up interaction
    followup_diagnosis: list[TextualSymptomAnalysisResult] |  None
    skin_cancer_risk_detected: bool | None # Result of skin cancer risk analysis
    
    skin_cancer_risk_metrics: dict[str, Any] | None  # Detailed ABCDE scoring and risk analysis

    #STAGE 2: Skin LesionImage Analysis (Optional)
    userInput_skin_symptoms: str | None #Used to store user input of their skin symptoms to be used as a value with skin_lesion_analysis for overall analysis (if image_required is True)
    skin_cancer_screening_responses: str | None # Used for instance 4 (overall analysis) when followup_qna_overall and skin screening questions are needed to be used
    image_input: str | None # Stores uploaded image in the form of file path, base64, or raw bytes
    skin_lesion_analysis: SkinLesionImageAnalysisResult | None

    #STAGE 3: Overall Analysis
    overall_analysis: OverallAnalysisResult | None

    #STAGE 4: Healthcare Treatment Recommendation
    # healthcare_recommendation: Optional[HealthcareRecommendationResult] # Final recommendation based on analysis
    
    #FINAL STAGE: Medical Report Generation
    medical_report: str | None #Generated comprehensive medical report