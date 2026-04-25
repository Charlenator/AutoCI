# AutoCI — Full Context Document
**Session:** 5
**Created:** April 26, 2026
**Purpose:** Complete context for building and presenting AutoCI

---

## IMPORTANT: UPLOADED DOCUMENTS
- `Artificial_Intelligence_Engineer_TCN.pdf`
- `Inference_Group_-_AI_Agent_Technical_Challenge.docx`
- `AutoCI_Overview.md` (updated PRD)
- `supabase_schema.sql` (database script)

---

## 1. SITUATION OVERVIEW
Charle is completing a technical challenge for a senior AI Engineer role at TCN Capital. The interview process has cleared two rounds; the final stage is a 30-minute presentation to co-founders (likely Neil and another). Submission must include a working web app and a deck.

**Deadline:** Tuesday, April 28 (absolute latest). Target submission Monday afternoon to allow for final polish.

**Core framing for the presentation:** LSS as structured chain-of-thought for LLMs. The architecture, not prompting, ensures rigorous reasoning.

**Stance on AI-assisted coding:** Frontend and boilerplate were accelerated with agentic coding; the backend design and all architectural decisions are human-driven. This will be stated upfront.

---

## 2. DECISIONS FULLY LOCKED (Session 5)
(Everything from Session 4 plus the following new locks)

- **Infrastructure switch**: Backend now deploys on **Modal** (instead of Hugging Face Spaces) because Modal natively supports DBOS workflows and long-running durable executions.
- **Five Whys protocol**: Locked in Phase 2a. Each call is independent, sequential, with a terminate path.
- **Ishikawa population**: Six parallel branch calls, locked.
- **DMAIC phase contracts**: Locked output_state schemas as typed JSON.
- **Validation Interceptor rules**: Locked.
- **SSE event format**: Six event types specified.
- **LiteLLM cost routing rules**: Locked.
- **Demo script and deck outline**: Locked (Phase 2b). Must be rehearsed.
- **Build sequence**: Node-by-node Sat/Sun/Mon plan with hard gates.
- **Database schema**: Supabase SQL attached.

---

## 3. ARCHITECTURE MAP (Node-Level)
The system is built as a set of numbered nodes in swimlanes. Refer to the updated PRD (`AutoCI_Overview.md`) for the full node list and connections. Key nodes:

- **F1-F8** frontend
- **A1-A7** API gateway
- **O1-O3** orchestration (O1 = DBOS workflow, O2 = Meta-Orchestrator, O3 = phase-gate)
- **D1-D3** detection
- **K1-K7** Kaizen engine (K4 = Five Whys, K5 = Ishikawa)
- **S1-S4** specialists (S1 = Translation, S2 = RAG, S3 = SQL, S4 = Research)
- **T1-T3** middleware (T1 = MCP analytics, T2 = validation, T3 = LiteLLM)
- **DB1-DB5** database tables
- **E1-E7** external APIs

**Build sequence** (from the Phase 2a email) is the roadmap.

---

## 4. DEMO STRATEGY (Locked)
- 10-minute script as detailed in Phase 2b email.
- Must land the Five Whys moment: five separate LLM calls visible in the graph and logs.
- If anything breaks, switch to pre-recorded screencast (already prepared).
- Cost reveal at end: $0.18 total.

**Presentation deck**: 16 slides, max one sentence per slide except architecture diagrams. Deck follows the outline in the Phase 2b email.

**Pre-rehearsed Q&A**: 8 expected questions with answers (Phase 2b).

---

## 5. KEY IMPLEMENTATION DETAILS

### Five Whys (K4)
- Atomic calls to Opus with extended thinking.
- Each call stores its answer in DB2 before the next runs.
- Early termination flag: if confidence < medium, chain stops.
- Code snippet available in Phase 2a.

### Ishikawa (K5)
- Six parallel calls to Sonnet.
- Each branch receives the Five Whys chain and role context.
- Branches can return empty if irrelevant.

### Validation Interceptor (T2)
- Python decorator, wraps agent commits.
- Checks sample size, outliers, schema, termination flags, intervention count.
- Fatal issues block phase advancement; warnings pass through.

### LiteLLM Routing (T3)
- Configuration in `api/llm/routing.py`.
- Logs every call to `agent_invocations` with cost and duration.
- Cost ticker on frontend updates via SSE.

### SSE Protocol
- Single EventSource per session on `/sessions/:id/stream`.
- Six event types: `node_status`, `output_delta`, `phase_transition`, `cost`, `validation`, `error`.
- Frontend dispatch table in `lib/sse.ts`.

### KPI Guardian (demo simulation)
- Production: APScheduler cron + Resend email with tokenised CTAs.
- Demo: "Run Goal Review" button (F6 → A2) fires a fake KPI miss, launches a Kaizen directly.

---

## 6. DATA LAYER (Supabase)
Schema created in attached `supabase_schema.sql`. Key tables:
- **Operational data**: roles, candidates, pipeline_events, hires, interviewers, offer_outcomes, keywords, posting_keywords, job_descriptions, industry_benchmarks.
- **Adzuna postings**: `adzuna_postings` with unique constraint on `adzuna_id`. Semantic dedup logic (concurrent hire vs. repost) implemented in application code.
- **Kaizen state**: `kaizen_sessions` (with `output_state` JSONB), `kaizen_nodes`.
- **Audit/invocation**: `agent_invocations`.
- **RAG corpus**: `corpus_chunks` (pgvector).

---

## 7. BUILD PLAN (PER PHASE 2A EMAIL)
- **Saturday**: Foundation, data layer, RAG ingest, LiteLLM, MCP analytics module, specialist agents, sync DMAIC engine, detection layer, Meta-Orchestrator, API gateway, frontend skeleton. Hard gate: full Kaizen runs end-to-end synchronously.
- **Sunday**: DBOS wrap (durable workflows), MCP server lift. Also prepare presentation.
- **Monday (Freedom Day)**: Real Adzuna ingestion, Google OAuth integration, live Tavily/NewsAPI, polish.
- **Tuesday AM**: Final dry-runs, README, submission.

---

## 8. GOTCHAS (FROM PHASE 2A)
- Supabase Edge Embeddings dimension consistency.
- DBOS workflow IDs = session_id.
- SSE headers to bypass CDN buffering.
- Modal cold start mitigation (pre-ping /health).
- Adzuna rate limits, cache aggressively.
- Google OAuth redirect URIs must be pre-registered.
- Five Whys wall clock ~15-25s due to Opus extended thinking.
- React Flow performance okay with ~30 nodes.

---

## 9. IP PROTECTION
- Private GitHub repo, share with their usernames.
- Copyright footer in source.
- Record a Loom walkthrough.

---

*Context document updated April 26, 2026 (Session 5).*