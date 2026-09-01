-- Retires the RAG chatbot's corpus. 002_rag_pgvector.sql is intentionally
-- left on disk: it has already been applied, and editing an applied
-- migration desynchronises any environment that replays from scratch.
-- The pgvector extension is deliberately NOT dropped: dropping a shared
-- extension can break unrelated objects.
drop table if exists document_chunks;
