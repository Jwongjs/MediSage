from google import genai
from config import settings

_MODEL = "text-embedding-004"
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def embed_text(text: str) -> list[float]:
    result = _get_client().models.embed_content(model=_MODEL, contents=text)
    return result.embeddings[0].values


async def embed_chunks(texts: list[str]) -> list[list[float]]:
    result = _get_client().models.embed_content(model=_MODEL, contents=texts)
    return [e.values for e in result.embeddings]


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + chunk_size]))
        i += chunk_size - overlap
    return chunks
