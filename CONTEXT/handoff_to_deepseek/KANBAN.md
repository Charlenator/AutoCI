# AutoCI — DeepSeek Kanban

> Source-of-truth checklist for every sub-task in `01_*.md` through `07_*.md`.
> DeepSeek updates this file as work progresses. Charle reviews + commits at
> the end of each task file (not each sub-task) unless a sub-task says
> otherwise.
>
> Status conventions:
> - **Backlog** — not started
> - **In progress** — DeepSeek is currently working on it
> - **Done** — code merged, tests passing, no follow-ups
> - **Blocked** — needs a decision from Charle (write the question in the Notes column)
>
> Format: one row per sub-task. Keep notes terse.

## Done

| ID | Sub-task | Date | Notes |
|---|---|---|---|
| 01.1 | S5 CV classifier (`s5_cv_classifier.py`) | 2026-05-04 | Built; 7 unit tests passing |
| 01.2 | S6 .docx field extractor (`s6_cv_extractor.py`) | 2026-05-04 | Built; 15 unit tests passing; python-docx now installed |
| 01.3 | S7 confidentiality classifier (`s7_confidentiality.py`) | 2026-05-04 | Built; 6 unit tests passing |
| 01.4 | Section-based smart-chunking helper (`cv_chunking.py`) | 2026-05-04 | Built; 8 unit tests passing |
| 01.5 | Email vectorizer helper (`email_vectorizer.py`) | 2026-05-04 | Built; 7 unit tests passing |
| 01.6 | Wire B5 pipeline into `inbound_processor.py` | 2026-05-04 | B4 stub replaced; 85 tests pass |
| 01.7 | End-to-end smoke via `/inbound/simulate` | 2026-05-04 | 25/25 pass after fix + Modal re-deploy. Full pipeline: S5 → S6 → S7 → chunk → embed → upsert + dedup verified. |
| 01.8 | Fix Edge Function: fetch .docx bytes via Resend Attachments API | 2026-05-04 | Real Resend webhooks omit attachment bytes; Edge Function v4 now calls GET /attachments and downloads from signed URL. Verified production: Pieter van der Merwe CV processed end-to-end. |
| — | Bug fix: Level 5 e2e test FK + UUID errors | 2026-05-04 | `session_id="e2e-test-001"` not valid UUID → `str(uuid.uuid4())`. Also needed `kaizen_sessions` row insert before `run_full_kaizen` call (FK ref). Live deploy OK. |
| 02.1 | `resend_client.py` — thin async-friendly wrapper around the Resend send API | 2026-05-04 | Code exists (written in prior session); uncommitted. Needs stage+commit. |
| 03.1 | `cal_com_client.py` — 14-day slot grid via cal.com v2 API | 2026-05-04 | Rewritten for v2 (header auth, date-only start/end, `data` IS slots dict). 17/17 unit tests passing. Live smoke: 63 slots across 4 days for eventTypeId=5572588. `.env` has `CAL_COM_DEFAULT_EVENT_TYPE_ID` added. Bugfix fac21c7: booking_url now uses UTC Z-suffix + urlencode (was sending +02:00 which JS Date parsed as invalid). |
| 04.1 | `routes/candidates.py` — /candidates/search + /candidates/{id}/cv + /candidates/{id}/schedule | 2026-05-04 | 3 routes + scheduling route. 12/12 B8 tests passing. |
| 04.2 | `frontend/src/app/candidates/page.tsx` rewrite | 2026-05-04 | "use client" page with search bar, results list, loading/empty/error states. |
| 04.3 | `CandidateTable.tsx` — sortable, filterable, with row badges | 2026-05-04 | 6-column table: Candidate, Skills (chips +N more), Match (score + bar), Flags (duplicate/missing/confidential), CV (signed-url download), Actions (Schedule button). |
| 04.4 | `ScheduleMeetingModal.tsx` — slot grid + send | 2026-05-04 | useReducer for slot fetch lifecycle. 14-day slot grid, 1-3 selection, custom message, POST to /schedule. Lint-clean. Build OK. |
| 04.5 | Wire CandidateTable + Modal into the page; smoke search → schedule → email | 2026-05-04 | Live smoke: 20+ CVs seeded via bulk script, search returns results with scores, schedule email sent via Resend. S2 match_threshold 0.7→0.3 & ts_rank fallback scoring. from_email hardcoded to recruitment@wabi-ai.tech. |
| 05.1 | Migration 008: `interventions` table | 2026-05-04 | Applied via Supabase MCP; `list_tables` confirms table exists. RLS disabled advisory flagged. |
| 05.2 | `K_SCOPING` agent (chat-loop scoping) | 2026-05-04 | Built with ScopingTurn/ScopingState dataclasses, LLM JSON contract, fallback handling. |
| 05.3 | `K_TOOL_SELECTOR` agent (picks tools per charter) | 2026-05-04 | Built with TOOL_CATALOG, ToolPlan dataclass, validation/dedup/fallback logic. Fix: `from typing import list` → dropped (builtin list, Python 3.14 compat). |
| 05.4 | FMEA agent + dataclass | 2026-05-04 | Built with FMEAEntry/FMEAOutput dataclasses, RPN computation, descending sort. Fix: `from typing import list` → dropped (same Python 3.14 issue). |
| 05.5 | K6 prompt update — emit `linked_root_cause` per intervention | 2026-05-04 | Extended Intervention dataclass, updated prompt, validation against supplied root_causes, "(unlinked)" flag. |
| 05.6 | Refactor `O2.run_full_kaizen` → consume tool list | 2026-05-04 | Added tool_plan param, _run_with_tool_plan method, D1/D2/K1/K2/K3/K4+K5/K6/FMEA branches, interventions DB insert, SSE events. Fix: 05.6 unit test used `__code__` (not iterable in Py3.14) → `inspect.signature()`. |

## Backlog

### Task 05 — Sprint C CIS rebrand

| ID | Sub-task | File ref |
|---|---|---|
| 05.7 | `routes/cis.py` — /cis/scope + /cis/run + /cis/interventions | 05_sprint_c_cis.md §7 |
| 05.8 | `frontend/src/app/cis/page.tsx` rewrite — charter bar, KPI strip, phase timeline | 05_sprint_cis.md §8 |
| 05.9 | `InterventionsTable.tsx` — per-Kaizen view | 05_sprint_cis.md §9 |
| 05.10 | Wire all of CIS together; smoke a full run | 05_sprint_cis.md §10 |

### Task 06 — Design pass

| ID | Sub-task | File ref |
|---|---|---|
| 06.1 | Drop `style_guide.css` content into `frontend/src/app/globals.css` | 06_design_pass.md §1 |
| 06.2 | Build `Sidebar.tsx` (replaces TopNav) per style_guide §4 | 06_design_pass.md §2 |
| 06.3 | Re-style topbar + crumb + topbar-right per §5 | 06_design_pass.md §3 |
| 06.4 | Re-style RightDrawer per §6 | 06_design_pass.md §4 |
| 06.5 | Re-style ChatPanel + Composer per §8 + §13 | 06_design_pass.md §5 |
| 06.6 | Re-style CitationChip + CitationDrawer + Citation + EvidenceBlock per §9 + §11 + §12 | 06_design_pass.md §6 |
| 06.7 | Re-style QueryTransformationCard per §10 | 06_design_pass.md §7 |
| 06.8 | Re-style Candidate Search page per §14 (assumes B8 done) | 06_design_pass.md §8 |
| 06.9 | Re-style CIS page per §15 (assumes Sprint C done) | 06_design_pass.md §9 |
| 06.10 | Re-style KnowledgeSourcesPanel modal per §16 | 06_design_pass.md §10 |
| 06.11 | A11y + responsive sweep | 06_design_pass.md §11 |

### Task 07 — Submission deliverables

| ID | Sub-task | File ref |
|---|---|---|
| 07.1 | `submission/README.md` — 1-2 page tech summary | 07_submission.md §1 |
| 07.2 | 8 screenshots per the screenshot list | 07_submission.md §2 |
| 07.3 | 5-min screen-record (walkthrough) | 07_submission.md §3 |
| 07.4 | Pin live demo URL in root README | 07_submission.md §4 |

## Blocked

| ID | Sub-task | Started | Reason |
|---|---|---|---|
