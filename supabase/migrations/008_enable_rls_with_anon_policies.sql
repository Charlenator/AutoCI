-- ============================================================
-- Migration 008: Enable RLS on all tables + add anon policies
-- ============================================================

-- 1) STORAGE: Add bucket-scoped policy for cv-attachments
--    Allows anon role to INSERT (upload) and SELECT (download)
--    files in the cv-attachments bucket only.
DROP POLICY IF EXISTS "anon_cv_attachments_all" ON storage.objects;
CREATE POLICY "anon_cv_attachments_all"
ON storage.objects
FOR ALL
TO public
USING (bucket_id = 'cv-attachments' AND auth.role() = 'anon')
WITH CHECK (bucket_id = 'cv-attachments' AND auth.role() = 'anon');

-- ============================================================
-- 2) PUBLIC TABLES: Enable RLS + add "allow anon all" policies
--    This keeps existing wide-open behaviour but with RLS
--    enabled so it can be hardened per-table later.
-- ============================================================

DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'public.roles',
        'public.interviewers',
        'public.candidates',
        'public.pipeline_events',
        'public.hires',
        'public.offer_outcomes',
        'public.keywords',
        'public.job_descriptions',
        'public.posting_keywords',
        'public.keyword_outcome_stats',
        'public.industry_benchmarks',
        'public.adzuna_postings',
        'public.kaizen_sessions',
        'public.kaizen_nodes',
        'public.agent_invocations',
        'public.corpus_chunks',
        'public.inbound_emails'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY;', tbl);
        EXECUTE format('DROP POLICY IF EXISTS "anon_all_%s" ON %s;',
            REPLACE(REPLACE(tbl, 'public.', ''), '.', '_'), tbl);
        EXECUTE format(
            'CREATE POLICY "anon_all_%s" ON %s FOR ALL TO public USING (auth.role() = ''anon'') WITH CHECK (auth.role() = ''anon'');',
            REPLACE(REPLACE(tbl, 'public.', ''), '.', '_'), tbl
        );
    END LOOP;
END $$;
