-- Migration 004: inbound CV email pipeline + confidentiality filtering.
-- Phase 6 foundation. Applied to live Supabase 2026-05-03.
-- Idempotent — safe to re-run.
--
-- Design choice 2026-05-03: keep one universal corpus_chunks table rather than
-- spawning cv_chunks / jd_chunks / rag_email_summaries. corpus_name + metadata
-- JSONB distinguish source types. Simpler vector index, single match RPC,
-- single confidentiality filter.

-- ===== 1. Extend candidates table for CV-driven applicants =====
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS skills_json JSONB;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS experience_summary TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS cv_storage_path TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS dedup_hash TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT false;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS missing_fields_json JSONB;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS confidential BOOLEAN DEFAULT false;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS source_email_id UUID;

CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_dedup_hash ON candidates(dedup_hash);
CREATE INDEX IF NOT EXISTS idx_candidates_confidential ON candidates(confidential) WHERE confidential = false;

-- ===== 2. inbound_emails — queue table for the Modal worker =====
CREATE TABLE IF NOT EXISTS inbound_emails (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  svix_id TEXT UNIQUE,                         -- dedup key from Resend webhook
  status TEXT NOT NULL DEFAULT 'pending',      -- pending | processing | processed | error | not_cv
  sender TEXT,
  recipient TEXT,
  subject TEXT,
  body_text TEXT,
  body_html TEXT,
  attachment_filename TEXT,
  attachment_storage_path TEXT,
  attachment_mime TEXT,
  attachment_size INTEGER,
  dedup_hash TEXT,                             -- sender+subject hash for cross-email dedup
  is_duplicate BOOLEAN DEFAULT false,
  classified_as_cv BOOLEAN,
  confidential BOOLEAN DEFAULT false,
  candidate_id UUID,                           -- FK populated after extraction
  error_log TEXT,
  raw_webhook_payload JSONB,                   -- raw Resend body for debugging
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_inbound_emails_status ON inbound_emails(status);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_dedup_hash ON inbound_emails(dedup_hash);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_received_at ON inbound_emails(received_at DESC);

-- Foreign keys (after both sides exist)
ALTER TABLE inbound_emails DROP CONSTRAINT IF EXISTS inbound_emails_candidate_id_fkey;
ALTER TABLE inbound_emails ADD CONSTRAINT inbound_emails_candidate_id_fkey
  FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE SET NULL;

ALTER TABLE candidates DROP CONSTRAINT IF EXISTS candidates_source_email_id_fkey;
ALTER TABLE candidates ADD CONSTRAINT candidates_source_email_id_fkey
  FOREIGN KEY (source_email_id) REFERENCES inbound_emails(id) ON DELETE SET NULL;

-- ===== 3. Confidentiality flag on corpus_chunks (universal) =====
ALTER TABLE corpus_chunks ADD COLUMN IF NOT EXISTS confidential BOOLEAN DEFAULT false;
CREATE INDEX IF NOT EXISTS idx_corpus_chunks_confidential ON corpus_chunks(confidential) WHERE confidential = false;

-- ===== 4. match_chunks RPC update — exclude confidential by default =====
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT,
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
    AND 1 - (cc.embedding <=> query_embedding) > match_threshold
  ORDER BY cc.embedding <=> query_embedding ASC
  LIMIT match_count;
END;
$$;

-- ===== 5. Storage bucket for CV attachments (private) =====
INSERT INTO storage.buckets (id, name, public)
VALUES ('cv-attachments', 'cv-attachments', false)
ON CONFLICT (id) DO NOTHING;
