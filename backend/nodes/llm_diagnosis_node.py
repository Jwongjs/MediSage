from typing import TypedDict
import re
from schemas.medical_schemas import TextualSymptomAnalysisResult
from llm.client import llm_client


def parse_diagnosis_details(raw_response: str) -> list[TextualSymptomAnalysisResult]:
    results: list[TextualSymptomAnalysisResult] = []

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
    async def __call__(self, state: dict) -> dict:
        state["current_workflow_stage"] = "textual_analysis"
        print("Diagnosis NODE CALLED!")
        msg = state.get('latest_user_message', 'NO MESSAGE')
        print(f"    Input: {msg}")

        state = await self.diagnose(state)

        workflow_path = []
        workflow_path.append("textual_only")
        state["workflow_path"] = workflow_path

        analysis = state.get('textual_analysis', [])
        print(f"Diagnosis complete - found {len(analysis)} diagnoses")
        return state

    async def diagnose(self, state: dict) -> dict:
        text = state.get("latest_user_message", "")

        skin_cancer_keywords = [
            "mole", "lesion", "growth", "bump", "spot", "rash", "patch", "scab",
            "discoloration", "freckle", "birthmark", "wart", "cyst", "lump",
            "melanoma", "cancer", "tumor", "nevus", "seborrheic", "keratosis"
        ]
        general_skin_keywords = [
            "skin", "dermatitis", "eczema", "psoriasis", "acne", "hives",
            "rosacea", "fungal", "bacterial", "viral", "infection"
        ]

        has_skin_cancer_indicators = any(kw in text.lower() for kw in skin_cancer_keywords)
        has_general_skin_symptoms = any(kw in text.lower() for kw in general_skin_keywords)

        if has_skin_cancer_indicators or has_general_skin_symptoms:
            state["userInput_skin_symptoms"] = text
            state["requires_skin_cancer_screening"] = True
            state["textual_analysis"] = [
                {"text_diagnosis": "Possible Skin Condition (Further Evaluation Required)", "diagnosis_confidence": None}
            ]
            state["average_confidence"] = 0.0
            return state

        state["userInput_symptoms"] = text
        state["requires_skin_cancer_screening"] = False

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical assistant. Provide accurate, structured responses. "
                    "Always follow the exact format requested. Be concise and professional."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Symptoms: {text}\n"
                    "List 5 most possible diagnoses in this exact format ONLY:\n"
                    "- Diagnosis: <name>\n"
                    "- Confidence: <0.0-1.0>\n\n"
                    "Repeat for each diagnosis. List from most likely to least likely."
                ),
            },
        ]

        output = await llm_client.complete(messages, max_tokens=300, temperature=0.1)
        parsed_diagnosis = parse_diagnosis_details(output)

        state["textual_analysis"] = parsed_diagnosis
        state["image_required"] = False
        return state
