import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from llm.client import LLMClient


@pytest.mark.asyncio
async def test_complete_returns_content(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    mock_response = MagicMock()
    mock_response.content = "- Diagnosis: Common Cold\n- Confidence: 0.85"

    with patch("llm.client.ChatGroq") as MockChatGroq:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind.return_value = mock_llm
        MockChatGroq.return_value = mock_llm

        client = LLMClient()
        result = await client.complete([{"role": "user", "content": "I have a headache"}])

    assert result == "- Diagnosis: Common Cold\n- Confidence: 0.85"


@pytest.mark.asyncio
async def test_complete_forwards_kwargs(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    mock_response = MagicMock()
    mock_response.content = "ok"

    with patch("llm.client.ChatGroq") as MockChatGroq:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind.return_value = mock_llm
        MockChatGroq.return_value = mock_llm

        client = LLMClient()
        await client.complete(
            [{"role": "user", "content": "test"}],
            max_tokens=200,
            temperature=0.3
        )

    mock_llm.bind.assert_called_once_with(max_tokens=200, temperature=0.3)
    mock_llm.ainvoke.assert_called_once()
