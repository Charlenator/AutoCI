-- Migration 007: dedup corpus_chunks + UNIQUE constraint to block future dupes.
-- Applied 2026-05-03 via Supabase MCP. 213 rows -> 79 rows after dedup.
--
-- Source of dupes: every Kaizen run re-vectorized adzuna postings + Tavily / news
-- snippets and re-inserted them. New UNIQUE index makes any future duplicate
-- INSERT raise a 23505 — callers should use upsert with ignore_duplicates or
-- catch the error.
--
-- Dedup key: (corpus_name, chunk_text, candidate_id_in_metadata).
-- For non-CV corpora candidate_id is NULL so the effective key is (corpus_name, chunk_text).
-- For the future 'cvs' corpus (Sprint B5) different candidates with identical
-- skill/experience text remain retrievable as separate rows.
-- Idempotent — safe to re-run.

WITH ranked AS (
  SELECT
    chunk_id,
    ROW_NUMBER() OVER (
      PARTITION BY corpus_name, chunk_text, COALESCE(metadata->>'candidate_id', '')
      ORDER BY (embedding IS NULL), created_at NULLS LAST, chunk_id
    ) AS rn
  FROM corpus_chunks
)
DELETE FROM corpus_chunks
WHERE chunk_id IN (SELECT chunk_id FROM ranked WHERE rn > 1);

ALTER TABLE corpus_chunks
  ADD COLUMN IF NOT EXISTS content_hash TEXT GENERATED ALWAYS AS (
    md5(corpus_name || '::' || chunk_text || '::' || COALESCE(metadata->>'candidate_id', ''))
  ) STORED;

CREATE UNIQUE INDEX IF NOT EXISTS corpus_chunks_content_hash_uniq
  ON corpus_chunks (content_hash);

COMMENT ON COLUMN corpus_chunks.content_hash IS
  'Stable dedup key: md5(corpus_name :: chunk_text :: candidate_id). Enforced by UNIQUE index corpus_chunks_content_hash_uniq.';
