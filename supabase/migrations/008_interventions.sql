-- Migration 008: interventions table
-- One row per concrete intervention proposed by K6_Improve, linked back
-- to the K4/K5 root cause that motivates it. Replaces the K7 Kanban.
-- Idempotent — safe to re-run.
-- Applied to live Supabase 2026-05-04.

CREATE TABLE IF NOT EXISTS interventions (
  intervention_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES kaizen_sessions(session_id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  linked_root_cause TEXT,           -- the K4/K5 finding text this intervention addresses
  impact TEXT CHECK (impact IN ('high', 'medium', 'low')),
  effort TEXT CHECK (effort IN ('XS', 'S', 'M', 'L', 'XL')),
  priority INT,                      -- 1 = highest
  owner TEXT,
  due_date DATE,
  status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'accepted', 'in_progress', 'done', 'rejected')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS interventions_session_idx ON interventions (session_id);