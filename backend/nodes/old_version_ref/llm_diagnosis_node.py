from typing import List, TypedDict, Tuple
import re
# from models.ai_schema import SymptomAnalysis  # We still use this to define and validate the output schema
from backend.adapters.old_version_reference.local_model_adapter import LocalModelAdapter
from schemas.medical_schemas import TextualSymptomAnalysisResult

import re
from typing import List, TypedDict

def parse_diagnosis_details(raw_response: str) -> Tuple[bool, List[TextualSymptomAnalysisResult]]:
    results: List[TextualSymptomAnalysisResult] = []

    # --- STEP 1: Parse ImageRequired ---
    image_required_match = re.search(r'ImageRequired\s*[:\-]?\s*(Yes|No)', raw_response, re.IGNORECASE)
    image_required = True  # default
    if image_required_match:
        image_required = image_required_match.group(1).strip().lower() == 'yes'

    # --- STEP 2: Extract Each Diagnosis Block ---
    diagnosis_pattern = re.compile(
        r"(?:[-*]?\s*)?Diagnosis:\s*(.*?)\s*"
        r"(?:[-*]?\s*)?Reasoning:\s*(.*?)\s*"
        r"(?:[-*]?\s*)?Confidence:\s*([0-9.]+)\s*"
        r"(?:[-*]?\s*)?Severity:\s*(.*?)(?=\s*-\s*Diagnosis|\s*$)",
        re.IGNORECASE | re.DOTALL
    )

    for match in diagnosis_pattern.finditer(raw_response):
        diagnosis, reasoning, confidence, severity = match.groups()
        result: TextualSymptomAnalysisResult = {
            "text_diagnosis": diagnosis.strip(),
            "reasoning": reasoning.strip(),
            "diagnosis_confidence": float(confidence.strip()),
            "severity": severity.strip().lower()
        }
        results.append(result)

    return image_required, results

class LLMDiagnosisNode:
    def __init__(self, adapter: LocalModelAdapter):
        self.adapter = adapter
    
    async def __call__(self, state:dict) -> dict:
        return await self.diagnose(state)
        
    async def diagnose(self, state:dict) -> dict:
        # Directly use the text since validation was done upstream.'
        text = state['latest_user_message']
        output = await self.adapter.generate_diagnosis(text)
        
        #parse multiple diagnoses
        image_required, parsed_diagnosis = parse_diagnosis_details(output)
        
        #Save list to the agent state
        state["textual_analysis"] = parsed_diagnosis
        #Save bool to indicate if image is required
        state["image_required"] = image_required
        return state
    