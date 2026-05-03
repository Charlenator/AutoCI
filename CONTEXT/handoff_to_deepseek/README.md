# Handoff: Claude Opus → DeepSeek

This directory hands the remaining must-have AutoCI work to a DeepSeek session.
DeepSeek is less context-tolerant and less able to "fill in" architectural
intent than Claude Opus, so every prompt in here is designed to be **small,
self-contained, and verifiable**.

## How Charle uses this directory

1. Open a fresh DeepSeek chat.
2. Paste the contents of [00_session_start.md](00_session_start.md). DeepSeek
   confirms it understands the project + reads the linked context files.
3. Pick the next un-checked card on [KANBAN.md](KANBAN.md).
4. Open the matching task file (e.g. [01_b5_modal_worker.md](01_b5_modal_worker.md))
   and paste **one sub-task prompt** at a time into DeepSeek.
5. Review DeepSeek's output. If it's good, ask it to update the Kanban
   (move that sub-task from "In progress" to "Done"). If it's not, push back
   — referenced sub-task prompts are tight enough that drift is usually
   visible at the diff stage.
6. Commit + push at the end of each *task file* (not each sub-task) unless a
   sub-task explicitly says otherwise. That keeps git history readable.

## File index

| File | Purpose |
|---|---|
| [00_session_start.md](00_session_start.md) | Paste at the start of every fresh DeepSeek chat. Loads project context, working rules, and the file hierarchy. |
| [KANBAN.md](KANBAN.md) | Running checklist of all sub-tasks across every task file. DeepSeek updates this as work progresses. |
| [01_b5_modal_worker.md](01_b5_modal_worker.md) | Fill the inbound CV pipeline body — S5 classifier, S6 .docx extractor, S7 confidentiality, smart-chunking, email vectorizer. |
| [02_b6_resend_send.md](02_b6_resend_send.md) | Resend send wrapper — thin Python client used by the candidate-invite flow. |
| [03_b7_cal_com.md](03_b7_cal_com.md) | cal.com slot-lookup wrapper — returns a 14-day grid for the Schedule Meeting flow. |
| [04_b8_candidate_search.md](04_b8_candidate_search.md) | Candidate Search interface + Schedule Meeting modal. Largest UI piece; biggest task file. |
| [05_sprint_c_cis.md](05_sprint_c_cis.md) | CIS rebrand: K_SCOPING + K_TOOL_SELECTOR + FMEA + interventions table + dynamic O2 + new CIS UI. |
| [06_design_pass.md](06_design_pass.md) | Apply `CONTEXT/style_guide.css` across every UI surface. Comes after B5–B8 + Sprint C are functional. |
| [07_submission.md](07_submission.md) | Submission deliverables — README, screenshots, screen-record, live URL. Final step. |

## Recommended order

The task files are numbered in the order Charle should run them. **Don't
re-order**: B5 needs the inbound flow live; B8 needs B5 + B6 + B7; Sprint C
needs the chat surfaces stable; design pass needs every component to exist;
submission needs the design pass done.

## What DeepSeek should NOT do

These rules survive in [00_session_start.md](00_session_start.md) but worth
flagging here too:

- **No LangChain / LangGraph.** Direct LiteLLM calls only.
- **No emojis in user-facing UI.** Stroked icons (Lucide) — never emoji.
- **No new npm packages** unless a sub-task explicitly says so.
- **No refactors beyond the sub-task scope.** If DeepSeek wants to "clean up"
  something adjacent, it should leave it alone and surface it at the end.
- **No backwards-compat shims** (renamed `_var`, "// removed" comments, etc.).
- **Don't update SESSION_RESUME.md, plan-of-record.md, or dev-progress-diagram.md**
  — those are Charle/Claude territory. DeepSeek only updates `KANBAN.md` here.

## When to call Claude Opus back in

- Architectural shifts (new agent, new table, new external service).
- Anything ambiguous in the brief that the prompts don't already resolve.
- DeepSeek hits a hard error twice and needs a different strategy.
- Final pre-submission review.
