-- Migration 003: Persist Adzuna posting URL so the frontend's citation drawer
-- (Phase 5 §D) can link out to the live posting.
-- Idempotent: safe to re-run.

ALTER TABLE adzuna_postings
    ADD COLUMN IF NOT EXISTS redirect_url TEXT;
