# SESSION RESUME — handoff between Claude Code sessions

> ## ⚠️ 2026-05-03 PIVOT — READ THIS FIRST
>
> The plan changed materially on 2026-05-03. The new plan-of-record lives at **`CONTEXT/plan-of-record.md`**. The old plan (`please-read-context-plan-fluffy-bentley.md`) has been archived under `CONTEXT/archive/`.
>
> Active dev tracking lives at **`CONTEXT/dev-progress-diagram.md`** — grouped mermaid diagram + status table for every node (UI / agent / route / table / external API / deploy target). Update it as nodes move from 📋 → ⚙️ → ✅.
>
> Working rules now in force (project-scoped):
> - **Effort estimates only** — XS/S/M/L/XL anchored to shipped work. No time-based estimates.
> - **Hard scope discipline** — cut anything that doesn't enhance the product or close a literal challenge-brief requirement. Quick wins welcome; large features only if strictly needed.
>
> The 🔥 "Tomorrow's first-up" bucket below is **superseded** by the new plan. Items 1-3 are absorbed into Phases 5/7 of the new plan; item 4 (Ask doesn't redirect chat) is a minor bug to retest after the Phase 5 chat tab redesign. Read `plan-of-record.md` for the full picture.
>
> Everything below this banner is **historical** (2026-05-02 state). Useful as backstory; not the current plan.

---

> **Last updated**: 2026-05-02 (evening) — end of a long working session. Today's wins: Phase 4 wave A + role-scope fix + DeepSeek consolidation + data-flow architecture review + Phase 4.5 T1.1, T1.2, T2.1 (K4/K5/K6 RAG) + §I close-out (corpus dedup, USD pricing $0.14/$0.28, redirect_url persistence, system diagram redo, manual-advance HITL, real-time cost ticker).

---

## Where things stand

The plan-of-record now lives **in-project** at:
`CONTEXT/please-read-context-plan-fluffy-bentley.md`

(A frozen copy of the original locked plan still exists at `C:\Users\dllaloux\.claude\plans\please-read-context-plan-fluffy-bentley.md` — it's the historical snapshot from the planning session. Read the in-project copy; it has the mid-execution amendments folded in.)

**Do not re-plan.** The strategic forks (split into two tabs, block-and-wait HITL, three-layer RAG self-check) are locked. The plan file's "Status at a glance" table has the up-to-date phase tracker.

| Phase | Status |
|---|---|
| 0 — CONTEXT cleanup | ✅ done |
| 1 — Token-level cost tracking | ✅ done (USD = $0 for DeepSeek — see plan caveat) |
| 2 — Multi-KPI detection | ✅ done (incl. role-scope fix 2026-05-02) |
| 3 — Generic Kaizen triggers | ✅ done |
| 4 — HITL + Amazon-narrative writeup agent | ✅ wave A backend / ⏳ wave B frontend (Donna iterating) |
| 4.5 — Data flow rewire | ✅ T1.1 + T1.2 + T2.1 done (writeup gets market_data; D2 reads live Adzuna; K4/K5 retrieve case studies). T2.2 + T3 deferred. |
| 5 — UI rewrite + challenge-audit upgrades | 📋 not started — **scope expanded** (clickable citations, query-transformation card, Knowledge Sources panel, tables, self-check) |
| 6 — Tools + extract→cleanse→verify (Part 2 deliverable) | 📋 not started — **email-debrief moved here**; CV→JD + Calendar + Gmail share an OAuth module |
| **7 — Cloud deployment (Vercel + Modal)** *(NEW)* | 📋 not started — was Out of Scope, flipped 2026-05-02 |
| **8 — Submission deliverables** *(NEW)* | 📋 not started |

A complete change log for Phases 0-3 + 4 wave A + the role-scope + DeepSeek fixes lives in section 0 of `IMPLEMENTATION_STATE.md`. The "Mid-execution discoveries" table at the bottom of the plan file lists 9 surprises that shaped how things shipped.

---

## Immediate next step (do this BEFORE writing code)

Verify the local environment is intact and pick up where the prior session left off:

1. **Run `/mcp`** and confirm `supabase` shows as connected. The token in `~/.claude.json` is the `sbp_*` Personal Access Token (the `sb_secret_*` project-scoped one was rejected by the MCP server). If disconnected, see the troubleshooting block at the bottom.

2. **Both servers should be running** (or start them):
   - Backend: from `backend/`, run `"C:/autoci-venv/Scripts/python.exe" -m uvicorn main:app --port 8000 --host 127.0.0.1`. The venv lives at `C:/autoci-venv` (short path) because the OneDrive-emoji project path tripped Windows long-path limits during install.
   - Frontend: from `frontend/`, run `npm run dev`. Up at `http://localhost:3000/dashboard`.

3. **Quick health check**:
   - `GET /health` → `{"status": "ok"}`
   - `GET /metrics/kpis?role_title=UX%20Designer` should return UX Designer with conv 10.7% 🔴 and OAR 60% 🔴 (post-role-scope-fix). If you see TTF=34.16 / OAR=78.1% for *every* role, the role-scoping fix has been reverted somehow — investigate.
   - `POST /trigger/goal-review` (no body) should auto-pick **UX Designer** (worst KPI gap) and run a full DMAIC with HITL pauses; the `phase_writeup` SSE events should land per phase.

If any step fails, **stop and surface the failure to Donna before patching**.

---

## Suggested next pieces of work

### 🔥 Tomorrow's first-up bucket — UX/feature fixes from Donna's 2026-05-02 evening browser test

These came directly out of clicking through the dashboard. **Do these BEFORE moving to Phase 5/6/7** — they're partly frontend polish that affects how every demo Kaizen looks, and partly behaviour changes that overlap with Phase 5's scope.

1. **Pointed Run Kaizen launcher** (replaces auto-pick-worst-KPI). The current `🎯 Run Kaizen` button auto-picks the role with the worst KPI gap, which feels random to a user and doesn't surface intent. Replace with an explicit upfront picker: **role dropdown + KPI dropdown (TTF / conversion / OAR / "any") + free-text "what's bothering you about this?" textarea**, then fire `/trigger/manual` with `{role_title, target_kpi, problem_brief}`. Auto-pick stays as a fallback if user hits "Just run one" with all fields empty. *Files*: `frontend/src/app/dashboard/page.tsx` (new component), `backend/api/routes/trigger.py` (already accepts the three kwargs — no backend change needed).

2. **Citation drawer (replaces hover tooltips on chips)**. Every `[1]/[2]/A1/R1/S1/T1/N1` chip should be clickable and open an expandable side-drawer/panel showing full chunk_text / posting / article / SQL+rows depending on source type. This is Phase 5 §D from the plan — pulled forward because hover tooltips don't show enough. Schema is already in place: writeups carry `evidence_citations[].snippet`; Adzuna postings have `redirect_url` (added 2026-05-02 §I); analyse/improve outputs carry `rag_citations`. *Files*: NEW `frontend/src/components/CitationDrawer.tsx`; wire from chip onClick.

3. **Drop Kanban → intervention table**. K7's Kanban output (To Do / In Progress / Done) was Donna's call to drop entirely since everything sits in "To Do" anyway. Replace with a **proper sortable table**: `Title | Description | Reason → root cause | Impact | Effort | Priority | Owner | Due`. The "Reason → root cause" column needs K6 to **map each intervention back to a specific root cause from K4/K5** so the user sees *why* each intervention exists. This is a backend prompt change (K6 emits `linked_root_cause: str` per intervention) AND a frontend rendering change. *Files*: `backend/api/agents/kaizen/k6_improve.py` (extend prompt + dataclass), `backend/api/agents/kaizen/k7_control.py` (probably retire — its Kanban is no longer rendered), frontend dashboard timeline section.

4. **Investigate "Ask doesn't redirect chat"**. Donna reported the Ask answer doesn't appear where she expected. The countdown removal (2026-05-02 §I) may have already fixed this — the timer was probably auto-advancing before she saw the answer. **First step**: re-test the Ask flow now that the countdown is gone. If the answer still feels invisible, it's because `_handle_ask` emits the answer as `output_delta` events tagged with the current phase (renders in that phase's agent groups in the timeline) — Donna probably expected it in the chat panel (left sidebar). Fix by: also pushing the Q&A as chat messages (frontend `setMessages`) so it shows in both places, OR rendering a highlighted Q&A block inside the writeup card itself (most contextual). *Files*: `backend/api/workflows/o2_meta_orchestrator.py:_handle_ask`, `frontend/src/app/dashboard/page.tsx`.

### Then back to the original priority order

5. **Phase 6 — Tools + extract→cleanse→verify pipeline** (1-2 days). Closes Part 2 of the challenge — without it we're at 1/3 tools. Includes the post-Kaizen email debrief (amendment §E) which doubles as the "Email" tool.

6. **Phase 7 — Cloud deploy (Vercel + Modal)** (~half day). Was Out of Scope; now mandatory per the brief.

7. **Phase 5 — Remaining UI rewrite items** (after items 1-4 above): animated React Flow node lighting during Kaizen, Knowledge Sources panel (§B), Query transformation card (§C), self-check layers.

8. **Phase 8 — Submission deliverables** (~half day). Tech summary + screenshots (system diagram is already a candidate) + screen-record + live URL.

9. **Tier 4.5 leftovers** (optional): T2.2 Evidence Selector, T3 corpus_chunks.metadata-filter cleanup, drop unused `expired_date`/`is_repost`/`original_posting_id` columns.

---

## Working with Donna

Read `Penthouse/.claude/CLAUDE.md` for the relationship context. Key beats specific to *this* project:

- **This project belongs to Charle, not Donna.** Donna is helping Charle iterate on it post-submission. She's the user, but design framing should respect Charle's original work.
- **Pause before destructive operations.** The seed v2 deletes pipeline data. Always confirm row counts before destructive SQL.
- **Surgical migrations only.** Each schema change goes in `supabase/migrations/NNN_*.sql` (idempotent) AND the canonical `supabase/supabase_schema.sql` so fresh installs match. Don't drift them.

---

## Troubleshooting: Supabase MCP not connected

If `/mcp` doesn't show `supabase`:

1. Check `~/.claude.json` under the project's `mcpServers` block. Should have:
   ```
   "supabase": {
     "type": "stdio",
     "command": "npx",
     "args": ["-y", "@supabase/mcp-server-supabase", "--project-ref=orxdunrevazwpyzkoaob"],
     "env": { "SUPABASE_ACCESS_TOKEN": "sb_secret_..." }
   }
   ```
2. If missing, re-run from the project root:
   ```
   claude mcp add supabase --scope local -e "SUPABASE_ACCESS_TOKEN=<token>" -- npx -y @supabase/mcp-server-supabase --project-ref=orxdunrevazwpyzkoaob
   ```
3. The MCP token is in Donna's personal Gmail (`leiajedi2022@gmail.com`) — most recent message from `charlecoetzee@gmail.com` with subject "Re: FOR CLAUDE". Token format: `sb_secret_...`.
4. The `sb_secret_*` format is a project-scoped key (newer style). If the MCP server rejects it, Donna can generate a Personal Access Token (`sbp_*`) at `https://supabase.com/dashboard/account/tokens` instead.

---

## Important file map

- **Plan**: `C:\Users\dllaloux\.claude\plans\please-read-context-plan-fluffy-bentley.md`
- **State**: `CONTEXT/IMPLEMENTATION_STATE.md`
- **Spec**: `CONTEXT/AutoCI_Overview.md`
- **Challenge scoring**: `CONTEXT/task_requirement_analysis.md`
- **Migrations to run**: `supabase/migrations/001_*.sql`, `supabase/migrations/002_*.sql`, `supabase/seed_v2_pipeline.sql`
- **Seed generator** (deterministic, re-runnable): `supabase/seed_generator.py`
