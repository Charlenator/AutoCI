# AutoCI — Plan of Record

> **Effective**: 2026-05-03 (replaces `please-read-context-plan-fluffy-bentley.md` — archived under `CONTEXT/archive/`).
> **Companion docs**: `CONTEXT/dev-progress-diagram.md` (live status of every node) · `CONTEXT/ROADMAP.md` (post-MVP wishlist + presentation future-work source).
> **Working rule (project-scoped)**: relative effort estimates only (XS / S / M / L / XL). No time-based estimates. Sizes are anchored to shipped work — see the t-shirt rubric in the dev-progress diagram or memory.
> **Working rule (project-scoped)**: hard scope discipline. Anything that doesn't enhance the product OR close a literal challenge-brief requirement gets cut into `ROADMAP.md`, not deleted. Quick wins are welcome; large features are not unless strictly needed.

---

## 1. TL;DR — what AutoCI is becoming

A single Next.js shell with **three independent interfaces** and a shared backend, all driven by the same Supabase + pgvector + LiteLLM (DeepSeek) foundation.

1. **RAG Chat** — landing interface. LLM-based Query Planner (rebuilt S1) decides between SQL templates / freeform SELECTs / vector retrieval, executes, returns answer with clickable citations. Above every answer: a "Query Transformation Card" showing how the prompt was interpreted.
2. **Candidate Search** — recruiter-facing search-and-schedule. Semantic search over CV chunks (with optional JD-paste → key-requirement extraction → multi-query fan-out). Sortable/filterable candidate table with download-CV link, missing-field flags, duplicate flags, and a Schedule Meeting button (cal.com slot grid → email send via Resend).
3. **Continuous Improvement Suite (CIS)** — rebranded Kaizen. Conversational scoping agent (`K_SCOPING`) holds a back-and-forth until the problem is clear, then `K_TOOL_SELECTOR` picks the subset of tools needed (could be diagnose-only via 5 Whys + Fishbone + Pareto, or full diagnose-to-fix with FMEA + interventions table + RACI). Existing K1–K7 become menu items, not a fixed pipeline.

Plus, persisted across all three interfaces:
- **Inbound email pipeline (decoupled)** — Resend webhook → Supabase Edge Function (dumb pipe: verify signature + Storage upload + insert `inbound_emails` row with `status='pending'` + return 200) → Modal Python worker (polls pending rows: classify → extract → confidentiality flag → dedup → vectorize via existing T4 embeddings → mark processed). **POC scope: `.docx` attachments only** (PDF parsing → ROADMAP). A `/simulate-inbound` endpoint replays webhook payloads for dev/test without burning real mail.
- **Always-visible right drawer** holding the React Flow system diagram. Lights up cumulatively as nodes are touched across all three interfaces.
- **Interventions table** (replaces Kanban) — per-Kaizen + a centralized cross-Kaizen view linking back to source.
- **Centralized logging** — every agent call, route hit, and pipeline step persisted to Supabase (long-term archival to S3 deferred).

Cloud deploy is mandatory: Vercel (frontend) + Modal (backend) + Supabase Edge Functions (webhook).

---

## 2. 2026-05-03 Final Scope Alignment — change summary

### REMOVED (deliberate scope cuts — were over-scoped or not in challenge requirements)
- ❌ **Interview Prep tab** (CV–JD matching, fit scoring, scheduling UI as a standalone tab) — fully removed. The CV/JD matching capability survives differently: as part of Candidate Search and as part of the inbound CV pipeline.
- ❌ **Kanban board** in Control phase — replaced by interventions table.
- ❌ **Company policies / fake reference documents** — not needed; existing tables + new candidate/email/event vectorization is enough structured content for ≥3.
- ❌ **Manual "Run CV Pipeline" button** — pipeline is fully webhook-driven.
- ❌ **Email "Index" button** — indexing happens inside the inbound webhook.
- ❌ **Google Calendar API path** — replaced by cal.com.
- ❌ **Gmail API path (OAuth, drafts, etc.)** — replaced by Resend.

### MOVED TO ROADMAP (post-MVP — see `CONTEXT/ROADMAP.md`)

These were considered for current scope but cut on the 2026-05-03 sense check. They survive as candidates for post-deploy polish or the presentation's future-work slide.

- ➡️ **RACI matrix tool** (cut from Phase 7) — not in brief; CIS already demos right-tool-for-job with FMEA.
- ➡️ **Pareto analysis tool** (cut from Phase 7) — not in brief; visual nice-to-have.
- ➡️ **Cross-Kaizen interventions view** (cut from Phase 7) — per-Kaizen view closes the requirement; portfolio-wide aggregation is polish.
- ➡️ **`system_logs` middleware** (cut from Phase 5) — `agent_invocations` already covers the LLM side; don't build a parallel logging layer pre-emptively.
- ➡️ **JD-paste fan-out search** (cut from Phase 6) — free-text semantic search alone closes the requirement.
- ➡️ **Three-layer RAG self-check** (confidence retry + numeric reasonableness) — citations cover RAG traceability; validated SQL templates cover numeric accuracy.
- ➡️ **Phase 4.5 T2.2 "Evidence Selector"** — no demonstrated need; revisit once corpora grow.

### CHANGED
- 🔄 **Email tool** — now Resend (send) + Resend inbound webhook (receive) → **decoupled** pipeline: Supabase Edge Function as dumb-pipe receiver (signature + Storage + queue insert + 200), then Modal Python worker handles classification, extraction, confidentiality, embeddings, dedup. **POC ingests `.docx` only** (PDF parsing → ROADMAP).
- 🔄 **Calendar tool** — now cal.com (free tier) for slot lookup. Recruiter ticks slots from a 14-day grid; selected slots become deep-link booking URLs in the candidate's invite email.
- 🔄 **S1 (Translation Agent) → Query Planner** — rebuilt as an LLM, schema-aware, JSON-emitting agent that decides on (a) validated SQL template, (b) freeform SELECT, or (c) pure vector retrieval. S3 becomes a thin SQL executor consuming whatever the planner produced.
- 🔄 **Kaizen orchestrator → CIS orchestrator** — `K_SCOPING` (chat loop) and `K_TOOL_SELECTOR` (picks tools per charter) sit in front. K1-K7 become menu items.
- 🔄 **Confidentiality enforcement** — filter-at-retrieval (a `confidential BOOLEAN` column on relevant rows + `match_chunks` exclusion) instead of Postgres RLS.

### ADDED
- ✨ **Resend inbound pipeline** (Edge Function, classifier, dedup, confidentiality, vectorize, Storage upload).
- ✨ **`/simulate-inbound` endpoint** (dev affordance).
- ✨ **Candidate Search interface** — semantic search bar, optional JD-paste mode, sortable/filterable candidate table, download-CV button, Schedule Meeting button.
- ✨ **Query Planner + Query Transformation Card** (UI shows parsed intent + chosen path before answer).
- ✨ **Validated SQL templates** — code-level dict of parameterized queries (TTF, conversion, OAR, candidate-by-skill, etc.) that the Query Planner prefers over freeform SQL.
- ✨ **4-layer SQL safety**: read-only Postgres role + regex allowlist + LLM prompt safety + validated templates first.
- ✨ **Citation Drawer** — clickable chips open a side drawer with full chunk text / posting / article / SQL+rows + download-CV link where applicable.
- ✨ **Knowledge Sources Panel** — inventory of every corpus + every queryable Supabase table, with row counts + sample rows. Confirms ≥3 structured documents claim.
- ✨ **CIS conversational scoping** (`K_SCOPING`) + **dynamic tool selector** (`K_TOOL_SELECTOR`).
- ✨ **3 new CI tools**: Pareto analysis, FMEA (Failure Mode & Effects Analysis), RACI matrix.
- ✨ **Interventions table** — per-Kaizen + cross-Kaizen centralized view, with linked-root-cause column mapping each intervention back to a K4/K5 finding.
- ✨ **Always-visible right drawer** for the React Flow system diagram, with grouped subgraphs and cumulative cross-interface lighting.
- ✨ **Centralized logging table** (`system_logs`) for all calls/steps.

### KEPT (from previous plan, still in scope)
- ✅ Token-level cost tracking (Phase 1) + USD pricing for DeepSeek.
- ✅ Multi-KPI detection (Phase 2) + role-scoped pipeline data.
- ✅ Generic Kaizen / `problem_brief` threading (Phase 3) — survives inside `K_SCOPING`.
- ✅ Per-phase writeup agent `K_WRITEUP` (Phase 4 wave A) — used when a CIS run hits a multi-phase tool.
- ✅ HITL gates between multi-phase tool steps (Phase 4 wave A) — kept; conversational scoping is a *pre-run* layer, HITL is *intra-run*.
- ✅ T1.1 + T1.2 + T2.1 — `market_data` to writeup, D2 live-salary signal, K4/K5 RAG case-study retrieval.
- ✅ Source citations on every answer (the only self-check layer kept).
- ✅ Cloud deploy mandate (Vercel + Modal + Supabase Edge).

---

## 3. Status at a glance

| # | Phase | Status | Notes |
|---|---|---|---|
| 0 | CONTEXT cleanup | ✅ done | Single living state doc. |
| 1 | Token-level cost tracking | ✅ done | USD pricing live ($0.14/$0.07/$0.28 per M). |
| 2 | Multi-KPI detection | ✅ done | 3 tiles, role-scoped, `seed_v2_pipeline.sql` applied. |
| 3 | Generic Kaizen | ✅ done | `problem_brief` threading + auto-pick + K1 three-mode framing. |
| 4 | HITL + writeup agent | ✅ wave A | Backend HITL gates + writeup agent shipped. Frontend wave B partially done; subsumed into Phase 5 below. |
| 4.5 | Data flow rewire | ✅ T1.1 + T1.2 + T2.1 | Writeup gets `market_data`; D2 live salary; K4/K5 RAG case studies. T2.2 + T3 dropped. |
| **5** | **Three-interface shell + Query Planner + diagrams + tables** | 📋 not started | Largest phase. Replaces old Phase 5. |
| **6** | **Email pipeline (Resend + inbound) + Calendar (cal.com) + CV ingestion** | 📋 not started | Replaces old Phase 6. Closes Part 2 challenge gap (3/3 tools). |
| **7** | **CIS rebrand + dynamic tool selector + new CI tools (Pareto / FMEA / RACI) + Interventions table** | 📋 not started | New phase, splits the old "Phase 5" mega-scope. |
| **8** | **Cloud deploy (Vercel + Modal + Edge Functions)** | 📋 not started | Was old Phase 7. |
| **9** | **Submission deliverables (tech summary, screenshots, screen-record, live URL)** | 📋 not started | Was old Phase 8. |

---

## 4. Architecture — proposed final shape

```
Next.js shell  (Vercel)
├── Top nav: 3 tabs
│   ├── Tab 1: RAG Chat
│   │   ├── Chat panel (messages, input)
│   │   ├── Query Transformation Card (per turn, above answer)
│   │   ├── Citation chips → Citation Drawer
│   │   └── Knowledge Sources Panel (toggle)
│   ├── Tab 2: Candidate Search
│   │   ├── Search bar (free text OR pasted JD)
│   │   ├── Sortable/filterable candidate table
│   │   ├── Download CV link per row (Supabase Storage signed URL)
│   │   └── Schedule Meeting → cal.com slot grid → invite email (Resend)
│   └── Tab 3: Continuous Improvement Suite
│       ├── Open text area (problem statement)
│       ├── Scoping chat (K_SCOPING back-and-forth)
│       ├── Charter preview + tool-selection display (K_TOOL_SELECTOR)
│       ├── Run with HITL gates between multi-phase steps
│       ├── Writeups + interventions table per run
│       └── Cross-run interventions view
└── Right drawer (always visible, collapsible)
    └── React Flow diagram, grouped subgraphs, cumulative lighting

FastAPI backend  (Modal)
├── /chat/query                      → Query Planner → SQL exec / RAG / both → answer
├── /candidates/search               → vector search over cv_chunks + filters
├── /candidates/{id}/cv              → signed URL to Supabase Storage
├── /candidates/{id}/schedule        → cal.com lookup + Resend draft+send
├── /cis/scope                       → K_SCOPING chat turn
├── /cis/run                         → K_TOOL_SELECTOR + dynamic tool execution
├── /sessions/{id}/stream            → SSE (kept)
├── /sessions/{id}/respond           → HITL decisions (kept)
├── /metrics/cost, /metrics/kpis     → kept
├── /sources                         → Knowledge Sources Panel inventory
└── /simulate-inbound                → dev affordance for inbound pipeline

Supabase Edge Function  (webhook target for Resend inbound — DUMB PIPE)
├── verify Resend signature
├── upload attachment to Storage (cv-attachments bucket)
├── INSERT inbound_emails (status='pending')
└── return 200 to Resend  (sub-second response)

Modal Python worker  (polls pending rows → heavy processing)
├── classify (.docx CV vs other)        ← LLM call
├── extract structured fields            ← python-docx + LLM
├── confidentiality flag                 ← LLM call
├── dedup hash check (sender + subject)
├── vectorize via T4 embeddings (OpenAI)
├── INSERT cv_chunks / candidates / rag_email_summaries
└── UPDATE inbound_emails SET status='processed'

Supabase  (DB + Storage)
├── Existing 11 tables (kept)
├── NEW: inbound_emails, interventions
├── EXTENDED: candidates (CV-driven applicant cols), corpus_chunks (+confidential col)
├── NEW: cv-attachments storage bucket (private)
└── pgvector + match_chunks RPC (now filters on confidentiality)
    Note: CVs / JDs / email summaries / event summaries all live as rows in the
    *single* corpus_chunks table, distinguished by corpus_name + metadata JSONB.
    Simplifies the vector index, the RPC, and the citation rendering path.

External APIs
├── Resend (send + inbound webhook)
├── cal.com (slot lookup)
├── Adzuna, Tavily, NewsAPI (kept)
├── OpenAI embeddings (kept)
└── DeepSeek via LiteLLM (kept)
```

\* `candidates` already exists as a schema table (recruitment pipeline). It will be extended with inbound-CV columns (`name`, `email`, `phone`, `skills_json`, `cv_storage_path`, `is_duplicate`, `missing_fields_json`, `confidential`, `source_email_id`).

---

## 5. Requirements-to-Features Mapping

The single most important table for the demo. Maps each literal challenge-brief requirement to the AutoCI feature(s) that satisfy it.

### Part 1 — RAG

| Requirement | AutoCI feature | Status |
|---|---|---|
| Working RAG pipeline | `/chat/query` → Query Planner → S2 RAG / S3 SQL / both | ✅ existing routes; planner upgrade in Phase 5 |
| ≥ 3 structured documents | 6+ corpora (`dmaic_methodology`, `role_benchmarks`, `kaizen_case_studies`, `market_intel`, `industry_news`, `cv_chunks`, `jd_chunks`, `rag_email_summaries`, `event_summaries`) **plus** queryable SQL tables | ✅ corpora exist; new ones added in Phases 6-7 |
| Vector / semantic search | pgvector + `match_chunks` RPC | ✅ existing |
| Web-deployed RAG interface | Vercel deploy of Next.js shell | 📋 Phase 8 |
| Prompt control / query transformation | Query Planner emits `{needs_sql, sql, vector_query, corpus_filter, explanation}` envelope; UI Query Transformation Card | 📋 Phase 5 |
| Source traceability | Citation chips on every answer + Citation Drawer with full chunk / posting / SQL+rows + download-CV link + Adzuna `redirect_url` | 📋 Phase 5 |
| Knowledge inventory visibility | Knowledge Sources Panel | 📋 Phase 5 |

### Part 2 — Tools + extract→cleanse→verify

| Requirement | AutoCI feature | Status |
|---|---|---|
| 3 tools (Calendar, Email, Web) | cal.com (slot lookup); Resend (send + inbound); Adzuna + Tavily + NewsAPI (kept) | 📋 Phase 6 |
| Extract from unstructured/semi-structured | Inbound webhook → CV classifier → field extraction (`pypdf` + DeepSeek) | 📋 Phase 6 |
| Cleanse & normalize | Field normalization (email lowercase, phone canonicalization, skills tokenized) + chunking for vector store | 📋 Phase 6 |
| Verify using rules / reference data | Dedup hash (sender+subject); confidentiality classifier; missing-field detection (rule-based); cross-reference against existing candidates | 📋 Phase 6 |
| Store/display verified output | Candidates table with `missing_fields`, `is_duplicate`, `confidential`, `verified_fields` flags; Candidate Search table with sortable columns + flag badges + download link + CSV export | 📋 Phases 5+6 |
| Example workflow ("attendee list with flagged fields") | Inbound CV email + cal.com event lookup + cross-reference candidate metadata → Candidate Search table with all flags surfaced | 📋 Phases 5+6 |

### Cross-cutting

| Requirement | AutoCI feature | Status |
|---|---|---|
| Cloud deployment | Vercel + Modal + Supabase Edge | 📋 Phase 8 |
| Polished demo with screenshots / screen-record | Submission deliverables | 📋 Phase 9 |

---

## 6. Naming registry

| Concept | User-facing name | Internal / code name |
|---|---|---|
| Tab 3 (formerly Kaizen) | Continuous Improvement Suite | `cis` |
| Pre-run scoping agent | (no surface label) | `K_SCOPING` |
| Tool selector | (no surface label) | `K_TOOL_SELECTOR` |
| Query planner (rebuilt S1) | (no surface label) | `S1_QueryPlanner` (filename: `s1_query_planner.py`) |
| SQL executor (was S3) | (no surface label) | `S3_SQLExecutor` |
| Citation drawer | "Sources" | `CitationDrawer` |
| Knowledge inventory panel | "Knowledge sources" | `KnowledgeSourcesPanel` |
| Interventions table | "Interventions" | `InterventionsTable` |

---

## 7. Phase breakdown

Each task tagged with relative effort (XS / S / M / L / XL). Anchors:
- **XS** — smaller than a Phase 4.5 Tier-3 cleanup
- **S** — comparable to T1.1 (single-signature change + prompt update)
- **M** — comparable to Phase 1 or T1.2 (schema + agent + integration)
- **L** — comparable to Phase 4 wave A (new agent + new infra + new route + orchestrator change)
- **XL** — bigger than anything shipped (e.g. full Resend inbound pipeline)

### Phase 5 — Three-interface shell + Query Planner + tables

| Task | Effort | Notes |
|---|---|---|
| Restructure `/dashboard` into 3-tab shell | M | Top nav, route wiring, shared right drawer. Retire marketing splash page. |
| Build always-visible React Flow drawer with grouped subgraphs | M | Reuse `/system-diagram` styling; add SSE-driven `node_status` lighting; cumulative across tabs. |
| Rebuild S1 as Query Planner (LLM, schema-aware) | L | New file `s1_query_planner.py`. Emits the JSON envelope. Knows the schema summary + the validated-templates dict. |
| Validated SQL templates dict | S | Templates for TTF, conversion, OAR, candidate-by-skill, candidate-by-name, etc. Each parameterized + schema-checked. |
| 4-layer SQL safety | M | Read-only role (DB) + regex allowlist (S3 executor) + prompt-side guardrails + template-first preference (planner). |
| Refactor S3 → SQL executor | S | Take in SQL from planner; pass through allowlist; execute via read-only role. |
| Query Transformation Card (frontend) | S | New SSE event `query_transformation`; renders parsed intent + chosen path. |
| Citation Drawer | M | New component; handles RAG / SQL / Adzuna / Tavily / News / writeup-node sources. Adzuna shows `redirect_url`; CV chunks show download link. |
| Knowledge Sources Panel | S | New `/sources` endpoint; lists corpora with chunk counts + tables with row counts + sample. |
| Findings table + Impact/Effort table (UI tables, not prose) | S | Replaces prose lines in detection/improve outputs. |
| Drop frontend Kanban code (not yet replaced) | XS | Delete-only; replacement in Phase 7. |

### Phase 6 — Email pipeline (Resend) + Calendar (cal.com) + CV ingestion

| Task | Effort | Notes |
|---|---|---|
| Schema migration 004 — `inbound_emails` table; extend `candidates` (name/email/phone/skills/cv_storage_path/dedup/missing/confidential); add `corpus_chunks.confidential`; update `match_chunks` RPC with `include_confidential` param; create `cv-attachments` storage bucket | ✅ M | **Applied 2026-05-03 via Supabase MCP.** Unified corpus design — CVs/JDs/email summaries all live in `corpus_chunks` distinguished by `corpus_name` + metadata, no separate vector tables. |
| Supabase Edge Function — dumb-pipe webhook receiver | M | TS function. Verify Resend signature → Storage upload → INSERT `inbound_emails` (status='pending') → 200. **No** PDF parsing, **no** LLM calls, **no** embeddings. Sub-second response. |
| Modal Python worker — pending-row processor | M | Polls (or webhook-triggered) `WHERE status='pending'`. Runs all heavy steps: classify → extract → confidentiality → dedup → vectorize → DB writes. |
| CV classifier agent (`is_cv?`) | S | DeepSeek call from Modal worker. JSON output `{is_cv, confidence}`. |
| CV field extractor agent (`.docx` only for POC) | M | `python-docx` text → DeepSeek extraction → normalized JSON. Handles missing-field flagging. PDF support → ROADMAP. |
| Confidentiality classifier agent | S | DeepSeek call from Modal worker. JSON output `{confidential: bool, reason}`. |
| Email vectorizer | S | Chunk + embed inbound email summary into `rag_email_summaries` via existing T4. |
| Dedup hash (sender + subject) | XS | Inline in Modal worker. |
| `match_chunks` RPC update — filter on confidentiality | XS | One WHERE-clause change. |
| `/simulate-inbound` endpoint | S | Replays a webhook payload locally for dev (skips signature verify, inserts directly). |
| Resend send wrapper | XS | Thin Python wrapper. |
| cal.com slot lookup wrapper | S | Free-tier API client (spike-verified 2026-05-03). Returns 14-day slot grid. |
| Candidate Search interface | M | New tab/route. Free-text semantic search bar + table + filters + download link + CSV export. (JD-paste fan-out → ROADMAP.) |
| Schedule Meeting flow: slot grid + selection + Resend invite | M | UI grid + selection state + Resend send with deep-link booking URLs per slot. |
| Test-CV generator prompt (handed to user, not built) | XS | LLM-offline-produced 20-50 `.docx` CVs; sent through `/simulate-inbound`. |

### Phase 7 — CIS rebrand + dynamic tools + Interventions table

| Task | Effort | Notes |
|---|---|---|
| `K_SCOPING` agent + chat-loop endpoint | M | Asks clarifying questions until charter is clear. Emits `{problem, scope, requested_outcomes, confidence}`. |
| `K_TOOL_SELECTOR` agent | S | Picks subset from `{D1, D2, D3, K1, K2, K3, K4, K5, K6, K7, Pareto, FMEA, RACI}` based on charter. Emits ordered tool list. |
| Refactor `O2.run_full_kaizen` to consume tool list | M | Loops over selected tools; HITL gates between multi-phase tools (kept). |
| FMEA tool | M | New agent emits Severity × Occurrence × Detection table. Frontend table + RPN sort. (Closes "verified output" framing for the brief.) |
| Interventions table — per-Kaizen view | S | Replaces Kanban. Includes `linked_root_cause` (mapped from K4/K5 by K6). (Cross-Kaizen aggregation → ROADMAP.) |
| K6 prompt update — emit `linked_root_cause` per intervention | XS | Single prompt + dataclass change. |
| Retire K7's Kanban output | XS | Delete + redirect output to interventions table. |
| Rebrand UI: "Kaizen" → "Continuous Improvement Suite" | XS | Copy changes. |

### Phase 8 — Cloud deploy

| Task | Effort | Notes |
|---|---|---|
| Vercel deploy of Next.js shell | S | Env-only config; `NEXT_PUBLIC_API_URL` to Modal endpoint. |
| Modal deploy of FastAPI backend | M | Verify secrets, Supabase connectivity, SSE through proxy. |
| Edge Function deploy + Resend webhook URL config | S | Point Resend inbound at the deployed Edge Function. |
| Smoke-test full flow on prod | S | All 3 interfaces + email round-trip. |
| Lock down: no localhost in committed code | XS | Audit + replace with env vars. |

### Phase 9 — Submission deliverables

| Task | Effort | Notes |
|---|---|---|
| `submission/README.md` (1-2 page tech summary) | S | Polished, reviewer-aimed. |
| 6-8 screenshots | XS | Per the screenshot list below. |
| 5-min screen-record | S | Full demo walkthrough. |
| Live demo URL pinned in README | XS | Vercel URL. |

**Screenshot list:**
1. RAG Chat with citation chips + Query Transformation Card
2. Citation Drawer open with full chunk text and download-CV link
3. Knowledge Sources Panel
4. Candidate Search table with filters + missing-field flags + duplicate flags
5. Cal.com slot grid + Resend invite email preview
6. CIS scoping chat → tool-selector output → mid-run with HITL gate
7. Interventions table (per-Kaizen + cross-Kaizen)
8. React Flow drawer fully lit up after a complete demo run

---

## 8. Critical files (updated)

| File | Phase | Status | Notes |
|---|---|---|---|
| `frontend/src/app/page.tsx` | 5 | 📋 | Replace marketing splash with the 3-tab shell. |
| `frontend/src/app/dashboard/page.tsx` | 5 | ⏳ | Becomes one of the 3 tabs (probably CIS). |
| `frontend/src/components/SystemFlowDrawer.tsx` | 5 | 📋 | NEW — always-visible React Flow drawer. |
| `frontend/src/components/QueryTransformationCard.tsx` | 5 | 📋 | NEW |
| `frontend/src/components/CitationDrawer.tsx` | 5 | 📋 | NEW |
| `frontend/src/components/KnowledgeSourcesPanel.tsx` | 5 | 📋 | NEW |
| `frontend/src/components/CandidateSearch.tsx` | 6 | 📋 | NEW — search + table + JD-paste. |
| `frontend/src/components/SlotGrid.tsx` | 6 | 📋 | NEW — cal.com slot grid. |
| `frontend/src/components/InterventionsTable.tsx` | 7 | 📋 | NEW |
| `backend/api/agents/specialists/s1_query_planner.py` | 5 | 📋 | NEW — replaces `s1_translation.py` (kept temporarily as fallback). |
| `backend/api/agents/specialists/s3_sql_executor.py` | 5 | 📋 | Refactor of `s3_sql.py`. |
| `backend/api/agents/specialists/sql_templates.py` | 5 | 📋 | NEW — validated query templates dict. |
| `backend/api/routes/sources.py` | 5 | 📋 | NEW — `/sources` for Knowledge Sources Panel. |
| `backend/api/agents/cis/k_scoping.py` | 7 | 📋 | NEW |
| `backend/api/agents/cis/k_tool_selector.py` | 7 | 📋 | NEW |
| `backend/api/agents/cis/fmea.py` | 7 | 📋 | NEW |
| `backend/api/routes/cis.py` | 7 | 📋 | NEW — `/cis/scope` + `/cis/run`. |
| `backend/api/routes/candidates.py` | 6 | 📋 | NEW — search + CV download + schedule. |
| `backend/api/routes/inbound.py` | 6 | 📋 | NEW — `/simulate-inbound`. |
| `backend/api/integrations/resend_client.py` | 6 | 📋 | NEW |
| `backend/api/integrations/cal_com_client.py` | 6 | 📋 | NEW |
| `backend/api/workers/inbound_processor.py` | 6 | 📋 | NEW — Modal Python worker for the pending-row pipeline. Classify → extract → confidentiality → vectorize. |
| `backend/api/agents/specialists/s5_cv_classifier.py` | 6 | 📋 | NEW — `.docx` CV vs other classifier. |
| `backend/api/agents/specialists/s6_cv_extractor.py` | 6 | 📋 | NEW — `python-docx` + LLM field extraction. |
| `backend/api/agents/specialists/s7_confidentiality.py` | 6 | 📋 | NEW — confidentiality flag classifier. |
| `supabase/functions/inbound-email/index.ts` | 6 | 📋 | NEW — Edge Function dumb-pipe (signature + Storage + queue insert + 200). No heavy work here. |
| `supabase/migrations/004_inbound_pipeline.sql` | 6 | 📋 | NEW — all new tables + columns + bucket + RPC update. |
| `supabase/migrations/005_interventions.sql` | 7 | 📋 | NEW |
| `vercel.json` + `modal_config.py` | 8 | 📋 | NEW / cleanup. |
| `submission/README.md` + `submission/screenshots/` | 9 | 📋 | NEW |

Files retired:
- `frontend/src/app/system-diagram/page.tsx` — folded into the always-visible drawer.
- `backend/api/agents/specialists/s1_translation.py` — replaced by `s1_query_planner.py` (kept temporarily as fallback during rebuild).
- `backend/api/agents/kaizen/k7_control.py` Kanban output path — replaced by interventions table.

---

## 9. Out of scope (deliberate — see `CONTEXT/ROADMAP.md` for everything)

The cuts above (RACI, Pareto, cross-Kaizen view, `system_logs`, JD-paste fan-out, three-layer self-check, T2.2 Evidence Selector) live in **`CONTEXT/ROADMAP.md`** with full reasoning + effort sizing. Other deliberate non-goals for the MVP:

- **Authentication / multi-user isolation** — single-user demo; not required by brief.
- **Mobile-responsive UI** — not required by brief.
- **DBOS durability** — `threading.Thread` is sufficient.
- **Embedded vector store outside Supabase** — pgvector inside Supabase is enough.
- **Long-term log archival to S3** — Supabase logging only for now.
- **CV–JD match scoring as a standalone feature** — Candidate Search semantic search closes the requirement.
- **Process map / SIPOC visual diagram** — overlaps with the global React Flow drawer.

Anything we cut during build (anywhere in Phases 5-9) gets moved into `ROADMAP.md` with reasoning, not deleted. The roadmap doubles as the source for the presentation's future-work slide.

---

## 10. Mid-execution discoveries (preserved from old plan, condensed)

| # | Discovery | Where it landed |
|---|---|---|
| 1 | DeepSeek consolidation (Claude config removed) | `t3_litellm_router.py` |
| 2 | Role-scoping bug in D1/K2/`/metrics/kpis` | Fixed via `role_title` threading |
| 3 | DeepSeek pricing not in LiteLLM (returns $0.00) | Hardcoded rates in T3: $0.14/$0.07/$0.28 per M |
| 4 | DeepSeek prompt caching kicks in unexpectedly | Free latency win |
| 5 | Adzuna 401 — missing key | `.env` updated |
| 6 | K7 was fabricating Kanban statuses (now retired entirely) | K7 retired in Phase 7 |
| 7 | HITL via thread-safe `queue.Queue`, not `asyncio.Queue` | Documented in Phase 4 |
| 8 | Architecture review: API data flow broken (S4 wrote, nothing read) | Surfaced Phase 4.5; T1.1+T1.2+T2.1 shipped |
| 9 | Windows long-path failures during install | Workaround: `C:/autoci-venv` |

---

## 11. Verification plan (per phase)

- **Phase 5** — Visit new shell. Three tabs render. Right drawer visible and collapsible. Ask "what's our average TTF for Java Devs?" → Query Transformation Card shows template-match + chosen formula → answer renders with `[1]` citation chip → click chip → drawer opens with full source. Knowledge Sources Panel lists corpora + tables.
- **Phase 6** — Send a real email with a CV PDF to the Resend inbound address. Within 30s a row appears in `inbound_emails`, `candidates`, and `cv_chunks`. CV PDF visible in Storage. Dedup confirmed (resend same email → flagged duplicate). Search "Java developer" in Candidate Search → seeded candidates surface in table; flags rendered. Click Schedule Meeting → 14-day slot grid loads → tick 3 slots → Send → candidate gets a Resend email with 3 booking deep-links.
- **Phase 7** — In CIS: type "why is offer acceptance dropping for UX?" → K_SCOPING asks 1-2 clarifying questions → K_TOOL_SELECTOR proposes (e.g.) "D1 → D2 → K3 (5 Whys + Fishbone) → FMEA → Interventions". Approve → run executes only those tools. Interventions table renders with `linked_root_cause` populated per row.
- **Phase 8** — Visit Vercel URL. App loads. Fire a CIS run. SSE events stream from Modal. Send a real email. Edge Function processes it. No localhost references in DevTools.
- **Phase 9** — `submission/README.md` exists, ≤2 pages. Screenshots present. Screen-record uploaded. Live URL works from a clean browser.

---

## 12. Working principles

- **Scope discipline.** Cut anything that doesn't enhance the product or close a brief gap. Add small wins; refuse big features unless strictly needed.
- **Effort estimates only, never time estimates.** XS/S/M/L/XL anchored to shipped work.
- **Hooks/automation: webhook-only triggers** for inbound CV. No manual buttons.
- **Pause before destructive operations.** Confirm row counts before destructive SQL. Idempotent migrations only.
- **Surgical migrations.** Each schema change in `supabase/migrations/NNN_*.sql` AND in `supabase/supabase_schema.sql`.
- **Vercel/Modal-ready.** Env vars only; no localhost in committed code.
- **Centralized logging by default.** Every agent call + route hit + pipeline step persisted.
- **Citations everywhere.** Every chat answer carries clickable source chips; every intervention links to its root cause; every writeup cites its evidence.
