# Task 07 — Submission deliverables

## Goal

Package the project for review: a 1–2 page tech summary, 8 screenshots, a
5-minute screen-record, and the live URL pinned in the README.

This task assumes Tasks 01–06 are functionally and visually complete.

## Files this task touches

- NEW: `submission/README.md`
- NEW: `submission/screenshots/*.png`
- NEW: `submission/screen_record.mp4` (or hosted link)
- MODIFY: `README.md` at project root — pin the live URL + reference the
  submission folder

## Acceptance criteria

- `submission/README.md` is ≤ 2 pages when rendered, reviewer-aimed,
  with the live URL pinned at the top.
- 8 screenshots present in `submission/screenshots/`, named per the list.
- Screen-record covers the golden path: chat with citation → drawer →
  candidate search → schedule → CIS run.
- Project-root `README.md` links to the submission folder.

---

## Sub-tasks

### 07.1 — `submission/README.md`

**File**: `submission/README.md` (NEW)

**Prompt to paste:**

```
Create submission/README.md.

Read first:
  - CONTEXT/plan-of-record.md §5 (Requirements-to-Features Mapping) — this
    is the spine of the README. Every challenge requirement maps to a
    specific AutoCI feature; that's what reviewers want to see.
  - CONTEXT/presentation_prep.md — Q&A pre-emption. Pull 3-4 of the
    strongest talking points into the README's "design decisions" section.

Write a 1-2 page README with these sections (in order):

  # AutoCI

  > One-paragraph summary: what AutoCI is, what stack, where it's deployed.

  ## Live demo

  - Frontend: https://autoci-three.vercel.app
  - Backend:  https://charlenator--autoci-backend-fastapi-app.modal.run
  - Source:   https://github.com/Charlenator/AutoCI

  ## Challenge requirements coverage

  Two columns, one per Part. Each row = one literal brief requirement +
  the AutoCI feature that satisfies it. Pull from plan-of-record.md §5.

  ## Architecture (one diagram or one tight paragraph)

  Three-interface shell. RAG Chat (Query Planner → SQL templates / freeform
  / vector / live web) with citation drawer + B-evidence drill-down.
  Candidate Search (semantic over CV chunks + Schedule Meeting via cal.com
  + Resend). CIS (conversational scoping → tool selector → DMAIC tools +
  FMEA + interventions table). Backend on Modal (FastAPI + LiteLLM/
  DeepSeek + bge-small-en-v1.5 embeddings). Storage on Supabase
  (postgres + pgvector + Edge Function for inbound webhook).

  ## Notable design decisions

  Pull 3-4 from presentation_prep.md. Suggested: no LangChain (custom
  primitives), CPU-only torch on Modal (image discipline), B-evidence in
  citation drawer (source traceability done right), confidentiality flag
  enforced at retrieval (filter, not RLS).

  ## Repository layout

  Tree-style listing of the top-level directories with one-line purpose.

  ## Running locally

  Three blocks: backend (uvicorn), frontend (npm run dev), Supabase MCP if
  needed. Reference backend/.env.example if it exists; if not, list the
  env vars needed.

  ## Submission deliverables

  - This README
  - submission/screenshots/  (8 PNGs)
  - submission/screen_record.mp4

Keep it tight. Reviewer attention is the constraint.
```

---

### 07.2 — Screenshots

**Files**: `submission/screenshots/*.png` (NEW)

**Prompt to paste:**

```
Capture 8 screenshots into submission/screenshots/. Names + content per
plan-of-record.md §9 ("Screenshot list"):

  01_rag_chat.png            — RAG Chat answer with citation chips +
                               Query Transformation Card visible.
  02_citation_drawer.png     — Citation Drawer open with B-evidence
                               "Source records" expanded showing the
                               underlying hires.
  03_knowledge_sources.png   — Knowledge Sources Panel modal open.
  04_candidate_search.png    — Candidate Search table with filters
                               applied + a missing-field flag visible.
  05_schedule_meeting.png    — Schedule Meeting modal with 14-day slot
                               grid + 2 slots selected.
  06_cis_charter.png         — CIS scoping chat → charter snapshot →
                               proposed tool list.
  07_cis_interventions.png   — CIS interventions table fully rendered
                               with linked_root_cause column.
  08_system_drawer.png       — Right drawer expanded showing the React
                               Flow system map after a complete demo run.

Capture rules:
  - 1280×800 or 1440×900 (consistent across all 8).
  - Real data — no Lorem Ipsum. Use the seeded pipeline data + one of the
    20 generated CVs.
  - Crop to the relevant content; don't include browser chrome / dev tools.
  - PNG, optimized (use https://squoosh.app or `pngquant` if file > 400 KB).

Add a screenshots/README.md listing the 8 names + a 1-line caption per
screenshot for the submission package.
```

---

### 07.3 — Screen-record

**File**: `submission/screen_record.mp4` (NEW) — OR a YouTube/Loom link in
the README if file size is too big to commit.

**Prompt to paste:**

```
Record a 5-minute screen-record covering the golden path.

Tools: any screen recorder (OBS, Loom, QuickTime). Aim for 1080p.

Script (rough timing):
  0:00-0:30   Intro — what AutoCI is, who it's for, the three tabs.
  0:30-1:30   RAG Chat — ask "what's our average time to fill for Java
              Developers?", show the Query Transformation Card collapsed
              + expanded, click a citation chip, expand "Source records"
              to show the 3 underlying hires.
  1:30-2:00   Live web search — ask "what are current market salaries for
              senior Java developers in Cape Town?", show the live-search
              pill in the QTC + the new Adzuna chunks in the drawer.
  2:00-3:00   Candidate Search — type "java", show the table, download a
              CV, click Schedule Meeting, pick 2 slots, send (don't
              actually send if you don't want to spam — just walk through
              it).
  3:00-4:30   CIS — type "Why is offer acceptance dropping for UX?", let
              scoping ask 1-2 questions, approve charter, run, narrate
              over the SSE'd phase writeups, end on the interventions
              table with linked_root_cause visible.
  4:30-5:00   Wrap — show the system drawer expanded, mention the
              architecture (Modal + Vercel + Supabase), point at the
              README.

Save as submission/screen_record.mp4. If the file is > 100 MB, upload
to a private Loom/YouTube and put the link in submission/README.md
under "Live demo" instead of committing the binary.
```

---

### 07.4 — Pin live URL in root README

**File**: `README.md` at project root (MODIFY)

**Prompt to paste:**

```
Update the root README.md.

If a README.md exists at the project root, update its top with:

  > **Live demo**: https://autoci-three.vercel.app
  > **Submission package**: see [submission/README.md](submission/README.md)
  > **Backend API**: https://charlenator--autoci-backend-fastapi-app.modal.run

If no README exists at the root, create one with just those three lines
plus a one-paragraph "what is AutoCI" intro. Keep it short — the
submission/README.md is the real document.

Do not touch any other doc.
```

## Definition of done

- 07.1-07.4 in KANBAN "Done"
- submission/README.md renders as ≤ 2 pages
- 8 screenshots present
- Screen-record uploaded (or committed)
- Root README points at live URL + submission package

## Commit + push

```
git add submission/ README.md CONTEXT/handoff_to_deepseek/KANBAN.md
git commit -m "Sprint 9: submission deliverables (README + 8 screenshots + screen-record + live URL pinned)"
git push origin main
```

After this, the project is submission-ready.
