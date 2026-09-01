import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from persistence.sessions import serialize_state
from diagnosis.merge import Criterion


def test_serialize_converts_criterion_dataclasses_to_dicts():
    state = {
        "canonical": [Criterion("HP:1", "Fever", "symptom")],
        "matrix": {}, "judgements": {}, "ranking": [], "patient_text": "x",
    }
    out = serialize_state(state)
    assert out["canonical"] == [{"key": "HP:1", "label": "Fever", "kind": "symptom"}]


def test_serialize_is_json_round_trippable():
    import json
    state = {
        "canonical": [Criterion("HP:1", "Fever", "symptom")],
        "matrix": {"A": {"HP:1": "strong"}},
        "judgements": {"HP:1": {"status": "supported", "evidence": "hot", "source": "llm"}},
        "ranking": [["A"]],
        "patient_text": "x",
        "steps": [{"stage": "differential_complete", "candidates": ["A"]}],
    }
    assert json.loads(json.dumps(serialize_state(state)))["final_ranking"] == [["A"]]


def test_serialize_never_emits_a_confidence_field():
    state = {
        "canonical": [], "matrix": {}, "judgements": {}, "ranking": [],
        "patient_text": "x",
    }
    blob = str(serialize_state(state)).lower()
    assert "confidence" not in blob


def test_serialize_drops_transient_keys():
    state = {
        "canonical": [], "matrix": {}, "judgements": {}, "ranking": [],
        "patient_text": "x", "profiles": {"A": []}, "open_questions": ["k1"],
    }
    out = serialize_state(state)
    assert "profiles" not in out
    assert "open_questions" not in out


def test_serialize_keeps_not_evaluated_candidates():
    # A candidate whose profile failed is a real part of what the user saw.
    state = {
        "canonical": [], "matrix": {}, "judgements": {}, "ranking": [["A"]],
        "patient_text": "x", "not_evaluated": ["Migraine"],
    }
    out = serialize_state(state)
    assert out["not_evaluated"] == ["Migraine"]


def test_serialize_defaults_not_evaluated_to_empty_list():
    state = {
        "canonical": [], "matrix": {}, "judgements": {}, "ranking": [],
        "patient_text": "x",
    }
    assert serialize_state(state)["not_evaluated"] == []


async def test_save_session_upserts_so_finalizing_twice_does_not_duplicate():
    # Without a conflict target, finalizing the same session twice adds a
    # second row and the user sees the consultation twice in their history.
    from unittest.mock import MagicMock, patch
    import persistence.sessions as sessions

    table = MagicMock()
    table.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "row-1"}])
    client = MagicMock()
    client.table.return_value = table

    with patch.object(sessions, "_get_supabase", return_value=client):
        await sessions.save_session("user-1", {
            "session_id": "sess-1", "patient_text": "x", "ranking": [["Appendicitis"]],
            "canonical": [], "matrix": {}, "judgements": {},
        })

    table.insert.assert_not_called()
    table.upsert.assert_called_once()
    assert table.upsert.call_args.kwargs["on_conflict"] == "user_id,session_id"
