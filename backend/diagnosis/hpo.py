from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_ARTICLE_RE = re.compile(r"^(the|a|an)\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")
_SYNONYM_RE = re.compile(r'^synonym:\s*"([^"]*)"')

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "hp.obo"


def normalize(text: str) -> str:
    """Canonical form used as the lookup key for every criterion string."""
    out = _PUNCT_RE.sub(" ", text.lower().strip())
    out = _WS_RE.sub(" ", out).strip()
    return _ARTICLE_RE.sub("", out).strip()


@dataclass(frozen=True)
class HpoIndex:
    by_term: dict[str, str]
    labels: dict[str, str]

    def lookup(self, text: str) -> str | None:
        return self.by_term.get(normalize(text))

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
