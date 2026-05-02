# AutoCI — "What Next" Implementation Plan

> **Last touched**: 2026-05-02 (mid-execution update — Phase 4 wave A + role-scope fix + DeepSeek consolidation landed; data-flow architecture review folded in as Phase 4.5).
>
> A Plan-of-record file. The strategic decisions below were locked in the session that wrote this. Execution discoveries are folded back in *as amendments*, not by rewriting earlier sections.

## Status at a glance (2026-05-02)

| Phase | Status | Notes |
|---|---|---|
| 0 — CONTEXT cleanup | ✅ done | Archive, single living state doc, deleted dup schema. |
| 1 — Token-level cost tracking | ✅ done | Token columns + `/metrics/cost` + cost ticker token tooltip all live. **Caveat**: USD pricing is `$0.00` for DeepSeek (LiteLLM doesn't auto-price it); see *Mid-execution discoveries* below. |
| 2 — Multi-KPI detection | ✅ done | 3 tiles, role-scoped, `seed_v2_pipeline.sql` applied (148 candidates / 468 events / 32 hires / 32 offers). |
| 3 — Generic Kaizen | ✅ done | `problem_brief` threading + auto-pick worst role + K1 three-mode framing all working. |
| **4 — HITL + writeup agent** | ✅ wave A backend, ⏳ wave B frontend | Backend smoke-test passes end-to-end (27 invocations, 5 HITL gates drained). Frontend: doc cards + clickable open-questions + custom-Kaizen launcher landed; Donna iterating on UX details (writeup placement, ask-mode visibility, Kanban honesty). |
| **4.5 — Data flow rewire** | ✅ T1.1 + T1.2 + T2.1 done — writeup gets `market_data`; D2 reads live Adzuna salary; K4/K5 retrieve case studies. T2.2 (Evidence Selector) + T3 (cleanup) deferred. |
| 5 — RAG chatbot as landing + animated React Flow | 📋 not started — **scope expanded** by 2026-05-02 challenge audit (clickable citations w/ full chunk view, explicit query transformation, three-layer self-check). See Plan amendments. |
| 6 — Tools + extract→cleanse→verify pipeline (**Part 2 deliverable**) | 📋 not started — re-scoped: CV→JD pipeline + Calendar + Gmail post-Kaizen email debrief + verified-output tables. |
| **7 — Cloud deployment (Vercel + Modal)** *(NEW)* | 📋 not started — **was Out of Scope; now mandatory per challenge brief**. |
| **8 — Submission deliverables** *(NEW)* | 📋 not started — 1-page tech summary + 6-8 screenshots + 5-min screen-record + live demo URL. |

---

## Plan amendments — 2026-05-02 (challenge audit)

After re-reading the Inference Group challenge brief end-to-end, the existing plan covers most requirements but misses several literal asks. The amendments below were locked with Donna and supersede earlier scope decisions.

### A. Web deployment is now IN scope (was Out of Scope)
- Brief: *"Deploy the RAG interface on the web (e.g., via Streamlit, Gradio, or native platform deployment)."*
- New **Phase 7 — Cloud deployment**: Next.js → Vercel; FastAPI → Modal (or equivalent — Render/Fly works too). All dev work from now on must stay deploy-ready: env vars only (no localhost hardcoding), `NEXT_PUBLIC_API_URL` as the single source of frontend→backend wiring, Modal-compatible Python (`modal_config.py` already scaffolded — clean it up).
- Donna's directive: *"just make sure everything remains vercel/modal-ready."*

### B. "≥3 structured documents" — Supabase tables count as structured content
- The brief examples (CSV, JSON, tabular PDF) are illustrative, not exhaustive. **Relational tables are structured content by definition.**
- Reframe the deliverable: AutoCI exposes structured content via *both* RAG (6 corpora in `corpus_chunks`) **and** SQL (11 Supabase tables: `roles`, `candidates`, `pipeline_events`, `hires`, `offer_outcomes`, `industry_benchmarks`, `kaizen_sessions`, `agent_invocations`, `adzuna_postings`, `corpus_chunks`, `keywords/job_descriptions/posting_keywords/keyword_outcome_stats`). The S3 SQLAgent path uses the structured tables directly.
- **Frontend deliverable** (Phase 5): a "Knowledge sources" panel listing every structured source — RAG corpora *and* tables — with row/chunk count, schema/columns, and a sample. Reviewer sees the whole inventory in one place.
- No new files needed.

### C. Query transformation must be explicitly visible (Phase 5 expansion)
- Brief: *"Demonstrate prompt control or query transformation that helps the agent interpret user intent and return structured answers."*
- Today's S1 keyword routing doesn't surface the transformation step.
- **Phase 5 work**: convert S1 to LLM-based intent classification AND emit a NEW SSE event `query_transformation` carrying `{user_query, normalized_intent, route: "s2_rag"|"s3_sql", chosen_formula?, params?}`. Frontend renders this above the answer as a small "How I read your question" card showing:
  - The original prompt
  - The normalized intent
  - Which agent it was routed to (and why — keyword(s) that triggered)
  - For SQL/T1 paths: the analytics formula chosen (e.g. `time_to_fill(role='Senior Java Developer', region='SA')`) and the param values
  - For RAG paths: the rewritten retrieval query + corpus filter
- This makes the "user input → tool/formula" step a first-class artifact rather than a hidden internal step.

### D. Source traceability — citations must be viewable / linkable in full
- Brief: *"Highlight how your RAG pipeline ensures data relevance, context retention, and traceability of sources."*
- Donna's directive: *"ensure sources are not only listed, but can be viewed or linked to in full."*
- **Phase 5 work**: every citation chip becomes a clickable link to a side drawer or modal that shows:
  - **RAG chunks (R-IDs)**: full `chunk_text` + `corpus_name` + `chunk_id` + `similarity` + `metadata` JSONB.
  - **Adzuna postings (A-IDs)**: full posting (title, company, salary range, location, posted_date) + `redirect_url` to the live Adzuna listing.
  - **Tavily / News (T-/N-IDs)**: full title + content + source URL (clickable, opens in new tab).
  - **Salary signal (S-ID)**: the SQL queries used (median Adzuna + median internal hires) + the raw rows that fed the median + sample size + computed delta.
  - **Kaizen-node (D-/K-IDs)**: link to the corresponding agent's structured output JSON in the timeline (scroll-to or modal).
- Backend: S2 / S3 / writeup must persist enough info per citation that the frontend can render the drawer without round-trips. Add `citations` table (or extend existing structures) so a Kaizen's citations are queryable post-run.

### E. Email tool — post-Kaizen debrief to self (replaces inbox-reading scope)
- Donna's directive: *"let's add in an email summary post-kaizen. Sending a full compiled write-up of the kaizen (debrief) to self."*
- Smarter than reading inboxes — produces a concrete artifact the reviewer can see.
- **NEW agent**: `backend/api/agents/kaizen/k_debrief.py` — runs after K7's writeup, compiles all 6 phase writeups + final KPIs + intervention impact/effort table + Kanban + citation list into a single Markdown email body. Sends via Gmail API to the Kaizen-trigger user (or creates a draft if `--draft` flag).
- New SSE event `email_sent` with `{message_id, draft_url?, recipient}`.
- Reuses the OAuth flow from Phase 6's CV-prep work — they share the Google Workspace integration. **Move the OAuth scaffolding to a shared module so both Phase 6 (Calendar + draft) and the email-debrief share it.**
- This counts as the "Email" tool for Part 2 ✅.

### F. Verified-output display — proper tables (not loose text)
- Donna's directive: *"display the findings in proper tables, including an impact/effort table for fixes, implementing the required pipeline."*
- **Phase 4 wave B / Phase 5 work**: the timeline currently dumps prose lines. Replace with structured tables for:
  1. **Findings table** in detection: `KPI | our value | target | benchmark | severity | delta% | source`
  2. **Impact/Effort matrix** in improve: `Intervention | Impact | Effort | Priority | Quadrant | Owner | Due` — render as both a sortable table AND a visual 2×2 quadrant scatter (Impact y-axis, Effort x-axis).
  3. **Kanban table** in control (already structured — render as proper columns, not stacked text).
  4. **Citations table** at the bottom of each writeup card: `# | source | id | snippet | link` — sortable, with the "link" column being clickable.
  5. **Verified-output table** for Phase 6 CV→JD pipeline: `extracted field | normalized value | verified? | source | flag`.
- These tables are also what gets rendered into the **email debrief** body (item E) — same data, two sinks.

### G. Phase 6 — re-frame as the explicit Part 2 deliverable
- Header in the plan should explicitly say "Phase 6 — Part 2 deliverable" so anyone (reviewer, future Claude session) sees the connection.
- Make the data-quality verification *visible* — the verified-output table from item F is the concrete deliverable for the brief's *"output a cleansed attendee list with missing fields flagged"* example.
- Phase 6 keeps Calendar + CV→JD work; email work moves to item E (post-Kaizen debrief). Both share the OAuth module.

### H. Submission deliverables (NEW Phase 8)
- 1-2 page technical summary (markdown). NOT the internal `IMPLEMENTATION_STATE.md` — a polished one-pager for the reviewer.
- 6-8 screenshots: KPI dashboard, a Kaizen run with HITL gates, a writeup card with citation chips + drawer open, Interview Prep CV→JD verified-output table, Knowledge Sources inventory panel, system architecture diagram, post-Kaizen email debrief in inbox.
- 5-minute screen-record walkthrough.
- Live demo URL (from Phase 7).

### I. Small fixes worth doing (not their own phase)
- **Corpus dedup bug**: `routes/knowledge.py:seed_rag_corpus` re-inserts on every call rather than upserting. `dmaic_methodology` started at 5 chunks, now sits at 65. Fix: skip-if-exists by chunk-text hash, or upsert by `(corpus_name, chunk_text)` unique constraint. ~30 min.
- **DeepSeek USD pricing**: hardcode rates in T3 so the cost ticker stops showing $0.00. ~30 min.
- **Live URL fields on Adzuna citations**: `s4_research.py` already gets `redirect_url` from the Adzuna API — persist it on `adzuna_postings` so item D's drawer can link out. ~15 min.

---

## Context

Charle's AutoCI submission landed at **~55% of the technical challenge requirements** per `CONTEXT/task_requirement_analysis.md`:
- **RAG (Part 1): ~85%** — solid (real pgvector, 5 corpora, 65 chunks, S1→S2/S3 routing). Weak on traceability and conversation history.
- **Tools/Pipeline (Part 2): ~20%** — only **1 of 3** required tools (Web). No Calendar, no Email, no extract→cleanse→verify pipeline.

The submission deadline (28 April 2026) has passed. This iteration is for portfolio polish and feature expansion, not the original interview deliverable. That gives us scope to do this well.

**The user's `what_next.txt` asks for two big things:**
1. A long list of feature changes (cost tracking, multi-KPI detection, RAG-chatbot landing, generic Kaizen, HITL between phases, single-page UI with animated React Flow).
2. A strategic question: **should we split into two apps?** (Interview Scheduler/Prep + CI Tool)

---

## Strategic Recommendation: YES, split — but inside one repo, one Next.js app, two top-level tabs

### Why split
The current AutoCI is a strong narrative ("LSS as structured CoT for LLMs") but it **fails the challenge's core tooling requirement**. Bolting Calendar + Email into AutoCI would muddy that narrative — it doesn't naturally need them. An **Interview Prep tool** consumes Calendar + Email + Web cleanly and is also a textbook "extract → cleanse → verify → display" pipeline (CV PDF → extract skills → match to JD → flag missing fields → draft invite email). Two apps, two crisp stories, both backed by the same Supabase + LiteLLM + RAG foundation.

### Why one repo
Same Supabase, same LiteLLM router, same RAG corpus, same SSE infra. The split is purely UI + orchestration. A monorepo with shared `backend/api/` modules and a Next.js shell that toggles between two apps is the lightest viable structure.

### Restart vs amend: **AMEND**
The foundation is solid: D1-D3, K1-K7, S1-S4 work, SSE streams cleanly, RAG has real embeddings, agents are decorator-validated. Throwing this away costs ~70% of working code for no gain. Risky changes (orchestrator pause/resume, schema migrations) get done surgically.

---

## Confirmed Decisions

1. **Split into two tabs.** AutoCI (existing, polished) + Interview Prep (new). Single Next.js shell. Shared backend.
2. **HITL = block-and-wait with 30s auto-advance.** Orchestrator converts to async; awaits per-session asyncio queue between phases.
3. **RAG self-checking = three layers:**
   - **Source citations** on every answer (chunk_id + similarity → `[1][2]` chips with hover preview).
   - **Confidence-gated retry**: LLM self-rates confidence; if below threshold, reformulate query and retrieve once more (cap at 1 retry to avoid spirals).
   - **Numeric reasonableness check**: any returned metric is bounded against a sanity range (e.g. TTF must be in [1, 365] days, OAR in [0, 1]); out-of-range answers get re-verified or flagged with a warning before being shown.
   - SQL-vs-RAG cross-checking deferred (not selected).

---

## Proposed Final Architecture (post-changes)

```
Next.js shell (single page, top tabs)
├── Tab 1: AutoCI (default)
│   ├── Default view: RAG chatbot (left, ~25%) + animated React Flow diagram (right, ~75%)
│   ├── Toggle: hide diagram → full-width chat
│   ├── Toggle: KPI dashboard view (3 KPIs vs goal, traffic-light)
│   ├── Toggle: Kaizen view (per-phase writeup + HITL "approve / ask question / reject")
│   └── Source: existing /dashboard, restructured
└── Tab 2: Interview Prep
    ├── Upload CV (PDF)
    ├── Select / paste JD
    ├── Generate fit summary (hits / misses / 3-line CV digest)
    ├── Pull interviewer calendar → propose 3 slot options
    ├── Draft invite email (interviewer + candidate)
    └── Send via Gmail API (or "copy-to-clipboard" fallback for demo safety)
```

---

## Phased Implementation Plan

Six phases, ordered by dependency. Each phase is shippable and independently testable.

### Phase 0 — Cleanup (small, do first) ✅ DONE
- **Files**: `CONTEXT/build_progress.md`, `build_progress.txt`, `current_implementation_state.md`, `AutoCI_Context_Session5.md`
- Consolidate to two living docs: `CONTEXT/AutoCI_Overview.md` (the "what") + `CONTEXT/IMPLEMENTATION_STATE.md` (the "where we are now"). Archive the rest under `CONTEXT/archive/`.
- Update `task_requirement_analysis.md` after Phase 5 lands (Calendar+Email = 3/3).
- Delete `CONTEXT/supabase_schema.sql` (duplicate of `supabase/supabase_schema.sql` — confirmed identical).

### Phase 1 — Token-level cost tracking ✅ DONE (with caveat)
- **Files**: `backend/api/tools/t3_litellm_router.py`, `supabase/supabase_schema.sql`, `backend/api/routes/metrics.py`
- LiteLLM exposes `response.usage.prompt_tokens` / `completion_tokens` — pull these into `InvocationLog`.
- Migration: add columns to `agent_invocations`: `input_tokens INT`, `output_tokens INT`, `cached_tokens INT`. Idempotent `ALTER TABLE … ADD COLUMN IF NOT EXISTS`.
- `/metrics/cost` returns per-session totals broken out by model + tokens + USD.
- Surface in cost ticker as hover-tooltip (USD on top, tokens underneath).

⚠️ **Caveat surfaced during execution**: `response._cost` from LiteLLM returns `0.0` for `deepseek-chat` because LiteLLM's pricing table doesn't have it via the OpenAI-compat path the router uses. Token counts are captured correctly. **Filed for later** in `IMPLEMENTATION_STATE.md` § 9. Fix options: hardcode per-1M rates in T3 (~$0.27/M input, ~$1.10/M output) and compute USD from token counts; or pass `custom_llm_provider="deepseek"` so LiteLLM looks up its own pricing.

### Phase 2 — Multi-KPI detection (3 KPIs vs goal) ✅ DONE
- **Files**: `supabase/supabase_schema.sql`, `supabase/seed.sql`, `backend/api/agents/detection/d2_external_benchmarking.py`, `d3_gap_analysis.py`, frontend KPI panel.
- **Schema**: extend `industry_benchmarks` to carry conversion_rate_median, offer_acceptance_median, source_yield_median (currently TTF only — confirmed by Explore agent).
- **Seed**: enrich `seed.sql` to ~150-200 pipeline events across 5 roles over 6 months so conversion / OAR / yield are statistically meaningful (currently only 46 events, 3 hires — too sparse). Use deterministic synthetic generator script committed at `supabase/seed_generator.py`.
- **3 KPIs to surface**: Time-to-Fill (TTF), Stage Conversion Rate (Applied→Hire), Offer Acceptance Rate (OAR).
- **Frontend**: KPI tile row at top of AutoCI tab — each tile shows current vs goal + traffic light (green/amber/red) + sparkline.

🔧 **Bug fixed during execution (2026-05-02)**: D1 + K2 + `/metrics/kpis` were all running on the *global* pipeline regardless of which role was being investigated, so every role returned identical KPI values (TTF=34.16, OAR=78.1%). Fixed by threading `role_title` through `O2.fetch_pipeline_data(role_title=...)` and adding `.eq("role_id", ...)` / `.in_("candidate_id", ...)` filters in `/metrics/kpis`. Now each role surfaces its own fingerprint — UX Designer correctly lights up two reds (conv 10.7%, OAR 60%); Java Dev shows red conversion + amber OAR; PM is healthy. **The handoff doc's "Java TTF should land amber/red" prediction was wrong because of this bug, not because the seed generator was off.**

### Phase 3 — Generic Kaizen (per-KPI or user-supplied) ✅ DONE
- **Files**: `backend/api/routes/trigger.py`, `backend/api/workflows/o2_meta_orchestrator.py`, `backend/api/agents/kaizen/k1_define.py`.
- `/trigger/manual` already accepts `problem_brief` (confirmed in code). Wire frontend to it: per-KPI "Investigate" button (passes the failing KPI as the brief) AND a "Custom investigation" textarea.
- `K1_define` receives the brief and shapes SIPOC around it — currently it's hardcoded to TTF in some prompt scaffolding; generalize.
- **Hardcoded "Senior Java Developer" demo flow goes away** (replace `/trigger/goal-review` with a parameterised version that picks the worst-performing KPI).

### Phase 4 — HITL + per-phase Amazon-narrative writeup
- **Files**: `backend/api/workflows/o2_meta_orchestrator.py`, `backend/api/sse/__init__.py`, NEW `backend/api/routes/sessions.py` (endpoint `/sessions/:id/respond`), NEW `backend/api/agents/kaizen/k_writeup.py` (writeup specialist), frontend dashboard.

- **Writeup specialist agent (NEW)** ✅ wave A: a small "narrative" agent that runs *after* each DMAIC phase. Takes the structured phase output + accumulated context (prior writeups, references, gap data) and returns an Amazon-narrative-style 0.5–1 page document. **Single DeepSeek call per phase** (the original plan said Sonnet — we consolidated the whole pipeline to DeepSeek mid-execution; see *Mid-execution discoveries*). Schema:
  ```
  { headline, tl_dr, key_findings[], hypothesis, evidence_citations[], next_step, open_questions[] }
  ```
  Each `evidence_citations[]` entry is `{ source: "kaizen_node|rag_chunk|adzuna_posting|news|tavily", id, snippet }` so refs survive into the export. The orchestrator already accumulates structured phase outputs — the writeup agent just consumes them.
  Implementation choice (recommended): a *standalone agent* not a prompt knob, because (a) Amazon-narrative tone needs its own system prompt, (b) the writeup agent's output schema is enforced separately from each phase's analytical schema, (c) we can swap models / temperature independently (lower temp for narrative — landed at 0.3).
- **SSE event** ✅ wave A: new `phase_writeup` event carrying the JSON above. Frontend renders in the chat panel as a structured "doc" card (headline + TL;DR + key findings as bullets + hypothesis + next step). Citations rendered as `[1][2]` chips that hover/click to source.
- **HITL pause** ✅ wave A — *implementation deviated from plan*: the original plan called for `await asyncio.Queue.get(timeout=...)`. In execution we kept the orchestrator running on a worker thread (`run_in_executor`) and used a thread-safe `queue.Queue` (`api/sse/__init__.py:wait_for_hitl_response`). Reason: converting every LLM call inside the orchestrator to async + `run_in_executor` was a much larger surface change for no real-world benefit (each Kaizen runs on its own task; the `queue.Queue` is safe across the worker-thread → event-loop boundary). 30s timeout, "advance"/"ask"/"abort" decisions, all working. `POST /sessions/:id/respond` lives in a new `api/routes/sessions.py` (not a chat.py endpoint).
- **"Ask" path**: the orchestrator instantiates `s1`/`s2`/`s3` directly and routes the user's message inline, streaming the answer back as `output_delta` events tagged with the current phase. After the answer streams, the orchestrator re-blocks for the next decision. Cleaner than a chat-route round-trip.
- **Per-phase technical log unchanged** — the structured `output_delta` events keep streaming into the diagram view. Writeup is additive, not a replacement.
- **Trigger UI examples** ✅ wave B (frontend): dashboard has a row of suggested generic Kaizens above the chat input — "UX offer drop", "Java conv ⤓", "Data Eng funnel", "Source mix", "PM scheduling lag". Each is a one-click `/trigger/manual` with a preset brief and matching role. **Plus** a 🎯 button next to the chat input that fires the typed text as a custom Kaizen brief (escape hatch). Suggested-Kaizens row design ended up as compact pill buttons rather than the originally-planned card row, to keep the sidebar narrow.
- **Frontend wave B status**: doc cards rendering with citation chips ✅; clickable open-questions ✅ (mid-pause clicks pre-fill ask box; post-pause clicks pre-fill chat box); writeup card placement is *AFTER* agent technical output, not before (Donna's call — synthesis at the bottom reads more naturally); chat works without an active Kaizen ✅; ask-mode UI rebuilt as multi-line textarea after `autoFocus` was triggering disorienting page scroll.
- **NOT delivered in wave B (yet)**: animated React Flow diagram (deferred to Phase 5); zustand state management (still 18+ useStates — accepted technical debt for now).

### Phase 4.5 — Data flow rewire (NEW, surfaced 2026-05-02)

**Why this exists**: a mid-execution architecture review revealed that S4 fetches Adzuna postings, Tavily web results, and NewsAPI articles, persists them to `adzuna_postings` and `corpus_chunks` (corpora `market_intel` / `industry_news` / `adzuna_postings`) — and then **almost nothing reads any of it back** during a Kaizen run.

**Map of the actual flow today** (from the Explore-agent audit):
```
S4 (during Kaizen)  ──┬──▶ adzuna_postings (DB)   ❌ never SELECTed during Kaizen
                       ├──▶ corpus_chunks (DB)    ❌ never RAG-retrieved during DMAIC
                       └──▶ in-memory market_data ✅ used ONCE in D3's prompt only
                                                  ❌ discarded after D3
                                                  ❌ never reaches D2, K1-K7, writeup
```

**The three real gaps**:
1. **Persisted data is read-once / write-many.** `adzuna_postings` grows on every Kaizen but no SELECT queries it. `market_intel` / `industry_news` / `adzuna_postings` corpora accumulate in `corpus_chunks` but RAG (S2) is only called from the chat path — never from a K-agent.
2. **No KPI-aware filtering.** A TTF Kaizen and an OAR Kaizen both get the same generic Adzuna salary blob in D3, even though OAR cares about competitor pay and TTF really doesn't.
3. **D2 ignores live market data entirely.** "External Benchmarking" only reads the static seeded `industry_benchmarks` table — the live external data we just paid to fetch isn't part of benchmarking.

**Plus schema waste**: `adzuna_postings.expired_date` / `is_repost` / `original_posting_id`, and `corpus_chunks.metadata` JSONB, are written but never read.

**Fix tiered by effort/payoff**:

**Tier 1 — small, high payoff (1-2 hrs each)**
- **T1.1: Pass `market_data` to K_WRITEUP.** Single signature change in `O2._emit_writeup`. Writeups can then cite "Adzuna shows R180k–R240k for UX in CT vs our R175k offers" with a real `evidence_citation` chip. This alone makes the data earn its keep narratively.
- **T1.2: D2 consults Adzuna for live salary medians.** `SELECT median(salary_min) FROM adzuna_postings WHERE title ILIKE role` joins live data into external benchmarking; static `industry_benchmarks` becomes the *fallback*, not the only source.

**Tier 2 — medium, structural (half day each)**
- **T2.1: K4 / K5 retrieve case studies via RAG.** Five Whys and Ishikawa pull `corpus_name='kaizen_case_studies'` filtered by similar KPI before the LLM call. "What root causes have other companies found for low OAR?" is exactly what RAG is for, and right now it's collecting dust during DMAIC.
- **T2.2: Add a thin "Evidence Selector" before each K phase.** One DeepSeek call per phase that takes (role, KPI, phase) and returns `{chunk_ids, postings_filter}`. K agents consume only the curated slice. Stops irrelevant news articles from polluting Five Whys context.

**Tier 3 — cleanup (low priority but easy)**
- **T3.1: Use `corpus_chunks.metadata` for filtered retrieval.** Already populated with `{role, source, topic}`; just filter on it during S2 calls.
- **T3.2: Either use or drop** `expired_date` / `is_repost` / `original_posting_id`. Posting freshness (`expired_date < now`) would be a meaningful filter — old postings shouldn't shape current benchmarks.

**Recommended sequencing**: T1.1 first (30-min change, every Kaizen visibly richer). Then T1.2. Then revisit Tier 2 only if the writeups still feel narratively thin. Tier 3 is end-of-cycle hygiene.

---

### Phase 5 — RAG chatbot as landing + animated React Flow diagram (UI rewrite) + challenge-audit upgrades

**Scope expanded 2026-05-02** — see Plan amendments §B, §C, §D, §F. The original UI rewrite still stands; new deliverables fold into the same phase because they share frontend touchpoints.

**Original scope (still planned):**
- **Files**: `frontend/src/app/dashboard/page.tsx`, `frontend/src/lib/sse.ts`, NEW `frontend/src/components/SystemFlow.tsx` (animated diagram), retire `frontend/src/app/page.tsx`'s marketing splash, retire `frontend/src/app/system-diagram/page.tsx` (merged into dashboard).
- New `/` route IS the dashboard. Three views, toggleable from a top bar:
  - **Chat** (default) — RAG chatbot panel (left, ~25%) + animated `SystemFlow` (right, ~75%); diagram has hide button collapsing to full-width chat.
  - **KPI dashboard** — 3 KPI tiles (Phase 2) + per-KPI "Investigate" buttons.
  - **Kaizen** — phase-by-phase writeup + HITL controls + drawer with full structured artefacts.
- **Animated diagram** uses existing `reactflow` v11. Each SSE `node_status` event lights up the matching node + animates the edge from previous active node. Re-uses styling already in `system-diagram/page.tsx`.
- **Chat enhancements** (S1/S2/S3 changes in `backend/`):
  - S1 routing becomes LLM-based (DeepSeek tagging) — current keyword router is brittle.
  - S2/S3 results return `chunk_id` + `similarity` + `corpus_name`. Frontend renders citations as `[1][2]` chips that on hover show the source chunk.
  - **Self-checking layer 1 — citations**: every answer carries chunk_id refs.
  - **Self-checking layer 2 — confidence retry**: LLM emits a `confidence: low|med|high` tag with each answer; on `low`, S2 reformulates query and retrieves once more. Hard cap of 1 retry.
  - **Self-checking layer 3 — numeric sanity**: numeric outputs validated against bounds defined per-metric (TTF ∈ [1, 365], OAR ∈ [0, 1], conversion ∈ [0, 1]). Out-of-range → flag + re-verify against T1 analytics formulas.
  - Trigger Tavily/NewsAPI dynamically when user query mentions "latest", "current market", "recent news" etc. Result chunks ingested to vector store live.
- **State management**: introduce `zustand` (small, lightweight) — current 18 useStates in one component is unsustainable.

**Added 2026-05-02 (challenge audit):**
- **Knowledge Sources panel** (per Plan amendment §B): a top-bar or drawer view listing every structured source — RAG corpora *and* Supabase tables — with row/chunk count, schema/columns, sample rows. One-glance proof that AutoCI uses ≥3 structured documents.
- **Query transformation card** (per amendment §C): NEW SSE event `query_transformation` carrying `{user_query, normalized_intent, route, chosen_formula, params, retrieval_query, corpus_filter}`. Frontend renders this above the answer as a "How I read your question" card.
- **Citation drawer** (per amendment §D): every chip is clickable. Drawer shows full chunk text / posting / article / SQL+rows depending on source type. Outbound URL where applicable (Adzuna `redirect_url`, Tavily / News source URL).
- **Findings + Impact/Effort tables** (per amendment §F): replace prose lines in detection / improve / control with proper sortable tables; render the impact/effort matrix as a 2×2 quadrant scatter alongside the table.

### Phase 6 — Tools + extract→cleanse→verify pipeline (**Part 2 deliverable**)
- **Files**: NEW `backend/api/agents/specialists/s5_interview_prep.py`, NEW `backend/api/routes/interview.py`, NEW `frontend/src/app/interview-prep/page.tsx` (or top-level tab inside the merged dashboard), Google OAuth scaffolding.
- **CV → JD fit**:
  - PDF parse via `pypdf` (server-side).
  - Extract skills/experience via DeepSeek extraction prompt.
  - JD already exists in `job_descriptions` table.
  - Compare embeddings + LLM-narrated hits/misses. Persist as `cv_evaluations` (new table).
- **Calendar**:
  - Google OAuth via `google-auth-oauthlib` — store refresh token in new `oauth_tokens` table.
  - Read interviewer's free/busy via Calendar API; surface 3 slot options.
- **Email draft (CV-prep flow)**:
  - Compose via Gmail draft API (NOT auto-send — "review then send" UX is safer for demo).
  - Email body = candidate fit summary + slot options.
- **NEW — Post-Kaizen email debrief** (per Plan amendment §E): after a Kaizen finishes, `K_DEBRIEF` agent compiles all 6 phase writeups + KPI snapshot + intervention impact/effort table + Kanban + citation table into one Markdown email body, sends to the trigger user via Gmail. New SSE event `email_sent`. Reuses the OAuth module from this phase. **This is the "Email" tool that satisfies Part 2 — concrete artifact in the user's inbox.**
- **Verified-output table** (per amendment §F): the CV→JD pipeline emits a structured table — `extracted field | normalized value | verified? | source | flag` — rendered in the frontend AND included in the email debrief. Reviewer sees the literal "extract → cleanse → verify → display" loop the brief describes.
- **This phase fixes the technical challenge Part 2 gap**: 3 tools (Calendar, Email, Web), full extract→cleanse→verify pipeline (CV → skills → match → flagged missing fields), verified-output displayed as a proper table.

### Phase 7 — Cloud deployment (Vercel + Modal) — *NEW 2026-05-02*

**Why**: the challenge brief literally says *"Deploy the RAG interface on the web"*. Localhost is a fail on a strict reading. Was originally Out of Scope; Donna's call to flip it.

**Files**: `vercel.json` (NEW), `modal_config.py` (already scaffolded — clean up + verify), `frontend/.env.production`, `backend/.env.production`, GitHub Action (optional).

- **Frontend → Vercel**: `frontend/` deploys cleanly as a Next.js project. `NEXT_PUBLIC_API_URL` becomes the Modal endpoint URL. CORS is already wide-open (Phase 1+).
- **Backend → Modal**: `modal_config.py` already has the scaffolding. Verify it deploys, all secrets present, Supabase connectivity intact, SSE works behind the Modal proxy (test the `text/event-stream` flow end-to-end).
- **Constraint going forward**: every commit must be Vercel/Modal-ready. No `localhost:*` URLs in committed code (use env vars). No new Python deps that break Modal's Debian-slim base. Test the deploy on every Phase 5 / Phase 6 PR.

### Phase 8 — Submission deliverables — *NEW 2026-05-02*

The bits that aren't code but *are* the deliverable.

- **Tech summary one-pager** (`SUBMISSION.md` or `submission/README.md`) — 1-2 pages of polished Markdown describing the approach, tools, data sources, architecture, key reasoning steps. **Not** the internal `IMPLEMENTATION_STATE.md`. Aimed at a reviewer who has 5 minutes.
- **Screenshots** (`submission/screenshots/`):
  1. KPI dashboard with the 3 tiles + traffic-light statuses
  2. A live Kaizen run mid-flight with HITL gate visible
  3. A writeup card with citation chips + drawer open showing full chunk
  4. Knowledge Sources panel listing all corpora + tables
  5. Interview Prep CV→JD verified-output table with flagged fields
  6. Post-Kaizen email debrief in inbox
  7. System architecture diagram (the existing `/system-diagram` page or a new render)
  8. (optional) Impact/Effort 2×2 quadrant
- **5-minute screen-record walkthrough** — fire a Kaizen, click through HITL gates, ask a question via Ask, show the email debrief, switch to Interview Prep, run a CV through, show the deployed URL.
- **Live demo URL** — Vercel URL from Phase 7. Pinned in the tech summary.

---

## Critical files

| File | Phase | Status | What changes |
|---|---|---|---|
| `supabase/supabase_schema.sql` | 1, 2, 6 | ✅ for 1+2 / 📋 for 6 | Token cost cols + conversion/OAR benchmarks landed; `oauth_tokens` / `cv_evaluations` still TODO |
| `supabase/seed_v2_pipeline.sql` (generated by `seed_generator.py`) | 2 | ✅ applied | 148 candidates / 468 events / 32 hires / 32 offers — committed to live Supabase |
| `backend/api/tools/t3_litellm_router.py` | 1 | ✅ | Token usage capture; **Claude config stripped** — single-model DeepSeek |
| `backend/api/workflows/o2_meta_orchestrator.py` | 3, 4 | ✅ | Generic `problem_brief`; HITL queue gates; phase writeup emit; **role-scoped fetch**; S1/S2/S3 instances for ask path |
| `backend/api/sse/__init__.py` | 4 | ✅ | `make_phase_writeup_event` + thread-safe `queue.Queue`-backed HITL response API |
| `backend/api/routes/trigger.py` | 3 | ✅ | `/trigger/manual` + `/trigger/goal-review` (auto-pick worst role) |
| `backend/api/routes/sessions.py` | 4 | ✅ | NEW — `POST /sessions/:id/respond` for HITL decisions |
| `backend/api/agents/kaizen/k_writeup.py` | 4 | ✅ | NEW — Amazon-narrative writeup specialist (single DeepSeek call/phase, temp 0.3) |
| `backend/api/agents/kaizen/k7_control.py` | 4.5 fix | ✅ | Rewritten — all items "To Do", owner/due/KPI derived per-intervention |
| `backend/api/routes/metrics.py` | 2 | ✅ | `/metrics/kpis` role-scoped; per-KPI status + delta |
| `backend/api/routes/chat.py` + `s1/s2/s3` | 5 | 📋 | LLM-based routing, citations, self-check — not started |
| `backend/api/agents/specialists/s5_interview_prep.py` | 6 | 📋 | NEW — CV/JD parse + match |
| `backend/api/agents/google_oauth.py` (or shared module) | 6 | 📋 | NEW — Google OAuth scaffolding shared by Calendar (Phase 6 CV-prep) + Gmail (Phase 6 email debrief) |
| `backend/api/agents/kaizen/k_debrief.py` | 6 | 📋 | NEW — compiles Kaizen artefacts → Markdown email body → sends via Gmail API. Emits `email_sent` SSE event. |
| `backend/api/routes/interview.py` | 6 | 📋 | NEW |
| `backend/api/routes/sources.py` | 5 | 📋 | NEW — `/sources` endpoint listing every corpus + SQL table for the Knowledge Sources panel |
| `frontend/src/app/dashboard/page.tsx` | 4, 5 | ⏳ | Phase 4 wave B largely done; Phase 5 view-toggle restructure + tables + clickable citations not started |
| `frontend/src/components/CitationDrawer.tsx` | 5 | 📋 | NEW — drawer rendering full chunk / posting / article / SQL+rows per source type |
| `frontend/src/components/QueryTransformationCard.tsx` | 5 | 📋 | NEW — shows S1's routing decision + chosen formula |
| `frontend/src/components/KnowledgeSources.tsx` | 5 | 📋 | NEW — inventory of corpora + tables |
| `frontend/src/components/InterventionTable.tsx` | 5 | 📋 | NEW — Impact/Effort sortable table + 2×2 quadrant scatter |
| `frontend/src/lib/sse.ts` | 4, 5 | ⏳ | `phase_writeup` event done; `query_transformation` + `email_sent` to add |
| `frontend/src/app/page.tsx` | 5 | 📋 | Replace marketing splash with merged dashboard |
| `frontend/src/components/SystemFlow.tsx` | 5 | 📋 | NEW — animated React Flow node lighting |
| `frontend/src/components/InterviewPrep.tsx` | 6 | 📋 | NEW |
| `vercel.json` + `modal_config.py` cleanup | 7 | 📋 | NEW — cloud deploy configs |
| `submission/README.md` + `submission/screenshots/` | 8 | 📋 | NEW — submission deliverables |

---

## Verification plan

- **Phase 1** ✅ verified 2026-05-02 — `/metrics/cost` returns tokens; cost ticker tooltip shows token counts. Last full Kaizen logged 27 invocations with 16,288 input / 7,684 output / 1,920 cached tokens. (USD shows $0.00 — known pricing-table gap.)
- **Phase 2** ✅ verified 2026-05-02 — `/metrics/kpis` returns 3 distinct KPI tiles per role. UX Designer: TTF 28.3d 🟢, conv 10.7% 🔴, OAR 60% 🔴. Java Dev: red conversion + amber OAR. PM/DevOps healthy. After role-scope fix, each role surfaces its own fingerprint.
- **Phase 3** ✅ verified 2026-05-02 — `/trigger/manual` with `problem_brief="why is offer acceptance so low for UX hires"` runs full DMAIC (gate bypassed by brief, K1 SIPOC framed around offer acceptance not TTF). `/trigger/goal-review` (no body) auto-picks UX Designer (worst KPI gap).
- **Phase 4** ✅ wave A verified — 5 HITL gates, 6 phase writeups streamed, advance signals consumed in order. ⏳ wave B — Donna iterating on writeup card placement / ask-mode UX / honest Kanban. To verify: open `/dashboard`, fire a custom Kaizen via 🎯 or a suggested-Kaizens pill, advance through 5 gates, click an open-question to confirm pre-fill.
- **Phase 4.5** 📋 to verify after T1.1 lands: writeup `evidence_citations` should include at least one `{source: "adzuna_posting", id: "<uuid>", snippet: "..."}` entry per Kaizen where Adzuna returned hits. After T1.2: D2's `external` output should report a *live* salary median alongside the seeded `industry_benchmarks` row.
- **Phase 5** 📋 — Visit `/`. RAG chatbot is default. Ask "what's our average TTF for Java Devs?" → answer with `[1]` citation chip → **click chip → drawer opens** showing full chunk_text + corpus + similarity (per amendment §D). Above the answer, a "How I read your question" card shows the routing decision + chosen formula (per amendment §C). Animated diagram lights up D1, D2 etc. as Kaizen progresses. Knowledge Sources panel lists 6+ corpora + 11 SQL tables (per amendment §B). Detection / improve phases render as proper tables, not prose lines (per amendment §F).
- **Phase 6** 📋 — Upload CV PDF, paste JD URL/text, click "Analyse". Get hits/misses + 3 calendar slots + a Gmail draft URL. Open Gmail, confirm draft exists. **Verified-output table** rendered in the UI with extracted/normalized/verified/flagged columns (per amendment §F). Separately: fire a full Kaizen → confirm a debrief email lands in the inbox with all 6 writeups + impact/effort table + citations (per amendment §E).
- **Phase 7** 📋 — Visit the Vercel URL. App loads. Fire a Kaizen. SSE events stream from the Modal backend to the Vercel frontend. Cost ticker updates. No localhost references in DevTools network tab.
- **Phase 8** 📋 — `submission/README.md` exists, ≤2 pages. `submission/screenshots/` has 6+ images. Screen-record uploaded somewhere accessible. Live demo URL works from a clean browser.

---

## Out of scope (deliberate)

- DBOS durability — docs claim it, code doesn't have it. Keep `threading.Thread` for now; mark as future work.
- ~~Cloud deployment (Vercel/Modal). Localhost-only.~~ — **REMOVED 2026-05-02**: cloud deploy is mandatory per the challenge brief. Now Phase 7. All ongoing work must remain Vercel/Modal-ready.
- Authentication / multi-user isolation. Single-user demo.
- Embedded vector store outside Supabase (e.g., separate Pinecone / Qdrant).
- Mobile-responsive UI.

---

## Mid-execution discoveries (2026-05-02)

Things that surprised us during execution. Folded back here so the original phase descriptions stay readable.

| # | Discovery | Impact | Where it landed |
|---|---|---|---|
| 1 | **DeepSeek consolidation** — Charle had already moved `TASK_ROUTING` to all-DeepSeek before this session; the orchestrator/router still had Claude Opus + Sonnet config as dead code. Donna's call: lock it down and remove Claude entirely. | Pipeline now single-model. Cost predictable. Plan's "Sonnet" / "Opus extended thinking" references are now stale — every call is `deepseek-chat`. | `t3_litellm_router.py`, `test_all.py`, `modal_config.py`, all CONTEXT docs updated. |
| 2 | **Role-scoping bug** — D1 + K2 + `/metrics/kpis` all ran on the global pipeline regardless of role. Identical KPI numbers across all roles. | The handoff doc's "Java should land amber/red" prediction was wrong because of *this bug*, not because of seed-generator calibration. | Fixed by passing `role_title` through `O2.fetch_pipeline_data` and adding `.eq("role_id", ...)` in the metrics route. |
| 3 | **DeepSeek pricing not in LiteLLM** — `response._cost` returns `0.0` for `deepseek-chat`. | Cost ticker shows `$0.00`. Token counts are correct. | Filed in `IMPLEMENTATION_STATE.md` § 9. Fix is small (hardcoded rates in T3) but not yet done. |
| 4 | **DeepSeek prompt caching kicked in unexpectedly** — first Phase 4 smoke test reported 1,920 cached tokens. The writeup agent's repeated system prompt across 6 calls is hitting their cache. Free latency win. | Future writeup-heavy work (Phase 4.5 T1.1, T2.2) will benefit even more. | None needed; just noted. |
| 5 | **Adzuna 401 (missing key)** — `ADZUNA_APP_ID` was literal `MISSING_CHECK_ADZUNA_DASHBOARD` in env. Donna fixed via `.env` update. | S4 Adzuna step now succeeds, salaries flow into D3's market_context. | `.env` updated; backend restarted. |
| 6 | **K7 was fabricating Kanban statuses** — sliced interventions arbitrarily into "To Do" / "In Progress" / "Done" columns and used hardcoded "Hiring Team" / "30 days" / "Time to Fill" for owner/due/KPI. | Demo showed dishonest plan. | `k7_control.py` rewritten: ALL items in "To Do" (the only honest column for a fresh plan), owner/due/KPI derived per-intervention from a structured DeepSeek call. |
| 7 | **HITL via thread-safe `queue.Queue`, not `asyncio.Queue`** — original plan wanted async-everywhere; in execution we kept the orchestrator on a worker thread (`run_in_executor`) and used `queue.Queue.get(timeout=30)` because converting every LLM call to async was a huge surface change for no real benefit. | Same UX for the user. Cleaner code. | Documented under Phase 4 above. |
| 8 | **Architecture review: API data flow is broken** — S4 persists Adzuna/Tavily/News to Supabase but K1-K7 + writeup never read any of it back. | Surfaced new Phase 4.5 (above). | Plan only — no code changes yet. |
| 9 | **Windows long-path failures during install** — Python venv inside the OneDrive-emoji project path failed on a deeply-nested LiteLLM file. | Worked around by putting the venv at `C:/autoci-venv` (short path). | One-off; documented in setup notes if a future session re-installs. |
