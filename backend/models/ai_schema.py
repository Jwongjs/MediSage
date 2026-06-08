import httpx
from pydantic_ai import AIModel 
from typing import Optional 
from pydantic import BaseModel, Field, conlist, constr, conint, validator

class SymptomInput(AIModel):
    text: str
    image: Optional[bytes] = Field(default=None, description="Base64 encoded image of the symptoms (optional).")
    
class SymptomAnalysis(AIModel):
    diagnosis: str = Field(description="Diagnosis based on symptoms.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    severity: Optional[str] = Field(description="Estimated severity level, e.g., 'low', 'moderate', or 'high'.")

class SelfCareAdvice(AIModel):
    sufficient: bool = Field(description="Is self-care sufficient for the diagnosed condition?")
    advice: str = Field(description="Self-care advice if applicable.")

class SpecialistRecommendation(AIModel):
    specialist: str = Field(description="Recommended type of doctor or specialist.")
    reason: str = Field(description="Why this specialist is recommended.")
    urgency: Optional[str] = Field(description="Urgency level for seeing the specialist, e.g., 'immediate', 'within a week', etc.")

class MedicalReport(AIModel):
    symptoms: str
    diagnosis: str
    confidence: float
    severity: str
    treatment: str
    recommendation: Optional[str] = None

class SessionEndCheck(AIModel):
    end_session: bool = Field(description="Flag to determine if the session should be ended.")
    reason: Optional[str] = Field(description="Reason for ending the session (e.g., diagnosis complete, referral given).")
