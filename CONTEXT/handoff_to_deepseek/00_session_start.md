# Session-start prompt for DeepSeek

> Paste the **PROMPT** block below at the very start of every fresh DeepSeek
> chat. After DeepSeek confirms it has read the linked context files and
> understands the rules, you can paste a sub-task prompt from one of the
> task files (`01_b5_modal_worker.md` etc.).

---

## PROMPT (copy the block below into DeepSeek)

```
You are continuing work on AutoCI, a recruitment-analytics platform built for a
take-home challenge. The project is mid-build: backend is deployed on Modal,
frontend on Vercel, Supabase as the database. I'm Charle, the primary developer.
You are taking over from Claude Opus for the remaining must-have features.

# What AutoCI is (one paragraph)

A Next.js single-page shell with three surfaces:
  1. RAG Chat — natural-language query layer. An LLM-driven Query Planner
     decides between validated SQL templates, freeform SELECT, vector retrieval
     against pgvector, or live web/news/jobs augmentation; the answer comes
     back with clickable citation chips that open a Citation Drawer.
  2. Candidate Search — recruiter-facing semantic search over CV chunks +
     Schedule Meeting flow that emails candidates a 14-day cal.com slot grid.
  3. Continuous Improvement Suite (CIS) — rebranded Kaizen tab. Conversational
     scoping agent picks the right diagnosis tools (5 Whys, Fishbone, FMEA,
     interventions table) per problem; HITL gates between phases.

Backend is FastAPI on Modal at:
  https://charlenator--autoci-backend-fastapi-app.modal.run

Frontend is Next.js 15 (App Router) on Vercel.

# READ THESE BEFORE WRITING ANY CODE (in this order)

1. CONTEXT/plan-of-record.md
   The locked plan. Sections to read in full: §1 (TL;DR), §3 (Status table),
   §4 (Architecture), §5 (Requirements-to-Features Mapping), §6 (Naming
   registry), §7 (Phase breakdown). Skim everything else.

2. CONTEXT/SESSION_RESUME.md
   The pivot banner at the top has the current state of every sprint. Items
   marked ✅ are shipped — do not re-implement them. Items not yet shipped
   are what you will work on.

3. CONTEXT/dev-progress-diagram.md
   Node-level status for every component (UI, route, agent, table, deploy
   target). Use it to confirm what's already done.

4. CONTEXT/style_guide.css
   The design system. Read the IMPLEMENTATION RULES at the top before doing
   ANY frontend work. The 18 numbered rules are non-negotiable.

5. The handoff directory itself: CONTEXT/handoff_to_deepseek/
   - README.md is the index.
   - KANBAN.md is your running checklist; you update it as work progresses.
   - 01_*.md through 07_*.md are the individual task files; Charle pastes
     one sub-task prompt at a time.

# Project file hierarchy (key paths only)

  Charle AutoCI/
  ├── backend/
  │   ├── main.py                          FastAPI app entry; CORS; startup hooks
  │   ├── modal_config.py                  Modal deploy config (DO NOT EDIT)
  │   ├── requirements.txt
  │   ├── test_all.py                      Run with: python -m pytest -q OR direct python test_all.py 1
  │   └── api/
  │       ├── routes/
  │       │   ├── chat.py                  /chat/query — Query Planner + SQL Executor + RAG + live search
  │       │   ├── trigger.py               /trigger/manual + /trigger/goal-review
  │       │   ├── stream.py                /sessions/{id}/stream — SSE
  │       │   ├── sessions.py              /sessions/{id}/respond — HITL
  │       │   ├── metrics.py               /metrics/cost + /metrics/kpis
  │       │   ├── rag.py                   /rag/ingest
  │       │   ├── knowledge.py             /knowledge/seed + /knowledge/update
  │       │   ├── sources.py               /sources — Knowledge Sources Panel inventory
  │       │   └── inbound.py               /inbound/simulate + /inbound/trigger + /inbound/drain
  │       ├── agents/
  │       │   ├── specialists/
  │       │   │   ├── s1_query_planner.py  Query Planner (LLM, schema-aware)
  │       │   │   ├── s2_rag.py            RAG retrieval via pgvector match_chunks RPC
  │       │   │   ├── s3_sql_executor.py   SQL Executor — runs plan; returns ExecutorResult with evidence_rows
  │       │   │   ├── s4_research.py       Tavily / News / Adzuna; live_augment(topic, sources)
  │       │   │   └── sql_templates.py     8 validated SQL templates with optional build_evidence
  │       │   ├── detection/               D1 / D2 / D3 (used by CIS)
  │       │   └── kaizen/                  K1–K7 + K_WRITEUP (CIS phase agents)
  │       ├── workers/
  │       │   └── inbound_processor.py     The Modal-side CV pipeline (B4 stub; B5 fills it)
  │       ├── tools/
  │       │   ├── t3_litellm_router.py     LiteLLM router; USD cost tracking
  │       │   └── t4_embeddings.py         BAAI/bge-small-en-v1.5; 384-d
  │       └── workflows/
  │           ├── o2_meta_orchestrator.py  Multi-agent orchestrator + HITL queue
  │           └── o3_phase_gate.py         Per-phase Define/Measure/Analyse/Improve/Control gates
  ├── frontend/
  │   ├── src/
  │   │   ├── app/
  │   │   │   ├── layout.tsx              Sidebar + topbar wrapper
  │   │   │   ├── page.tsx                Landing → redirects to chat tab
  │   │   │   ├── globals.css             *** drop CONTEXT/style_guide.css HERE in design pass ***
  │   │   │   ├── candidates/page.tsx     Candidate Search (currently a stub)
  │   │   │   ├── cis/page.tsx            Continuous Improvement Suite (currently a stub)
  │   │   │   └── dashboard/page.tsx      Old dashboard route (not in scope)
  │   │   ├── components/
  │   │   │   ├── TopNav.tsx              Tab strip — design pass replaces with Sidebar
  │   │   │   ├── RightDrawer.tsx         React Flow drawer
  │   │   │   └── chat/
  │   │   │       ├── ChatPanel.tsx
  │   │   │       ├── Citation.tsx        Renders one citation card; B-evidence section lives here
  │   │   │       ├── CitationChip.tsx
  │   │   │       ├── CitationDrawer.tsx
  │   │   │       ├── KnowledgeSourcesPanel.tsx
  │   │   │       └── QueryTransformationCard.tsx
  │   │   └── lib/
  │   │       ├── chat-types.ts           QueryPlan, SqlResult, Citation, LiveSearchPayload, etc.
  │   │       └── sse.ts                  Generic SSE client
  ├── supabase/
  │   ├── supabase_schema.sql             Canonical schema (always update alongside migrations)
  │   ├── migrations/                     001 → 007 applied
  │   └── functions/inbound-email/        Edge Function (DEPLOYED; do not redeploy)
  ├── dev-tools/
  │   └── cv_generator/                   make_cvs.py + 20 sample .docx CVs
  └── CONTEXT/
      ├── plan-of-record.md
      ├── SESSION_RESUME.md
      ├── dev-progress-diagram.md
      ├── presentation_prep.md
      ├── ROADMAP.md
      ├── style_guide.css                 *** the design system ***
      └── handoff_to_deepseek/            *** this directory ***

# Working rules — non-negotiable

These come from accumulated decisions across the build. Violating them
creates rework. Follow them by default; if a sub-task prompt explicitly
overrides one, the prompt wins.

1. NO LangChain / LangGraph. Direct LiteLLM calls via api/tools/t3_litellm_router.py.
   Reasons: the orchestration layer is already built; framework abstractions
   would obscure the DMAIC-as-architecture story; latency budget matters.

2. NO emojis in user-facing UI. Stroked icons (Lucide) only. Emojis OK in
   dev tooling (CONTEXT/, dev-tools/, comments, commit messages).

3. Natural language first; jargon in brackets. "Average time to fill" not
   "TTF avg". Backend IDs (template IDs, route names) stay technical.

4. UI components stay simple + prop-driven; Tailwind / pure CSS only. NO
   choreographed micro-interactions, NO animation libs, NO design-system
   libraries (Material, Chakra, etc.). The design pass uses CONTEXT/
   style_guide.css; nothing else.

5. Effort estimates are t-shirt sizes (XS / S / M / L / XL) anchored to
   shipped work, never time-based. The plan-of-record §7 has anchors.

6. Commit at logical-unit boundaries (a working feature), not per prompt.
   Push when a logical unit is complete. Never amend, never force-push.

7. NO new npm packages without an explicit sub-task instruction.

8. Schema changes go in supabase/migrations/NNN_*.sql AND supabase/
   supabase_schema.sql. Idempotent migrations only.

9. Validate at system boundaries (user input, external APIs); trust internal
   code. Don't add error-handling for scenarios that can't happen.

10. Don't add features, refactor, or introduce abstractions beyond what the
    sub-task requires. If you see something tangential to clean up, leave it
    and mention it at the end.

# Verification & test rules

- Backend tests: `cd backend && python test_all.py 1` (level-1 unit tests).
  Add tests for new agents / templates / helpers when you ship them.
- Frontend: `cd frontend && npm run lint && npm run build` should pass.
- Backend smoke after a deploy-touching change: `curl -s
  https://charlenator--autoci-backend-fastapi-app.modal.run/health` → 200.
- The deployed Modal URL is the source of truth for backend; localhost dev
  also works (run `python -m uvicorn main:app --port 8000 --host 127.0.0.1`
  from `backend/`).

# Kanban — your running checklist

CONTEXT/handoff_to_deepseek/KANBAN.md tracks every sub-task across every task
file. After finishing a sub-task:
  - Move its row from "In progress" to "Done"
  - Add a one-line note about anything surprising
  - Don't update any other CONTEXT/*.md file

When starting a sub-task:
  - Move its row from "Backlog" to "In progress"
  - Note the date

# Confirm you understand

Before I paste the first sub-task prompt, please reply with:

1. The Modal backend URL (from this prompt).
2. Three of the 10 working rules above (in your own words).
3. The path to the running checklist file.
4. The path to the design system file.

If any of those are wrong I'll re-paste this; if they're right I'll paste the
first sub-task prompt.
```

## After DeepSeek confirms

Pick a sub-task from `KANBAN.md`. Open the matching task file
(e.g. `01_b5_modal_worker.md`). Copy ONE sub-task prompt block. Paste it
into DeepSeek. When the work is good, ask DeepSeek to update `KANBAN.md`.
Move on.
