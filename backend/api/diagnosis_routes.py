from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, Response
from typing import Optional
from dataclasses import asdict, is_dataclass
from datetime import datetime
import uuid
import json
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from api.auth_routes import require_privacy_policy, get_current_user
from persistence.sessions import save_session, list_sessions, get_session, delete_session

diagnosis_router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

ANSWER_TO_STATUS = {
    "yes": "supported",
    "no": "contradicted",
    "unsure": "not_mentioned",
}


def _view(state: dict) -> dict:
    """The client-facing projection of graph state.

    Deliberately narrow: `profiles` and any ordering weights stay server-side.
    No numeric score of any kind crosses this boundary.
    """
    canonical = [asdict(c) if is_dataclass(c) else dict(c) for c in state.get("canonical", [])]
    return {
        "stage": state.get("stage"),
        "patient_text": state.get("patient_text", ""),
        "ranking": [
            {"rank": i + 1, "diagnoses": group}
            for i, group in enumerate(state.get("ranking") or [])
        ],
        "not_evaluated": state.get("not_evaluated", []),
        "canonical": canonical,
        "matrix": state.get("matrix", {}),
        "judgements": state.get("judgements", {}),
        "open_questions": state.get("open_questions", []),
        "grounded": state.get("grounded", {}),
        "summary": state.get("summary"),
    }


def _step(state: dict, action: str) -> dict:
    """One replayable entry per interaction. No scores, no profiles."""
    return {
        "action": action,
        "stage": state.get("stage"),
        "ranking": [list(group) for group in (state.get("ranking") or [])],
        "not_evaluated": list(state.get("not_evaluated") or []),
        "open_questions": list(state.get("open_questions") or []),
    }


@diagnosis_router.post("/diagnosis/start", dependencies=[Depends(require_privacy_policy)])
@limiter.limit("20/minute")
async def start_diagnosis(
    request: Request,
    patient_text: str = Form(...),
    session_id: Optional[str] = Form(None),
):
    session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}

    try:
        graph = request.app.state.diagnosis_graph
        result = await graph.ainvoke(
            {"session_id": session_id, "patient_text": patient_text, "stage": "started"},
            config,
        )
        steps = [_step(result, "start")]
        await graph.aupdate_state(config, {"steps": steps})
        return {"success": True, "session_id": session_id, "result": _view(result)}
    except Exception as exc:
        logger.error("Diagnosis start failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@diagnosis_router.post("/diagnosis/{session_id}/answers", dependencies=[Depends(require_privacy_policy)])
@limiter.limit("30/minute")
async def submit_answers(request: Request, session_id: str, answers: dict = Body(...)):
    """answers: {criterion_key: "yes" | "no" | "unsure"}"""
    config = {"configurable": {"thread_id": session_id}}

    try:
        graph = request.app.state.diagnosis_graph
        snapshot = await graph.aget_state(config)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Session not found")

        judgements = dict(snapshot.values.get("judgements") or {})
        for key, answer in answers.items():
            status = ANSWER_TO_STATUS.get(answer)
            if status is None:
                continue
            judgements[key] = {
                "status": status,
                "evidence": "Reported by patient" if status != "not_mentioned" else None,
                "source": "patient_answer",
            }

        await graph.aupdate_state(config, {"judgements": judgements, "answers": answers})

        from graphs.diagnosis_workflow import MergeRankNode
        refreshed = await MergeRankNode()(dict(snapshot.values) | {"judgements": judgements})
        steps = list(snapshot.values.get("steps") or []) + [_step(refreshed, "answers")]
        await graph.aupdate_state(config, {
            "ranking": refreshed["ranking"],
            "open_questions": refreshed["open_questions"],
            "steps": steps,
        })

        return {"success": True, "session_id": session_id, "result": _view(refreshed)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Answer submission failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@diagnosis_router.post("/diagnosis/{session_id}/finalize", dependencies=[Depends(require_privacy_policy)])
@limiter.limit("20/minute")
async def finalize_diagnosis(request: Request, session_id: str):
    config = {"configurable": {"thread_id": session_id}}

    try:
        graph = request.app.state.diagnosis_graph
        snapshot = await graph.aget_state(config)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await graph.ainvoke(None, config)
        result["steps"] = list(result.get("steps") or []) + [_step(result, "finalize")]
        # Write the step back before persisting: otherwise the checkpoint and the
        # saved row disagree, and a save_session failure loses the entry entirely.
        await graph.aupdate_state(config, {"steps": result["steps"]})
        user = get_current_user(request)
        if user:
            await save_session(user["id"], result)
        return {"success": True, "session_id": session_id, "result": _view(result)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Finalize failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@diagnosis_router.get("/diagnosis/history", dependencies=[Depends(require_privacy_policy)])
async def history_list(request: Request, limit: int = 20, offset: int = 0):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"sessions": await list_sessions(user["id"], limit, offset)}


@diagnosis_router.get("/diagnosis/history/{row_id}", dependencies=[Depends(require_privacy_policy)])
async def history_detail(request: Request, row_id: str):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # 404 for a malformed id too, not 400: a client must not be able to tell
    # "no such row" from "not yours" from "not a uuid".
    try:
        row = await get_session(row_id, user["id"])
    except Exception as exc:
        logger.error("History lookup failed for %s: %s", row_id, exc)
        raise HTTPException(status_code=404, detail="Session not found")
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


@diagnosis_router.delete("/diagnosis/history/{row_id}", dependencies=[Depends(require_privacy_policy)])
async def history_delete(request: Request, row_id: str):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not await delete_session(row_id, user["id"]):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": row_id}


@diagnosis_router.post("/patient/export_report", dependencies=[Depends(require_privacy_policy)])
async def export_report_file(
    request: Request,
    session_id: str = Form(...),
    format: str = Form(...),
    include_details: bool = Form(True),
    report_data: str = Form(...),
):
    try:
        graph = request.app.state.patient_graph
        config = {"configurable": {"thread_id": session_id}}
        snapshot = await graph.aget_state(config)
        session_state = snapshot.values if snapshot and snapshot.values else json.loads(report_data)

        from nodes.medical_report_node import MedicalReportNode
        report_node = MedicalReportNode()
        file_content = await report_node.generate_export_file(
            state=session_state, format=format, include_details=include_details
        )

        if format == "pdf":
            media_type = "application/pdf"
            filename = f"medical-report-{session_id}.pdf"
        elif format == "word":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"medical-report-{session_id}.docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use pdf or word.")

        return Response(
            content=file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.get("/debug/routes")
async def debug_routes():
    return {"message": "Routes working", "endpoints": [
        "/diagnosis/start", "/diagnosis/{session_id}/answers",
        "/diagnosis/{session_id}/finalize", "/diagnosis/history",
        "/diagnosis/history/{row_id}",
        "/patient/export_report", "/health",
    ]}


@diagnosis_router.get("/health")
async def health_check():
    from config import settings
    health = {
        "status": "healthy",
        "version": "2.0.0",
        "env": settings.APP_ENV,
        "timestamp": datetime.now().isoformat(),
        "checks": {},
    }

    try:
        from api.auth_routes import supabase
        supabase.table("user_profiles").select("id").limit(1).execute()
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {e}"
        health["status"] = "degraded"

    try:
        from llm.client import llm_client
        await llm_client.complete([{"role": "user", "content": "ping"}], max_tokens=5)
        health["checks"]["llm"] = "ok"
    except Exception as e:
        health["checks"]["llm"] = f"error: {e}"
        health["status"] = "degraded"

    return health
