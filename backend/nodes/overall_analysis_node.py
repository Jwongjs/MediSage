from typing import Dict, Any
import re
from llm.client import llm_client

_SYSTEM_PROMPT = (
    "You are an AI medical assistant. Provide accurate, structured responses. "
    "Always follow the exact format requested. Be concise and professional."
)


class OverallAnalysisNode:
    async def __call__(self, state):
        print("OVERALL ANALYSIS NODE CALLED!")
        state["current_workflow_stage"] = "performing_overall_analysis"
        
        state = await self.perform_overall_analysis(state)
        
        state["current_workflow_stage"] = "overall_analysis_complete"
        return state
    
    async def perform_overall_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            workflow_path = state.get("workflow_path", [])
            print(f"WORKFLOW PATH: {workflow_path}")

            if workflow_path == ["textual_only"]:
                enhanced_analysis = await self._analyze_textual_only(state)
            elif (
                "followup_only" in workflow_path
                or "skin_to_standard_followup" in workflow_path
                or "skin_cancer_high_risk" in workflow_path
            ):
                enhanced_analysis = await self._analyze_textual_and_followup(state)
            else:
                enhanced_analysis = await self._analyze_fallback(state)

            state["overall_analysis"] = enhanced_analysis
            print(f"Overall analysis complete: {enhanced_analysis.get('final_diagnosis', 'Unknown')}")
            return state

        except Exception as e:
            print(f"Overall analysis error: {e}")
            state["overall_analysis"] = self._fallback_analysis(state)
            return state
    
    async def _analyze_textual_only(self, state: Dict[str, Any]) -> Dict[str, Any]:
        userInput_symptoms = state.get("userInput_symptoms", "")
        textual_analysis = state.get("textual_analysis", [])

        if not textual_analysis:
            raise ValueError("No textual analysis available")

        primary_diagnosis = textual_analysis[0]
        diagnosis = primary_diagnosis.get("text_diagnosis", "Unknown")
        confidence = primary_diagnosis.get("diagnosis_confidence", 0.0) or 0.0

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"MEDICAL ANALYSIS\n\n"
                    f"CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})\n"
                    f"Original Symptoms: {userInput_symptoms}\n\n"
                    f"Provide output in this EXACT format:\n"
                    f"- Severity: <mild/moderate/severe/critical>\n"
                    f"- User Explanation: <Simple definition of {diagnosis} and its main causes>\n"
                    f"- Clinical Reasoning: <detailed medical justification>\n"
                    f"- Specialist: <most appropriate specialist type>\n\n"
                    f"Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words."
                ),
            },
        ]

        assessment_text = await llm_client.complete(messages, max_tokens=400, temperature=0.3)
        return self._parse_enhanced_analysis(assessment_text, primary_diagnosis)
    
    async def _analyze_textual_and_followup(self, state: Dict[str, Any]) -> Dict[str, Any]:
        followup_qna = state.get("followup_qna_overall", "")
        followup_diagnosis = state.get("followup_diagnosis", [])

        if not followup_diagnosis:
            raise ValueError("No follow-up diagnosis available")

        enhanced_diagnosis = followup_diagnosis[0]
        diagnosis = enhanced_diagnosis.get("text_diagnosis", "Unknown")
        confidence = enhanced_diagnosis.get("diagnosis_confidence", 0.0) or 0.0

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"ENHANCED MEDICAL ANALYSIS\n\n"
                    f"Follow-up Information:\n{followup_qna}\n\n"
                    f"CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})\n\n"
                    f"Provide output in this EXACT format:\n"
                    f"- Severity: <mild/moderate/severe/critical>\n"
                    f"- User Explanation: <Simple definition of {diagnosis} and its main causes>\n"
                    f"- Clinical Reasoning: <detailed medical justification>\n"
                    f"- Specialist: <most appropriate specialist type>\n\n"
                    f"Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words."
                ),
            },
        ]

        assessment_text = await llm_client.complete(messages, max_tokens=400, temperature=0.3)
        return self._parse_enhanced_analysis(assessment_text, enhanced_diagnosis)
    
    def _parse_enhanced_analysis(self, assessment_text: str, primary_diagnosis: dict) -> Dict[str, Any]:
        severity_match = re.search(r"-\s*Severity:\s*(.+)", assessment_text, re.IGNORECASE)
        explanation_match = re.search(
            r"-\s*User Explanation:\s*(.+?)(?:\n-|\Z)", assessment_text, re.IGNORECASE | re.DOTALL
        )
        reasoning_match = re.search(
            r"-\s*Clinical Reasoning:\s*(.+?)(?:\n-|\Z)", assessment_text, re.IGNORECASE | re.DOTALL
        )
        specialist_match = re.search(r"-\s*Specialist:\s*(.+)", assessment_text, re.IGNORECASE)

        severity = severity_match.group(1).strip() if severity_match else "moderate"
        user_explanation = explanation_match.group(1).strip() if explanation_match else "Analysis completed."
        clinical_reasoning = reasoning_match.group(1).strip() if reasoning_match else "Systematic analysis performed."
        specialist = specialist_match.group(1).strip() if specialist_match else "general_practitioner"

        if severity.lower() not in {"mild", "moderate", "severe", "critical"}:
            severity = "moderate"

        return {
            "final_diagnosis": primary_diagnosis.get("text_diagnosis", "Unknown"),
            "final_confidence": primary_diagnosis.get("diagnosis_confidence", 0.0) or 0.0,
            "final_severity": severity.lower(),
            "user_explanation": user_explanation,
            "clinical_reasoning": clinical_reasoning,
            "specialist_recommendation": specialist,
        }
        
    async def _analyze_fallback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        textual_analysis = state.get("textual_analysis", [])
        primary = textual_analysis[0] if textual_analysis else {
            "text_diagnosis": "Unknown", "diagnosis_confidence": 0.0
        }
        return {
            "final_diagnosis": primary.get("text_diagnosis", "Unknown"),
            "final_confidence": primary.get("diagnosis_confidence", 0.0) or 0.0,
            "final_severity": "moderate",
            "user_explanation": "Analysis completed based on available symptom data.",
            "clinical_reasoning": "Systematic symptom analysis performed.",
            "specialist_recommendation": "general_practitioner",
        }

    def _fallback_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        textual_analysis = state.get("textual_analysis", [])
        primary = textual_analysis[0] if textual_analysis else {}
        return {
            "final_diagnosis": primary.get("text_diagnosis", "Analysis incomplete"),
            "final_confidence": 0.0,
            "final_severity": "moderate",
            "user_explanation": "Unable to complete full analysis.",
            "clinical_reasoning": "Analysis encountered an error.",
            "specialist_recommendation": "general_practitioner",
        }