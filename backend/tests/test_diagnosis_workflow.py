import sys, os
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graphs.diagnosis_workflow import MergeRankNode
from diagnosis.merge import Criterion


async def test_merge_rank_node_populates_matrix_and_ranking():
    state = {
        "profiles": {
            "Appendicitis": [
                {"text": "Right lower quadrant pain", "importance": "strong", "kind": "symptom"},
                {"text": "Fever", "importance": "moderate", "kind": "symptom"},
            ],
            "Migraine": [
                {"text": "Headache", "importance": "strong", "kind": "symptom"},
            ],
        },
        "candidates": ["Appendicitis", "Migraine"],
        "judgements": {},
    }
    out = await MergeRankNode()(state)
    assert out["matrix"].keys() == {"Appendicitis", "Migraine"}
    assert len(out["canonical"]) == 3
    assert isinstance(out["ranking"], list)
    assert isinstance(out["ranking"][0], list)
    assert "open_questions" not in out


async def test_ranking_never_emits_a_numeric_score():
    state = {
        "profiles": {"A": [{"text": "Fever", "importance": "strong", "kind": "symptom"}]},
        "candidates": ["A"],
        "judgements": {},
    }
    out = await MergeRankNode()(state)
    assert all(isinstance(group, list) for group in out["ranking"])
    assert all(isinstance(name, str) for group in out["ranking"] for name in group)


async def test_candidates_with_no_criteria_are_separated_not_ranked():
    # A failed Node B profile must not be presented as an evaluated candidate.
    state = {
        "profiles": {
            "A": [{"text": "Fever", "importance": "strong", "kind": "symptom"}],
            "Failed": [],
        },
        "candidates": ["A", "Failed"],
        "judgements": {},
    }
    out = await MergeRankNode()(state)
    assert out["not_evaluated"] == ["Failed"]
    assert all("Failed" not in group for group in out["ranking"])
    assert "A" in [name for group in out["ranking"] for name in group]


async def test_summary_node_reports_unknown_severity_when_unparseable():
    from nodes.summary_node import SummaryNode
    with patch("nodes.summary_node.llm_client") as client:
        client.complete = AsyncMock(return_value="I cannot determine this.")
        state = await SummaryNode()({"ranking": [["Appendicitis"]], "patient_text": "x"})
    assert state["summary"]["severity"] == "unknown"
