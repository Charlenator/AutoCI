# AutoCI

> **The solution to smarter AI orchestration was developed 50 years ago. Six Sigma methodologies were built to eliminate the cognitive shortcuts that cause humans to reason poorly under complexity. It turns out LLMs have the same problem. Wire the methodology directly into the architecture, and you fix it in both. AutoCI runs a full DMAIC diagnostic engagement autonomously and delivers a consulting-grade report in under two minutes, for less than twenty cents.**

---

## Rigour in the prompt can always be skipped. Rigour in the architecture cannot.

LLMs share the same failure modes as human analysts: anchoring on the most plausible explanation, producing a good-enough answer, confirming the hypothesis implied by the question. The standard fix is better prompting. AutoCI takes a different approach.

**Six Sigma frameworks don't just make human consultants more rigorous - they make AI agents more rigorous too.**

DMAIC. Five Whys. Ishikawa. SIPOC. In AutoCI, these aren't instructions passed to a model, ***they are the architecture***. Five Whys is five independent, sequential agent calls. Each must commit to a single causal answer before the next begins. DMAIC phase gates prevent any jump from problem identification to recommendations. The model has no path around the logic. No shortcuts, no jumping to conclusions.

**This is the intersection of Six Sigma process improvement and agentic AI.** Not AI with a methodology bolted on. A methodology with AI as the execution engine.

---

## The AI adapts to the humans. Not the other way around.

Project managers and Six Sigma practitioners already have a working language: Kaizens, Kanban boards, Impact/Effort matrices, 30/60/90 day implementation plans. AutoCI speaks it natively. A Black Belt can read the output without translation.

Non-technical users don't learn new tools. They don't change how they work. They get an email, and a report waiting when they open it.

---

## What AutoCI does

| Step | What happens |
|------|--------------|
| **Detect** | Monitors your recruitment pipeline against internal targets and live industry benchmarks. Finds problems you didn't know to look for. |
| **Define** | Scopes the problem with a financial impact estimate and a SIPOC process map. |
| **Measure** | Quantifies the gap at stage level, identifies outliers, cross-references market data. |
| **Analyse** | Runs Five Whys as five atomic sequential calls. Builds an Ishikawa (fishbone) diagram branch by branch. Surfaces the confirmed root cause with citations. |
| **Improve** | Generates prioritised interventions backed by case-study precedent and live market research. Plots them on an Impact/Effort matrix. |
| **Control** | Produces a Kanban-style implementation plan with 30/60/90 day milestones. Exportable as a single document. |

A consulting engagement takes four weeks and costs tens of thousands of dollars. AutoCI delivers the same artefact in ~90 seconds for about **$0.18** in LLM API calls.

---

## Architecture *(NOTE: To be replaced with full diagram img)*

```
┌─────────────────────────────────────────────────┐
│  TIER 3 — Meta-Orchestrator                     │
│  "What problems should we be solving?"          │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  TIER 2 — Problem Detection Layer               │
│  Internal + External Benchmarking + Gap Analysis│
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  TIER 1 — Kaizen Engine (DMAIC)                 │
│  Define → Measure → Analyse → Improve → Control │
│  Phase-gated. Every step a Durable DBOS workflow│
└─────────────────────────────────────────────────┘
```
 
Every agent invocation is a node in a live React Flow graph. You watch the system reason in real time — every tool call, every retrieval, every LLM completion visible as it happens. A Six Sigma Project Manager can read every output artefact without translation. The AI speaks their language. 

---

## Tech stack

| Layer | Tool |
|-------|------|
| Frontend | Next.js (App Router) on Vercel |
| Backend | FastAPI on Modal (Docker) |
| Orchestration | DBOS — durable, crash-resumable workflows |
| Database + Vector | Supabase (Postgres + pgvector) |
| Embeddings | Supabase Edge Embeddings (text-embedding-3-small) |
| LLM Interface | LiteLLM — provider-agnostic, hot-swappable |
| LLMs | Claude Sonnet, Claude Opus (extended thinking), DeepSeek |
| Analytics Library | Custom MCP server — hard-coded formulas aligned with data schema eliminates hallucinations in the data analysis layer |
| Live data | Adzuna API, Tavily, NewsAPI, Google Calendar, Gmail |

---

## Quick start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase project with `vector` extension enabled
- Modal account
- API keys: Anthropic, DeepSeek, Adzuna, Tavily, NewsAPI, Google Cloud (OAuth)

### Setup

```bash
# Clone
git clone https://github.com/your-username/autoci.git
cd autoci

# Frontend
cd frontend
npm install
npm run dev          # → http://localhost:3000 for local dev

# Backend (local dev)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload   # → http://localhost:8000 for local dev

# Deploy to Modal
modal deploy backend/modal_config.py
```

### Database
Run `supabase/schema.sql` in your Supabase SQL editor to create all tables, then `supabase/seed.sql` for demo data.

---

## Project structure (NOTE: likely to change while building, review continuously)

```
autoci/
├── frontend/              # Next.js app
│   ├── app/               # App Router pages
│   ├── components/        # React components (panels, graph, drawer)
│   └── lib/               # Supabase client, SSE client, utils
├── backend/               # FastAPI + Modal
│   ├── main.py            # FastAPI app
│   ├── modal_config.py    # Modal deployment config
│   ├── api/
│   │   ├── routes/        # REST + SSE endpoints
│   │   ├── agents/        # Detection, DMAIC, Specialist agents
│   │   ├── tools/         # MCP server, validation interceptor, LiteLLM router
│   │   └── workflows/     # DBOS durable workflow definitions
│   └── scripts/           # DB reset, seed utilities
├── supabase/
│   ├── schema.sql         # Full database schema
│   └── seed.sql           # Demo data (NovaCo synthetic)
└── README.md
```

---

## License

© 2026 Charle Coetzee. Built as part of an interview exercise. All rights reserved.
