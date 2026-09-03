from __future__ import annotations

import asyncio
import json
import logging
import re

from knowledge.interface import retrieve_criteria_passages
from llm.client import llm_client

logger = logging.getLogger(__name__)

RETRIEVAL_K = 15
_IMPORTANCES = {"strong", "moderate", "weak"}
_KINDS = {"symptom", "history", "lab", "imaging", "demographic"}

# Keyed on the normalised diagnosis name. A profile depends only on the
# condition, never on the patient, so it is safe to share across sessions.
# The grounded flag is stored WITH the profile: a profile generated without
# passages must not report itself as grounded on a later cache hit.
_CACHE: dict[str, tuple[list[dict], bool]] = {}

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
        criteria.append({
            "text": text,
            "plain_label": (entry.get("plain_label") or "").strip(),
            "importance": importance if importance in _IMPORTANCES else "moderate",
            "kind": kind if kind in _KINDS else "symptom",
        })
    return criteria


async def _profile_for(diagnosis: str) -> tuple[list[dict], bool]:
    cache_key = diagnosis.strip().lower()
    cached = _CACHE.get(cache_key)
    if cached is not None:
        criteria, grounded = cached
        return [dict(c) for c in criteria], grounded

    passages = await retrieve_criteria_passages(diagnosis, k=RETRIEVAL_K)
    grounded = bool(passages)
    context = "\n\n".join(f"[{p.source}] {p.text}" for p in passages)

    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Condition: {diagnosis}\n"
                f"Relevant documents:\n{context or '(none available)'}\n\n"
                "Output the diagnostic criteria as a JSON array. Each element:\n"
                '{"id": <int>, "description": "<criterion, clinical language>", '
                '"plain_label": "<the SAME criterion in plain everyday words, '
                "max 6 words, for a patient with no medical background -- keep it "
                'as specific as the clinical version, do not generalize it away>", '
                '"importance": "strong|moderate|weak", '
                '"kind": "symptom|history|lab|imaging|demographic"}\n\n'
                "importance: strong = core criterion, absence severely impacts the "
                "diagnosis; moderate = important supportive criterion; weak = auxiliary.\n"
                "kind: symptom = something the patient can report; history = past "
                "events or exposures; lab/imaging = test findings; demographic = age, "
                "sex, or risk group.\n"
                "Output JSON only."
            ),
        },
    ]
    raw = await llm_client.complete(messages, max_tokens=900, temperature=0.1)
    criteria = parse_profile(raw)
    if criteria:
        _CACHE[cache_key] = (criteria, grounded)
    return [dict(c) for c in criteria], grounded


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
        grounded: dict[str, bool] = {}
        for diagnosis, result in zip(candidates, results):
            if isinstance(result, Exception):
                logger.error("Profile generation failed for %s: %s", diagnosis, result)
                profiles[diagnosis], grounded[diagnosis] = [], False
            else:
                profiles[diagnosis], grounded[diagnosis] = result

        state["profiles"] = profiles
        state["grounded"] = grounded
        state["stage"] = "profiles_complete"
        return state
