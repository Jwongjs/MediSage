from __future__ import annotations
from langgraph.graph import StateGraph, END
from schemas.chat_schemas import ChatState
import logging

logger = logging.getLogger(__name__)


async def _retrieve_node(state: ChatState) -> ChatState:
    from rag.retriever import retrieve
    chunks = await retrieve(user_id=state["user_id"], query=state["query"])
    state["retrieved_chunks"] = chunks
    return state


async def _synthesize_node(state: ChatState) -> ChatState:
    from llm.client import llm_client
    chunks = state.get("retrieved_chunks", [])
    context = "\n\n".join(
        f"[Source {i+1} - {c.get('source_type', 'unknown')}]\n{c['chunk_text']}"
        for i, c in enumerate(chunks)
    )
    history = state.get("conversation_history", [])
    messages = [
        {
            "role": "system",
            "content": (
                "You are a medical AI assistant helping a patient review their diagnostic history. "
                "Answer ONLY from the context provided. If the context lacks sufficient information, say so. "
                "Never fabricate medical information. Always recommend consulting a healthcare professional.\n\n"
                f"CONTEXT FROM YOUR MEDICAL RECORDS:\n{context if context else 'No relevant records found.'}"
            ),
        },
        *history,
        {"role": "user", "content": state["query"]},
    ]
    answer = await llm_client.complete(messages, max_tokens=500, temperature=0.1)
    state["answer"] = answer
    state["sources"] = [
        f"{c.get('source_type', 'unknown')} - {c.get('source_id', '')}" for c in chunks
    ]
    return state


def compile_rag_chatbot():
    workflow = StateGraph(ChatState)
    workflow.set_entry_point("retrieve")
    workflow.add_node("retrieve", _retrieve_node)
    workflow.add_node("synthesize", _synthesize_node)
    workflow.add_edge("retrieve", "synthesize")
    workflow.add_edge("synthesize", END)
    return workflow.compile()
