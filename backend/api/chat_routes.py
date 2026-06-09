from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
import logging

from api.auth_routes import require_privacy_policy, get_current_user
from schemas.chat_schemas import ChatMessage, ChatState
from rag.retriever import ingest_document

chat_router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    query: str
    # ChatMessage is a TypedDict (not a Pydantic model); use List[dict] to avoid validation errors
    conversation_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


@chat_router.post("/chat/ask", dependencies=[Depends(require_privacy_policy)])
async def ask_chat(request: Request, body: ChatRequest):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    graph = request.app.state.rag_graph
    initial_state: ChatState = {
        "user_id": user["id"],
        "query": body.query,
        "conversation_history": body.conversation_history or [],
    }

    try:
        result = await graph.ainvoke(initial_state)
        return ChatResponse(answer=result["answer"], sources=result.get("sources", []))
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/chat/ingest-report/{report_id}", dependencies=[Depends(require_privacy_policy)])
async def ingest_report(request: Request, report_id: str):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from nodes.medical_report_node import MedicalReportNode
        report_node = MedicalReportNode()
        report = await report_node.get_medical_report_by_id(report_id, user["id"])
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        text = report.get("medical_report_content", "") or ""
        count = await ingest_document(
            user_id=user["id"],
            source_type="medical_report",
            source_id=report_id,
            text=text,
            metadata={
                "report_title": report.get("report_title", ""),
                "session_id": report.get("session_id", ""),
            },
        )
        return {"ingested_chunks": count, "report_id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
