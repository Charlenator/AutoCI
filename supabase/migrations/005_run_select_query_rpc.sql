-- Migration 005: run_select_query RPC for the new S1 Query Planner / S3 SQL Executor pipeline.
-- Applied to live Supabase 2026-05-03 via Supabase MCP.
-- Idempotent — safe to re-run.
--
-- This is layer 4 of SQL safety, after:
--   1. Validated SQL templates (preferred path in the Query Planner)
--   2. Regex allowlist on freeform SQL (Python side, in s3_sql_executor.py)
--   3. LLM prompt safety ("only generate SELECT")
-- Layer 4 sits at the database boundary: even if the application layers were
-- bypassed, this function will reject any non-SELECT statement.

CREATE OR REPLACE FUNCTION run_select_query(sql_text TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
DECLARE
  result JSONB;
  trimmed TEXT;
BEGIN
  trimmed := trim(sql_text);

  IF trimmed = '' THEN
    RAISE EXCEPTION 'Empty SQL';
  END IF;

  -- Must start with SELECT or WITH (for CTEs)
  IF trimmed !~* '^\s*(SELECT|WITH)\s' THEN
    RAISE EXCEPTION 'Only SELECT (and WITH ... SELECT) statements are allowed';
  END IF;

  -- Forbidden keywords. \y is a Postgres POSIX regex word boundary.
  IF trimmed ~* '\y(DROP|INSERT|UPDATE|DELETE|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|REPLACE|MERGE|VACUUM|REINDEX|COPY|EXECUTE|CALL|DO|LOCK|COMMIT|ROLLBACK|SAVEPOINT|SET)\y' THEN
    RAISE EXCEPTION 'Forbidden keyword detected in SQL';
  END IF;

  -- Stacked statement guard (no semicolons except optional trailing one)
  IF position(';' IN regexp_replace(trimmed, ';\s*$', '')) > 0 THEN
    RAISE EXCEPTION 'Multiple statements not allowed';
  END IF;

  EXECUTE format(
    'SELECT COALESCE(jsonb_agg(t), ''[]''::jsonb) FROM (%s) t',
    regexp_replace(trimmed, ';\s*$', '')
  ) INTO result;

  RETURN result;
END;
$$;

COMMENT ON FUNCTION run_select_query(TEXT) IS
  'Safe read-only SQL execution gateway used by S1 Query Planner / S3 SQL Executor. Returns rows as JSONB; rejects any non-SELECT or stacked statement.';
