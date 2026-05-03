-- pgvector `match_chunks` RPC — cosine similarity search over corpus_chunks.
-- Updated 2026-05-03 (Migration 004): added `include_confidential` parameter.
-- Confidential rows are excluded by default so RAG retrieval respects privacy
-- on CV/email-summary corpora. Pass `include_confidential := true` only for
-- authorized read paths (recruiter UI with proper auth).
--
-- Usage:
--   SELECT * FROM match_chunks(
--     query_embedding := openai_embed('what slows down hiring'),
--     match_threshold := 0.7,
--     match_count     := 5,
--     corpus_filter   := 'cvs',                -- optional
--     include_confidential := false            -- default
--   );

CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    corpus_filter TEXT DEFAULT NULL,
    include_confidential BOOLEAN DEFAULT false
)
RETURNS TABLE(
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
    WHERE (corpus_filter IS NULL OR cc.corpus_name = corpus_filter)
      AND cc.embedding IS NOT NULL
      AND (include_confidential = true OR cc.confidential = false)
      AND 1 - (cc.embedding <=> query_embedding) > match_threshold
    ORDER BY cc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
