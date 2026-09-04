from __future__ import annotations

import asyncio
import json
import logging
import re

from config import settings
from llm.client import LLMClient

# Own client, not the shared llm_client: gpt-oss-120b is a reasoning model
# that spends a variable, sometimes large share of its budget on hidden
# reasoning before any visible output, so it needs its own model choice and
# a generous max_tokens rather than sharing Node A/C/Summary's caps.
llm_client = LLMClient(model=settings.PROFILE_LLM_MODEL)

logger = logging.getLogger(__name__)

_IMPORTANCES = {"strong", "moderate", "weak"}
_KINDS = {"symptom", "history", "lab", "imaging", "demographic"}
# Only the kinds a patient can answer for themselves survive parsing. A lab or
# imaging criterion sits at not_mentioned forever -- nobody can self-report
# their own WBC count -- and ranking counts an unaddressed strong/moderate
# criterion against the condition, so keeping them would push lab-diagnosed
# conditions down for evidence the patient was never able to give. demographic
# goes with them: nothing in this flow collects age or sex. _KINDS stays whole
# so a rejected kind is recognised as itself instead of falling back to
# "symptom" and slipping through.
_KEPT_KINDS = {"symptom", "history"}

# Keyed on the normalised diagnosis name. A profile depends only on the
# condition, never on the patient, so it is safe to share across sessions.
_CACHE: dict[str, list[dict]] = {}

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)

_SYSTEM = (
    "You are a medical expert writing diagnostic criteria for a condition. "
    "Output valid JSON only. No prose before or after."
)


def clear_cache() -> None:
    _CACHE.clear()


def parse_profile(raw: str) -> list[dict]:
    fenced = _FENCE_RE.search(raw)
    payload = fenced.group(1) if fenced else raw
    start, end = payload.find("["), payload.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        entries = json.loads(payload[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Profile JSON did not parse")
        return []

    criteria = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        text = (entry.get("description") or "").strip()
        if not text:
            continue
        importance = entry.get("importance", "moderate")
        kind = entry.get("kind", "symptom")
        kind = kind if kind in _KINDS else "symptom"
        if kind not in _KEPT_KINDS:
            continue
        # Exclusion criteria are dropped for a reason Node C makes structural:
        # `supported` requires a verbatim quote from the patient, and an absence
        # cannot be quoted -- nobody writes "I have no nausea." So a negated
        # criterion can never be supported by the narrative, only sits at
        # not_mentioned, and drags the condition down through the same
        # strong/moderate penalty that unanswerable lab criteria did. It also
        # renders as a double negative: a checked "No nausea or vomiting" under
        # "Do you have these?" reads both ways. Node B is asked to LABEL these
        # rather than suppress them -- a model told not to write exclusion
        # criteria writes them anyway, just unlabelled and undetectable.
        if entry.get("polarity") == "absent":
            continue
        criteria.append({
            "text": text,
            "plain_label": (entry.get("plain_label") or "").strip(),
            "importance": importance if importance in _IMPORTANCES else "moderate",
            "kind": kind,
        })
    return criteria


async def _profile_for(diagnosis: str) -> list[dict]:
    cache_key = diagnosis.strip().lower()
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return [dict(c) for c in cached]

    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Condition: {diagnosis}\n\n"
                "Output the diagnostic criteria as a JSON array. Each element:\n"
                '{"id": <int>, "description": "<criterion, clinical language>", '
                '"plain_label": "<the SAME criterion in plain everyday words, '
                "max 6 words, for a patient with no medical background -- keep it "
                'as specific as the clinical version, do not generalize it away>", '
                '"importance": "strong|moderate|weak", '
                '"polarity": "present|absent", '
                '"kind": "symptom|history"}\n\n'
                "importance: strong = core criterion, absence severely impacts the "
                "diagnosis; moderate = important supportive criterion; weak = auxiliary.\n"
                "kind: symptom = something the patient notices and can report "
                "themselves, without a clinician examining them; history = past "
                "events or exposures.\n"
                "polarity: present = the criterion is met when the patient HAS the "
                "finding; absent = it is met when the patient does NOT have it, or "
                "when another disorder has been ruled out.\n"
                "Write only criteria the patient can answer for themselves."
                "this patient has no way to report them. Label polarity honestly "
                "instead of rewording a criterion to make it look positive.\n"
                'For a "symptom" entry, phrase "description" as the standard '
                "clinical term for the finding, the way it would appear in a "
                "differential-diagnosis note or a medical ontology -- not a "
                'descriptive paraphrase: "Abdominal pain", not "diffuse '
                'abdominal cramping" or "crampy belly pain that comes and '
                'goes." Name one concept per entry; do not stack qualifiers '
                "onto the noun phrase.\n"
                "Output JSON only."
            ),
        },
    ]
    raw = await llm_client.complete(messages, max_tokens=2000, temperature=0.1)
    criteria = parse_profile(raw)
    if criteria:
        _CACHE[cache_key] = criteria
    return [dict(c) for c in criteria]


class ProfileNode:
    """Generates one criteria profile per candidate.

    Receives NO patient text. Generating criteria in sight of the presentation
    they will be judged against makes the model write criteria that fit the
    patient, which collapses the whole mechanism into self-agreement.
    """

    async def __call__(self, state: dict) -> dict:
        candidates = state.get("candidates", [])
        results = await asyncio.gather(
            *(_profile_for(d) for d in candidates), return_exceptions=True
        )

        profiles: dict[str, list[dict]] = {}
        for diagnosis, result in zip(candidates, results):
            if isinstance(result, Exception):
                logger.error("Profile generation failed for %s: %s", diagnosis, result)
                profiles[diagnosis] = []
            else:
                profiles[diagnosis] = result

        state["profiles"] = profiles
        state["stage"] = "profiles_complete"
        return state
