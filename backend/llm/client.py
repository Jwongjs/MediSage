import asyncio
import logging
import os
from groq import RateLimitError
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = logging.getLogger(__name__)

# Groq meters output tokens per minute, so a busy pipeline gets 429s that
# clear on their own. Without a retry a single one aborts the whole
# diagnosis mid-run, losing every node that already succeeded.
_MAX_RETRIES = 3
_FALLBACK_DELAYS = (5.0, 15.0, 30.0)


def _retry_after(error: RateLimitError) -> float | None:
    """The reset delay Groq reports, when it reports one.

    Worth preferring over a guess: the limit being hit here is per-MINUTE,
    so a textbook 1/2/4-second backoff would exhaust its retries well
    inside a window that has not moved. The fallbacks below are sized for
    a rolling per-minute window instead.
    """
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    try:
        return float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None


def _to_lc_message(msg: dict):
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if role == "system":
        return SystemMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


class LLMClient:
    def __init__(self, model: str | None = None):
        self._llm = None
        self._model = model

    @property
    def llm(self):
        # Build ChatGroq lazily on first use, not at import. The Groq SDK
        # requires an API key at construction, so eager init crashes the whole
        # module on import when no key is set (e.g. CI test collection). With
        # lazy init the module imports cleanly and only fails if actually called.
        if self._llm is None:
            self._llm = ChatGroq(
                model=self._model or os.getenv("LLM_MODEL"),
                groq_api_key=os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY"),
            )
        return self._llm

    async def complete(self, messages: list[dict], **kwargs) -> str:
        lc_messages = [_to_lc_message(m) for m in messages]
        llm = self.llm.bind(**kwargs) if kwargs else self.llm
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await llm.ainvoke(lc_messages)
                return response.content
            except RateLimitError as error:
                if attempt == _MAX_RETRIES:
                    raise
                delay = _retry_after(error) or _FALLBACK_DELAYS[attempt]
                logger.warning(
                    "Groq rate limited, retrying in %ss (attempt %d/%d)",
                    delay, attempt + 1, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)


llm_client = LLMClient()