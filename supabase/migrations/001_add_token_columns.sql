-- Migration 001: Token-level cost tracking on agent_invocations
-- Run via Supabase SQL Editor. Safe to re-run.

ALTER TABLE agent_invocations ADD COLUMN IF NOT EXISTS input_tokens INT DEFAULT 0;
ALTER TABLE agent_invocations ADD COLUMN IF NOT EXISTS output_tokens INT DEFAULT 0;
ALTER TABLE agent_invocations ADD COLUMN IF NOT EXISTS cached_tokens INT DEFAULT 0;
