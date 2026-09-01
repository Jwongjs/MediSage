from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_PERSISTED = ("patient_text", "steps", "canonical", "matrix", "judgements")


def _get_supabase():
    from api.auth_routes import supabase
    return supabase


def serialize_state(state: dict) -> dict:
    """Reduce graph state to the JSON-safe subset worth keeping.

    `profiles` is dropped — it is reconstructible from the cache and is the
    bulkiest field. `open_questions` is derived and recomputed on read.
    """
    out: dict = {}
    for field in _PERSISTED:
        value = state.get(field)
        if field == "canonical" and value:
            value = [asdict(c) if is_dataclass(c) else dict(c) for c in value]
        out[field] = value if value is not None else ([] if field in ("steps", "canonical") else {})
    out["final_ranking"] = state.get("ranking") or []
    # Candidates that could not be assessed are part of what the user saw.
    out["not_evaluated"] = state.get("not_evaluated") or []
    return out


async def save_session(user_id: str, state: dict) -> dict:
    payload = serialize_state(state)
    ranking = payload["final_ranking"]
    top = ranking[0][0] if ranking and ranking[0] else "Diagnosis session"

    row = {
        "user_id": user_id,
        "session_id": state.get("session_id", ""),
        "title": top,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    # Upsert, not insert: finalizing the same session twice must update
    # the row, not add a second one to the user's history.
    result = (
        _get_supabase()
        .table("diagnosis_sessions")
        .upsert(row, on_conflict="user_id,session_id")
        .execute()
    )
    return (result.data or [{}])[0]


async def list_sessions(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    result = (
        _get_supabase()
        .table("diagnosis_sessions")
        .select("id, session_id, title, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data or []


async def get_session(session_row_id: str, user_id: str) -> dict | None:
    result = (
        _get_supabase()
        .table("diagnosis_sessions")
        .select("*")
        .eq("id", session_row_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


async def delete_session(session_row_id: str, user_id: str) -> bool:
    result = (
        _get_supabase()
        .table("diagnosis_sessions")
        .delete()
        .eq("id", session_row_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(result.data)
