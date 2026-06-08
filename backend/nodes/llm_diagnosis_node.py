from typing import TypedDict, Tuple
import re
from adapters.local_model_adapter4 import LocalModelAdapter
from schemas.medical_schemas import TextualSymptomAnalysisResult

def parse_diagnosis_details(raw_response: str) -> list[TextualSymptomAnalysisResult]:
    results: list[TextualSymptomAnalysisResult] = []
    
    # --- Extract Each Diagnosis Block ---
    diagnosis_pattern = re.compile(
        r"-\s*Diagnosis:\s*(.*?)\s*"
        r"-\s*Confidence:\s*([0-9.]+)\s*",

        re.IGNORECASE | re.DOTALL
    )

    for match in diagnosis_pattern.finditer(raw_response):
        diagnosis, confidence = match.groups()
        result: TextualSymptomAnalysisResult = {
            "text_diagnosis": diagnosis.strip(),
            "diagnosis_confidence": float(confidence.strip()),
        }
        results.append(result)
        
    results.sort(key=lambda x: x["diagnosis_confidence"], reverse=True)

    return results

class LLMDiagnosisNode:
    def __init__(self, adapter: LocalModelAdapter):
        self.adapter = adapter 
    
    async def __call__(self, state:dict) -> dict:
        state["current_workflow_stage"] = "textual_analysis"
        
        print("🩺 LLM DIAGNOSIS NODE CALLED!")
        print(f"    Input: {state.get('latest_user_message', 'NO MESSAGE')}")
        
        # Process the diagnosis
        state = await self.diagnose(state)
        
        # Workflow path set based on logic
        workflow_path = []
        
        #Determine initial path 
        if state.get("image_required", False):
            workflow_path.append("textual_to_image")
        else:
            workflow_path.append("textual_only")
        
        state["workflow_path"] = workflow_path
        
        print(f"✅ LLM Diagnosis complete - found {len(state.get('textual_analysis', []))} diagnoses")
        
        return state
        
    async def diagnose(self, state:dict) -> dict:
        # Directly use the text since validation was done upstream.'
        text = state.get("latest_user_message", "")
        
        # Pre-filter for skin conditions
        skin_cancer_keywords = [
            'mole', 'lesion', 'growth', 'bump', 'spot', 'rash', 'patch', 'scab',
            'discoloration', 'freckle', 'birthmark', 'wart', 'cyst', 'lump',
            'melanoma', 'cancer', 'tumor', 'nevus', 'seborrheic', 'keratosis'
        ]
        
        general_skin_keywords = [
            'skin', 'dermatitis', 'eczema', 'psoriasis', 'acne', 'hives',
            'rosacea', 'fungal', 'bacterial', 'viral', 'infection'
        ]
        
        # Check for skin cancer specific symptoms
        has_skin_cancer_indicators = any(keyword in text.lower() for keyword in skin_cancer_keywords)
        has_general_skin_symptoms = any(keyword in text.lower() for keyword in general_skin_keywords)
        
        if has_skin_cancer_indicators or has_general_skin_symptoms:
            state["userInput_skin_symptoms"] = text
            state["requires_skin_cancer_screening"] = True

            placeholder_skin_diagnoses = [
                {"text_diagnosis": "Possible Skin Cancer Condition (Further Evaluation Required)", "diagnosis_confidence": None},
            ]
            
            state["textual_analysis"] = placeholder_skin_diagnoses
            state["average_confidence"] = 0.0
            
            return state
        else:
            state["userInput_symptoms"] = text # Store user input (non-skin symptoms) to be used later with textual_analysis for overall analysis
            state["requires_skin_cancer_screening"] = False

            # Get Q8 model for diagnosis
            output = await self.adapter.generate_diagnosis(text)
            
            #parse multiple diagnoses
            parsed_diagnosis = parse_diagnosis_details(output)
            
            #Save list to the agent state
            state["textual_analysis"] = parsed_diagnosis
            #Save bool to indicate if image is required
            state["image_required"] = False 

            return state