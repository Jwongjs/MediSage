import json
import sys, os
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.differential_node import parse_differential, DifferentialNode


def _payload(*entries):
    return json.dumps([{"name": n, "definition": d} for n, d in entries])


def test_parse_extracts_name_and_definition():
    raw = _payload(("Appendicitis", "Inflammation of the appendix."))
    assert parse_differential(raw) == [
        {"name": "Appendicitis", "definition": "Inflammation of the appendix."},
    ]


def test_parse_tolerates_fenced_json():
    raw = "```json\n" + _payload(("Appendicitis", "x")) + "\n```"
    assert len(parse_differential(raw)) == 1


def test_parse_strips_any_confidence_the_model_volunteers_in_the_name():
    # The prompt forbids it, but the parser must not let one leak into state.
    raw = json.dumps([{"name": "Appendicitis (confidence: 0.8)", "definition": "x"}])
    assert parse_differential(raw)[0]["name"] == "Appendicitis"


def test_parse_deduplicates_case_insensitively():
    raw = _payload(("Appendicitis", "a"), ("appendicitis", "b"))
    assert len(parse_differential(raw)) == 1


def test_parse_returns_empty_for_unparseable_output():
    assert parse_differential("I cannot help with that.") == []


def test_parse_defaults_missing_definition_to_empty_string():
    raw = json.dumps([{"name": "Appendicitis"}])
    assert parse_differential(raw)[0]["definition"] == ""


def test_parse_preserves_hyphenated_diagnosis_names():
    # A bare hyphen is part of the name, not a suffix separator. Mangling it
    # poisons the Node B cache key and the retrieval lookup downstream.
    raw = _payload(("Non-Hodgkin lymphoma", "x"), ("Guillain-Barre syndrome", "x"))
    names = [c["name"] for c in parse_differential(raw)]
    assert names == ["Non-Hodgkin lymphoma", "Guillain-Barre syndrome"]


def test_parse_still_strips_a_spaced_dash_suffix_from_the_name():
    raw = json.dumps([{"name": "Appendicitis - most likely", "definition": "x"}])
    assert parse_differential(raw)[0]["name"] == "Appendicitis"


def test_parse_still_strips_a_colon_suffix_from_the_name():
    raw = json.dumps([{"name": "Appendicitis: most likely", "definition": "x"}])
    assert parse_differential(raw)[0]["name"] == "Appendicitis"


async def test_node_sets_candidates_and_stage():
    with patch("nodes.differential_node.llm_client") as mock:
        mock.complete = AsyncMock(return_value=_payload(
            ("Appendicitis", "x"), ("Migraine", "y"),
        ))
        state = await DifferentialNode()({"patient_text": "belly hurts"})
    assert state["candidates"] == ["Appendicitis", "Migraine"]
    assert state["stage"] == "differential_complete"


async def test_node_populates_an_explanation_per_candidate():
    with patch("nodes.differential_node.llm_client") as mock:
        mock.complete = AsyncMock(return_value=_payload(
            ("Appendicitis", "Inflammation of the appendix."),
        ))
        state = await DifferentialNode()({"patient_text": "belly hurts"})
    assert state["explanations"]["Appendicitis"].text == "Inflammation of the appendix."
    assert state["explanations"]["Appendicitis"].source == "AI-generated"


async def test_node_leaves_explanation_none_when_definition_is_empty():
    with patch("nodes.differential_node.llm_client") as mock:
        mock.complete = AsyncMock(return_value=json.dumps([{"name": "Appendicitis"}]))
        state = await DifferentialNode()({"patient_text": "belly hurts"})
    assert state["explanations"]["Appendicitis"] is None


async def test_node_caps_candidates_at_five():
    with patch("nodes.differential_node.llm_client") as mock:
        mock.complete = AsyncMock(return_value=_payload(
            *[(f"Condition {i}", "x") for i in range(1, 9)]
        ))
        state = await DifferentialNode()({"patient_text": "x"})
    assert len(state["candidates"]) == 5
