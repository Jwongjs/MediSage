from __future__ import annotations

import logging
import re

from knowledge.interface import get_consumer_explanation
from llm.client import llm_client

logger = logging.getLogger(__name__)

_VALID_SEVERITY = {"mild", "moderate", "severe", "critical"}

_SYSTEM = (
    "You are an AI medical assistant. Follow the requested format exactly. "
    "Be concise and professional."
)


class SummaryNode:
    """Severity, specialist and a cited plain-language explanation.

    Emits no confidence value. The explanation comes from an authoritative
    source or is omitted — it is never model-generated.
    """

    async def __call__(self, state: dict) -> dict:
        ranking = state.get("ranking") or []
        if not ranking or not ranking[0]:
            state["summary"] = None
            state["stage"] = "complete"
            return state

        top = ranking[0][0]
        summary: dict = {"severity": "unknown", "specialist_recommendation": "general_practitioner"}

        try:
            messages = [
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Condition under consideration: {top}\n"
                        f"Patient information: {state.get('patient_text', '')}\n\n"
                        "Respond in this EXACT format:\n"
                        "- Severity: <mild/moderate/severe/critical>\n"
                        "- Specialist: <most appropriate specialist type>"
                    ),
                },
            ]
            raw = await llm_client.complete(messages, max_tokens=120, temperature=0.2)

            sev = re.search(r"-\s*Severity:\s*(\w+)", raw, re.IGNORECASE)
            spec = re.search(r"-\s*Specialist:\s*(.+)", raw, re.IGNORECASE)
            if sev and sev.group(1).lower() in _VALID_SEVERITY:
                summary["severity"] = sev.group(1).lower()
            else:
                # Fail toward caution, never toward reassurance. An unparseable
                # severity is surfaced as unknown rather than invented as mild.
                summary["severity"] = "unknown"
            if spec:
                summary["specialist_recommendation"] = spec.group(1).strip()
        except Exception as exc:
            logger.error("Summary generation failed: %s", exc)

        explanation = await get_consumer_explanation(top)
        if explanation is not None:
            summary["user_explanation"] = explanation.text
            summary["explanation_source"] = explanation.source
            summary["explanation_url"] = explanation.url

        state["summary"] = summary
        state["stage"] = "complete"
        return state
