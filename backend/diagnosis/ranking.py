from __future__ import annotations

from collections import defaultdict
from itertools import groupby

IMPORTANCES = ("strong", "moderate", "weak")
STATUSES = ("supported", "contradicted", "not_mentioned")


def tally(diagnosis: str, matrix: dict, judgements: dict) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for key, importance in matrix.get(diagnosis, {}).items():
        judgement = judgements.get(key) or {}
        status = judgement.get("status", "not_mentioned")
        if status not in STATUSES:
            status = "not_mentioned"
        counts[(importance, status)] += 1
    return counts


def sort_key(counts: dict[tuple[str, str], int]) -> tuple:
    """Lexicographic ordering key. No weights, no arithmetic across fields.

    Contradiction of a core criterion is the strongest evidence against a
    candidate, so it leads. Negation gives descending order for the fields
    where more is better.
    """
    g = lambda i, s: counts.get((i, s), 0)  # noqa: E731
    return (
        g("strong", "contradicted"),
        -g("strong", "supported"),
        g("strong", "not_mentioned"),
        g("moderate", "contradicted"),
        -g("moderate", "supported"),
        g("moderate", "not_mentioned"),
        g("weak", "contradicted"),
        -g("weak", "supported"),
    )


def rank(matrix: dict, judgements: dict) -> list[list[str]]:
    """Diagnoses grouped into tiers. Diagnoses in one tier are genuinely tied."""
    scored = sorted(
        ((sort_key(tally(d, matrix, judgements)), d) for d in matrix),
        key=lambda pair: (pair[0], pair[1]),
    )
    return [sorted(d for _, d in group) for _, group in groupby(scored, key=lambda pair: pair[0])]


_WEIGHT = {"strong": 3, "moderate": 2, "weak": 1}


def split_rank(key: str, matrix: dict, candidates: list[str]) -> float:
    """How much answering this criterion could reorder the differential.

    NOT a confidence value. It orders the question list and is never attached
    to a diagnosis, returned to the client, or displayed.
    """
    present = [d for d in candidates if key in matrix.get(d, {})]
    if not present:
        return 0.0
    split = min(len(present), len(candidates) - len(present))
    if split == 0:
        return 0.0
    weight = sum(_WEIGHT.get(matrix[d][key], 0) for d in present) / len(present)
    return split * weight


def open_questions(canonical, matrix: dict, judgements: dict, candidates: list[str]) -> list[str]:
    """Criterion keys worth asking about, best first."""
    scored = []
    for crit in canonical:
        if crit.kind != "symptom":
            continue
        status = (judgements.get(crit.key) or {}).get("status", "not_mentioned")
        if status != "not_mentioned":
            continue
        rank_value = split_rank(crit.key, matrix, candidates)
        if rank_value <= 0:
            continue
        scored.append((rank_value, crit.key))

    # Descending by value; key name ascending as a deterministic tie-break.
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [key for _, key in scored]
