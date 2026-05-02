# AutoCI — Current Implementation State

> **Date**: 2026-05-02 | **Branch**: main | **Last commit**: b6e9e6c (uncommitted changes from Phases 0-3 below)
> This document describes only what exists *right now* — no planned features, no gaps, no wishlist.

---

## 0. Recent Changes (2026-05-02 — Phases 0-4 + 4.5 wave-A fixes of `please-read-context-plan-fluffy-bentley.md`)

These changes are **in working tree, not yet committed**.

**Phase 4.5 §I — small-fix close-out (2026-05-02 evening)**:
- `K6` (improve agent) rewritten: now uses JSON-output prompt; real Impact/Effort/Priority extraction from LLM response (was hardcoded Medium/Medium/55 for every intervention). Optional `rag_agent` constructor arg + `citation_id_offset` so K6's R-IDs continue from K3's count. Citations bubble up via `ImproveOutput.rag_citations`.
- Corpus dedup: `routes/knowledge.py:seed_rag_corpus` now actually skips populated corpora (the docstring was lying). Dedup also done on the live DB — 156 duplicate rows removed; 5/3/4 unique chunks remain in dmaic_methodology / kaizen_case_studies / role_benchmarks.
- DeepSeek USD pricing in T3 router: `compute_cost_usd()` helper computes from token counts when LiteLLM returns 0. Rates locked at **$0.14/M input**, **$0.07/M cached input**, **$0.28/M output** (Donna's call 2026-05-02 — keep these explicit).
- Adzuna `redirect_url` persisted: migration `003_adzuna_redirect_url.sql` applied; `s4_research.search_adzuna` captures it; `_persist_adzuna` writes it. Foundation for Phase 5 §D's clickable citation drawer.
- HITL countdown removed (manual-advance only): `HITL_TIMEOUT_SECONDS` cranked to 86400 (24h, effectively infinite); frontend countdown effect removed; UI label changed from "Auto-advance in Xs" to "manual advance". Reason: timer was racing the Ask path — user submits a question, timer expires before the answer streams back.
- Real-time cost ticker: orchestrator now calls `_emit_cost_snapshot(session_id)` after each phase's writeup. Dashboard ticker updates incrementally instead of waiting for end-of-Kaizen.
- System diagram (`/system-diagram`) rewritten with all 36+ components (frontend / API / orchestrator / detection / kaizen / specialists / tools / DB / external APIs / planned), color-coded by family, properly spaced across 9 lanes. Animated edges on hot path (Kaizen flow). Legend with edge-type key. Doubles as a Phase 8 submission asset.
- CONTEXT folder cleanup: deleted `CONTEXT/checklists/` (20 CSV files, all duplicate of this doc + plan).

(K6 RAG details are in the Phase 4.5 T2.1 entry below — the same pattern is now active in K4, K5, and K6.)

**Phase 0 — CONTEXT folder cleanup**
- Archived `AutoCI_Context_Session5.md`, `build_progress.md`, `build_progress.txt` to `CONTEXT/archive/`
- Deleted duplicate `CONTEXT/supabase_schema.sql` (verified byte-identical to `supabase/supabase_schema.sql`)
- Renamed `current_implementation_state.md` → `IMPLEMENTATION_STATE.md` (this file)

**Phase 1 — Token-level cost tracking**
- `backend/api/tools/t3_litellm_router.py`: `InvocationLog` gains `input_tokens`, `output_tokens`, `cached_tokens`. LiteLLM's `response.usage` now captured.
- Schema: `agent_invocations` gains 3 INT columns (added in canonical schema; idempotent migration at `supabase/migrations/001_add_token_columns.sql`).
- `/metrics/cost` returns per-model token totals + `total_input_tokens`, `total_output_tokens`, `total_cached_tokens`. Accepts optional `?session_id=` filter.
- SSE `cost` event carries token fields; orchestrator pushes them on Kaizen completion.
- Dashboard cost ticker (both spots) shows token counts in hover tooltip.

**Phase 2 — Multi-KPI detection**
- Schema: `industry_benchmarks` gains `conversion_rate_median`, `offer_acceptance_median`, `source_yield_median`. `roles` gains `target_conversion_rate`, `target_offer_acceptance_rate`. Migration: `supabase/migrations/002_multi_kpi_benchmarks.sql` (also backfills industry medians for the 5 existing role families).
- `supabase/seed_generator.py` (deterministic, seed=42) — produces per-role KPI fingerprints. Output committed at `supabase/seed_v2_pipeline.sql`: **148 candidates, 468 events, 32 hires, 32 offers** (vs. old 20/46/3/4).
- `t1_mcp_analytics.py`: new `applied_to_hire_rate()` formula.
- `d1_internal_benchmarking.py`: returns clean `kpis` dict alongside legacy fields. `InternalBenchmarkResult` schema gained `kpis` field.
- `d2_external_benchmarking.py`: new `run_multi_kpi(role_title, kpis)` method — direction-aware (lower-is-better for TTF, higher-is-better for the rest). Legacy `run()` kept.
- `d3_gap_analysis.py`: accepts both legacy TTF list and the new comparisons dict; flags whichever KPIs land amber/red.
- `o2_meta_orchestrator.py`: D2 call uses `run_multi_kpi`; SSE output reports all 3 KPIs with traffic-light icons.
- `/metrics/kpis?role_title=X&region=Y`: NEW endpoint — returns `{kpi, value, target, benchmark, status, delta_pct}` per tile WITHOUT triggering a Kaizen.
- Dashboard: 3 KPI tiles above the timeline. Refreshes on mount and on Kaizen completion.

**Phase 3 — Generic Kaizen**
- `/trigger/manual`: now correctly threads `problem_brief` (was being misrouted as `role_title`). Adds optional `target_kpi` field. New `TriggerResponse` echoes resolved role + target_kpi.
- `/trigger/goal-review`: auto-picks the role with the largest target/benchmark gap. Falls back to old default if no benchmarks loaded.
- `o2_meta_orchestrator.run_full_kaizen()`: signature gains `problem_brief` and `target_kpi` kwargs. Either of them forces the Kaizen to proceed past detection even if D3 finds no gap (so user-driven investigations work). Threads both into K1.
- `k1_define.py`: rewritten with three-mode framing: brief-driven (user wins), KPI-targeted, or gap-driven. SIPOC and KPI target no longer TTF-anchored by default.

**Live Supabase state** (applied 2026-05-02 via Supabase MCP):
- Migration 001 (token columns on `agent_invocations`) ✅
- Migration 002 (multi-KPI benchmark cols + role targets, 10 benchmark rows backfilled) ✅
- Seed v2 (148 candidates, 468 events, 32 hires, 32 offers, role-fingerprinted) ✅

**Single-model DeepSeek pipeline** (set 2026-05-02): every task in `TASK_ROUTING` resolves to `deepseek-chat`. Claude/Anthropic config + secrets removed from `t3_litellm_router.py`, `test_all.py`, `modal_config.py`. Router structure preserved so multi-model routing can return without touching call sites.

**Role-scoped pipeline data** (fixed 2026-05-02): `O2.fetch_pipeline_data(role_title=...)` and `/metrics/kpis` now filter `candidates` / `pipeline_events` / `hires` / `offer_outcomes` by `role_id`. Previously D1 + K2 + the KPI tile route all computed against the global pipeline regardless of which role the Kaizen targeted, producing identical KPI values across roles.

**Phase 4.5 T2.1 — K4 + K5 retrieve case studies via RAG** (2026-05-02):
- `K4FiveWhysAgent.__init__` and `K5IshikawaAgent.__init__` accept an optional `rag_agent`. K3 forwards it down. Orchestrator (`O2.__init__`) passes `self.s2` (the existing `RAGAgent` instance from Phase 4 wave A) when constructing K3.
- K4 does ONE retrieval up front (top 4 chunks, `corpus_filter="kaizen_case_studies"`) and injects the same case-study block into all 15 why-call system prompts (5 whys × 3 perspectives). Citations surface as `R1`–`R4`.
- K5 does ONE retrieval per branch (top 2 chunks, `corpus_filter="kaizen_case_studies"`) — 6 retrievals total, queried as `"{category} root causes: {problem}"`. Citation IDs are offset by K4's count to avoid collision.
- K3 aggregates all citations into a new `AnalyseOutput.rag_citations: list[dict]` field. Each citation: `{id, source: "rag_chunk", corpus, snippet, branch?}`. The orchestrator surfaces them in detection-phase SSE output ("📚 8 case study chunks retrieved from `kaizen_case_studies`...").
- `WriteupAgent` system prompt extended to teach the LLM that R-IDs are available; writeups can cite them when a finding has prior-Kaizen precedent.
- **Verified 2026-05-02** with Senior Java Developer Kaizen: K4's "why" answers cited `R2` and `R4` inline across all 3 perspectives (process / people / data); analyse writeup headline became *"Pay is not the problem; screening and offer process are."* combining the S1 salary signal with the R2/R4 case-study evidence; control writeup explicitly cited *"paying 73% above the Adzuna median (S1)"*.
- Token cost: 21,455 input / 7,757 output / 2,304 cached — +17% input vs T1.2 baseline, which is the cost of injecting ~600 tokens of case-study text into 15 K4 calls + 6 K5 calls. DeepSeek caching helps but each call still re-pays ~150-200 tokens after the cache hit. Acceptable trade for the analytical jump.
- **Known small bug (not introduced by T2.1)**: K4's why-chain converges too quickly — Why 4 and Why 5 of the same perspective often produce identical answers. Pre-existing prompt deficiency in K4; the chain isn't drilling deeper after the first concrete root cause. Filed for later.

**Phase 4.5 T1.2 — D2 computes live salary signal vs Adzuna** (2026-05-02):
- `D2._live_salary_signal(role_title)` queries `hires.salary` (where `accepted=true`) and `adzuna_postings.salary_min/max` (filtered `ILIKE %role%`), computes the median delta, and returns a structured signal with `status ∈ {ok, low_confidence, insufficient_data}` so downstream is honest about sample-size limitations. Severity is direction-aware (paying *below* market is unfavourable; above is fine).
- `O2.run_full_kaizen` surfaces the signal as a new D2 SSE output line ("✅ **Salary vs live market** (low confidence): R780k our hires (n=3) vs R450k Adzuna median (n=3) — +73.3%") and folds it into `market_data["salary_signal"]` so all 6 writeups see it.
- `WriteupAgent._format_market_data` renders the signal with stable ID `S1` at the top of the market block (highest-value item, derived signal), with explicit handling for `insufficient_data` ("cite this gap if pay is part of your hypothesis").
- **Verified 2026-05-02** with two opposing demos:
  - **Senior Java Developer** (`status="low_confidence"`, +73.3% above Adzuna median): writeup chain pivoted from the default "pay is the issue" reflex to *"Pipeline volume, not pay, is the bottleneck"* (measure) → *"this is a process failure, not a candidate quality or compensation issue"* (analyse) → "Interview 2 redesign is the highest-leverage fix" (improve). The signal was used to *eliminate* a hypothesis, not just reinforce one.
  - **UX Designer** (`status="insufficient_data"`, only 1 of 10 Adzuna postings disclosed salary): the writeup correctly cited the data gap rather than fabricating a comparison.
- Token cost: 18,364 input / 6,642 output / 2,432 cached — ~2% over T1.1 baseline; salary signal block hits the cache.

**Phase 4.5 T1.1 — `market_data` flows into the writeup agent** (2026-05-02):
- `WriteupAgent.run()` gains `market_data: dict | None` kwarg. New helper `_format_market_data` renders Adzuna postings (capped 6) / Tavily results (capped 4) / NewsAPI articles (capped 4) into a stable-ID block (A1/A2/T1/T2/N1/N2) the LLM can cite.
- System prompt extended: tells the LLM the new citation IDs are available and to call out market data that contradicts or reinforces internal data. Schema's `evidence_citations[].source` now lists `kaizen_node | adzuna_posting | tavily | news | rag_chunk`.
- `O2._emit_writeup` gains a `market_data` kwarg. `run_full_kaizen` threads the same `market_data` snapshot (built once at detection time) into all 6 writeup calls.
- **Verified 2026-05-02**: A UX Designer Kaizen with `problem_brief="why is offer acceptance so low for UX hires"` produced writeups citing `A1` (R180k Adzuna posting) alongside `D1`/`D2` kaizen-node citations across detection → define → measure → analyse → improve → control. Token cost: **18,006 input / 6,344 output / 2,432 cached** (vs. pre-T1.1 baseline of 16,288 / 7,684 / 1,920 — only +1,718 input tokens, output actually *decreased* as writeups got more concrete). DeepSeek prompt caching absorbs most of the new market block on subsequent writeup calls.

**Phase 4 wave A — HITL gates + writeup agent** (2026-05-02, backend only — frontend wave B pending):
- NEW agent `backend/api/agents/kaizen/k_writeup.py` (`WriteupAgent`) — single DeepSeek call per phase, returns Pydantic-validated `{headline, tl_dr, key_findings[], hypothesis, evidence_citations[], next_step, open_questions[]}`. Temperature 0.3.
- NEW SSE event type `phase_writeup` (built by `make_phase_writeup_event`) carrying the writeup JSON. Emitted once per completed phase.
- NEW HITL queue infrastructure in `api/sse/__init__.py`: thread-safe `queue.Queue` per session. `wait_for_hitl_response(session_id, timeout=30)` blocks the orchestrator (running on a `run_in_executor` worker thread) until `put_hitl_response()` is called from the FastAPI event loop.
- NEW endpoint `POST /sessions/{id}/respond` (in `api/routes/sessions.py`) — body `{decision: "advance"|"ask"|"abort", message?}`. The `ask` path routes the message through S1 → S2 or S3 inline and emits chat-style `output_delta` events tagged with the current phase, then re-blocks for the next decision.
- Orchestrator changes: after every DMAIC phase (detection→define→measure→analyse→improve, but NOT after final control), `O2._emit_writeup` runs the writeup agent and emits the SSE event, then `O2._await_hitl` blocks for up to 30s. On timeout → auto-advance. On abort → `KaizenSessionResult.phase="aborted"`. `O2.s1`/`s2`/`s3` instances added so the ask path doesn't need a chat route round-trip.

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
├── supabase_schema.sql              # Full schema (11 tables, 2 extensions, 1 RPC) — UPDATED Phase 1+2
├── seed.sql                         # Original synthetic seed (20 candidates, 46 events) — superseded
├── seed_generator.py                # NEW (Phase 2) — deterministic generator
├── seed_v2_pipeline.sql             # NEW (Phase 2) — 148 candidates, 468 events, 32 hires, 32 offers
├── rpc_match_chunks.sql             # pgvector cosine search RPC
└── migrations/
    ├── 001_add_token_columns.sql    # NEW (Phase 1) — input/output/cached_tokens on agent_invocations
    └── 002_multi_kpi_benchmarks.sql # NEW (Phase 2) — conversion/OAR/yield benchmark cols + role targets
CONTEXT/
├── AutoCI_Overview.md
├── AGENTS.md
├── CLAUDE.md
├── build_progress.txt
├── task_requirement_analysis.md
├── current_implementation_state.md
├── AutoCI_Context_Session5.md
├── supabase_schema.sql
(checklists/ folder removed 2026-05-02 — content covered by this file + plan)
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
| `/trigger/manual` | POST | `trigger.py` | **(Phase 3 update)** Body: `{role_id?, role_title?, problem_brief?, target_kpi?}`. Brief or target_kpi forces Kaizen to proceed past detection. |
| `/trigger/goal-review` | POST | `trigger.py` | **(Phase 3 update)** Optional body `{role_title?, region?}`. Auto-picks worst role from KPI gaps if no role specified. |
| `/sessions/{id}/stream` | GET | `stream.py` | SSE endpoint — yields events from `sse.event_generator(session_id)` |
| `/chat/query` | POST | `chat.py` | Takes `{session_id, message}`, runs S1→S2 or S1→S3 routing |
| `/metrics/cost` | GET | `metrics.py` | **(Phase 1 update)** Returns total + per-model token breakdown + USD. Optional `?session_id=`. |
| `/metrics/kpis` | GET | `metrics.py` | **NEW (Phase 2)** `?role_title=&region=` → 3-tile KPI snapshot with target/benchmark/status. |
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
| `cost` | `make_cost_event()` | total_usd, session_id, **input_tokens, output_tokens, cached_tokens** *(Phase 1)* | End of Kaizen |
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
| **D1** | `d1_internal_benchmarking.py` | `D1InternalBenchmarkingAgent.run()` | **(Phase 2)** Uses `AnalyticsLibrary` for TTF, conversion rates, source yields, OAR. Returns clean `kpis` dict (`{time_to_fill, conversion_rate, offer_acceptance}` with `value/unit/label`) alongside legacy fields. |
| **D2** | `d2_external_benchmarking.py` | `D2ExternalBenchmarkingAgent.run() / run_multi_kpi()` | **(Phase 2)** `run_multi_kpi(role, kpis)` compares all 3 KPIs vs benchmark medians; severity is direction-aware (lower-is-better for TTF, higher-is-better for the rest). Legacy TTF-only `run()` retained. |
| **D3** | `d3_gap_analysis.py` | `D3GapAnalysisAgent.analyze()` | **(Phase 2)** Accepts both legacy TTF list and new comparisons dict. Flags any KPI rated amber/red by D2; secondary stage-dropoff signal kept. |
| **S1** | `s1_translation.py` | `TranslationAgent.classify()` | Keyword-based routing: metric keywords → SQL agent, other → RAG agent |
| **S2** | `s2_rag.py` | `RAGAgent.retrieve()` | Embeds query → calls `match_chunks` RPC → returns top-k chunks with context |
| **S3** | `s3_sql.py` | `SQLAgent.execute()` | Known metric keywords → T1 analytics. Unknown → T3 generates SQL |
| **S4** | `s4_research.py` | `ResearchAgent` | 3 public methods: `search_tavily()`, `search_news()`, `search_adzuna()`. All synchronous httpx. Persists to `adzuna_postings` + `corpus_chunks` |
| **K1** | `k1_define.py` | `K1DefineAgent.run()` | **(Phase 3)** Three-mode framing — `problem_brief` (user-driven, wins), `target_kpi` (KPI-targeted), or gap-driven. SIPOC and KPI target generalised — no longer TTF-anchored by default. |
| **K2** | `k2_measure.py` | `K2MeasureAgent.run()` | LLM computes baseline KPIs from pipeline data |
| **K3** | `k3_analyse_host.py` | `K3AnalyseHostAgent.run()` | Spawns K4 (5 sequential calls + step callback) and K5 (6 parallel calls) |
| **K4** | `k4_five_whys.py` | — | 5 sequential atomic LLM calls to DeepSeek via LiteLLM (single-model pipeline) |
| **K5** | `k5_ishikawa.py` | — | 6 parallel branch LLM calls (People, Process, Technology, Environment, Materials, Measurement) |
| **K6** | `k6_improve.py` | `K6ImproveAgent.run()` | LLM generates intervention cards + Impact/Effort matrix |
| **K7** | `k7_control.py` | `K7ControlAgent.run()` | LLM builds 30/60/90 day Kanban board |

---

## 4. Tools & Middleware

| Tool | File | What it does |
|---|---|---|
| **T1** | `t1_mcp_analytics.py` | Static methods: `time_to_fill()`, `stage_conversion_rate()`, `stage_dropoff_rate()`, `offer_acceptance_rate()`, `source_yield()`. No LLM. |
| **T2** | `t2_validation_interceptor.py` | `@validate_agent_output` decorator — checks Pydantic schema, sample size >= 5, z-score outliers > 3σ |
| **T3** | `t3_litellm_router.py` | `LiteLLMRouter.route()` — every task class (Five Whys, SQL gen, orchestration, narrative, translation, research, tagging, extraction, parsing) routes to `deepseek-chat`. Single-model pipeline with one API key; router structure preserved for future multi-model routing. **(Phase 1)** Captures `response.usage.prompt_tokens`, `completion_tokens`, and `prompt_tokens_details.cached_tokens` into `agent_invocations`. |
| **T4** | `t4_embeddings.py` | `EmbeddingService` — calls OpenAI `text-embedding-ada-002` for 1536-d vectors. Falls back to zero-vector if `OPENAI_API_KEY` not set. |

---

## 5. Database — Supabase Schema (Current)

**Extensions**: `uuid-ossp`, `vector` (pgvector)

**Tables (11):**

| Table | Key Columns | Purpose |
|---|---|---|
| `roles` | role_id, title, department, target_ttf_days, **target_conversion_rate, target_offer_acceptance_rate** *(Phase 2)*, opened_date, status | Job roles being recruited |
| `interviewers` | interviewer_id, name, department, calendar_id, average_scheduling_lag_days | Interviewers (calendar_id column exists but never populated) |
| `candidates` | candidate_id, role_id (FK), source_channel, applied_date, external_id | Applicants |
| `pipeline_events` | event_id, candidate_id (FK), stage, event_date, outcome, interviewer_id (FK) | Stage transitions (Applied→Screening→Interview→Offer→Hire) |
| `hires` | hire_id, candidate_id (FK), role_id (FK), offer_date, start_date, accepted | Successful hires |
| `offer_outcomes` | outcome_id, candidate_id (FK), offer_date, salary_offered, accepted, counter_reason | Offer details |
| `industry_benchmarks` | role_family, region, median_ttf_days, p25_ttf_days, p75_ttf_days, **conversion_rate_median, offer_acceptance_median, source_yield_median** *(Phase 2)*, sample_size, data_source | External benchmarks |
| `adzuna_postings` | id, role_title, company, salary_min, salary_max, location, posted_date, raw_json | Live job postings from Adzuna API |
| `kaizen_sessions` | session_id, status, output_state (JSONB), created_at | Kaizen session persistence |
| `kaizen_nodes` | node_id, session_id (FK), agent_id, status, output (JSONB) | Per-agent output tracking |
| `agent_invocations` | invocation_id, session_id (FK), from_agent, to_agent, model_used, cost_usd, duration_ms, **input_tokens, output_tokens, cached_tokens** *(Phase 1)* | Per-LLM-call cost trace |
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
- **No Google OAuth** — no OAuth route, no token storage, no Google Calendar/Gmail API calls *(targeted: Phase 6)*
- **No email integration** — no Resend/SendGrid/SMTP, no email reading/sending *(targeted: Phase 6)*
- **No calendar integration** — no calendar API calls, `interviewers.calendar_id` column exists but never populated *(targeted: Phase 6)*
- **No HITL between phases** — orchestrator runs end-to-end on a background thread *(targeted: Phase 4)*
- **No phase writeup agent** — phase outputs are structured JSON only, no narrative summaries *(targeted: Phase 4)*
- **No DBOS deployment** — `o1` is a dashed placeholder in architecture, `modal_config.py` is a stub
- **No Vercel deployment** — no `vercel.json`, no build/deploy GitHub Action
- **No Modal deployment** — `modal_config.py` exists but is a minimal stub
- **No real OpenAI key** — embeddings fall back to zero-vectors (OPENAI_API_KEY not set)
- **No conversation history management** — chat stores messages in frontend `useState` only
- **No data cleansing/verification pipeline** — API data stored raw, no deduplication or cross-verification *(partially addressed by Phase 6's CV pipeline)*
- **No CSV/PDF export** — no download buttons for Kaizen reports or pipeline data
- **No authentication** — no login, no session auth, CORS allows all origins
- **No real APScheduler** — scheduling mentioned in overview but not implemented
- **DeepSeek USD cost not computed by LiteLLM** — `response._cost` returns `0.0` for `deepseek-chat` because LiteLLM's pricing table doesn't have it via the OpenAI-compat path we use. Token counts (input/output/cached) ARE captured correctly. Fix options: hardcode per-1M rates in T3 and compute from token counts (≈$0.27/M input, $1.10/M output), or pass `custom_llm_provider="deepseek"` so LiteLLM looks up its pricing.
