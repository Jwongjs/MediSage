from __future__ import annotations

import logging
import re

from llm.client import llm_client

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 5

_LIST_RE = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*(.+)$")
_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
# A dash only separates a suffix when it is spaced. A bare hyphen belongs to
# the name itself ("Non-Hodgkin lymphoma"), and cutting there would poison
# the Node B cache key and the retrieval lookup.
_TRAILING_RE = re.compile(r"\s+[-–]\s+.*$|\s*:\s*.*$")

_SYSTEM = (
    "You are an AI medical assistant generating a differential diagnosis. "
    "Follow the requested format exactly. Be concise and professional."
)


def parse_candidates(raw: str) -> list[str]:
    """Extract diagnosis names from a numbered or bulleted list.

    Any confidence value the model volunteers is stripped here so it cannot
    reach state. This system has no numeric confidence.
    """
    names: list[str] = []
    seen: set[str] = set()

    for line in raw.splitlines():
        match = _LIST_RE.match(line)
        if not match:
            continue
        name = _PAREN_RE.sub("", match.group(1).strip())
        name = _TRAILING_RE.sub("", name).strip().rstrip(".")
        if not name:
            continue
        folded = name.lower()
        if folded in seen:
            continue
        seen.add(folded)
        names.append(name)

    return names


class DifferentialNode:
    async def __call__(self, state: dict) -> dict:
        patient_text = state.get("patient_text", "")
        messages = [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Patient information:\n{patient_text}\n\n"
                    f"List up to {MAX_CANDIDATES} conditions that could explain this "
                    "presentation, as a numbered list of diagnosis names only.\n"
                    "Output ONLY the list. No confidence values, no probabilities, "
                    "no percentages, no commentary."
                ),
            },
        ]
        raw = await llm_client.complete(messages, max_tokens=200, temperature=0.1)
        candidates = parse_candidates(raw)[:MAX_CANDIDATES]

        logger.info("Differential produced %d candidates", len(candidates))
        state["candidates"] = candidates
        state["stage"] = "differential_complete"
        return state
