-- Migration 002: pgvector + document_chunks for RAG
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK (source_type IN ('medical_report', 'uploaded_document')),
    source_id TEXT,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS document_chunks_user_source_idx
    ON document_chunks (user_id, source_type, source_id);

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own chunks" ON document_chunks
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own chunks" ON document_chunks
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own chunks" ON document_chunks
    FOR DELETE USING (auth.uid() = user_id);

-- RPC for cosine similarity search
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(768),
    match_user_id UUID,
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID, chunk_text TEXT, source_type TEXT,
    source_id TEXT, chunk_index INT, metadata JSONB, similarity FLOAT
)
LANGUAGE sql STABLE AS $$
    SELECT id, chunk_text, source_type, source_id, chunk_index, metadata,
           1 - (embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE user_id = match_user_id
      AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Verify
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'document_chunks' ORDER BY ordinal_position;
