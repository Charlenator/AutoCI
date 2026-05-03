# AutoCI

> **The solution to smarter AI orchestration was developed 50 years ago. Six Sigma methodologies were built to eliminate the cognitive shortcuts that cause humans to reason poorly under complexity. It turns out LLMs have the same problem. Wire the methodology directly into the architecture, and you fix it in both. AutoCI runs full Continuous Improvement engagements, semantic candidate search, and traceable RAG chat — all driven by the same agent foundation, all delivered with consulting-grade rigour for cents per session.**

---

## Rigour in the prompt can always be skipped. Rigour in the architecture cannot.

LLMs share the same failure modes as human analysts: anchoring on the most plausible explanation, producing a good-enough answer, confirming the hypothesis implied by the question. The standard fix is better prompting. AutoCI takes a different approach.

**Six Sigma frameworks don't just make human consultants more rigorous — they make AI agents more rigorous too.**

DMAIC. Five Whys. Ishikawa. SIPOC. FMEA. Pareto. In AutoCI, these aren't instructions passed to a model — ***they are the architecture***. Five Whys is five independent, sequential agent calls. Each must commit to a single causal answer before the next begins. DMAIC phase gates prevent any jump from problem identification to recommendations. The model has no path around the logic. No shortcuts, no jumping to conclusions.

**This is the intersection of Six Sigma process improvement and agentic AI.** Not AI with a methodology bolted on. A methodology with AI as the execution engine.

---

## The AI adapts to the humans. Not the other way around.

Project managers and Six Sigma practitioners already have a working language: Continuous Improvement charters, FMEAs, Impact/Effort matrices, Pareto charts, intervention plans backed by linked root causes. AutoCI speaks it natively. A Black Belt can read the output without translation.

Recruiters get a candidate-search experience that accepts pasted job descriptions, returns ranked applicants from semantically-matched CVs, surfaces missing-field flags and duplicate detection, and books interviews via a real calendar slot grid — without leaving the app.

Anyone asking the system a question gets an answer with **clickable citations**: every claim links back to the chunk, posting, news article, or SQL row it was drawn from.

---

## What AutoCI does

AutoCI is a single shell with three independent interfaces, all backed by the same agent foundation, RAG corpus, and structured database.

### 1. RAG Chat — traceable answers with visible reasoning

Every question is processed by an LLM Query Planner that decides whether the answer needs structured SQL, semantic vector retrieval, or both — and shows you the decision in a "How I read your question" card before the answer arrives.

| Step | What happens |
|------|--------------|
| **Plan** | LLM Query Planner inspects the question against the database schema. Emits a JSON plan: validated SQL template, freeform SELECT, vector retrieval, or a combination. |
| **Execute** | SQL runs against a read-only Postgres role through a 4-layer safety pipeline (validated templates first, regex allowlist, prompt-side guardrails, role isolation). Vector retrieval hits pgvector with confidentiality filtering. |
| **Cite** | Every answer carries clickable source chips. Click any chip → side drawer shows the full chunk text, posting, article, or SQL+rows. CV chunks include a download link to the original PDF. |
| **Inventory** | A Knowledge Sources panel lists every corpus and queryable table — schema, row counts, samples — so you can see exactly what the system has access to. |

### 2. Candidate Search — extract, cleanse, verify, schedule

Recruiters search a curated candidate database that's populated entirely by an inbound email pipeline.

| Step | What happens |
|------|--------------|
| **Extract** | Resend inbound webhook delivers any email with a CV attachment to a Supabase Edge Function. The function classifies the attachment, extracts structured fields with `pypdf` + LLM extraction, and chunks the CV for vector storage. |
| **Cleanse** | Field normalization (email lowercase, phone canonicalization, skill tokenization). Hash-based deduplication catches resubmissions. |
| **Verify** | Confidentiality classifier flags sensitive content (excluded from RAG retrieval). Missing-field detector flags rows with incomplete data. |
| **Search** | Semantic search bar accepts free text or a pasted job description. JD-paste mode extracts 3-5 key requirements and runs a fan-out vector search. Results render in a sortable, filterable table with download links and flag badges. |
| **Schedule** | Click Schedule Meeting → 14-day cal.com slot grid → tick available slots → candidate receives a Resend email with deep-link booking URLs for the slots you chose. |

### 3. Continuous Improvement Suite — diagnose deep, fix what matters

Type a problem statement. The system holds a back-and-forth conversation until it understands the issue, then picks the right Six Sigma tools for the job — not the full DMAIC chain every time.

| Step | What happens |
|------|--------------|
| **Scope** | A scoping agent asks clarifying questions until the problem, target outcome, and success criteria are clear. Outputs a Continuous Improvement Charter. |
| **Plan** | A tool selector picks the right subset from the toolbox: Internal/External Benchmarking, Gap Analysis, SIPOC, Five Whys, Ishikawa, Pareto, FMEA, RACI matrix, Impact/Effort prioritization. |
| **Execute** | Selected tools run sequentially with HITL gates between phases. The user can advance, ask a clarifying question (which routes through the same RAG pipeline), or abort. |
| **Report** | Every phase produces an Amazon-narrative writeup with citations to the kaizen-node, RAG chunks, Adzuna postings, news articles, and live SQL queries that informed it. |
| **Track** | Interventions table replaces a Kanban board. Each intervention links back to its specific root cause from Five Whys / Ishikawa. A cross-Kaizen view aggregates all historical interventions across all sessions. |

A traditional consulting engagement takes four weeks and costs tens of thousands of dollars. AutoCI delivers the same artefact in **~90 seconds** for about **$0.18** in LLM API calls.

---

## Architecture

```
                    ┌────────────────────────────────────────┐
                    │   Next.js shell (Vercel)               │
                    │   ┌─────────┬─────────┬─────────────┐  │
                    │   │  Chat   │ Cand.   │  Cont.Impr. │  │
                    │   │         │ Search  │   Suite     │  │
                    │   └─────────┴─────────┴─────────────┘  │
                    │   Right drawer: live React Flow graph  │
                    └────────────────┬───────────────────────┘
                                     │
                    ┌────────────────▼───────────────────────┐
                    │   FastAPI backend (Modal)              │
                    │   • Query Planner → SQL / RAG / both   │
                    │   • CIS orchestrator: scope → select → │
                    │     execute → writeup → interventions  │
                    │   • SSE event stream + HITL queue      │
                    └────────────────┬───────────────────────┘
                                     │
                    ┌────────────────▼───────────────────────┐
                    │   Supabase                             │
                    │   • Postgres (recruitment + CIS data)  │
                    │   • pgvector (RAG corpora + CV chunks) │
                    │   • Storage (CV attachments)           │
                    │   • Edge Function: inbound email →     │
                    │     classify → extract → vectorize     │
                    └────────────────────────────────────────┘
                                     │
                ┌────────────────────┴────────────────────┐
                │                                         │
        ┌───────▼─────────┐                  ┌────────────▼─────┐
        │ External APIs   │                  │  Communication   │
        │ • Adzuna        │                  │  • Resend        │
        │ • Tavily        │                  │    (send + in)   │
        │ • NewsAPI       │                  │  • cal.com       │
        │ • DeepSeek/LLM  │                  │    (slot lookup) │
        └─────────────────┘                  └──────────────────┘
```

Every agent invocation is a node in a live React Flow graph pinned to a right-side drawer. Use any of the three interfaces and watch the relevant nodes light up — agents, retrievals, SQL queries, external API calls, all visible as they happen. By the end of a demo, the full graph of touched components is illuminated.

---

## Tech stack

| Layer | Tool |
|-------|------|
| Frontend | Next.js 15 (App Router) on Vercel |
| Backend | FastAPI on Modal |
| Orchestration | Worker-thread orchestrator with thread-safe HITL queue + SSE event stream |
| Database + Vector | Supabase (Postgres + pgvector) |
| Object Storage | Supabase Storage (CV attachments bucket) |
| Inbound Email Pipeline | Supabase Edge Functions (Deno/TypeScript) |
| Embeddings | OpenAI `text-embedding-ada-002` (1536-d) |
| LLM Interface | LiteLLM — provider-agnostic router |
| LLMs | DeepSeek (chat) — single-model pipeline, ~$0.14/$0.28 per M input/output |
| Analytics Library | Custom MCP-style server with hard-coded formulas — eliminates hallucinations in numeric reasoning |
| Email | Resend (send + inbound webhook with verified domain) |
| Calendar | cal.com (free-tier slot lookup API) |
| Web research | Adzuna API (jobs), Tavily (web search), NewsAPI (news) |

---

## Quick start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase project with `vector` extension enabled
- Modal account
- Resend account with a verified sending domain (for inbound webhook)
- cal.com account (free tier sufficient)
- API keys: DeepSeek, OpenAI (embeddings), Adzuna, Tavily, NewsAPI, Resend

### Setup

```bash
git clone https://github.com/Charlenator/autoci.git
cd autoci

# Frontend
cd frontend
npm install
npm run dev          # → http://localhost:3000

# Backend (local dev)
cd ../backend
python -m venv venv
# On Windows with long paths in the project root, install the venv
# at a short path (e.g. C:/autoci-venv) and activate from there.
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload   # → http://localhost:8000

# Deploy to Modal
modal deploy backend/modal_config.py

# Deploy Supabase Edge Function (inbound email handler)
supabase functions deploy inbound-email
```

### Database

Apply schema and migrations in order:
```bash
# In your Supabase SQL editor, in order:
supabase/supabase_schema.sql            # Full schema
supabase/migrations/001_*.sql           # Token columns
supabase/migrations/002_*.sql           # Multi-KPI benchmarks
supabase/migrations/003_*.sql           # Adzuna redirect_url
supabase/migrations/004_*.sql           # Inbound pipeline (emails, CV chunks, confidentiality)
supabase/migrations/005_*.sql           # Interventions table
supabase/migrations/006_*.sql           # System logs
supabase/seed_v2_pipeline.sql           # Demo recruitment data (148 candidates / 468 events / 32 hires)
```

Point the Resend inbound webhook at the deployed Edge Function URL. Configure the `cv-attachments` storage bucket as private (signed URLs only).

---

## Project structure

```
autoci/
├── frontend/                              # Next.js shell
│   ├── src/app/                           # 3-tab shell + RAG chat / candidate search / CIS
│   ├── src/components/                    # CitationDrawer, KnowledgeSourcesPanel,
│   │                                      # SystemFlowDrawer, CandidateSearch,
│   │                                      # SlotGrid, InterventionsTable, etc.
│   └── src/lib/                           # SSE client, Supabase client
├── backend/
│   ├── main.py                            # FastAPI entry point
│   ├── modal_config.py                    # Modal deployment config
│   └── api/
│       ├── routes/                        # /chat, /candidates, /cis, /sources,
│       │                                  # /sessions, /trigger, /metrics, /simulate-inbound
│       ├── agents/
│       │   ├── specialists/               # S1 QueryPlanner, S2 RAG, S3 SQLExecutor, S4 Research
│       │   ├── detection/                 # D1, D2, D3
│       │   └── cis/                       # K_SCOPING, K_TOOL_SELECTOR, K1-K6, Pareto, FMEA, RACI
│       ├── tools/                         # T1 Analytics, T2 Validation, T3 LiteLLM, T4 Embeddings
│       ├── workflows/                     # O2 dynamic tool runner
│       ├── integrations/                  # Resend client, cal.com client
│       └── sse/                           # Event stream + HITL queue
├── supabase/
│   ├── supabase_schema.sql                # Full schema
│   ├── migrations/                        # Numbered idempotent migrations
│   ├── functions/inbound-email/           # Edge Function: email → CV pipeline
│   └── seed_v2_pipeline.sql               # Deterministic demo seed
├── CONTEXT/                               # Plan-of-record + dev progress diagram
└── README.md
```

---

## License

© 2026 Charle Coetzee. Built as part of an interview exercise. All rights reserved.
