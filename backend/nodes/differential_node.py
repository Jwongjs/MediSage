from __future__ import annotations

import json
import logging
import re

from knowledge.interface import Explanation
from llm.client import llm_client

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 5

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
# A dash only separates a suffix when it is spaced. A bare hyphen belongs to
# the name itself ("Non-Hodgkin lymphoma"), and cutting there would poison
# the Node B cache key and the retrieval lookup.
_TRAILING_RE = re.compile(r"\s+[-–]\s+.*$|\s*:\s*.*$")

_SYSTEM = (
    "You are an AI medical assistant generating a differential diagnosis. "
    "Output valid JSON only. No prose before or after."
)


def parse_differential(raw: str) -> list[dict]:
    """Extract {name, definition} entries from the model's JSON array.

    Any confidence value the model volunteers is stripped from the name here
    so it cannot reach state. This system has no numeric confidence.
    """
    fenced = _FENCE_RE.search(raw)
    payload = fenced.group(1) if fenced else raw
    start, end = payload.find("["), payload.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        entries = json.loads(payload[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Differential JSON did not parse")
        return []

    candidates: list[dict] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = _PAREN_RE.sub("", (entry.get("name") or "").strip())
        name = _TRAILING_RE.sub("", name).strip().rstrip(".")
        if not name:
            continue
        folded = name.lower()
        if folded in seen:
            continue
        seen.add(folded)
        candidates.append({
            "name": name,
            "definition": (entry.get("definition") or "").strip(),
        })

    return candidates


class DifferentialNode:
    """Node A: candidate conditions, plus a plain-language definition of each.

    NOTE: unlike the rest of this pipeline, the definition is ungrounded --
    the model's own general knowledge, not a retrieved or verified source.
    That is a deliberate scope choice for this feature, not an oversight; see
    DOCUMENTATION.md §6.
    """

    async def __call__(self, state: dict) -> dict:
        patient_text = state.get("patient_text", "")
        messages = [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Patient information:\n{patient_text}\n\n"
                    f"List up to {MAX_CANDIDATES} conditions that could explain this "
                    "presentation. Output a JSON array. Each element:\n"
                    '{"name": "<diagnosis name>", "definition": "<one short, '
                    "plain-language sentence, max 20 words, defining what this "
                    'condition is, for a patient with no medical background>"}\n'
                    "No confidence values, no probabilities, no percentages, no "
                    "commentary. Output JSON only."
                ),
            },
        ]
        raw = await llm_client.complete(messages, max_tokens=500, temperature=0.1)
        entries = parse_differential(raw)[:MAX_CANDIDATES]

        candidates = [e["name"] for e in entries]
        explanations = {
            e["name"]: (
                Explanation(text=e["definition"], source="AI-generated", url="")
                if e["definition"] else None
            )
            for e in entries
        }

        logger.info("Differential produced %d candidates", len(candidates))
        state["candidates"] = candidates
        state["explanations"] = explanations
        state["stage"] = "differential_complete"
        return state
