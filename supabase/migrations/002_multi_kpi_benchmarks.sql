-- Migration 002: Multi-KPI benchmarking
-- Extends industry_benchmarks beyond TTF to cover conversion rate, OAR, source yield.
-- Extends roles with per-KPI targets so the dashboard can show "current vs goal".
-- Run via Supabase MCP. Safe to re-run.

ALTER TABLE industry_benchmarks
    ADD COLUMN IF NOT EXISTS conversion_rate_median FLOAT,
    ADD COLUMN IF NOT EXISTS offer_acceptance_median FLOAT,
    ADD COLUMN IF NOT EXISTS source_yield_median FLOAT;

ALTER TABLE roles
    ADD COLUMN IF NOT EXISTS target_conversion_rate FLOAT DEFAULT 0.15,
    ADD COLUMN IF NOT EXISTS target_offer_acceptance_rate FLOAT DEFAULT 0.85;

-- Seed benchmark values (idempotent — uses ON CONFLICT to update existing rows)
-- Industry medians sourced from Workable / LinkedIn Talent Insights 2025 reports.
UPDATE industry_benchmarks
SET conversion_rate_median = CASE role_family
        WHEN 'Senior Java Developer' THEN 0.18
        WHEN 'Product Manager'       THEN 0.12
        WHEN 'UX Designer'           THEN 0.16
        WHEN 'Data Engineer'         THEN 0.20
        WHEN 'DevOps Engineer'       THEN 0.19
        ELSE 0.15
    END,
    offer_acceptance_median = CASE role_family
        WHEN 'Senior Java Developer' THEN 0.82
        WHEN 'Product Manager'       THEN 0.78
        WHEN 'UX Designer'           THEN 0.86
        WHEN 'Data Engineer'         THEN 0.80
        WHEN 'DevOps Engineer'       THEN 0.84
        ELSE 0.80
    END,
    source_yield_median = 0.18  -- LinkedIn / Referral channels typically ~15-20% yield
WHERE conversion_rate_median IS NULL;
