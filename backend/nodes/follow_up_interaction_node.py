import os
from typing import Any
import re
import logging
from llm.client import llm_client

logger = logging.getLogger(__name__)

# ── Follow-up question mode ───────────────────────────────────────────────
# "personalized" → AI generates questions from the symptoms + differential.
# "general"      → a fixed, condition-agnostic question set is always used.
# Flip the default below, or override without touching code by setting the
# FOLLOWUP_QUESTION_MODE environment variable (e.g. in backend/.env).
QUESTION_MODE = os.getenv("FOLLOWUP_QUESTION_MODE", "general").lower()
# ──────────────────────────────────────────────────────────────────────────


class FollowUpInteractionNode:
    """Symptom-text follow-up: generates personalized questions from the current
    differential, then re-diagnoses using the patient's answers."""

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        # The graph drives the two phases directly via wrapper nodes; this entry
        # point picks the phase based on whether answers are already present.
        followup_response = state.get("followup_response", {})
        if followup_response and not state.get("requires_user_input", True):
            return await self._process_responses_phase(state, followup_response)
        return await self._generate_questions_phase(state)

    async def _generate_questions_phase(self, state: dict[str, Any]) -> dict[str, Any]:
        """Select follow-up questions per QUESTION_MODE, then await the answers."""
        if QUESTION_MODE == "general":
            questions = self._get_general_questions()
        else:
            questions = await self._generate_personalized_questions(state)
            if not questions:  # generation failed — fall back to the general set
                questions = self._get_general_questions()

        state["followup_questions"] = questions[:5]
        state["followup_type"] = "standard"
        state["requires_user_input"] = True
        state["current_workflow_stage"] = "awaiting_followup_responses"
        return state

    async def _generate_personalized_questions(self, state: dict[str, Any]) -> list[str]:
        """Generate questions tailored to the symptoms + current differential."""
        symptoms = state.get("userInput_symptoms", "") or state.get("latest_user_message", "")
        differential = state.get("textual_analysis", []) or []
        dx_list = ", ".join(
            d.get("text_diagnosis", "") for d in differential if d.get("text_diagnosis")
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical assistant conducting a focused follow-up. "
                    "Generate concise, clinically relevant questions that help distinguish "
                    "between the candidate diagnoses and clarify the patient's presentation. "
                    "Target onset, duration, severity, character, aggravating and relieving "
                    "factors, and red-flag symptoms specific to the suspected conditions."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Patient's reported symptoms: {symptoms}\n"
                    f"Current differential diagnoses: {dx_list or 'undetermined'}\n\n"
                    "Generate exactly 5 follow-up questions, personalized to the symptoms and "
                    "differential above, that would most improve diagnostic confidence. "
                    "Output ONLY a numbered list, one question per line, with no preamble."
                ),
            },
        ]

        try:
            output = await llm_client.complete(messages, max_tokens=300, temperature=0.3)
            return self._parse_questions(output)
        except Exception as e:
            logger.error(f"Follow-up question generation failed: {e}")
            return []

    async def _process_responses_phase(
        self, state: dict[str, Any], responses: dict[str, str]
    ) -> dict[str, Any]:
        """Re-diagnose using the original symptoms enriched with follow-up answers."""
        original_symptoms = state.get("userInput_symptoms", "") or state.get("latest_user_message", "")
        enhanced_symptoms = self._combine_symptoms_and_responses(original_symptoms, responses)

        state["followup_responses"] = responses
        state["followup_qna_overall"] = enhanced_symptoms
        state["requires_user_input"] = False

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
                    f"Symptoms and follow-up answers:\n{enhanced_symptoms}\n\n"
                    "List the 5 most likely diagnoses in this exact format ONLY:\n"
                    "- Diagnosis: <name>\n"
                    "- Confidence: <0.0-1.0>\n\n"
                    "Repeat for each diagnosis. List from most likely to least likely."
                ),
            },
        ]
        output = await llm_client.complete(messages, max_tokens=300, temperature=0.1)

        from nodes.llm_diagnosis_node import parse_diagnosis_details
        diagnosis_results = parse_diagnosis_details(output)
        state["followup_diagnosis"] = diagnosis_results

        confidences = [d.get("diagnosis_confidence", 0.0) for d in diagnosis_results]
        state["average_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0

        # Mark the follow-up path so overall analysis uses the enriched diagnosis.
        workflow_path = state.get("workflow_path", [])
        if "followup_only" not in workflow_path:
            workflow_path.append("followup_only")
        state["workflow_path"] = workflow_path

        state["current_workflow_stage"] = "followup_analysis_complete"
        logger.info(f"Follow-up diagnosis complete - found {len(diagnosis_results)} diagnoses")
        return state

    def _combine_symptoms_and_responses(
        self, original_symptoms: str, responses: dict[str, str]
    ) -> str:
        """Combine original symptoms with follow-up Q&A pairs for re-analysis."""
        combined = f"Initial user symptom input: {original_symptoms}\n\nFollow-up information:\n"
        for question, response in responses.items():
            combined += f"Q: {question}\nA: {response}\n\n"
        return combined.strip()

    def _parse_questions(self, questions_text: str) -> list[str]:
        """Parse a numbered/bulleted list of questions from the LLM response."""
        questions = []
        for line in questions_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() or line.startswith(("-", "•", "*")):
                question = re.sub(r"^\s*\d+[\.\)]\s*", "", line)  # "1. " / "1) "
                question = re.sub(r"^[-•*]\s*", "", question)      # "- " / "• " / "* "
                if question:
                    questions.append(question)
        return questions

    def _get_general_questions(self) -> list[str]:
        """Fixed, condition-agnostic questions (used in general mode and as fallback)."""
        return [
            "How long have you been experiencing these symptoms?",
            "Have the symptoms gotten worse, better, or stayed the same since they started?",
            "On a scale of 0–10, how severe are your symptoms right now?",
            "Have you noticed anything that makes them better or worse?",
            "Do you have any other symptoms, relevant medical history, or current medications?",
        ]
