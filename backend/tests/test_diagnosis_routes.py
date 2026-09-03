import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.diagnosis_routes import _view, _step, ANSWER_TO_STATUS
from diagnosis.merge import Criterion


def test_view_groups_ranking_with_tie_ranks():
    state = {
        "ranking": [["A", "B"], ["C"]],
        "matrix": {"A": {}, "B": {}, "C": {}},
        "canonical": [], "judgements": {}, "open_questions": [], "grounded": {},
    }
    view = _view(state)
    assert view["ranking"][0]["rank"] == 1
    assert view["ranking"][0]["diagnoses"] == ["A", "B"]
    assert view["ranking"][1]["rank"] == 2


def test_view_serializes_criteria_as_dicts():
    state = {
        "ranking": [], "matrix": {}, "judgements": {}, "open_questions": [], "grounded": {},
        "canonical": [Criterion("HP:1", "Fever", "symptom")],
    }
    assert _view(state)["canonical"] == [
        {"key": "HP:1", "label": "Fever", "kind": "symptom", "plain_label": ""}
    ]


def test_view_never_leaks_a_confidence_or_score_field():
    state = {
        "ranking": [["A"]], "matrix": {"A": {}}, "canonical": [],
        "judgements": {}, "open_questions": [], "grounded": {},
    }
    blob = str(_view(state)).lower()
    assert "confidence" not in blob
    assert "split_rank" not in blob


def test_view_exposes_not_evaluated_candidates():
    state = {
        "ranking": [["A"]], "matrix": {"A": {}}, "canonical": [], "judgements": {},
        "open_questions": [], "grounded": {}, "not_evaluated": ["Migraine"],
    }
    assert _view(state)["not_evaluated"] == ["Migraine"]


def test_step_records_ranking_and_questions_without_scores():
    state = {
        "stage": "ranked", "ranking": [["A", "B"]], "not_evaluated": ["C"],
        "open_questions": ["HP:1"],
    }
    step = _step(state, "start")
    assert step["action"] == "start"
    assert step["ranking"] == [["A", "B"]]
    assert step["not_evaluated"] == ["C"]
    blob = str(step).lower()
    assert "confidence" not in blob and "split_rank" not in blob


def test_yes_maps_to_supported():
    assert ANSWER_TO_STATUS["yes"] == "supported"


def test_no_maps_to_contradicted():
    assert ANSWER_TO_STATUS["no"] == "contradicted"


def test_unsure_maps_to_not_mentioned():
    assert ANSWER_TO_STATUS["unsure"] == "not_mentioned"


# --- Endpoint-level tests over a stub graph -------------------------------
# A minimal two-node graph with the real shape: an interrupt before `summary`,
# so `start` leaves the checkpoint mid-run and `finalize` resumes into it.

import httpx
from fastapi import FastAPI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

import api.diagnosis_routes as routes
from schemas.diagnosis_schemas import DiagnosisState


async def _prepare(state):
    state["stage"] = "ranked"
    state["ranking"] = [["Appendicitis"]]
    state["open_questions"] = ["HP:0001945"]
    return state


async def _summary(state):
    state["stage"] = "complete"
    state["summary"] = {"severity": "mild", "specialist_recommendation": "GP"}
    return state


def _stub_app():
    workflow = StateGraph(DiagnosisState)
    workflow.set_entry_point("prepare")
    workflow.add_node("prepare", _prepare)
    workflow.add_node("summary", _summary)
    workflow.add_edge("prepare", "summary")
    workflow.add_edge("summary", END)
    graph = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["summary"])

    app = FastAPI()
    app.state.limiter = routes.limiter
    app.state.diagnosis_graph = graph
    app.include_router(routes.diagnosis_router)
    return app, graph


def _client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_finalize_returns_404_for_a_session_that_was_never_started():
    app, _ = _stub_app()
    async with _client(app) as client:
        response = await client.post("/diagnosis/never-started/finalize")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


async def test_finalize_writes_the_finalize_step_back_to_the_checkpoint():
    app, graph = _stub_app()

    async with _client(app) as client:
        started = await client.post(
            "/diagnosis/start", data={"patient_text": "belly pain"}
        )
        assert started.status_code == 200
        # The server owns the session id; a client cannot choose its own thread.
        session_id = started.json()["session_id"]
        finalized = await client.post(f"/diagnosis/{session_id}/finalize")
        assert finalized.status_code == 200

    config = {"configurable": {"thread_id": session_id}}

    steps = (await graph.aget_state(config)).values["steps"]
    assert [s["action"] for s in steps] == ["start", "finalize"]
    assert steps[-1]["stage"] == "complete"


async def test_start_ignores_a_client_supplied_session_id():
    # With no accounts the session id is the only credential for a session, so
    # a caller must not be able to choose it and collide with a live thread.
    app, _ = _stub_app()
    async with _client(app) as client:
        r = await client.post(
            "/diagnosis/start", data={"patient_text": "belly pain", "session_id": "attacker-chosen"}
        )
    assert r.status_code == 200
    issued = r.json()["session_id"]
    assert issued != "attacker-chosen"
    assert len(issued) == len("session_") + 32
