from __future__ import annotations

import logging
import re

from llm.client import llm_client

logger = logging.getLogger(__name__)

_VALID_SEVERITY = {"mild", "moderate", "severe", "critical"}

_SYSTEM = (
    "You are an AI medical assistant. Follow the requested format exactly. "
    "Be concise and professional."
)


class SummaryNode:
    """Severity, specialist and a plain-language explanation.

    Emits no confidence value. The explanation itself is Node A's own
    ungrounded definition of the top candidate, reused from state -- see
    DifferentialNode. The specialist recommendation is judged against the
    whole differential (every ranked candidate, not just the top one), and
    defaults to a general practitioner unless the differential clearly needs
    more -- a specific specialist for every ranked condition is the kind of
    textbook-correct-but-impractical answer (e.g. neurology for migraine)
    that a first-line GP visit would actually triage.
    """

    async def __call__(self, state: dict) -> dict:
        ranking = state.get("ranking") or []
        if not ranking or not ranking[0]:
            state["summary"] = None
            state["stage"] = "complete"
            return state

        top = ranking[0][0]
        all_candidates = [name for group in ranking for name in group]
        summary: dict = {"severity": "unknown", "specialist_recommendation": "general_practitioner"}

        try:
            messages = [
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Conditions under consideration, most to least supported: "
                        f"{', '.join(all_candidates)}\n"
                        f"Patient information: {state.get('patient_text', '')}\n\n"
                        "Respond in this EXACT format:\n"
                        "- Severity: <mild/moderate/severe/critical>\n"
                        "- Specialist: <the type of doctor the patient should see first>\n\n"
                        "For Specialist: default to \"General practitioner\". Most "
                        "presentations, including recurring or chronic ones like "
                        "migraine, are correctly triaged by a GP first, who refers "
                        "onward if needed. Only name a specific specialist if the "
                        "differential above would clearly bypass a GP regardless of "
                        "which candidate turns out correct, or severity is severe or "
                        "critical."
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

        # DifferentialNode already generated this candidate's definition
        # earlier in the pipeline -- reuse it instead of a second LLM call.
        explanation = (state.get("explanations") or {}).get(top)
        if explanation is not None:
            summary["user_explanation"] = explanation.text
            summary["explanation_source"] = explanation.source
            summary["explanation_url"] = explanation.url

        state["summary"] = summary
        state["stage"] = "complete"
        return state
