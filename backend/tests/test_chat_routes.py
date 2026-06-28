import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

FAKE_USER = {"id": "user-abc", "email": "test@example.com"}


@pytest.fixture
def chat_app():
    from api.chat_routes import chat_router
    from api.auth_routes import require_privacy_policy

    app = FastAPI()
    app.dependency_overrides[require_privacy_policy] = lambda: None

    mock_graph = AsyncMock()
    app.state.rag_graph = mock_graph
    app.include_router(chat_router)

    return app, mock_graph


@pytest.mark.asyncio
async def test_ask_chat_returns_answer(chat_app):
    app, mock_graph = chat_app
    mock_graph.ainvoke.return_value = {
        "answer": "You likely have a common cold.",
        "sources": ["report-session-1"],
    }

    with patch("api.chat_routes.get_current_user", return_value=FAKE_USER):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat/ask", json={"query": "What do I have?"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "You likely have a common cold."
    assert data["sources"] == ["report-session-1"]


@pytest.mark.asyncio
async def test_ask_chat_no_user_returns_401(chat_app):
    app, _ = chat_app

    with patch("api.chat_routes.get_current_user", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat/ask", json={"query": "test"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ask_chat_graph_error_returns_500(chat_app):
    app, mock_graph = chat_app
    mock_graph.ainvoke.side_effect = RuntimeError("graph exploded")

    with patch("api.chat_routes.get_current_user", return_value=FAKE_USER):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat/ask", json={"query": "test"})

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_ingest_report_success(chat_app):
    app, _ = chat_app
    fake_report = {
        "medical_report_content": "Patient presents with headache...",
        "report_title": "Session Report",
        "session_id": "session-xyz",
    }

    with patch("api.chat_routes.get_current_user", return_value=FAKE_USER), \
         patch("nodes.medical_report_node.MedicalReportNode.get_medical_report_by_id", new_callable=AsyncMock, return_value=fake_report), \
         patch("api.chat_routes.ingest_document", new_callable=AsyncMock, return_value=4):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat/ingest-report/report-123")

    assert response.status_code == 200
    data = response.json()
    assert data["ingested_chunks"] == 4
    assert data["report_id"] == "report-123"


@pytest.mark.asyncio
async def test_ingest_report_not_found_returns_404(chat_app):
    app, _ = chat_app

    with patch("api.chat_routes.get_current_user", return_value=FAKE_USER), \
         patch("nodes.medical_report_node.MedicalReportNode.get_medical_report_by_id", new_callable=AsyncMock, return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat/ingest-report/missing-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ingest_report_no_user_returns_401(chat_app):
    app, _ = chat_app

    with patch("api.chat_routes.get_current_user", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat/ingest-report/report-123")

    assert response.status_code == 401
