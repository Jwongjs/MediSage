import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.mark.asyncio
async def test_embed_text_returns_768_dim():
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    from rag.embedder import embed_text
    vector = await embed_text("chest pain and shortness of breath")
    assert isinstance(vector, list)
    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector)


@pytest.mark.asyncio
async def test_embed_chunks_returns_list():
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    from rag.embedder import embed_chunks
    vectors = await embed_chunks(["symptom one", "symptom two"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 768


def test_chunk_text_splits_long_text():
    from rag.embedder import chunk_text
    text = " ".join([f"word{i}" for i in range(1200)])
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 500 for c in chunks)
