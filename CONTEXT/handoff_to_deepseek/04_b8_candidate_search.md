# Task 04 — B8: Candidate Search interface + Schedule Meeting flow

## Goal

The recruiter-facing surface. A semantic search over CV chunks (via
`s2_rag.py` against `corpus_name='cvs'`) renders sortable / filterable
candidate rows; each row has download-CV (Storage signed URL), missing-field
flags, duplicate flags, and a Schedule Meeting button. Schedule Meeting
opens a modal showing a 14-day cal.com slot grid; tick 1–3 slots → click
Send → Resend emails the candidate with deep-link booking URLs.

This task assumes B5 (Task 01), B6 (Task 02), and B7 (Task 03) are done.

## Files this task touches

- NEW: `backend/api/routes/candidates.py`
- MODIFY: `backend/main.py` (register the new router)
- NEW: `frontend/src/components/CandidateTable.tsx`
- NEW: `frontend/src/components/ScheduleMeetingModal.tsx`
- REWRITE: `frontend/src/app/candidates/page.tsx`
- ADD TESTS: `backend/test_all.py`

## Acceptance criteria

- `/candidates/search?q=Java&limit=20` returns a JSON list of candidate
  cards with `name`, `email`, `phone`, `skills` (top 5), `experience_summary`,
  `match_score` (0..1), `is_duplicate`, `missing_fields`, `cv_storage_path`,
  `id`.
- `/candidates/{id}/cv` returns a Supabase Storage signed URL (5-min TTL).
- `/candidates/{id}/schedule` accepts `{slots: [{start, end, booking_url}, ...]}`
  and triggers Resend with a templated invite email; returns `{resend_id}`.
- Frontend: visiting `/candidates`, typing in the search bar, hitting Enter,
  shows the table with rows. Clicking Schedule Meeting opens the modal.
  Picking 2 slots and Send pops a toast on success.
- No design polish required here; styling lives in Task 06. Use plain
  Tailwind for now.

---

## Sub-tasks

### 04.1 — `routes/candidates.py`

**Files**: `backend/api/routes/candidates.py` (NEW), `backend/main.py` (1-line edit)

**Done when**: Three routes exist and pass smoke-test cURLs against the
deployed Modal URL.

**Prompt to paste:**

```
Create backend/api/routes/candidates.py and register it in backend/main.py.

Read first:
  - backend/api/routes/chat.py — note the FastAPI / Pydantic shape, the
    request.state.supabase + request.state.llm pattern, and how /chat/query
    composes a response.
  - backend/api/agents/specialists/s2_rag.py — RAGAgent.retrieve(query,
    top_k, corpus_filter) is what we'll use for the search.
  - backend/api/integrations/resend_client.py and cal_com_client.py — the
    schedule route uses both.

Implement three routes on a new APIRouter:

  POST /candidates/search
    Body: {q: str, limit: int = 20}
    Returns: list of candidate cards (see acceptance criteria above)

    Logic:
      1. RAGAgent.retrieve(q, top_k=limit, corpus_filter="cvs")
      2. Group chunks by metadata->>candidate_id; the highest-similarity
         chunk per candidate becomes that candidate's match_score.
      3. For the top N candidate_ids, fetch the candidates rows in one
         supabase.table("candidates").select("*").in_("id", ids).execute().
      4. Build cards: name, email, phone, top-5 skills (from skills_json),
         experience_summary (truncate to 160 chars), match_score,
         is_duplicate, missing_fields_json, cv_storage_path, id.
      5. Sort cards by match_score desc.
      6. Filter out confidential=true rows? NO — Candidate Search is the
         recruiter view; confidential filter is only for the chat-side
         match_chunks RPC. But return confidential=true on the card so the
         UI can show a lock icon if needed.

  GET /candidates/{candidate_id}/cv
    Returns: {url: str, expires_at: ISO}
    Logic:
      1. Look up the candidate's cv_storage_path. If null, return 404.
      2. supabase.storage.from_("cv-attachments").create_signed_url(path,
         expires_in=300) → 5-minute TTL.
      3. Return the URL + the absolute expiry time.

  POST /candidates/{candidate_id}/schedule
    Body: {
      slots: [{start: str, end: str, booking_url: str}, ...],
      message: str | None,         # optional custom message from the recruiter
    }
    Returns: {resend_id: str, slots_sent: int}
    Logic:
      1. Look up the candidate's name + email. 404 if not found.
      2. Render an HTML invite email:
         - Greeting using candidate name.
         - Optional recruiter message (escape HTML).
         - 1-3 slot rows; each row is a styled <a href={booking_url}>
           "Tuesday May 6, 2:30 PM" </a>.
         - Sign-off referencing AutoCI as the system.
         (Keep it plain — Task 06 design pass refines styling.)
      3. ResendClient().send_email(to=candidate.email, subject="Interview slots
         for {role}", html=rendered_html).
      4. Return {resend_id, slots_sent}.

  Error handling:
    - All routes raise HTTPException(404) when the candidate is missing.
    - Schedule route raises HTTPException(400) if slots is empty or has >3
      entries.
    - On Resend / cal.com errors, raise HTTPException(502) with the upstream
      message.

In backend/main.py:
  - Import the new candidates router: `from api.routes import ... candidates`
  - app.include_router(candidates.router, prefix="/candidates", tags=["candidates"])

Add a level1_unit() test that:
  - Mocks supabase to return a fixed candidate row + a fixed RAGAgent result
  - Calls /candidates/search and asserts the response shape
  - Asserts /candidates/{id}/schedule with empty slots returns 400

Smoke (after deploy):
  curl -X POST https://charlenator--autoci-backend-fastapi-app.modal.run/candidates/search \
    -H "Content-Type: application/json" -d '{"q":"java","limit":3}'

Do not modify any other file. Do not add any new dependency.
```

---

### 04.2 — `frontend/src/app/candidates/page.tsx` rewrite

**File**: `frontend/src/app/candidates/page.tsx` (REWRITE)

**Done when**: Page renders a search bar at top, fires `/candidates/search`
on Enter / button-click, shows a loading state, and renders results via
`<CandidateTable>` with a `<ScheduleMeetingModal>` portaled in.

**Prompt to paste:**

```
Rewrite frontend/src/app/candidates/page.tsx.

Read first:
  - frontend/src/components/chat/ChatPanel.tsx — note the fetch pattern,
    pending state, error rendering, and use of process.env.NEXT_PUBLIC_API_URL.
  - frontend/src/lib/chat-types.ts — define new types here as needed (see
    below).

Add to frontend/src/lib/chat-types.ts:

  export interface CandidateCard {
    id: string;
    name: string | null;
    email: string | null;
    phone: string | null;
    skills: string[];
    experience_summary: string | null;
    match_score: number;
    is_duplicate: boolean;
    missing_fields: string[];
    cv_storage_path: string | null;
    confidential: boolean;
  }

  export interface CandidatesSearchResponse {
    results: CandidateCard[];
  }

  export interface CalSlot {
    start: string;
    end: string;
    booking_url: string;
  }

Rewrite candidates/page.tsx as a "use client" page component:

  'use client';

  Three pieces of state:
    - query (string), driven by an <input>
    - results (CandidateCard[] | null), null = "haven't searched yet"
    - pending (bool), schedulingFor (CandidateCard | null)

  Layout (plain Tailwind for now; Task 06 design pass replaces this):
    - <header> with title "Candidate Search" + a search input + a Search
      button. Pressing Enter or clicking Search fires fetch.
    - If pending, show "Searching…".
    - If results === null, show an empty state ("Type a query above").
    - Otherwise, <CandidateTable rows={results} onSchedule={(card) =>
      setSchedulingFor(card)} />.
    - <ScheduleMeetingModal candidate={schedulingFor} onClose={() =>
      setSchedulingFor(null)} /> at the bottom of the tree (rendered when
      schedulingFor != null).

  Fetch:
    POST `${API_BASE}/candidates/search` with {q: query, limit: 20}.
    On error: setResults([]) and surface a small <p className="text-red-600">
    with the message.

Do not change any other route or page. Do not add any new dependency.
```

---

### 04.3 — `CandidateTable.tsx`

**File**: `frontend/src/components/CandidateTable.tsx` (NEW)

**Done when**: Stateless component renders a table of `CandidateCard[]`.
Columns: Name + email + phone, Skills (top 5 as chips), Match score (0..1
with a small bar), Flags (duplicate badge, missing-fields badge if any),
CV (link that calls `/candidates/{id}/cv` and opens the signed URL),
Actions (Schedule Meeting button). Plain Tailwind only.

**Prompt to paste:**

```
Create frontend/src/components/CandidateTable.tsx.

Props:
  rows: CandidateCard[];
  onSchedule: (card: CandidateCard) => void;

Read first:
  - frontend/src/lib/chat-types.ts — CandidateCard type lives here.
  - The acceptance criteria above for the columns.

Implementation:
  - Single <table> with <thead> + <tbody>.
  - Columns: Candidate (name big, email + phone small), Skills (top 5 as
    small grey chips, "+N more" if more), Match (formatted as 0.74 + a
    horizontal bar of width=match_score*100%), Flags (duplicate pill if
    is_duplicate, missing-fields pill listing the count if missing_fields
    has any), CV (button "Download" that fetches /candidates/{id}/cv and
    opens response.url in a new tab; disabled if cv_storage_path is null),
    Actions (Schedule Meeting button → calls onSchedule(row)).
  - On the CV download button error, surface an inline <span className="text-red-600">.
  - Use plain Tailwind. No icon libraries. No new packages.

Do not modify any other file.
```

---

### 04.4 — `ScheduleMeetingModal.tsx`

**File**: `frontend/src/components/ScheduleMeetingModal.tsx` (NEW)

**Done when**: Modal that — when `candidate != null` — fetches a 14-day slot
grid from a (yet-to-be-added) `GET /candidates/slots` endpoint OR (simpler)
calls cal.com directly via a new backend endpoint `GET /scheduling/slots`.
Shows a date-grouped grid of slots. Recruiter ticks up to 3, optionally
adds a custom message, clicks Send. POSTs to
`/candidates/{id}/schedule` with the chosen slots and the message. Pops a
success toast and closes the modal on success.

**Prompt to paste:**

```
Create frontend/src/components/ScheduleMeetingModal.tsx.

Read first:
  - frontend/src/lib/chat-types.ts — CalSlot, CandidateCard.
  - 04.1 above — note that /candidates/{id}/schedule expects {slots,
    message} and returns {resend_id, slots_sent}.

Add a new backend route first (yes, this means a small backend edit; do it
in this same DeepSeek session):

  GET /scheduling/slots?days=14
  Returns: {slots: [{start, end, booking_url}, ...]} flattened across all dates,
  sorted by start time. Internally calls CalComClient().get_slots(days=14)
  and flattens.

Add this route to a new file backend/api/routes/scheduling.py and register
it in main.py. One route, ~20 LOC.

Then implement the modal:

  Props:
    candidate: CandidateCard | null;
    onClose: () => void;
    onSent?: (resendId: string, slotsSent: number) => void;

  When candidate becomes non-null:
    1. Fetch /scheduling/slots?days=14. Store result.
    2. Show a date-grouped list (one section per date label like "Mon, May 4").
       Each section lists slots as small <button> chips showing "09:00–09:30".
    3. User clicks chips to toggle (max 3 selected). Show "X / 3 selected".
    4. Optional <textarea> for a custom message.
    5. Send button — disabled if 0 slots selected. On click:
         POST /candidates/{candidate.id}/schedule with the selected slots +
         message. On success: call onSent(...) and onClose(). On error:
         show error inline.

  Layout: simple modal — fixed inset-0 black/40 backdrop + centered white
  card. Plain Tailwind, no transitions. Task 06 design pass refines.

  When candidate === null, render nothing (return null).

Do not modify any other file beyond what's listed.
Do not add any new dependency.
```

---

### 04.5 — End-to-end smoke

**File**: none (manual)

**Done when**: From the deployed Vercel UI, you can search for "java",
click Schedule Meeting on any candidate, pick 2 slots, hit Send, see a
success toast, and (in your inbox) receive the invite email with two
working booking links.

**Prompt to paste:**

```
End-to-end smoke for B8.

Pre-req: B5 has produced at least 5 candidate rows in Supabase with
skills_json populated (use /inbound/simulate with a few CVs from
dev-tools/cv_generator/output/).

Pre-req: RESEND_FROM_EMAIL is set in the Modal Secret. If not, add it
(it's the verified sender on Resend — ask Charle for the value).

1. Open the deployed Vercel URL → /candidates.
2. Type "java" + Enter. Confirm 3+ rows render with names, skills chips,
   match scores, action buttons.
3. Click Download on any row's CV. A signed-URL .docx download should
   start. Confirm the file matches the candidate.
4. Click Schedule Meeting on one row. Modal opens with a 14-day slot grid.
5. Pick 2 slots from different days. Optional: type a custom message.
   Click Send.
6. Toast says "Invite sent (resend_id=...)". Modal closes.
7. Check the candidate's email — invite email arrives within 30s with
   2 working booking links. Clicking a link opens cal.com and books the
   slot.

If anything fails, leave the matching sub-task in "In progress" and write
a "Blocked" row with the question for Charle.

Update KANBAN.md: 04.1-04.5 → "Done".
```

## Definition of done

- All 5 sub-tasks moved to KANBAN "Done"
- `python test_all.py 1` passes
- One end-to-end search → schedule → email round-trip succeeds

## Commit + push

After 04.5 passes:

```
git add backend/api/routes/candidates.py backend/api/routes/scheduling.py backend/main.py backend/test_all.py frontend/src/lib/chat-types.ts frontend/src/components/CandidateTable.tsx frontend/src/components/ScheduleMeetingModal.tsx frontend/src/app/candidates/page.tsx CONTEXT/handoff_to_deepseek/KANBAN.md
git commit -m "Sprint B8: Candidate Search interface + Schedule Meeting flow (search route, table, slot modal, Resend invite)"
git push origin main
```
