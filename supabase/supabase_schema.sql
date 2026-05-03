-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; --renamed from 'pgvector' 

-- ======================================================================
-- 1. CORE RECRUITMENT DATA
-- ======================================================================

CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    target_ttf_days INT NOT NULL CHECK (target_ttf_days > 0),
    target_conversion_rate FLOAT DEFAULT 0.15,
    target_offer_acceptance_rate FLOAT DEFAULT 0.85,
    opened_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'filled', 'closed', 'on_hold')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE interviewers (
    interviewer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    department TEXT,
    calendar_id TEXT,               -- Google Calendar ID
    average_scheduling_lag_days FLOAT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE candidates (
    candidate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(role_id) ON DELETE SET NULL,
    source_channel TEXT NOT NULL,   -- e.g., 'LinkedIn', 'Referral', 'Direct'
    applied_date DATE NOT NULL,
    external_id TEXT UNIQUE,        -- ATS candidate ID, anonymized
    -- Migration 004: CV-driven applicant fields (NULL for synthetic pipeline candidates)
    name TEXT,
    email TEXT,
    phone TEXT,
    skills_json JSONB,
    experience_summary TEXT,
    cv_storage_path TEXT,
    dedup_hash TEXT,
    is_duplicate BOOLEAN DEFAULT false,
    missing_fields_json JSONB,
    confidential BOOLEAN DEFAULT false,
    source_email_id UUID,           -- FK to inbound_emails (defined later for forward ref)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pipeline_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    stage TEXT NOT NULL,            -- e.g., 'Applied', 'Screening', 'Interview 1', 'Offer', 'Hired', 'Rejected'
    event_date DATE NOT NULL,
    outcome TEXT,                   -- e.g., 'Advanced', 'Rejected', 'Offer Extended', etc.
    interviewer_id UUID REFERENCES interviewers(interviewer_id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE hires (
    hire_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(role_id) ON DELETE SET NULL,
    offer_date DATE,
    start_date DATE,
    salary NUMERIC(12,2),
    accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE offer_outcomes (
    offer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(role_id) ON DELETE SET NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('Accepted', 'Declined')),
    decline_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- 2. KEYWORDS & JOB DESCRIPTION TAGGING
-- ======================================================================

CREATE TABLE keywords (
    keyword_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    label TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,         -- e.g., 'role_type', 'skill', 'tool', 'seniority'
    avg_ttf_days FLOAT DEFAULT NULL,
    avg_acceptance_rate FLOAT DEFAULT NULL,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE job_descriptions (
    jd_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(role_id) ON DELETE SET NULL,
    description_text TEXT NOT NULL,
    posted_date DATE NOT NULL,
    embedding VECTOR(1536)          -- embedded representation for semantic search
);

-- Many-to-many: a JD (or any posting) can have multiple keyword tags
CREATE TABLE posting_keywords (
    posting_id UUID NOT NULL,       -- references either job_descriptions.jd_id or adzuna_postings.posting_id
    posting_type TEXT NOT NULL CHECK (posting_type IN ('internal_jd', 'adzuna')),
    keyword_id UUID REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    PRIMARY KEY (posting_id, posting_type, keyword_id)
);

-- Normalized keyword-to-outcome stats (refreshed by analytics jobs)
CREATE TABLE keyword_outcome_stats (
    keyword_id UUID REFERENCES keywords(keyword_id) ON DELETE CASCADE PRIMARY KEY,
    total_postings INT DEFAULT 0,
    avg_ttf_days FLOAT,
    avg_acceptance_rate FLOAT,
    common_decline_reasons TEXT[],
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- 3. INDUSTRY BENCHMARKS
-- ======================================================================

CREATE TABLE industry_benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_family TEXT NOT NULL,      -- canonical role name, e.g., 'Senior Java Developer'
    region TEXT NOT NULL,           -- 'South Africa', 'Global', etc.
    median_ttf_days FLOAT NOT NULL,
    p25_ttf_days FLOAT,
    p75_ttf_days FLOAT,
    conversion_rate_median FLOAT,    -- Applied → Hire conversion (industry median)
    offer_acceptance_median FLOAT,   -- Offer acceptance rate (industry median)
    source_yield_median FLOAT,       -- Median source channel yield
    sample_size INT,
    data_source TEXT DEFAULT 'synthetic',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- 4. ADZUNA POSTINGS (LIVE MARKET DATA)
-- ======================================================================

CREATE TABLE adzuna_postings (
    posting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    adzuna_id TEXT UNIQUE NOT NULL, -- unique ID from Adzuna
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    salary_min NUMERIC(12,2),
    salary_max NUMERIC(12,2),
    posted_date DATE NOT NULL,
    expired_date DATE,
    is_repost BOOLEAN DEFAULT FALSE,
    original_posting_id UUID REFERENCES adzuna_postings(posting_id) ON DELETE SET NULL,
    redirect_url TEXT, -- live posting URL (Phase 4.5 §I — for citation drawer link-out)
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- 5. KAIZEN SESSIONS & AGENT STATE
-- ======================================================================

CREATE TABLE kaizen_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(role_id) ON DELETE SET NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN (
        'competitive_gap', 'predictive_drift', 'candidate_yield',
        'offer_acceptance', 'keyword_outcome', 'goal_review_simulation', 'manual'
    )),
    phase TEXT NOT NULL DEFAULT 'detection' CHECK (phase IN (
        'detection', 'define', 'measure', 'analyse', 'improve', 'control', 'done'
    )),
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN (
        'running', 'completed', 'failed', 'interrupted'
    )),
    output_state JSONB DEFAULT '{}',  -- stores all phase artefacts as defined in contracts
    dbos_workflow_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Nodes in the React Flow graph; rehydrated from this table
CREATE TABLE kaizen_nodes (
    node_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES kaizen_sessions(session_id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,          -- e.g., 'K1', 'S2'
    node_type TEXT NOT NULL CHECK (node_type IN ('agent', 'human', 'tool', 'subprocess')),
    status TEXT NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'active', 'complete', 'error')),
    edge_weights JSONB DEFAULT '{}',
    position_x FLOAT DEFAULT 0.0,
    position_y FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- 6. AGENT INVOCATION LOG (COST TRACE)
-- ======================================================================

CREATE TABLE agent_invocations (
    invocation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES kaizen_sessions(session_id) ON DELETE CASCADE,
    from_agent TEXT,                 -- agent that triggered the call
    to_agent TEXT,                   -- target agent
    tool_used TEXT,                  -- 'llm', 'sql', 'rag', 'tavily', etc.
    model_used TEXT,                 -- e.g., 'claude-sonnet-4-6'
    input_summary TEXT,              -- truncated prompt / query
    output_summary TEXT,             -- truncated result
    cost_usd NUMERIC(10,6) DEFAULT 0,
    duration_ms INT DEFAULT 0,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cached_tokens INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ======================================================================
-- 7. RAG CORPUS (pgvector)
-- ======================================================================

CREATE TABLE corpus_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    corpus_name TEXT NOT NULL,       -- e.g., 'lss_case_studies', 'role_benchmarks', 'cvs', 'jds', 'inbound_emails', 'event_summaries'
    chunk_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',    -- e.g., {"candidate_id": "...", "role": "Java Developer"}
    embedding VECTOR(1536) NOT NULL,
    confidential BOOLEAN DEFAULT false, -- Migration 004: filtered out by match_chunks RPC by default
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migration 004: inbound CV email pipeline (queue table for the Modal worker)
CREATE TABLE inbound_emails (
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
    dedup_hash TEXT,
    is_duplicate BOOLEAN DEFAULT false,
    classified_as_cv BOOLEAN,
    confidential BOOLEAN DEFAULT false,
    candidate_id UUID REFERENCES candidates(candidate_id) ON DELETE SET NULL,
    error_log TEXT,
    raw_webhook_payload JSONB,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Resolve forward FK (candidates.source_email_id → inbound_emails)
ALTER TABLE candidates ADD CONSTRAINT candidates_source_email_id_fkey
    FOREIGN KEY (source_email_id) REFERENCES inbound_emails(id) ON DELETE SET NULL;

-- ======================================================================
-- 8. INDEXES & PERFORMANCE
-- ======================================================================

-- Core data
CREATE INDEX idx_pipeline_candidate ON pipeline_events(candidate_id);
CREATE INDEX idx_pipeline_stage_date ON pipeline_events(stage, event_date);
CREATE INDEX idx_hires_role ON hires(role_id);
CREATE INDEX idx_offer_role ON offer_outcomes(role_id);

-- Keywords
CREATE INDEX idx_posting_keywords_lookup ON posting_keywords(posting_id, posting_type);
CREATE INDEX idx_keywords_label ON keywords(label);

-- Benchmarks
CREATE INDEX idx_benchmarks_role ON industry_benchmarks(role_family, region);

-- Kaizen
CREATE INDEX idx_kaizen_sessions_role ON kaizen_sessions(role_id);
CREATE INDEX idx_kaizen_nodes_session ON kaizen_nodes(session_id);
CREATE INDEX idx_agent_invocations_session ON agent_invocations(session_id);

-- RAG vector search (cosine similarity is default but we can specify)
CREATE INDEX idx_corpus_embedding ON corpus_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_corpus_chunks_confidential ON corpus_chunks(confidential) WHERE confidential = false;

-- Migration 004 indexes
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_dedup_hash ON candidates(dedup_hash);
CREATE INDEX idx_candidates_confidential ON candidates(confidential) WHERE confidential = false;
CREATE INDEX idx_inbound_emails_status ON inbound_emails(status);
CREATE INDEX idx_inbound_emails_dedup_hash ON inbound_emails(dedup_hash);
CREATE INDEX idx_inbound_emails_received_at ON inbound_emails(received_at DESC);
-- For exact nearest neighbour (optional, small dataset)
-- CREATE INDEX idx_corpus_embedding ON corpus_chunks USING hnsw (embedding vector_cosine_ops);

-- ======================================================================
-- 9. TRIGGER: auto-update updated_at
-- ======================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kaizen_sessions_updated_at BEFORE UPDATE ON kaizen_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kaizen_nodes_updated_at BEFORE UPDATE ON kaizen_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_keywords_updated_at BEFORE UPDATE ON keywords
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_keyword_outcome_stats_updated_at BEFORE UPDATE ON keyword_outcome_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();