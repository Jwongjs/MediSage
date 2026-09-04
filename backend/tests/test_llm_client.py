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


def _rate_limit_error(retry_after: str | None = None):
    import httpx
    from groq import RateLimitError
    headers = {"retry-after": retry_after} if retry_after is not None else {}
    response = httpx.Response(
        429, headers=headers, request=httpx.Request("POST", "http://groq.test")
    )
    return RateLimitError("rate limited", response=response, body=None)


def _mock_groq(MockChatGroq, side_effect):
    mock_response = MagicMock()
    mock_response.content = "ok"
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=side_effect)
    mock_llm.bind.return_value = mock_llm
    MockChatGroq.return_value = mock_llm
    return mock_llm, mock_response


@pytest.mark.asyncio
async def test_complete_retries_after_a_rate_limit(monkeypatch):
    # A 429 clears on its own once the per-minute window rolls. Aborting on the
    # first one throws away every node that already succeeded in the run.
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    with patch("llm.client.ChatGroq") as MockChatGroq, \
         patch("llm.client.asyncio.sleep", new=AsyncMock()) as sleep:
        mock_response = MagicMock()
        mock_response.content = "recovered"
        mock_llm, _ = _mock_groq(
            MockChatGroq, [_rate_limit_error("4"), mock_response]
        )
        result = await LLMClient().complete([{"role": "user", "content": "hi"}])

    assert result == "recovered"
    assert mock_llm.ainvoke.await_count == 2
    # Groq's own reset delay is preferred over the fallback ladder.
    sleep.assert_awaited_once_with(4.0)


@pytest.mark.asyncio
async def test_complete_falls_back_when_no_retry_after_header(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    with patch("llm.client.ChatGroq") as MockChatGroq, \
         patch("llm.client.asyncio.sleep", new=AsyncMock()) as sleep:
        mock_response = MagicMock()
        mock_response.content = "recovered"
        _mock_groq(MockChatGroq, [_rate_limit_error(), mock_response])
        await LLMClient().complete([{"role": "user", "content": "hi"}])

    # 5s, not a 1s textbook backoff -- the window this waits on is per-minute.
    sleep.assert_awaited_once_with(5.0)


@pytest.mark.asyncio
async def test_complete_gives_up_and_raises_after_max_retries(monkeypatch):
    # The caller must still see the failure rather than a silent empty result:
    # evidence_node turns an unparseable response into not_mentioned.
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    from groq import RateLimitError
    with patch("llm.client.ChatGroq") as MockChatGroq, \
         patch("llm.client.asyncio.sleep", new=AsyncMock()) as sleep:
        mock_llm, _ = _mock_groq(MockChatGroq, _rate_limit_error("1"))
        with pytest.raises(RateLimitError):
            await LLMClient().complete([{"role": "user", "content": "hi"}])

    assert mock_llm.ainvoke.await_count == 4  # initial attempt + 3 retries
    assert sleep.await_count == 3


@pytest.mark.asyncio
async def test_complete_does_not_retry_other_errors(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    with patch("llm.client.ChatGroq") as MockChatGroq, \
         patch("llm.client.asyncio.sleep", new=AsyncMock()):
        mock_llm, _ = _mock_groq(MockChatGroq, RuntimeError("upstream 500"))
        with pytest.raises(RuntimeError):
            await LLMClient().complete([{"role": "user", "content": "hi"}])

    assert mock_llm.ainvoke.await_count == 1
