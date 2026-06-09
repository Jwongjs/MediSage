import os
import logging
from typing import Any
from supabase import create_client, Client
from rag.embedder import embed_text, embed_chunks, chunk_text

logger = logging.getLogger(__name__)

_TOP_K = 5
_SIMILARITY_THRESHOLD = 0.7


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
    """Return top-k most similar chunks for a user query."""
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
    return result.data or []
