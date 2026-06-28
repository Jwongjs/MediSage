from google import genai
from google.genai import types
from config import settings

_MODEL = "gemini-embedding-001"
_DIMENSIONS = 768
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def embed_text(text: str) -> list[float]:
    result = _get_client().models.embed_content(
        model=_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=_DIMENSIONS),
    )
    return result.embeddings[0].values


async def embed_chunks(texts: list[str]) -> list[list[float]]:
    # gemini-embedding-001 reliably accepts only a single input per request;
    # multi-input batches can fail and silently abort ingestion. Embed each
    # chunk individually using the same single-input path as embed_text.
    return [await embed_text(text) for text in texts]


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + chunk_size]))
        i += chunk_size - overlap
    return chunks
