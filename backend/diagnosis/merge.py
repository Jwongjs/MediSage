from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from diagnosis.hpo import HpoIndex, normalize

ACCEPT_THRESHOLD = 0.90
MARGIN_THRESHOLD = 0.03
CLUSTER_THRESHOLD = 0.93


@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    kind: str


@dataclass(frozen=True)
class MergeResult:
    canonical: list[Criterion]
    matrix: dict[str, dict[str, str]]


def local_key(text: str) -> str:
    digest = hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()[:10]
    return f"LOCAL:{digest}"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def _resolve(text: str, kind: str, hpo: HpoIndex, embed_fn, hpo_vectors):
    """Return (key, label) for one criterion string."""
    if kind != "symptom":
        return local_key(text), text

    hit = hpo.lookup(text)
    if hit:
        return hit, hpo.label(hit)

    if embed_fn is None or not hpo_vectors:
        return local_key(text), text

    vec = await embed_fn(text)
    scored = sorted(
        ((_cosine(vec, v), hp_id) for hp_id, v in hpo_vectors.items()),
        reverse=True,
    )
    if not scored:
        return local_key(text), text

    top_score, top_id = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else 0.0
    # Both gates must hold. The margin is what keeps "chest pain" and
    # "chest tightness" — near-identical vectors, distinct concepts — apart.
    if top_score >= ACCEPT_THRESHOLD and (top_score - runner_up) >= MARGIN_THRESHOLD:
        return top_id, hpo.label(top_id)

    return local_key(text), text


async def _build_hpo_vectors(profiles, hpo: HpoIndex, embed_fn):
    """Embed only HPO labels, and only when a fallback will actually be needed."""
    if embed_fn is None:
        return {}
    needs_fallback = any(
        c.get("kind", "symptom") == "symptom" and hpo.lookup(c.get("text", "")) is None
        for crits in profiles.values()
        for c in crits
    )
    if not needs_fallback:
        return {}
    return {hp_id: await embed_fn(label) for hp_id, label in hpo.terms()}


async def merge_profiles(
    profiles: dict[str, list[dict]],
    hpo: HpoIndex,
    embed_fn=None,
) -> MergeResult:
    hpo_vectors = await _build_hpo_vectors(profiles, hpo, embed_fn)

    canonical: dict[str, Criterion] = {}
    matrix: dict[str, dict[str, str]] = {d: {} for d in profiles}

    for diagnosis, criteria in profiles.items():
        for crit in criteria:
            text = (crit.get("text") or "").strip()
            if not text:
                continue
            kind = crit.get("kind", "symptom")
            importance = crit.get("importance", "moderate")

            key, label = await _resolve(text, kind, hpo, embed_fn, hpo_vectors)
            canonical.setdefault(key, Criterion(key=key, label=label, kind=kind))

            # A diagnosis listing the same concept twice keeps the stronger call.
            existing = matrix[diagnosis].get(key)
            if existing is None or _rank_importance(importance) > _rank_importance(existing):
                matrix[diagnosis][key] = importance

    return MergeResult(canonical=list(canonical.values()), matrix=matrix)


def _rank_importance(value: str) -> int:
    return {"strong": 3, "moderate": 2, "weak": 1}.get(value, 0)
