from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from diagnosis.merge import normalize

_SYNONYM_RE = re.compile(r'^synonym:\s*"([^"]*)"')

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "hp.obo"


_PROSE_LEAD_RE = re.compile(
    r"^(?:presence of|history of|evidence of|signs? of|symptoms? of)\s+", re.IGNORECASE
)
_PAREN_ANY_RE = re.compile(r"\s*\([^)]*\)")
_TRAILING_CLAUSE_RE = re.compile(r"\s*(?:,|--|—)\s.*$")


def strip_prose(text: str) -> str:
    """Reduce a written-out criterion to the concept an ontology would name.

    Node B emits clinical prose -- "Presence of nausea", "Low-grade fever
    (typically <38.5C)", "Acute abdominal pain, often localized to the RLQ" --
    while HPO names bare concepts. Measured on real Node B output, stripping
    these wrappers lifts exact-match resolution from 9% to 35%.

    Deliberately does NOT split compounds ("Nausea and/or vomiting"): mapping a
    compound to one of its parts silently drops the other concept, and the two
    are not the same criterion.
    """
    out = _PAREN_ANY_RE.sub("", text)
    out = _TRAILING_CLAUSE_RE.sub("", out)
    return _PROSE_LEAD_RE.sub("", out).strip()


@dataclass(frozen=True)
class HpoIndex:
    by_term: dict[str, str]
    labels: dict[str, str]

    def lookup(self, text: str) -> str | None:
        hit = self.by_term.get(normalize(text))
        if hit is not None:
            return hit
        stripped = strip_prose(text)
        if stripped and stripped != text:
            return self.by_term.get(normalize(stripped))
        return None

    def label(self, hp_id: str) -> str:
        return self.labels.get(hp_id, hp_id)

    def terms(self) -> list[tuple[str, str]]:
        """(hp_id, primary label) pairs — the corpus for embedding fallback."""
        return sorted(self.labels.items())


def parse_obo(text: str) -> HpoIndex:
    by_term: dict[str, str] = {}
    labels: dict[str, str] = {}

    for block in text.split("\n["):
        if not block.startswith("Term]") and not block.startswith("[Term]"):
            continue
        if re.search(r"^is_obsolete:\s*true", block, re.MULTILINE):
            continue

        id_match = re.search(r"^id:\s*(HP:\d+)", block, re.MULTILINE)
        name_match = re.search(r"^name:\s*(.+)$", block, re.MULTILINE)
        if not id_match or not name_match:
            continue

        hp_id = id_match.group(1)
        name = name_match.group(1).strip()
        labels[hp_id] = name
        # First writer wins: a term's own label outranks another term's synonym.
        by_term.setdefault(normalize(name), hp_id)

        for line in block.splitlines():
            syn = _SYNONYM_RE.match(line.strip())
            if syn:
                by_term.setdefault(normalize(syn.group(1)), hp_id)

    return HpoIndex(by_term=by_term, labels=labels)


def load_hpo(path: Path | None = None) -> HpoIndex:
    target = path or _DEFAULT_PATH
    if not target.exists():
        return HpoIndex(by_term={}, labels={})
    return parse_obo(target.read_text(encoding="utf-8"))
