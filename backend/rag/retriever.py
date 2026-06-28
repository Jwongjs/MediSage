import os
import logging
from typing import Any
from supabase import create_client, Client
from rag.embedder import embed_text, embed_chunks, chunk_text

logger = logging.getLogger(__name__)

_TOP_K = 5
# Kept permissive: chat queries about one's own records ("summarize my reports")
# are often only loosely similar to the stored chunks, so a high threshold
# silently returns nothing. The synthesis prompt guards against hallucination.
_SIMILARITY_THRESHOLD = 0.3
_FALLBACK_CHUNK_CHARS = 2000


def _get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_API_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_API_KEY required")
    return create_client(url, key)


async def ingest_document(
    user_id: str,
    source_type: str,
    source_id: str,
    text: str,
    metadata: dict | None = None,
) -> int:
    """Chunk, embed, and upsert a document. Returns chunk count inserted."""
    supabase = _get_supabase()
    chunks = chunk_text(text)
    if not chunks:
        logger.warning(f"Ingestion skipped — empty text: user={user_id} source={source_id}")
        return 0

    embeddings = await embed_chunks(chunks)
    rows = [
        {
            "user_id": user_id,
            "source_type": source_type,
            "source_id": source_id,
            "chunk_index": i,
            "chunk_text": chunk,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    supabase.table("document_chunks").delete().eq("user_id", user_id).eq("source_id", source_id).execute()
    supabase.table("document_chunks").insert(rows).execute()
    logger.info(f"Ingested {len(rows)} chunks: user={user_id} source={source_id}")
    return len(rows)


async def retrieve(user_id: str, query: str, top_k: int = _TOP_K) -> list[dict[str, Any]]:
    """Return top-k most similar chunks for a user query.

    Falls back to the user's saved medical_reports when vector search yields
    nothing, so the chatbot still works for reports that were never chunked
    (e.g. saved before ingestion existed, or ingestion failed silently).
    """
    supabase = _get_supabase()
    query_embedding = await embed_text(query)
    result = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_user_id": user_id,
            "match_count": top_k,
            "match_threshold": _SIMILARITY_THRESHOLD,
        },
    ).execute()
    chunks = result.data or []
    if chunks:
        return chunks

    logger.info(f"Vector search empty for user={user_id}; falling back to medical_reports")
    return _fallback_from_reports(user_id, top_k)


def _fallback_from_reports(user_id: str, top_k: int) -> list[dict[str, Any]]:
    """Build retrieval chunks directly from the user's most recent saved reports."""
    supabase = _get_supabase()
    result = (
        supabase.table("medical_reports")
        .select("id, report_title, created_at, medical_report_content, patient_symptoms, overall_analysis")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(top_k)
        .execute()
    )
    rows = result.data or []
    chunks: list[dict[str, Any]] = []
    for row in rows:
        text = row.get("medical_report_content") or ""
        if not text:
            analysis = row.get("overall_analysis") or {}
            text = (
                f"Report: {row.get('report_title', '')}\n"
                f"Symptoms: {row.get('patient_symptoms', '')}\n"
                f"Diagnosis: {analysis.get('final_diagnosis', '')}\n"
                f"Severity: {analysis.get('final_severity', '')}\n"
                f"Explanation: {analysis.get('user_explanation', '')}"
            )
        chunks.append(
            {
                "chunk_text": text[:_FALLBACK_CHUNK_CHARS],
                "source_type": "medical_report",
                "source_id": row.get("id", ""),
                "metadata": {
                    "report_title": row.get("report_title", ""),
                    "created_at": row.get("created_at", ""),
                },
            }
        )
    return chunks
