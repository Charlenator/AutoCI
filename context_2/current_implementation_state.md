# AutoCI — Current Implementation State

> **Date**: 2026-04-29 | **Branch**: main | **Commit**: f50dcec
> This document describes only what exists *right now* — no planned features, no gaps, no wishlist.

---

## 1. File Structure (Active Source Files)

```
backend/
├── main.py                          # FastAPI entry point + startup seed
├── mcp_server.py                    # MCP Analytics Tool Server stub
├── modal_config.py                  # Modal deployment config (stub)
├── test_all.py                      # 5-level test suite
├── api/
│   ├── routes/
│   │   ├── chat.py                  # POST /chat/query
│   │   ├── metrics.py               # GET /metrics/cost
│   │   ├── rag.py                   # POST /rag/ingest
│   │   ├── stream.py                # GET /sessions/:id/stream
│   │   ├── trigger.py               # POST /trigger/manual, /trigger/goal-review
│   │   └── knowledge.py            # POST /knowledge/seed, /knowledge/update
│   ├── agents/
│   │   ├── detection/
│   │   │   ├── d1_internal_benchmarking.py
│   │   │   ├── d2_external_benchmarking.py
│   │   │   └── d3_gap_analysis.py
│   │   ├── kaizen/
│   │   │   ├── k1_define.py
│   │   │   ├── k2_measure.py
│   │   │   ├── k3_analyse_host.py
│   │   │   ├── k4_five_whys.py
│   │   │   ├── k5_ishikawa.py
│   │   │   ├── k6_improve.py
│   │   │   └── k7_control.py
│   │   └── specialists/
│   │       ├── s1_translation.py
│   │       ├── s2_rag.py
│   │       ├── s3_sql.py
│   │       └── s4_research.py
│   ├── tools/
│   │   ├── t1_mcp_analytics.py
│   │   ├── t2_validation_interceptor.py
│   │   ├── t3_litellm_router.py
│   │   └── t4_embeddings.py
│   ├── workflows/
│   │   └── o2_meta_orchestrator.py
│   └── sse/
│       └── __init__.py              # push_event + 6 event builder functions
frontend/
├── next.config.ts
├── package.json
├── tsconfig.json
├── postcss.config.mjs
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Route: /  (marketing splash page)
│   │   ├── globals.css
│   │   ├── dashboard/
│   │   │   └── page.tsx             # Route: /dashboard  (main app)
│   │   └── system-diagram/
│   │       ├── page.tsx             # Route: /system-diagram
│   │       └── system-diagram.css
│   └── lib/
│       └── sse.ts                   # connectSSE() — EventSource wrapper
supabase/
├── supabase_schema.sql              # Full schema (11 tables, 2 extensions, 1 RPC)
└── seed.sql                         # Synthetic seed data
CONTEXT/
├── AutoCI_Overview.md
├── AGENTS.md
├── CLAUDE.md
├── build_progress.txt
├── task_requirement_analysis.md
├── current_implementation_state.md
├── AutoCI_Context_Session5.md
├── supabase_schema.sql
└── checklists/                      # 16 CSV checklists
```

---

## 2. Frontend — What's Rendered

### Route: `/` (landing page)
- Hero text: "AutoCI System — Six Sigma-powered recruitment analytics"
- Links: "View System Architecture" → `/system-diagram`, "Documentation" → nextjs.org

### Route: `/dashboard` (the actual app)
**Layout**: 2-panel (left sidebar + centre timeline)

**Left sidebar (300px, white bg):**
- 💬 Chat header with cost ticker (monospace, `$cost.toFixed(6)`)
- 📡 Activity Log — dark terminal-style box showing last 12 `step_progress` events (yellow=in progress, green=done, blue=active)
- Chat messages — scrollable list showing user/assistant/system messages with bold markdown rendering
- Chat input — text input + Send button (requires session from Kaizen)
- 🌱 Seed RAG Corpus button — POST `/knowledge/seed` (DMAIC docs + benchmarks + case studies)
- 📚 Update External Knowledge button — POST `/knowledge/update` (fetches Adzuna+Tavily+NewsAPI for Java+Python Developer)
- 🎯 Run Kaizen button — POST `/trigger/goal-review`, opens SSE stream

**Centre panel (flex: 1, grey bg):**
- Top bar: "📊 Kaizen Results" + active phase indicator (pulsing dot + phase name) + cost
- Scrollable timeline of 6 DMAIC phases, each a card:
  - Detection (🔍) → Define (📋) → Measure (📏) → Analyse (🔬) → Improve (💡) → Control (📊)
  - Each card shows: phase icon + label + status badge (Running/✓ Complete/Waiting)
  - Output entries grouped by agent ID (D1, D2, D3, S4, K1-K7), each with a colored left-border and agent badge
  - Phase cards transition colors: idle=white 50% opacity → active=yellow glow → complete=green tint
- Empty state: 🎯 "Ready to Investigate" with instructions to click Run Kaizen

**State management**: All React `useState` in a single component — 15 state variables, no Context/Redux.

### Route: `/system-diagram`
- Static system architecture page with colored swimlane sections (Frontend, API Gateway, Agents, Data/External)
- Each component is listed with its node ID (F1-F10, A1-A9, O1-O3, D1-D3, K1-K7, S1-S4, T1-T4, DB1-DB5, E1-E8)

### API calls from frontend:
| Button/Action | Method | Endpoint | Body |
|---|---|---|---|
| Run Kaizen | POST | `/trigger/goal-review` | (none) |
| Send chat | POST | `/chat/query` | `{session_id, message}` |
| Seed RAG | POST | `/knowledge/seed` | (none) |
| Update Knowledge | POST | `/knowledge/update` | `{roles: ["Java Developer","Python Developer"]}` |
| SSE stream | GET | `/sessions/:id/stream` | EventSource |
| Cost ticker | — | derived from SSE `cost` events | — |

**API_BASE**: `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"`

---

## 3. Backend — Routes & Logic

### API Routes (all registered in `main.py`)

| Route | Method | Module | What it does |
|---|---|---|---|
| `/trigger/manual` | POST | `trigger.py` | Creates session, runs full Kaizen async via `threading.Thread(target=o2.run_full_kaizen, ...)` |
| `/trigger/goal-review` | POST | `trigger.py` | Same as manual — creates session + runs Kaizen async |
| `/sessions/{id}/stream` | GET | `stream.py` | SSE endpoint — yields events from `sse.event_generator(session_id)` |
| `/chat/query` | POST | `chat.py` | Takes `{session_id, message}`, runs S1→S2 or S1→S3 routing |
| `/metrics/cost` | GET | `metrics.py` | Returns total cost from `agent_invocations` table |
| `/rag/ingest` | POST | `rag.py` | File upload → paragraph chunk → embed via T4 → insert to `corpus_chunks` |
| `/knowledge/seed` | POST | `knowledge.py` | Seeds 3 corpora (dmaic_methodology, role_benchmarks, kaizen_case_studies) |
| `/knowledge/update` | POST | `knowledge.py` | Fetches Tavily+NewsAPI+Adzuna for given roles, persists + embeds |
| `/health` | GET | `main.py` | `{"status": "ok", "service": "AutoCI"}` |

### SSE Event Types (6 types, defined in `sse/__init__.py`)

| Type | Builder | Fields | When emitted |
|---|---|---|---|
| `node_status` | `make_node_event()` | agent_id, status, label, data | Agent starts/completes |
| `phase_transition` | `make_phase_event()` | phase, status, data | DMAIC phase starts/completes |
| `output_delta` | `make_output_event()` | phase, content, agent_id | Per-line output text |
| `step_progress` | `make_step_event()` | agent_id, step, progress, total | Fine-grained agent progress |
| `cost` | `make_cost_event()` | total_usd, session_id | End of Kaizen |
| `connected` | (sent automatically) | session_id | On SSE connection |

### Kaizen Lifecycle (`o2_meta_orchestrator.py` — `run_full_kaizen()`)

Runs sequentially with SSE events between every step:

```
1. D1 — Internal Benchmarking (TTF, conversion rates, source yields, offer acceptance)
2. S4 — Market Research (4 steps: Tavily → NewsAPI → Adzuna → Persist)
3. D2 — External Benchmarking (industry comparison via Adzuna benchmarks)
4. D3 — Gap Analysis (delta > 20% = amber, > 50% = red, kaizen_required flag)
5. [Gate] If kaizen_required=false → stop
6. K1 — Define (SIPOC + problem statement + financial impact + KPI target)
7. K2 — Measure (baseline KPIs from pipeline data)
8. K3 — Analyse Host (spawns K4 + K5)
9. K4 — Five Whys (5 sequential atomic LLM calls via LiteLLM)
   K5 — Ishikawa (6 parallel branch calls)
10. K6 — Improve (intervention cards + recommendation)
11. K7 — Control (Kanban board 30/60/90 day items)
12. Cost event → frontend ticker
```

### Agent Details (Current Implementation)

| Agent | File | Class/Method | Approach |
|---|---|---|---|
| **D1** | `d1_internal_benchmarking.py` | `D1InternalBenchmarkingAgent.run()` | Uses `AnalyticsLibrary` for TTF, conversion rates, source yields. Decorated with `@validate_agent_output` |
| **D2** | `d2_external_benchmarking.py` | `D2ExternalBenchmarkingAgent.run()` | Queries `industry_benchmarks` table, compares internal TTF vs benchmarks, returns delta_pct |
| **D3** | `d3_gap_analysis.py` | `D3GapAnalysisAgent.analyze()` | Compares internal vs external, flags >20% deltas as amber, >50% as red. Uses T3 LiteLLM for narrative |
| **S1** | `s1_translation.py` | `TranslationAgent.classify()` | Keyword-based routing: metric keywords → SQL agent, other → RAG agent |
| **S2** | `s2_rag.py` | `RAGAgent.retrieve()` | Embeds query → calls `match_chunks` RPC → returns top-k chunks with context |
| **S3** | `s3_sql.py` | `SQLAgent.execute()` | Known metric keywords → T1 analytics. Unknown → T3 generates SQL |
| **S4** | `s4_research.py` | `ResearchAgent` | 3 public methods: `search_tavily()`, `search_news()`, `search_adzuna()`. All synchronous httpx. Persists to `adzuna_postings` + `corpus_chunks` |
| **K1** | `k1_define.py` | `K1DefineAgent.run()` | LLM generates SIPOC + problem statement + financial impact |
| **K2** | `k2_measure.py` | `K2MeasureAgent.run()` | LLM computes baseline KPIs from pipeline data |
| **K3** | `k3_analyse_host.py` | `K3AnalyseHostAgent.run()` | Spawns K4 (5 sequential calls + step callback) and K5 (6 parallel calls) |
| **K4** | `k4_five_whys.py` | — | 5 sequential atomic LLM calls to Opus via LiteLLM |
| **K5** | `k5_ishikawa.py` | — | 6 parallel branch LLM calls (People, Process, Technology, Environment, Materials, Measurement) |
| **K6** | `k6_improve.py` | `K6ImproveAgent.run()` | LLM generates intervention cards + Impact/Effort matrix |
| **K7** | `k7_control.py` | `K7ControlAgent.run()` | LLM builds 30/60/90 day Kanban board |

---

## 4. Tools & Middleware

| Tool | File | What it does |
|---|---|---|
| **T1** | `t1_mcp_analytics.py` | Static methods: `time_to_fill()`, `stage_conversion_rate()`, `stage_dropoff_rate()`, `offer_acceptance_rate()`, `source_yield()`. No LLM. |
| **T2** | `t2_validation_interceptor.py` | `@validate_agent_output` decorator — checks Pydantic schema, sample size >= 5, z-score outliers > 3σ |
| **T3** | `t3_litellm_router.py` | `LiteLLMRouter.complete()` — routes to claude-opus-4-7-thinking (Five Whys), claude-sonnet-4-6 (orchestration/narrative), deepseek-chat (tagging/parsing). Logs every call to `agent_invocations`. |
| **T4** | `t4_embeddings.py` | `EmbeddingService` — calls OpenAI `text-embedding-ada-002` for 1536-d vectors. Falls back to zero-vector if `OPENAI_API_KEY` not set. |

---

## 5. Database — Supabase Schema (Current)

**Extensions**: `uuid-ossp`, `vector` (pgvector)

**Tables (11):**

| Table | Key Columns | Purpose |
|---|---|---|
| `roles` | role_id, title, department, target_ttf_days, opened_date, status | Job roles being recruited |
| `interviewers` | interviewer_id, name, department, calendar_id, average_scheduling_lag_days | Interviewers (calendar_id column exists but never populated) |
| `candidates` | candidate_id, role_id (FK), source_channel, applied_date, external_id | Applicants |
| `pipeline_events` | event_id, candidate_id (FK), stage, event_date, outcome, interviewer_id (FK) | Stage transitions (Applied→Screening→Interview→Offer→Hire) |
| `hires` | hire_id, candidate_id (FK), role_id (FK), offer_date, start_date, accepted | Successful hires |
| `offer_outcomes` | outcome_id, candidate_id (FK), offer_date, salary_offered, accepted, counter_reason | Offer details |
| `industry_benchmarks` | role_title, median_ttf_days, p25_ttf_days, p75_ttf_days, source, region | External benchmarks |
| `adzuna_postings` | id, role_title, company, salary_min, salary_max, location, posted_date, raw_json | Live job postings from Adzuna API |
| `kaizen_sessions` | session_id, status, output_state (JSONB), created_at | Kaizen session persistence |
| `kaizen_nodes` | node_id, session_id (FK), agent_id, status, output (JSONB) | Per-agent output tracking |
| `corpus_chunks` | chunk_id, corpus_name, chunk_text, metadata, embedding (VECTOR(1536)) | RAG knowledge base |

**RPC Function (1):**
- `match_chunks(query_embedding VECTOR(1536), match_threshold FLOAT, match_count INT, corpus_filter TEXT DEFAULT NULL)` — cosine similarity search over `corpus_chunks`, returns `chunk_id, chunk_text, corpus_name, metadata, similarity`

**Indexes:**
- `corpus_chunks_embedding_idx` — `IVFFLAT` index on `corpus_chunks.embedding` with `lists=100`

---

## 6. Current Data Population (from startup + seed)

**RAG Corpus** — 65 chunks across 5 corpora (verified working with real non-zero embeddings):

| Corpus | Chunks | Source |
|---|---|---|
| `dmaic_methodology` | 20 | Seeded on startup — 5 DMAIC docs (overview, SIPOC, Five Whys, Kanban, TTF) |
| `role_benchmarks` | 16 | Seeded on startup — 4 role docs (Java, PM, UX, conversion funnel) |
| `kaizen_case_studies` | 12 | Seeded on startup — 3 case studies (TTF reduction, offer acceptance, scheduling) |
| `market_intel` | 15 | Tavily web search results (previously ingested) |
| `industry_news` | 2 | NewsAPI articles (previously ingested) |

**Seed Data** (`seed.sql`):
- 4 roles (Senior Java Developer, Product Manager, UX Designer, Data Engineer)
- 3 interviewers with random scheduling lag (4.5, 2.8, 6.1 days)
- 12 candidates across various source channels (LinkedIn, Referral, Seek, Company Website, Agency)
- 24 pipeline events spanning stages from Applied to Hired
- 4 hires (Java Dev hired after 35d, PM after 42d, UX after 28d, Data Eng after 38d)
- 4 offer outcomes (3 accepted, 1 rejected — salary too low)
- 4 industry benchmarks (Java Dev: 35d median, PM: 40d, UX: 30d, Data Eng: 32d)

---

## 7. SSE Data Flow

```
Frontend                                  Backend
────────                                  ──────
1. Click "Run Kaizen" ──POST────────▶  /trigger/goal-review
2. Receive session_id ◀───200 JSON────  response: {session_id}
3. new EventSource(url) ──GET────────▶  /sessions/{id}/stream
4.                      ◀───SSE────────  push_event() from O2 orchestrator
   • node_status    → updates phase status + chat messages
   • phase_transition → updates current phase + card highlighting
   • output_delta   → appends to phase output arrays (grouped by agent)
   • step_progress  → adds to activity log (last 12 shown, up to 100 stored)
   • cost           → updates cost ticker
   • connected      → "🔗 Connected to session: abc12345..."
5. SSE closed on unmount or new Kaizen
```

---

## 8. Startup Sequence (`main.py`)

1. Load `.env` (supabase URL + key, API keys)
2. Create FastAPI app with CORS (allow all origins)
3. Create Supabase client, LiteLLM Router, MetaOrchestrator
4. On startup event:
   - Verify Supabase connectivity (SELECT 1 from industry_benchmarks)
   - Pre-seed RAG corpus (3 corpora, skips if already present)
5. Inject `supabase`, `llm`, `orchestrator` into `request.state` via middleware
6. Register 7 route modules from `api/routes/`

---

## 9. What Does NOT Exist (confirmed absent)

These are NOT in the codebase:
- **No Google OAuth** — no OAuth route, no token storage, no Google Calendar/Gmail API calls
- **No email integration** — no Resend/SendGrid/SMTP, no email reading/sending
- **No calendar integration** — no calendar API calls, `interviewers.calendar_id` column exists but never populated
- **No DBOS deployment** — `o1` is a dashed placeholder in architecture, `modal_config.py` is a stub
- **No Vercel deployment** — no `vercel.json`, no build/deploy GitHub Action
- **No Modal deployment** — `modal_config.py` exists but is a minimal stub
- **No real OpenAI key** — embeddings fall back to zero-vectors (OPENAI_API_KEY not set)
- **No conversation history management** — chat stores messages in frontend `useState` only
- **No data cleansing/verification pipeline** — API data stored raw, no deduplication or cross-verification
- **No CSV/PDF export** — no download buttons for Kaizen reports or pipeline data
- **No authentication** — no login, no session auth, CORS allows all origins
- **No real APScheduler** — scheduling mentioned in overview but not implemented
