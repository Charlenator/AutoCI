# AutoCI

---

## The Idea

Most AI tools are built like search engines with a chat interface. You bring the question, the AI fetches an answer. That model has a ceiling, and the ceiling is the quality of your question.

AutoCI is built differently.

It watches your recruitment pipeline the way a Six Sigma consultant would: continuously, methodically, and with a bias toward finding problems you didn't know to look for. When it detects a gap, it does not surface a notification. It runs a full diagnostic engagement using Lean Six Sigma's DMAIC methodology, then hands you a consulting-grade report with a root cause, a set of prioritised interventions, and a 90-day implementation plan.

The insight that makes this work is not a new model or a new framework. It is a reframing of something the process improvement world has known for decades.

---

## The Core Thesis

**Lean Six Sigma was designed to fix how humans think. It turns out it also fixes how LLMs think.**

LSS methodologies -- DMAIC, Five Whys, Ishikawa, SIPOC -- were built to combat human cognitive shortcuts: premature anchoring, satisficing, confirmation bias, and stopping too early. These are not uniquely human failure modes. LLMs exhibit the same patterns. Ask a model to diagnose a complex operational problem and it will anchor on the most plausible explanation, produce a good-enough answer, and confirm the implied hypothesis in your question.

The conventional response is better prompting. AutoCI's response is better architecture.

By hard-coding LSS frameworks into the orchestration layer, AutoCI does not rely on prompt engineering to get rigorous outputs. The model **structurally cannot** skip logic steps. Five Whys is five independent, sequential agent calls—each must commit to a single "why" before the next even begins. DMAIC phase gates prevent jumping from problem identification to recommendations. The Ishikawa diagram is populated branch by branch, not generated from a single completion.

This is the difference between asking an AI to think rigorously and building a system where rigorous thinking is the only available execution path.

**The secondary insight**: most AI tools demand non-technical users adapt to the AI. AutoCI inverts this—every output artefact is written in the native language of program managers and Six Sigma practitioners. A Black Belt can read it without translation.

---

## What It Does

AutoCI monitors a company’s recruitment pipeline against two benchmarks:
- The company’s own performance targets
- Live industry benchmarks (from job board data and a synthetic Talent Insights dataset)

When a gap is detected—either an active failure or a statistically significant trend toward one—it launches a **Kaizen** (a full DMAIC investigation):

- **Define**: scopes the problem, produces a SIPOC diagram and financial impact estimate.
- **Measure**: quantifies the gap, identifies outliers, cross-references market data.
- **Analyse**: runs **Five Whys as five sequential atomic LLM calls**, builds an Ishikawa diagram from a structured data model, surfaces the confirmed root cause.
- **Improve**: generates prioritised interventions (researched and cited), plots them on an Impact/Effort matrix.
- **Control**: delivers a Kanban-style implementation plan with 30/60/90 day milestones, exportable as a single document.

A manual consulting engagement takes four weeks and tens of thousands of dollars. AutoCI completes the full cycle in under two minutes, at a cost of about **$0.18** in LLM API calls.

The system is designed for recruitment, but its architecture is industry-agnostic—any process with a defined unit of production, target metric, and defect can be modelled.

---

## System Architecture (Swimlane / Node-Level)

The entire system is composed of numbered, testable nodes organised into swimlanes.

### Swimlane Diagram
*(Visual representation built with React Flow; also available at mermaid.live)*
Frontend (Vercel/Next.js) – F1..F8
API Gateway (Modal/FastAPI) – A1..A7
Orchestration (DBOS) – O1..O3
Detection Layer (Tier 2) – D1..D3
Kaizen Engine (Tier 1 DMAIC) – K1..K7
Specialist Agents – S1..S4
Tools/Middleware – T1..T3
Data (Supabase) – DB1..DB5
External APIs – E1..E7

### Node Specifications

**Frontend (Vercel / Next.js 14, App Router)**
- **F1** – Three-panel layout shell
- **F2** – Chat panel (left) – user queries + HITL approvals
- **F3** – React Flow graph (centre) – live agent nodes & edges
- **F4** – Output drawer (right) – builds progressively, exports as PDF
- **F5** – Cost ticker – per-session cumulative LLM spend
- **F6** – "Run Goal Review" button – simulates KPI Guardian trigger
- **F7** – SSE client – single EventSource per session
- **F8** – Supabase JS client – initial state hydration

**API Gateway (Modal / FastAPI)**
- **A1** – `POST /trigger/manual` – manual Kaizen trigger
- **A2** – `POST /trigger/goal-review` – demo simulation trigger
- **A3** – `GET /sessions/:id/stream` – SSE endpoint
- **A4** – `POST /chat/query` – strategic discovery chatbot
- **A5** – `GET /metrics/cost` – cost aggregation
- **A6** – `POST /rag/ingest` – admin RAG corpus ingestion
- **A7** – `GET /health` – health probe

**Orchestration (DBOS workflows on Modal)**
- **O1** – Kaizen workflow (DBOS durable) – each DMAIC phase a Durable Step
- **O2** – Meta-Orchestrator (Tier 3) – filters, prioritizes, launches Kaizens
- **O3** – Phase-gate enforcer – prevents skipping phases; advances sequentially

**Detection Layer (Tier 2)**
- **D1** – Internal Benchmarking Agent
- **D2** – External Benchmarking Agent (Adzuna + synthetic LinkedIn)
- **D3** – Gap Analysis Agent (computes delta, classifies severity)

**Kaizen Engine (Tier 1 DMAIC) – Phase-Gated**
- **K1** – Define Agent (SIPOC + financial impact)
- **K2** – Measure Agent (metrics dashboard)
- **K3** – Analyse Agent host (root cause narrative)
- **K4** – Five Whys (5 atomic calls, thesis proof) – spawned by K3
- **K5** – Ishikawa data model (6 parallel branch calls) – spawned by K3
- **K6** – Improve Agent (Impact/Effort matrix + intervention cards)
- **K7** – Control Agent (Kanban board)

**Specialist Agents**
- **S1** – Translation Agent (NL → SQL/RAG, schema-injected)
- **S2** – RAG Retrieval Agent (hybrid pgvector search)
- **S3** – SQL Agent (wraps MCP Analytics Library)
- **S4** – Research Agent (Tavily, NewsAPI, Adzuna, Calendar, Email)

**Tools / Middleware**
- **T1** – MCP Analytics Library (hard-coded recruitment formulas)
- **T2** – Validation Interceptor (rule-based middleware, not an agent)
- **T3** – LiteLLM Router (cost-aware model routing)

**Data (Supabase)**
- **DB1** – roles, pipeline_events, candidates, hires, interviewers, etc.
- **DB2** – kaizen_sessions, kaizen_nodes
- **DB3** – agent_invocations (cost log)
- **DB4** – adzuna_postings (deduplicated)
- **DB5** – corpus_chunks (pgvector, RAG knowledge base)

**External APIs**
- **E1** – Adzuna API
- **E2** – Tavily API
- **E3** – NewsAPI
- **E4** – Google Calendar API
- **E5** – Gmail API (metadata only)
- **E6** – Anthropic API (Claude Sonnet & Opus)
- **E7** – DeepSeek API

---

## Agent Contracts & Protocols

### Five Whys – Atomic Call Protocol (K4)
The single most important piece of code. Each "why" is a **separate LLM call** to Opus (extended thinking) via LiteLLM.

**Input per call**: level (1–5), original problem, parent answer (except level 1), role context, top-3 RAG precedents.  
**Output**: a single causal answer with confidence, evidence references, and optional termination if no causal predecessor exists.  
**Orchestration**: calls are **sequential**, each writes its result to `kaizen_sessions.output_state.five_whys` before the next begins. If a call terminates early, the chain is flagged `shallow_root_cause`.

### Ishikawa Population Protocol (K5)
Six branches (People, Process, Technology, Environment, Materials, Measurement) are populated **in parallel**, each via a separate LLM call receiving only its branch definition, the problem, the completed Five Whys chain, and precedents. A branch may return zero causes if irrelevant.

### DMAIC Phase Contracts (output_state schemas)
Every phase commits a typed JSON blob to `output_state.<phase>`. The Validation Interceptor checks schema conformity and analytical rules before the phase gate (O3) allows advancement.

**Define** – `{ sipoc, financial_impact_estimate, problem_statement, in_scope, out_of_scope }`  
**Measure** – `{ metrics[], stage_dropoff, outliers, benchmark_comparison }`  
**Analyse** – `{ five_whys[], ishikawa{}, confirmed_root_cause, causal_narrative }`  
**Improve** – `{ interventions[], impact_effort_matrix, recommended_first_three }`  
**Control** – `{ kanban[], success_metric, review_cadence, rollback_criteria }`

### Validation Interceptor (T2)
A decorator that wraps every agent commit. Rules include:
- Schema conformity (enforced by Pydantic)
- Sample size minimum (n≥5)
- Outlier flagging (z > 3σ)
- Five Whys early termination flag
- Too few interventions warning
Fatal issues block the phase gate; warnings are annotated but pass through.

---

## Human-in-the-Loop
Two touchpoints:
1. **Pre-Kaizen (email)** – the KPI Guardian (production) sends a Resend email with "Launch Kaizen" and "Dismiss" tokens. For the demo, the "Run Goal Review" button simulates this.
2. **During-Kaizen (left panel chat)** – the Orchestrator (O2) surfaces questions and requests approvals. Runs in Auto mode (3s countdown) or Manual.

---

## LiteLLM Cost-Aware Routing (T3)
A single routing table maps task classes to models:
- Five Whys, net-new SQL → `claude-opus-4-7-thinking` (extended thinking)
- Orchestration, DMAIC narrative, translation, research synthesis → `claude-sonnet-4-6`
- Tagging, extraction, high-volume parsing → `deepseek-chat`
Every call is logged to `agent_invocations` with cost, model, and duration.

---

## RAG System
Knowledge base: LSS Recruitment Case Studies, Role Benchmark CSV, DMAIC Tool Reference Library, Adzuna postings corpus.  
Embeddings: Supabase Edge Embeddings (text-embedding-3-small, 1536d).  
Retrieval: hybrid semantic similarity + structured SQL filters via pgvector.  
All retrieval activity is visible in the React Flow graph and Activity Log.

---

## UI Layout
Three panels:
- **Left** – Chat & HITL (F2). Both user queries and Orchestrator questions use the same input.
- **Centre** – React Flow graph (F3). Shows every agent as a node, edges for invocations, live colour updates via SSE. The graph re-renders from DB2 on resume.
- **Right** – Output drawer (F4). Hidden until a Kaizen starts, then builds progressively. Exports the full output as a single styled document (print CSS).

Persistent elements: cost ticker (F5, top-right) and optional Activity Log overlay.

---

## Kaizen Session Persistence & Durability
- DBOS workflows (O1) wrap the entire Kaizen; every phase is a Durable Step.
- State lives in `kaizen_sessions.output_state` and `kaizen_nodes`.
- SSE delivers only state transitions (Idle → Active → Complete), keeping the frontend performant.
- Crashes or network interruptions resume from the last completed phase.

---

## Tech Stack (Final)
| Layer | Tool |
|---|---|
| Frontend | Next.js (App Router) on Vercel |
| Backend / Agents | FastAPI + Modal (Docker) |
| Durable Orchestration | DBOS (on Modal) |
| Database + Vector | Supabase (pgvector) |
| Embeddings | Supabase Edge Embeddings |
| LLM Interface | LiteLLM |
| LLMs | Claude Sonnet, Claude Opus (extended thinking), DeepSeek |
| MCP Server | Custom Analytics Library MCP (T1) – single MCP server |
| Live job data | Adzuna API (free tier) |
| Web research | Tavily + NewsAPI |
| Calendar/Email | Google Calendar & Gmail (OAuth, metadata only) |
| Scheduling | APScheduler (inside FastAPI container on Modal) |
| Transactional email | Resend (production only; mocked in demo) |
| Real-time updates | SSE (server-sent events) |
| Graph visualization | React Flow |

---

## The Engineered Demo Moment
1. Click "Run Goal Review" → a fake KPI miss triggers detection.
2. Internal and External Benchmarking agents fire; gap analysis shows +200% TTF vs. industry.
3. The Meta-Orchestrator launches a Kaizen. The React Flow graph lights up.
4. **Five Whys runs as five separate, visible API calls** – K4 pulses five times, each answer streams into the drawer. This is the thesis proof.
5. Ishikawa branches populate in parallel. Improve and Control phases complete.
6. The right panel contains a full Six Sigma report, exportable in one click.
7. The cost ticker shows **$0.18** – compared to a $50k consulting engagement.

The system doesn’t ask for permission; it finds the problem and delivers the solution.

---

*AutoCI — built as a technical interview exercise. April 2026.*