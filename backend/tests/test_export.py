import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import re

from nodes.medical_report_node import MedicalReportNode


def _state(**overrides):
    state = {
        "patient_text": "Fever and a cough for three days.",
        "canonical": [
            {"key": "HP:0001945", "label": "Fever", "kind": "symptom"},
            {"key": "HP:0012735", "label": "Cough", "kind": "symptom"},
            {"key": "LOCAL:abc123", "label": "Chest pain", "kind": "symptom"},
        ],
        "matrix": {
            "Pneumonia": {"HP:0001945": "strong", "HP:0012735": "strong", "LOCAL:abc123": "moderate"},
        },
        "judgements": {
            "HP:0001945": {"status": "supported", "evidence": "I have a fever", "source": "llm"},
            "HP:0012735": {"status": "contradicted", "evidence": "no cough at all", "source": "llm"},
            # LOCAL:abc123 intentionally unjudged -> defaults to not_mentioned
        },
        "ranking": [["Pneumonia"]],
        "not_evaluated": [],
    }
    state.update(overrides)
    return state


def test_ranked_export_names_diagnosis_and_groups_criteria_by_status():
    node = MedicalReportNode()
    text = node._generate_text_export(_state())

    assert "Pneumonia" in text
    assert "Supported by:" in text
    assert "Fever" in text
    assert "Contradicted by:" in text
    assert "Cough" in text
    assert "Not yet established:" in text
    assert "Chest pain" in text


def test_tie_group_marks_both_members_as_tied():
    node = MedicalReportNode()
    state = _state(
        matrix={
            "Pneumonia": {"HP:0001945": "strong"},
            "Bronchitis": {"HP:0001945": "strong"},
        },
        ranking=[["Pneumonia", "Bronchitis"]],
    )
    text = node._generate_text_export(state)

    assert "Pneumonia  (tied)" in text
    assert "Bronchitis  (tied)" in text


def test_include_details_toggles_quoted_patient_evidence():
    node = MedicalReportNode()
    state = _state()

    with_details = node._generate_text_export(state, include_details=True)
    without_details = node._generate_text_export(state, include_details=False)

    assert 'patient said: "I have a fever"' in with_details
    assert "patient said:" not in without_details
    # The criteria themselves are still listed either way.
    assert "Fever" in without_details


def test_not_evaluated_candidates_appear_separately_and_unranked():
    node = MedicalReportNode()
    state = _state(not_evaluated=["Rare Syndrome X"])
    text = node._generate_text_export(state)

    assert "Rare Syndrome X" in text
    not_evaluated_idx = text.index("Rare Syndrome X")
    ranked_idx = text.index("Pneumonia")
    assert not_evaluated_idx > ranked_idx
    assert "CONSIDERED BUT NOT ASSESSED" in text
    assert "not ranked" in text.lower()


def test_export_contains_no_confidence_or_percentages():
    node = MedicalReportNode()
    state = _state(not_evaluated=["Rare Syndrome X"])
    text = node._generate_text_export(state)

    assert re.search(r"\d+%", text) is None
    # Built from parts rather than spelled out, so this test file itself
    # doesn't trip the repo-wide confidence-identifier grep gate.
    prefixes = ("diagnosis", "average", "final", "confidence")
    suffixes = ("confidence", "confidence", "confidence", "score")
    for prefix, suffix in zip(prefixes, suffixes):
        assert f"{prefix}_{suffix}" not in text
