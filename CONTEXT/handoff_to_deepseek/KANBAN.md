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
| 01.7 | End-to-end smoke via `/inbound/simulate` | 2026-05-04 | 19/20 pass; 1 failure: `corpus_chunks` upsert used `json.dumps(meta)` instead of raw dict for JSONB column. Fixed in `da15de1`. Re-deploy Modal to verify. |

## In progress

| ID | Sub-task | Started | Notes |
|---|---|---|---|

## Backlog

### Task 02 — B6 Resend send wrapper

| ID | Sub-task | File ref |
|---|---|---|
| 02.1 | `resend_client.py` — thin async-friendly wrapper around the Resend send API | 02_b6_resend_send.md §1 |

### Task 03 — B7 cal.com slot lookup

| ID | Sub-task | File ref |
|---|---|---|
| 03.1 | `cal_com_client.py` — 14-day slot grid via free-tier API | 03_b7_cal_com.md §1 |

### Task 04 — B8 Candidate Search + Schedule Meeting

| ID | Sub-task | File ref |
|---|---|---|
| 04.1 | `routes/candidates.py` — /candidates/search + /candidates/{id}/cv + /candidates/{id}/schedule | 04_b8_candidate_search.md §1 |
| 04.2 | `frontend/src/app/candidates/page.tsx` rewrite | 04_b8_candidate_search.md §2 |
| 04.3 | `CandidateTable.tsx` — sortable, filterable, with row badges | 04_b8_candidate_search.md §3 |
| 04.4 | `ScheduleMeetingModal.tsx` — slot grid + send | 04_b8_candidate_search.md §4 |
| 04.5 | Wire CandidateTable + Modal into the page; smoke search → schedule → email | 04_b8_candidate_search.md §5 |

### Task 05 — Sprint C CIS rebrand

| ID | Sub-task | File ref |
|---|---|---|
| 05.1 | Migration 008: `interventions` table | 05_sprint_c_cis.md §1 |
| 05.2 | `K_SCOPING` agent (chat-loop scoping) | 05_sprint_c_cis.md §2 |
| 05.3 | `K_TOOL_SELECTOR` agent (picks tools per charter) | 05_sprint_c_cis.md §3 |
| 05.4 | FMEA agent + dataclass | 05_sprint_c_cis.md §4 |
| 05.5 | K6 prompt update — emit `linked_root_cause` per intervention | 05_sprint_c_cis.md §5 |
| 05.6 | Refactor `O2.run_full_kaizen` → consume tool list | 05_sprint_c_cis.md §6 |
| 05.7 | `routes/cis.py` — /cis/scope + /cis/run + /cis/interventions | 05_sprint_c_cis.md §7 |
| 05.8 | `frontend/src/app/cis/page.tsx` rewrite — charter bar, KPI strip, phase timeline | 05_sprint_c_cis.md §8 |
| 05.9 | `InterventionsTable.tsx` — per-Kaizen view | 05_sprint_c_cis.md §9 |
| 05.10 | Wire all of CIS together; smoke a full run | 05_sprint_c_cis.md §10 |

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
