-- Migration 006: switch embedding model from OpenAI text-embedding-ada-002 (1536-d)
-- to BAAI/bge-small-en-v1.5 (384-d). Free, locally-runnable, comparable
-- retrieval quality. Eliminates the OpenAI API dependency for embeddings.
--
-- Applied to live Supabase 2026-05-03 via Supabase MCP.
--
-- SIDE EFFECT: existing 213 chunks lose their embedding column. They are
-- re-embedded by a one-off Python script (scripts/reembed_corpus.py) using
-- the new model.
--
-- Idempotent — checks current column dimensionality before changing.

DO $$
DECLARE
  current_dim INT;
BEGIN
  SELECT atttypmod INTO current_dim
  FROM pg_attribute
  WHERE attrelid = 'public.corpus_chunks'::regclass
    AND attname = 'embedding';

  IF current_dim = 384 THEN
    RAISE NOTICE 'embedding column is already VECTOR(384), skipping migration';
    RETURN;
  END IF;

  EXECUTE 'DROP INDEX IF EXISTS idx_corpus_embedding';
  EXECUTE 'DROP INDEX IF EXISTS corpus_chunks_embedding_idx';
  EXECUTE 'DROP FUNCTION IF EXISTS match_chunks(vector, double precision, integer, text, boolean)';
  EXECUTE 'DROP FUNCTION IF EXISTS match_chunks(vector, double precision, integer, text)';
  EXECUTE 'ALTER TABLE corpus_chunks DROP COLUMN embedding';
  EXECUTE 'ALTER TABLE corpus_chunks ADD COLUMN embedding VECTOR(384)';
END $$;

CREATE INDEX IF NOT EXISTS idx_corpus_embedding
  ON corpus_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding VECTOR(384),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 5,
  corpus_filter TEXT DEFAULT NULL,
  include_confidential BOOLEAN DEFAULT false
)
RETURNS TABLE (
  chunk_id UUID,
  chunk_text TEXT,
  corpus_name TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    cc.chunk_id,
    cc.chunk_text,
    cc.corpus_name,
    cc.metadata,
    1 - (cc.embedding <=> query_embedding) AS similarity
  FROM corpus_chunks cc
  WHERE
    (corpus_filter IS NULL OR cc.corpus_name = corpus_filter)
    AND (include_confidential = true OR cc.confidential = false)
    AND cc.embedding IS NOT NULL
    AND 1 - (cc.embedding <=> query_embedding) > match_threshold
  ORDER BY cc.embedding <=> query_embedding ASC
  LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_chunks IS
  'Cosine similarity search over corpus_chunks. Embeddings are 384-d via BAAI/bge-small-en-v1.5. Confidentiality-filtered by default.';
