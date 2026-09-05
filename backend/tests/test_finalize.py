import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from diagnosis.finalize import apply_checked_symptoms
from diagnosis.merge import Criterion


def test_checked_key_becomes_supported_patient_answer():
    canonical = [Criterion("k1", "Fever", "symptom")]
    judgements = {"k1": {"status": "not_mentioned", "evidence": None, "source": "llm"}}
    out = apply_checked_symptoms(canonical, judgements, {"k1"})
    assert out["k1"] == {"status": "supported", "evidence": None, "source": "patient_answer"}


def test_unchecked_key_becomes_not_mentioned_patient_answer():
    canonical = [Criterion("k1", "Fever", "symptom")]
    judgements = {"k1": {"status": "supported", "evidence": "I have a fever", "source": "llm"}}
    out = apply_checked_symptoms(canonical, judgements, set())
    assert out["k1"] == {"status": "not_mentioned", "evidence": None, "source": "patient_answer"}


def test_contradicted_key_is_never_overridden():
    canonical = [Criterion("k1", "Fever", "symptom")]
    judgements = {"k1": {"status": "contradicted", "evidence": "no fever", "source": "llm"}}
    # Even if the client somehow submits it as checked, contradicted stays.
    out = apply_checked_symptoms(canonical, judgements, {"k1"})
    assert out["k1"] == {"status": "contradicted", "evidence": "no fever", "source": "llm"}


def test_a_key_missing_from_judgements_defaults_to_not_mentioned_before_reconciling():
    canonical = [Criterion("k1", "Fever", "symptom")]
    out = apply_checked_symptoms(canonical, {}, {"k1"})
    assert out["k1"]["status"] == "supported"


def test_keys_not_in_canonical_are_ignored_even_if_checked():
    canonical = [Criterion("k1", "Fever", "symptom")]
    out = apply_checked_symptoms(canonical, {}, {"k1", "not-a-real-key"})
    assert set(out.keys()) == {"k1"}


def test_non_symptom_kind_is_never_touched_regardless_of_checked():
    canonical = [Criterion("k1", "WBC count", "lab")]
    judgements = {"k1": {"status": "supported", "evidence": "WBC 14,000", "source": "llm"}}
    # Checked, unchecked, doesn't matter -- there is no checkbox for a lab result.
    out_checked = apply_checked_symptoms(canonical, judgements, {"k1"})
    out_unchecked = apply_checked_symptoms(canonical, judgements, set())
    assert out_checked["k1"] == {"status": "supported", "evidence": "WBC 14,000", "source": "llm"}
    assert out_unchecked["k1"] == {"status": "supported", "evidence": "WBC 14,000", "source": "llm"}


def test_checked_symptom_agreeing_with_supported_preserves_llm_evidence():
    canonical = [Criterion("k1", "Fever", "symptom")]
    judgements = {"k1": {"status": "supported", "evidence": "I have a fever", "source": "llm"}}
    out = apply_checked_symptoms(canonical, judgements, {"k1"})
    assert out["k1"] == {"status": "supported", "evidence": "I have a fever", "source": "llm"}


def test_unchecked_symptom_agreeing_with_not_mentioned_passes_through_unchanged():
    canonical = [Criterion("k1", "Fever", "symptom")]
    judgements = {"k1": {"status": "not_mentioned", "evidence": None, "source": "llm"}}
    out = apply_checked_symptoms(canonical, judgements, set())
    assert out["k1"] == {"status": "not_mentioned", "evidence": None, "source": "llm"}
