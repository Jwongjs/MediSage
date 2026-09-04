from __future__ import annotations

import json
import logging
import re

from config import settings
from llm.client import LLMClient

logger = logging.getLogger(__name__)

llm_client = LLMClient(model=settings.EVIDENCE_LLM_MODEL)

# Sized against the output-token ceiling, not readability: Node C returns one
# JSON entry per criterion, so this count -- not max_tokens -- is what decides
# how much the model has to emit. Lowering max_tokens instead would truncate
# the JSON mid-object, and _parse turns an unparseable response into {}, which
# reconcile then reads as not_mentioned for the whole batch (_parse does log a
# warning, so it is traceable, but the run still completes with the evidence
# gone).
#
# 40 was the value that produced a hard 429: Groq priced one batch at 1439
# expected output tokens against a 1000/min ceiling and refused it before
# generating anything. That is a SIZE rejection, so it would fire on the first
# request of the day -- no amount of waiting or retrying clears it, only a
# smaller batch. 15 keeps a batch's visible JSON near ~550 tokens, well inside
# the ceiling with room for a reasoning model's hidden tokens on top.
CHUNK_SIZE = 15
_STATUSES = {"supported", "contradicted", "not_mentioned"}
_NEEDS_EVIDENCE = {"supported", "contradicted"}

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _verbatim_span(evidence: str, patient_text: str) -> str | None:
    """Locate the model's quote in the patient's text, tolerating whitespace.

    Returns the span as the PATIENT wrote it — their casing, their line
    breaks — because the UI quotes the patient's own words. A quote that
    cannot be located is not evidence.
    """
    words = evidence.split()
    if not words:
        return None
    pattern = re.compile(r"\s+".join(map(re.escape, words)), re.IGNORECASE)
    found = pattern.search(patient_text)
    return found.group(0) if found else None


_SYSTEM = (
    "You are a medical expert assessing which diagnostic criteria a patient's "
    "account supports. Output valid JSON only. No prose before or after."
)


def chunk_criteria(criteria: list, size: int = CHUNK_SIZE) -> list[list]:
    """Split into disjoint batches. Every criterion appears exactly once."""
    if not criteria:
        return []
    if len(criteria) <= size:
        return [list(criteria)]
    return [list(criteria[i : i + size]) for i in range(0, len(criteria), size)]


def reconcile(raw_judgements: dict, requested: list, patient_text: str) -> dict:
    """Force the model's output onto the requested key set.

    The key set is fixed by the merge stage. Anything the model omits defaults
    to not_mentioned; anything it invents is discarded; any evidence span that
    is not a verbatim substring of the patient text is rejected and the
    criterion downgraded. The model never decides what was asked.
    """
    out: dict[str, dict] = {}

    for crit in requested:
        entry = raw_judgements.get(crit.key)
        if not isinstance(entry, dict):
            out[crit.key] = {"status": "not_mentioned", "evidence": None, "source": "llm"}
            continue

        status = entry.get("status")
        evidence = entry.get("evidence")

        if status not in _STATUSES:
            status, evidence = "not_mentioned", None
        elif status in _NEEDS_EVIDENCE:
            span = _verbatim_span(evidence, patient_text) if isinstance(evidence, str) else None
            if span is None:
                logger.debug("Non-verbatim evidence rejected for %s", crit.key)
                status, evidence = "not_mentioned", None
            else:
                evidence = span
        else:
            evidence = None

        out[crit.key] = {"status": status, "evidence": evidence, "source": "llm"}

    return out


def _parse(raw: str) -> dict:
    fenced = _FENCE_RE.search(raw)
    payload = fenced.group(1) if fenced else raw
    start, end = payload.find("{"), payload.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        parsed = json.loads(payload[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Evidence JSON did not parse")
        return {}
    return parsed if isinstance(parsed, dict) else {}


async def _evaluate(patient_text: str, batch: list) -> dict:
    # Plain-language label: shorter than the clinical name, and closer to the
    # register patients actually write in, which is what this prompt judges
    # against. Falls back to the clinical label for criteria with none set.
    listing = "\n".join(f'  "{c.key}": {c.plain_label or c.label}' for c in batch)
    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Patient information:\n{patient_text}\n\n"
                f"Diagnostic criteria to assess:\n{listing}\n\n"
                "For each criterion decide:\n"
                "- supported: the patient information explicitly mentions it or a "
                "close clinical equivalent\n"
                "- contradicted: the patient information explicitly rules it out\n"
                "- not_mentioned: the patient information says nothing either way\n\n"
                "For supported and contradicted you MUST quote the exact words from "
                "the patient information, copied verbatim. Do not paraphrase. For "
                "not_mentioned use null.\n\n"
                "Output a JSON object keyed by criterion id:\n"
                '{"<id>": {"status": "supported|contradicted|not_mentioned", '
                '"evidence": "<verbatim quote or null>"}}\n'
                "Include every criterion id. Output JSON only."
            ),
        },
    ]
    raw = await llm_client.complete(messages, max_tokens=2000, temperature=0.0)
    return _parse(raw)


class EvidenceNode:
    async def __call__(self, state: dict) -> dict:
        patient_text = state.get("patient_text", "")
        canonical = state.get("canonical", [])
        existing = state.get("judgements", {}) or {}

        merged: dict[str, dict] = {}
        batches = chunk_criteria(canonical)
        # One request per batch, each emitting one JSON entry per criterion.
        # This is the number to read when a run gets rate limited: it is what
        # decides total output tokens per minute, and nothing upstream of the
        # merge stage is visible from the 429 itself.
        logger.info(
            "Evidence: %d criteria in %d batch(es) of up to %d",
            len(canonical), len(batches), CHUNK_SIZE,
        )
        for batch in batches:
            raw = await _evaluate(patient_text, batch)
            merged.update(reconcile(raw, batch, patient_text))

        # A patient's own yes/no always outranks the model's read of the text,
        # but only for criteria that still exist. The merge stage owns the key set.
        canonical_keys = {c.key for c in canonical}
        for key, judgement in existing.items():
            if key in canonical_keys and judgement.get("source") == "patient_answer":
                merged[key] = judgement

        state["judgements"] = merged
        state["stage"] = "evidence_complete"
        return state
