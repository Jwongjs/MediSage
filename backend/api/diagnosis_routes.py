from fastapi import APIRouter, Body, Form, HTTPException, Request, Response
from dataclasses import asdict, is_dataclass
from datetime import datetime
import uuid
import json
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

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
    explanations = {
        name: (asdict(e) if is_dataclass(e) else e)
        for name, e in (state.get("explanations") or {}).items()
    }
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
        "explanations": explanations,
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


@diagnosis_router.post("/diagnosis/start")
@limiter.limit("20/minute")
async def start_diagnosis(
    request: Request,
    patient_text: str = Form(...),
):
    # With no accounts, the session id IS the bearer credential for this
    # session: anyone holding it can read the differential and download the
    # export. So it is server-generated at full uuid4 entropy and never
    # client-supplied -- a caller-chosen id could collide with, and write
    # into, someone else's live thread.
    session_id = f"session_{uuid.uuid4().hex}"
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


@diagnosis_router.post("/diagnosis/{session_id}/answers")
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


@diagnosis_router.post("/diagnosis/{session_id}/finalize")
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
        # The step is written back to the checkpoint only. Nothing is persisted
        # beyond the process: the client keeps the result, or exports it.
        await graph.aupdate_state(config, {"steps": result["steps"]})
        return {"success": True, "session_id": session_id, "result": _view(result)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Finalize failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@diagnosis_router.post("/patient/export_report")
@limiter.limit("20/minute")
async def export_report_file(
    request: Request,
    session_id: str = Form(...),
    format: str = Form(...),
    include_details: bool = Form(True),
):
    try:
        graph = request.app.state.diagnosis_graph
        config = {"configurable": {"thread_id": session_id}}
        snapshot = await graph.aget_state(config)
        # Export only what the server actually computed. The previous
        # client-supplied fallback let any caller render arbitrary JSON into
        # a document carrying MediSage letterhead and the clinical disclaimer.
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Session not found")
        session_state = snapshot.values

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@diagnosis_router.get("/debug/routes")
async def debug_routes():
    return {"message": "Routes working", "endpoints": [
        "/diagnosis/start", "/diagnosis/{session_id}/answers",
        "/diagnosis/{session_id}/finalize",
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
        from llm.client import llm_client
        await llm_client.complete([{"role": "user", "content": "ping"}], max_tokens=5)
        health["checks"]["llm"] = "ok"
    except Exception as e:
        health["checks"]["llm"] = f"error: {e}"
        health["status"] = "degraded"

    return health
