import sys, os
from unittest.mock import AsyncMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.differential_node import parse_candidates, DifferentialNode


def test_parse_extracts_numbered_diagnoses():
    raw = "1. Acute gastroenteritis\n2. Appendicitis\n3. Urinary tract infection"
    assert parse_candidates(raw) == [
        "Acute gastroenteritis", "Appendicitis", "Urinary tract infection",
    ]


def test_parse_handles_bulleted_output():
    assert parse_candidates("- Appendicitis\n- Migraine") == ["Appendicitis", "Migraine"]


def test_parse_ignores_preamble_prose():
    raw = "Here are the possibilities:\n1. Appendicitis\n2. Migraine"
    assert parse_candidates(raw) == ["Appendicitis", "Migraine"]


def test_parse_strips_any_confidence_the_model_volunteers():
    # The prompt forbids it, but the parser must not let one leak into state.
    assert parse_candidates("1. Appendicitis (confidence: 0.8)") == ["Appendicitis"]


def test_parse_deduplicates_case_insensitively():
    assert parse_candidates("1. Appendicitis\n2. appendicitis") == ["Appendicitis"]


def test_parse_returns_empty_for_unparseable_output():
    assert parse_candidates("I cannot help with that.") == []


async def test_node_sets_candidates_and_stage():
    with patch("nodes.differential_node.llm_client") as mock:
        mock.complete = AsyncMock(return_value="1. Appendicitis\n2. Migraine")
        state = await DifferentialNode()({"patient_text": "belly hurts"})
    assert state["candidates"] == ["Appendicitis", "Migraine"]
    assert state["stage"] == "differential_complete"


async def test_node_caps_candidates_at_five():
    with patch("nodes.differential_node.llm_client") as mock:
        mock.complete = AsyncMock(
            return_value="\n".join(f"{i}. Condition {i}" for i in range(1, 9))
        )
        state = await DifferentialNode()({"patient_text": "x"})
    assert len(state["candidates"]) == 5


def test_parse_preserves_hyphenated_diagnosis_names():
    # A bare hyphen is part of the name, not a suffix separator. Mangling it
    # poisons the Node B cache key and the retrieval lookup downstream.
    raw = "1. Non-Hodgkin lymphoma\n2. Guillain-Barre syndrome\n3. Post-viral cough"
    assert parse_candidates(raw) == [
        "Non-Hodgkin lymphoma", "Guillain-Barre syndrome", "Post-viral cough",
    ]


def test_parse_still_strips_a_spaced_dash_suffix():
    assert parse_candidates("1. Appendicitis - inflammation of the appendix") == ["Appendicitis"]


def test_parse_still_strips_a_colon_suffix():
    assert parse_candidates("1. Appendicitis: most likely") == ["Appendicitis"]
