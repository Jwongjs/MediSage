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
    can override it. Likewise `lab`/`imaging`/`demographic` criteria have no
    checkbox -- a remote patient can't self-report their own WBC count --
    so `checked` is ignored for them and the existing judgement passes
    through unchanged. When the checkbox state merely agrees with what the
    model already found, the existing judgement (with its real verbatim
    evidence) is kept rather than overwritten with a patient_answer stub.
    """
    out: dict[str, dict] = {}
    for crit in canonical:
        existing = judgements.get(crit.key) or {}
        if existing.get("status") == "contradicted":
            out[crit.key] = existing
            continue
        if crit.kind not in ("symptom", "history"):
            out[crit.key] = existing or {"status": "not_mentioned", "evidence": None, "source": "llm"}
            continue
        is_checked = crit.key in checked
        existing_status = existing.get("status")
        if (is_checked and existing_status == "supported") or (
            not is_checked and existing_status == "not_mentioned"
        ):
            out[crit.key] = existing
            continue
        status = "supported" if is_checked else "not_mentioned"
        out[crit.key] = {"status": status, "evidence": None, "source": "patient_answer"}
    return out
