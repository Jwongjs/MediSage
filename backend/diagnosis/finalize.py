from __future__ import annotations

from diagnosis.merge import Criterion


def apply_checked_symptoms(
    canonical: list[Criterion], judgements: dict, checked: set[str]
) -> dict:
    """Reconcile the user's final checkbox state into judgements.

    Same "patient's answer outranks the model's read" precedent
    EvidenceNode already uses for supported/not_mentioned -- just applied
    once at finalize instead of incrementally. `contradicted` is never
    touched: there is no checkbox for it, so nothing the client submits
    can override it.
    """
    out: dict[str, dict] = {}
    for crit in canonical:
        existing = judgements.get(crit.key) or {}
        if existing.get("status") == "contradicted":
            out[crit.key] = existing
            continue
        status = "supported" if crit.key in checked else "not_mentioned"
        out[crit.key] = {"status": status, "evidence": None, "source": "patient_answer"}
    return out
