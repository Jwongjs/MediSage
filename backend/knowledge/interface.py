"""The Project B boundary.

Project A imports these two functions and nothing else from this package.
Until Project B lands, retrieval is served from a small on-disk corpus and
consumer explanations are unavailable.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "criteria_corpus.json"
_corpus: dict[str, list[dict]] | None = None


@dataclass(frozen=True)
class Passage:
    text: str
    source: str
    source_id: str


@dataclass(frozen=True)
class Explanation:
    text: str
    source: str
    url: str


def _load_corpus() -> dict[str, list[dict]]:
    global _corpus
    if _corpus is None:
        if _CORPUS_PATH.exists():
            _corpus = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
        else:
            logger.warning("No criteria corpus at %s - profiles will be ungrounded", _CORPUS_PATH)
            _corpus = {}
    return _corpus


async def retrieve_criteria_passages(diagnosis_name: str, k: int = 15) -> list[Passage]:
    """Passages describing the diagnostic criteria for a condition.

    Keyed on the diagnosis name ONLY. Never pass patient text here — the
    isolation between profile generation and the presentation being judged
    is what keeps profile generation from confirming its own diagnosis.
    """
    entries = _load_corpus().get(diagnosis_name.strip().lower(), [])
    return [
        Passage(text=e["text"], source=e.get("source", "corpus"), source_id=e.get("id", ""))
        for e in entries[:k]
    ]


async def get_consumer_explanation(diagnosis_name: str) -> Explanation | None:
    """Plain-language description of a condition from an authoritative source.

    Returns None until Project B wires up MedlinePlus. Callers MUST omit the
    field rather than substituting model-generated text.
    """
    return None
