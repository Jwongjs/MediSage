from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_ARTICLE_RE = re.compile(r"^(the|a|an)\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Canonical form used as the lookup key for every criterion string."""
    out = _PUNCT_RE.sub(" ", text.lower().strip())
    out = _WS_RE.sub(" ", out).strip()
    return _ARTICLE_RE.sub("", out).strip()


@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    kind: str
    # Patient-facing rewrite of `label`, supplied by Node B alongside the
    # clinical description. `label` stays clinical -- it drives display in
    # the read-only groups and is what the exported report shows a
    # clinician. Falls back to the raw criterion text when Node B omits it.
    plain_label: str = ""


@dataclass(frozen=True)
class MergeResult:
    canonical: list[Criterion]
    matrix: dict[str, dict[str, str]]


def local_key(text: str) -> str:
    digest = hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()[:10]
    return f"LOCAL:{digest}"


async def merge_profiles(profiles: dict[str, list[dict]]) -> MergeResult:
    """Dedupe raw per-diagnosis criteria into one canonical list plus a
    diagnosis -> key -> importance matrix, keyed on exact normalized text.

    No ontology, no embeddings: two criteria merge only when their
    normalized text is identical. This is a correctness fix, not a cost
    optimization -- without it, the same fact evaluated once per diagnosis
    that lists it could plausibly return a different verdict each time
    (autoregressive generation gives no guarantee of self-consistency for
    a repeated near-identical ask), corrupting the ranking tally, not just
    the display.
    """
    canonical: dict[str, Criterion] = {}
    matrix: dict[str, dict[str, str]] = {d: {} for d in profiles}

    for diagnosis, criteria in profiles.items():
        for crit in criteria:
            text = (crit.get("text") or "").strip()
            if not text:
                continue
            kind = crit.get("kind", "symptom")
            importance = crit.get("importance", "moderate")
            plain_label = (crit.get("plain_label") or "").strip() or text

            key = local_key(text)
            # First writer wins: a criterion's own text is its label
            # wherever it's first seen, regardless of how later diagnoses
            # happen to phrase the same normalized concept.
            canonical.setdefault(
                key, Criterion(key=key, label=text, kind=kind, plain_label=plain_label)
            )

            existing = matrix[diagnosis].get(key)
            if existing is None or _rank_importance(importance) > _rank_importance(existing):
                matrix[diagnosis][key] = importance

    return MergeResult(canonical=list(canonical.values()), matrix=matrix)


def _rank_importance(value: str) -> int:
    return {"strong": 3, "moderate": 2, "weak": 1}.get(value, 0)
