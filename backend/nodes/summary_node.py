from __future__ import annotations

import logging
import re

from config import settings
from llm.client import LLMClient

# Own model, own Groq rate-limit bucket. Must be non-reasoning: the budget is
# 120 tokens and the reply is read by two regexes, so hidden reasoning would
# eat the whole allowance, both regexes would miss, and severity would fall
# back to "unknown" every run -- a silent failure, not a raised one.
llm_client = LLMClient(model=settings.SUMMARY_LLM_MODEL)

logger = logging.getLogger(__name__)

_VALID_SEVERITY = {"mild", "moderate", "severe", "critical"}

# An angle-bracketed span is a template slot the model copied instead of
# filling in. No real specialist name contains one, so this is safe to
# reject outright rather than trying to repair.
_PLACEHOLDER_RE = re.compile(r"[<>]")

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
    that a first-line GP visit would actually triage. For mild and moderate
    severity, the GP is paired with the specialist the leading condition
    would correspond to, rather than the specialist being withheld until
    referral; severe/critical or a differential that would clearly bypass a
    GP regardless of which candidate is correct still names the specialist
    alone.
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
                        "Respond in this EXACT format, replacing each placeholder:\n"
                        "- Severity: one of mild, moderate, severe, critical\n"
                        "- Specialist: <name the type of doctor to see first>\n\n"
                        "Specialist selection rules:\n"
                        "1. If severity is severe or critical, name only the most appropriate specialist or emergency-care pathway.\n"
                        "2. If severity is mild or moderate, name \"General practitioner\" followed by the relevant specialist in parentheses when a specialist is reasonably indicated. Example: \"General practitioner (Dermatologist if it persists)\".\n"
                        "3. If no specific specialist is clearly indicated, use \"General practitioner\".\n"
                        "4. Do not recommend a specialist solely because one of the differential conditions is associated with that specialty; consider the patient's actual presentation.\n\n"

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
                # Validated, not trusted -- the way severity is checked against
                # _VALID_SEVERITY above. This capture is ".+", so it takes
                # whatever follows the label, including the prompt's own
                # placeholder echoed back unfilled. Not hypothetical: that
                # reached the report page as the literal text
                # "<the type of doctor the patient should see first>". A
                # specialist cannot be whitelisted the way severity can, so the
                # test is for the shape of an unfilled slot instead.
                candidate = spec.group(1).strip()
                if candidate and not _PLACEHOLDER_RE.search(candidate):
                    summary["specialist_recommendation"] = candidate
                else:
                    logger.warning(
                        "Summary specialist unusable (%r), keeping default",
                        candidate,
                    )
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
