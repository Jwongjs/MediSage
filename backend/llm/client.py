import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def _to_lc_message(msg: dict):
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if role == "system":
        return SystemMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


class LLMClient:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        # Build ChatGroq lazily on first use, not at import. The Groq SDK
        # requires an API key at construction, so eager init crashes the whole
        # module on import when no key is set (e.g. CI test collection). With
        # lazy init the module imports cleanly and only fails if actually called.
        if self._llm is None:
            self._llm = ChatGroq(
                model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
                groq_api_key=os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY"),
            )
        return self._llm

    async def complete(self, messages: list[dict], **kwargs) -> str:
        lc_messages = [_to_lc_message(m) for m in messages]
        llm = self.llm.bind(**kwargs) if kwargs else self.llm
        response = await llm.ainvoke(lc_messages)
        return response.content


llm_client = LLMClient()