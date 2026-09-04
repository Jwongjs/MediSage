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


async def test_summary_node_rejects_echoed_placeholder_specialist():
    """A model that copies the template instead of filling it in is not a
    recommendation. This surfaced on the report page as the literal text
    "<the type of doctor the patient should see first>" in the specialist
    badge, because the capture was `.+` with nothing checking it."""
    from nodes.summary_node import SummaryNode
    reply = (
        "- Severity: moderate\n"
        "- Specialist: <the type of doctor the patient should see first>"
    )
    with patch("nodes.summary_node.llm_client") as client:
        client.complete = AsyncMock(return_value=reply)
        state = await SummaryNode()({"ranking": [["Migraine"]], "patient_text": "x"})
    # Severity still parses -- only the unusable field falls back.
    assert state["summary"]["severity"] == "moderate"
    assert state["summary"]["specialist_recommendation"] == "general_practitioner"


async def test_summary_node_rejects_echoed_current_specialist_placeholder():
    """Same failure as above, reintroduced when the prompt's placeholder was
    reworded to "name the type of doctor to see first" -- still wrapped in
    brackets, but a model can echo that instruction text verbatim as if it
    were the answer. This surfaced on the report page as that literal
    sentence in the specialist badge."""
    from nodes.summary_node import SummaryNode
    reply = (
        "- Severity: moderate\n"
        "- Specialist: <name the type of doctor to see first>"
    )
    with patch("nodes.summary_node.llm_client") as client:
        client.complete = AsyncMock(return_value=reply)
        state = await SummaryNode()({"ranking": [["Migraine"]], "patient_text": "x"})
    assert state["summary"]["severity"] == "moderate"
    assert state["summary"]["specialist_recommendation"] == "general_practitioner"


async def test_summary_node_keeps_a_real_specialist():
    from nodes.summary_node import SummaryNode
    reply = "- Severity: severe\n- Specialist: Cardiologist"
    with patch("nodes.summary_node.llm_client") as client:
        client.complete = AsyncMock(return_value=reply)
        state = await SummaryNode()({"ranking": [["MI"]], "patient_text": "x"})
    assert state["summary"]["specialist_recommendation"] == "Cardiologist"
