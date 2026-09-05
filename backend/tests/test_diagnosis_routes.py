import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

def _make_mock_pool(execute_side_effect=None):
    """Stand in for the psycopg pool /health probes with `async with pool.connection()`."""
    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=execute_side_effect)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.connection = MagicMock(return_value=cm)
    return pool


def _make_mock_graph(next_nodes=None, state=None):
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.next = next_nodes or []
    mock_snapshot.values = state or {}
    mock_graph.aget_state = AsyncMock(return_value=mock_snapshot)
    mock_graph.ainvoke = AsyncMock(return_value=state or {})
    return mock_graph


@pytest.fixture
def diag_app():
    from api.diagnosis_routes import diagnosis_router

    app = FastAPI()
    app.include_router(diagnosis_router)

    return app


@pytest.mark.asyncio
async def test_health_returns_healthy_when_probes_pass(diag_app):
    # Task 7: /health actively probes the DB and LLM. Mock both so they
    # succeed and the endpoint reports "healthy".
    diag_app.state.db_pool = _make_mock_pool()
    with patch("llm.client.llm_client.complete", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
            response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"] == {"database": "ok", "llm": "ok"}


@pytest.mark.asyncio
async def test_health_returns_degraded_when_db_probe_fails(diag_app):
    # When a dependency is unreachable the status drops to "degraded" but the
    # endpoint still returns 200 so load balancers get a body to inspect.
    diag_app.state.db_pool = _make_mock_pool(execute_side_effect=RuntimeError("db down"))
    with patch("llm.client.llm_client.complete", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
            response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"].startswith("error")


@pytest.mark.asyncio
async def test_textual_analysis_returns_session_and_workflow_info(diag_app):
    result_state = {"session_id": "s-001", "average_confidence": 0.85}
    mock_graph = _make_mock_graph(next_nodes=["overall_analysis"], state=result_state)
    diag_app.state.patient_graph = mock_graph

    async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
        response = await client.post(
            "/patient/textual_analysis",
            data={"user_symptoms": "I have a headache and fever", "session_id": "s-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["session_id"] == "s-001"
    assert "workflow_info" in data
    assert data["workflow_info"]["workflow_complete"] is False


@pytest.mark.asyncio
async def test_textual_analysis_graph_error_returns_500(diag_app):
    mock_graph = AsyncMock()
    mock_graph.ainvoke.side_effect = RuntimeError("LLM unavailable")
    diag_app.state.patient_graph = mock_graph

    async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
        response = await client.post(
            "/patient/textual_analysis",
            data={"user_symptoms": "headache"},
        )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_followup_questions_without_responses_resumes_graph(diag_app):
    result_state = {"session_id": "s-001", "followup_questions": ["Do you have a fever?"]}
    mock_graph = _make_mock_graph(next_nodes=["process_followup_responses"], state=result_state)
    diag_app.state.patient_graph = mock_graph

    async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
        response = await client.post(
            "/patient/followup_questions",
            data={"session_id": "s-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    mock_graph.ainvoke.assert_called_once_with(None, {"configurable": {"thread_id": "s-001"}})


@pytest.mark.asyncio
async def test_followup_questions_with_responses_updates_state(diag_app):
    import json
    result_state = {"session_id": "s-001", "requires_user_input": False}
    mock_graph = _make_mock_graph(next_nodes=["overall_analysis"], state=result_state)
    diag_app.state.patient_graph = mock_graph

    responses = json.dumps({"q1": "Yes, I have a fever"})
    async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
        response = await client.post(
            "/patient/followup_questions",
            data={"session_id": "s-001", "followup_responses": responses},
        )

    assert response.status_code == 200
    mock_graph.aupdate_state.assert_called_once()


@pytest.mark.asyncio
async def test_overall_analysis_resumes_graph(diag_app):
    result_state = {"session_id": "s-001", "overall_analysis": "Tension headache."}
    mock_graph = _make_mock_graph(next_nodes=["medical_report"], state=result_state)
    diag_app.state.patient_graph = mock_graph

    async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
        response = await client.post(
            "/patient/overall_analysis",
            data={"session_id": "s-001"},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_medical_report_completes_without_auto_ingestion(diag_app):
    result_state = {"session_id": "s-001", "medical_report": "Full report text here."}
    mock_graph = _make_mock_graph(next_nodes=[], state=result_state)
    diag_app.state.patient_graph = mock_graph

    async with AsyncClient(transport=ASGITransport(app=diag_app), base_url="http://test") as client:
        response = await client.post(
            "/patient/medical_report",
            data={"session_id": "s-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["workflow_info"]["workflow_complete"] is True
