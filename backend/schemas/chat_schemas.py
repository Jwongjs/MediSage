from typing_extensions import TypedDict
from typing import List, Any


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatState(TypedDict, total=False):
    user_id: str
    query: str
    conversation_history: List[ChatMessage]
    retrieved_chunks: List[Any]
    answer: str
    sources: List[str]
