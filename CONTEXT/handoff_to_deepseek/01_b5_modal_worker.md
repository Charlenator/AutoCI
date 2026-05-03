# Task 01 — B5: Fill the Modal worker (inbound CV pipeline)

## Goal

Replace the B4 stub in [`backend/api/workers/inbound_processor.py`](../../backend/api/workers/inbound_processor.py) with the real pipeline:
download attachment → classify (is this a CV?) → extract structured fields →
confidentiality flag → section-based smart-chunking → vectorize → upsert
candidate row + corpus_chunks rows → mark `inbound_emails` row processed.

## Files this task touches

- NEW: `backend/api/agents/specialists/s5_cv_classifier.py`
- NEW: `backend/api/agents/specialists/s6_cv_extractor.py`
- NEW: `backend/api/agents/specialists/s7_confidentiality.py`
- NEW: `backend/api/workers/cv_chunking.py` (smart-chunking helper)
- NEW: `backend/api/workers/email_vectorizer.py` (non-CV vectorizer helper)
- MODIFY: `backend/api/workers/inbound_processor.py`
- ADD TESTS: `backend/test_all.py`

## Acceptance criteria

- `/inbound/simulate` with one of `dev-tools/cv_generator/output/*.docx` produces:
  - One row in `candidates` with `name`, `email`, `phone`, `skills_json`,
    `experience_summary`, `cv_storage_path`, `confidential`, `source_email_id` set.
  - 5–8 rows in `corpus_chunks` with `corpus_name='cvs'`, `metadata` JSON
    containing `candidate_id`, `chunk_kind`, `section_label`, `confidential: true`.
  - The `inbound_emails` row flips to `status='processed'` (or `not_cv` if
    classified non-CV) with `classified_as_cv` set and `processed_at`
    populated.
- A second `/inbound/simulate` with the same .docx is a no-op (dedup hash
  matches; row stays `status='processed'`).
- Backend tests still pass: `cd backend && python test_all.py 1`.

---

## Sub-tasks

### 01.1 — S5 CV classifier

**File**: `backend/api/agents/specialists/s5_cv_classifier.py` (NEW)

**Done when**: Module exposes `class CVClassifierAgent` with method
`is_cv(text: str, llm: LiteLLMRouter) -> dict` returning
`{"is_cv": bool, "confidence": float, "reason": str}`. Uses a single
DeepSeek call via `llm.route(...)`. Tolerates LLM errors gracefully (returns
a low-confidence False with a `reason="LLM error: ..."`).

**Prompt to paste:**

```
Create backend/api/agents/specialists/s5_cv_classifier.py.

Read these files first:
  - backend/api/agents/specialists/s1_query_planner.py — copy its LLM-call +
    JSON-parsing pattern (json.loads, the markdown-fence stripper, the
    fallback path).
  - backend/api/tools/t3_litellm_router.py — note the route() signature.
  - backend/api/workers/inbound_processor.py — your output is consumed at
    the # ---- B5 placeholder ---- comment.

Implement:

  class CVClassifierAgent:
      def __init__(self, llm_router: LiteLLMRouter): ...
      def is_cv(self, text: str, *, session_id: str | None = None) -> dict:
          """Returns {is_cv: bool, confidence: float (0..1), reason: str}."""

System prompt for the LLM: explain that the agent is judging whether a piece
of extracted text is a candidate's CV (not a cover letter, not a marketing
PDF, not a job posting). Ask for JSON output:
  {"is_cv": true|false, "confidence": 0..1, "reason": "<one sentence>"}

Edge cases:
  - empty/whitespace text → return {"is_cv": False, "confidence": 0.0,
    "reason": "empty input"} without calling the LLM.
  - LLM error or non-JSON response → return
    {"is_cv": False, "confidence": 0.0, "reason": "LLM error: <exc>"}.

Use the route name "translation" (it's the cheapest in t3_litellm_router).
Pass from_agent="s5_cv_classifier", to_agent="t3_llm" so cost tracking works.

Add a test in backend/test_all.py inside level1_unit() that imports the
class and asserts an empty input returns is_cv=False with confidence 0.0.

Do not modify any other file. Do not add any new dependency.
```

---

### 01.2 — S6 .docx field extractor

**File**: `backend/api/agents/specialists/s6_cv_extractor.py` (NEW)

**Done when**: Module exposes `class CVExtractorAgent` with method
`extract(docx_bytes: bytes, llm: LiteLLMRouter) -> dict` returning a
normalized record with `name`, `email`, `phone`, `summary`, `skills`
(list[str]), `experience` (list of `{role, company, start_date, end_date,
description}`), `education` (list of `{school, degree, year}`),
`missing_fields` (list[str]), and a `raw_text` field carrying the full
extracted .docx text (used downstream by the chunking helper).

**Prompt to paste:**

```
Create backend/api/agents/specialists/s6_cv_extractor.py.

Read first:
  - backend/api/workers/inbound_processor.py — see how the worker passes the
    attachment bytes in (it doesn't yet; you'll wire that in 01.6).
  - backend/api/agents/specialists/s5_cv_classifier.py — same shape for the
    LLM-call + JSON-parsing pattern.
  - backend/requirements.txt — python-docx is already there.

Implement:

  class CVExtractorAgent:
      def __init__(self, llm_router: LiteLLMRouter): ...
      def extract(self, docx_bytes: bytes, *, session_id: str | None = None) -> dict:
          """
          Returns a normalized CV record:
            {
              "name": str|None,
              "email": str|None,
              "phone": str|None,
              "summary": str|None,
              "skills": list[str],
              "experience": [{"role","company","start_date","end_date","description"}, ...],
              "education": [{"school","degree","year"}, ...],
              "missing_fields": list[str],   # subset of {"name","email","phone","summary","skills","experience","education"}
              "raw_text": str,               # the full text we extracted from the .docx
            }
          """

Steps:
  1. Use python-docx to read every paragraph from the docx. Concatenate to
     raw_text. If python-docx raises, return a record with everything None
     and missing_fields = ["name","email","phone","summary","skills",
     "experience","education"] and raw_text = "".
  2. Send raw_text to the LLM with a JSON-output system prompt asking for the
     fields above. Cap raw_text at 8000 chars on the way in.
  3. Normalize: lowercase email, strip whitespace, lowercase + dedupe skills.
  4. Compute missing_fields by checking which top-level keys are None or
     empty after normalization. (skills/experience/education count as
     missing only if empty list.)
  5. On any LLM/JSON error, fall back to a record with raw_text populated
     but every other field None / empty list / missing.

Use the route name "translation". Pass from_agent="s6_cv_extractor",
to_agent="t3_llm".

Add a test in test_all.py that constructs an in-memory docx via python-docx
with a known name + email + phone, then asserts the extractor returns those
fields populated and missing_fields is empty.

Do not modify any other file. Do not add any new dependency.
```

---

### 01.3 — S7 confidentiality classifier

**File**: `backend/api/agents/specialists/s7_confidentiality.py` (NEW)

**Done when**: Module exposes `class ConfidentialityAgent` with method
`classify(text: str, *, session_id: str | None = None) -> dict` returning
`{"confidential": bool, "reason": str}`. Defaults to `confidential=True`
on any uncertainty (we'd rather over-flag than leak).

**Prompt to paste:**

```
Create backend/api/agents/specialists/s7_confidentiality.py.

Read first:
  - backend/api/agents/specialists/s5_cv_classifier.py — same shape.
  - supabase/migrations/004_inbound_pipeline.sql — note that
    candidates.confidential and corpus_chunks.confidential default to true
    when populated by the worker (see 01.6).

Implement:

  class ConfidentialityAgent:
      def __init__(self, llm_router: LiteLLMRouter): ...
      def classify(self, text: str, *, session_id: str | None = None) -> dict:
          """Returns {confidential: bool, reason: str}.

          Default to confidential=True on any uncertainty: we'd rather over-flag
          a personal CV than leak. The non-confidential bucket is for clearly
          generic content (job postings, public articles, sample data).
          """

System prompt: explain that personal data — names, emails, phone numbers,
salary expectations, references, work histories tied to identifiable people —
is confidential. Generic content (a public job posting, a Wikipedia paragraph,
a benchmark study) is not.

Edge cases:
  - empty text → confidential=True, reason="empty input"
  - LLM error → confidential=True, reason="LLM error: <exc>"

Use route "translation". from_agent="s7_confidentiality", to_agent="t3_llm".

Add a test in test_all.py asserting empty input returns confidential=True.

Do not modify any other file. Do not add any new dependency.
```

---

### 01.4 — Section-based smart-chunking helper

**File**: `backend/api/workers/cv_chunking.py` (NEW)

**Done when**: Module exposes `def chunk_cv(record: dict, candidate_id: str)
-> list[dict]` returning 5–8 chunk records ready to insert into
`corpus_chunks`. Each chunk has `corpus_name='cvs'`, `chunk_text`, and
`metadata` dict containing `candidate_id`, `chunk_kind`, `section_label`,
optional `role_target` for per-job chunks, and `confidential: True`.

**Prompt to paste:**

```
Create backend/api/workers/cv_chunking.py.

Read first:
  - CONTEXT/plan-of-record.md — the "CV smart-chunking strategy" row in §7
    Phase 6 has the locked decision: per-CV chunks are
    {identity, skills, summary, education} + one chunk per individual job.
  - backend/api/agents/specialists/s6_cv_extractor.py — your input is the
    record returned by extract().

Implement:

  def chunk_cv(record: dict, candidate_id: str) -> list[dict]:
      """
      Build 5-8 corpus_chunks rows from a CVExtractorAgent record.

      Output rows have shape:
        {
          "corpus_name": "cvs",
          "chunk_text": str,          # what gets embedded
          "metadata": {
            "candidate_id": candidate_id,
            "chunk_kind": "identity"|"skills"|"summary"|"experience"|"education",
            "section_label": str,     # human-readable label for citations
            "role_target": str|None,  # only for chunk_kind="experience"; the role title
            "confidential": True,
          },
        }
      """

Chunking rules:
  - identity chunk: combine name + email + phone + (location if present in
    raw_text) into a short text. chunk_kind="identity",
    section_label="Identity".
  - skills chunk: a comma-separated list of normalized skills.
    chunk_kind="skills", section_label="Skills".
  - summary chunk: only if record["summary"] is non-empty.
    chunk_kind="summary", section_label="Profile".
  - one experience chunk per item in record["experience"]. chunk_text =
    "{role} at {company} ({start_date}–{end_date}): {description}".
    chunk_kind="experience", section_label="Experience: {role}",
    role_target={role}.
  - one education chunk if record["education"] is non-empty (combine all
    rows into one chunk_text). chunk_kind="education",
    section_label="Education".
  - Skip any chunk whose text would be empty after the rule.

Cap each chunk_text at 2000 chars. Do not embed here — that's the worker's
job in 01.6.

Add tests in test_all.py covering:
  - A full record with name/email/phone/summary/skills/2 experience items
    /1 education item produces 6 chunks with expected chunk_kinds.
  - A record with no summary skips the summary chunk.

Do not modify any other file. Do not add any new dependency.
```

---

### 01.5 — Email vectorizer helper (non-CV inbound mail)

**File**: `backend/api/workers/email_vectorizer.py` (NEW)

**Done when**: Module exposes `def vectorize_email(subject: str, body: str,
inbound_id: str) -> list[dict]` returning 1–3 chunks ready for
`corpus_chunks` with `corpus_name='inbound_emails'`. Used when the
classifier returns `is_cv=False` but the email still has useful content.

**Prompt to paste:**

```
Create backend/api/workers/email_vectorizer.py.

Read first:
  - backend/api/workers/cv_chunking.py — same shape for the output rows.
  - backend/api/agents/specialists/s4_research.py — note _persist_chunks for
    a similar "split into 1-3 chunks" pattern.

Implement:

  def vectorize_email(subject: str, body: str, inbound_id: str) -> list[dict]:
      """
      Split a non-CV inbound email into 1-3 corpus_chunks rows.

      Output:
        {
          "corpus_name": "inbound_emails",
          "chunk_text": str,
          "metadata": {
            "inbound_id": inbound_id,
            "chunk_kind": "subject"|"body",
            "confidential": True,
          },
        }
      """

Rules:
  - One subject chunk if subject is non-empty (chunk_kind="subject").
  - Split body into paragraphs; group into chunks of <=2000 chars; emit
    one body chunk per group (chunk_kind="body").
  - Total max 3 chunks. If the body has 5 paragraphs, merge to keep it
    under 3 body chunks.
  - Empty subject AND empty body → return [].

Add a test in test_all.py covering a typical 1-paragraph email and an
empty-body email.

Do not modify any other file. Do not add any new dependency.
```

---

### 01.6 — Wire S5/S6/S7 + chunking + vectorizer into `process_pending_email`

**File**: `backend/api/workers/inbound_processor.py` (MODIFY)

**Done when**: The B4 stub block (lines ~103-145 of `inbound_processor.py`,
the `# ---- B5 placeholder ----` comment) is replaced with:

1. Download the attachment from Storage (`cv-attachments` bucket) via the
   stored `attachment_storage_path`.
2. Compute dedup hash; if a candidate with the same hash already exists,
   short-circuit to `final_status='processed'`, `notes` mentions duplicate.
3. S5 classifier: is the .docx (or text body for non-attachment emails) a CV?
4. If is_cv: S6 extractor → S7 confidentiality on the raw_text → upsert
   candidates row with the normalized fields → call `chunk_cv` → embed
   each chunk via `EmbeddingService` → upsert `corpus_chunks` rows with
   `ignore_duplicates=True, on_conflict='content_hash'`.
5. If not_cv: call `vectorize_email` → embed → upsert `corpus_chunks`.
6. Update `inbound_emails` row to final status with `classified_as_cv`,
   `candidate_id` if applicable, `processed_at`.
7. Populate `result.notes` with one line per agent invocation for traceability.

**Prompt to paste:**

```
Modify backend/api/workers/inbound_processor.py to replace the B4 stub
(everything from "# ---- B5 placeholder ----" down to the "result.final_status
= final_status" assignment near the end) with the real pipeline.

Before writing: read all of these files in full so you understand the
contracts you're calling:
  - backend/api/agents/specialists/s5_cv_classifier.py
  - backend/api/agents/specialists/s6_cv_extractor.py
  - backend/api/agents/specialists/s7_confidentiality.py
  - backend/api/workers/cv_chunking.py
  - backend/api/workers/email_vectorizer.py
  - backend/api/tools/t4_embeddings.py — note EmbeddingService.embed_batch
  - backend/api/tools/t3_litellm_router.py — note LiteLLMRouter() init
  - supabase/supabase_schema.sql — confirm column names on candidates +
    corpus_chunks + inbound_emails

Implement the new flow inside process_pending_email():

  Step 1 — Download attachment.
    - If row["attachment_storage_path"] is set, download from the
      "cv-attachments" Storage bucket via supabase.storage.from_(...).download(...).
    - On any download error, set result.error and final_status="error" and
      return.

  Step 2 — Dedup.
    - Compute hash: sha256 of (sender + subject) lowercased + the bytes of
      the attachment if present. Store as row["dedup_hash_calculated"]
      (don't write to DB — use this only for a one-shot existing-candidate
      check below).
    - If a candidate row already exists with that dedup_hash, set
      result.candidate_id = that row's id, final_status="processed",
      notes.append("duplicate of existing candidate"), and short-circuit.

  Step 3 — Classify.
    - Build a LiteLLMRouter (no need to thread it from the caller; create
      one locally with supabase_client=supabase).
    - For .docx attachments: extract raw_text via python-docx INSIDE this
      step (don't make S5 do that — it just sees text). For non-.docx,
      classifier sees row["body"] (which the Edge Function persists; if
      empty, call it not_cv with reason "no docx attachment, no body").
    - S5.is_cv(raw_text) → tentative_is_cv decision.

  Step 4a — CV path (is_cv == True):
    - S6.extract(docx_bytes) → record dict.
    - S7.classify(record["raw_text"]) → confidentiality flag.
    - INSERT or UPSERT candidates row with the record fields + dedup_hash,
      cv_storage_path = row["attachment_storage_path"], confidential =
      S7's flag, source_email_id = inbound_id. Capture the new candidate_id.
    - chunk_cv(record, candidate_id) → list of chunk dicts.
    - For each batch (use embed_batch for efficiency), embed
      [c["chunk_text"] for c in chunks].
    - For each chunk, supabase.table("corpus_chunks").upsert({
        "corpus_name": c["corpus_name"],
        "chunk_text": c["chunk_text"],
        "metadata": json.dumps(c["metadata"]),
        "embedding": emb,
        "confidential": c["metadata"]["confidential"],
      }, on_conflict="content_hash", ignore_duplicates=True).execute()
    - result.candidate_id = candidate_id, result.chunk_count = len(chunks),
      result.classified_as_cv = True, final_status = "processed".

  Step 4b — Not-CV path (is_cv == False):
    - vectorize_email(row["subject"], row["body"] or "", inbound_id) → chunks.
    - Embed + upsert as in 4a.
    - result.classified_as_cv = False, result.chunk_count = len(chunks),
      final_status = "not_cv".

  Step 5 — Final inbound_emails update.
    - Build update_payload with status=final_status, classified_as_cv,
      processed_at = utc-now.isoformat(), error_log=None,
      candidate_id=result.candidate_id if applicable.
    - supabase.table("inbound_emails").update(...).eq("id", inbound_id).execute()

  Throughout: append concise lines to result.notes describing what fired
  ("classifier: is_cv=True conf=0.92", "extracted 7 fields, 0 missing",
  "confidentiality: True (personal data)", "chunked into 6 sections",
  "embedded + upserted 6 corpus_chunks rows"). These end up in the response
  payload of /inbound/simulate so Charle can see what happened.

  On any uncaught exception: set result.error, final_status="error", attempt
  to update inbound_emails to status="error" with error_log=str(exc), and
  return.

After implementing, run: cd backend && python test_all.py 1
All existing tests must pass. New tests for 01.1-01.5 must pass.

Do not modify the route handlers in backend/api/routes/inbound.py — they
already call process_pending_email correctly.

Do not add any new dependency.
```

---

### 01.7 — End-to-end smoke

**File**: none (manual verification step)

**Done when**: One of the generated CVs in `dev-tools/cv_generator/output/`
flows through `/inbound/simulate` and produces a candidate row + 5–8 corpus
chunks. Re-running the same simulation is a no-op.

**Prompt to paste:**

```
Run the end-to-end smoke for B5.

1. Pick one .docx from dev-tools/cv_generator/output/. Read it via the file
   system; you can base64-encode the bytes if /inbound/simulate expects
   that (check backend/api/routes/inbound.py for the exact contract).

2. POST to https://charlenator--autoci-backend-fastapi-app.modal.run/inbound/simulate
   with a payload that matches the simulate route's Pydantic model. The
   route deployment is automatic — modal_config.py picks up code changes
   on the next push to main, but for local-dev testing you can also hit
   http://127.0.0.1:8000/inbound/simulate after starting uvicorn.

3. Confirm:
   a. The response shows final_status="processed", classified_as_cv=true,
      candidate_id=<uuid>, chunk_count between 5 and 8, notes lines per
      step.
   b. supabase.table("candidates").select("*").eq("id", <candidate_id>).execute()
      returns one row with name/email/phone/skills_json populated and
      confidential=true.
   c. supabase.table("corpus_chunks").select("*").contains("metadata",
      {"candidate_id": <candidate_id>}).execute() returns 5-8 rows.
   d. supabase.table("inbound_emails").select("*").eq("id", <inbound_id>).execute()
      shows status="processed", processed_at populated.

4. Re-run /inbound/simulate with the same .docx + same sender + same
   subject. Confirm:
   - final_status="processed" (or "duplicate" if you chose that label)
   - notes mentions "duplicate of existing candidate"
   - No new candidate row, no new corpus_chunks rows.

5. Update KANBAN.md: move 01.1-01.7 from "Backlog" to "Done" with today's
   date. Note any surprises (e.g. extractor missed a field that should
   have been caught).

If anything fails, leave the broken sub-task in "In progress" and write a
"Blocked" row with the question for Charle.

Don't update any other CONTEXT/*.md file.
```

## Definition of done

- All 7 sub-tasks moved to KANBAN "Done"
- `python test_all.py 1` passes
- One manual round-trip via `/inbound/simulate` succeeds end-to-end

## Commit + push

After 01.7 passes:

```
git add backend/api/agents/specialists/s5_*.py backend/api/agents/specialists/s6_*.py backend/api/agents/specialists/s7_*.py backend/api/workers/cv_chunking.py backend/api/workers/email_vectorizer.py backend/api/workers/inbound_processor.py backend/test_all.py CONTEXT/handoff_to_deepseek/KANBAN.md
git commit -m "Sprint B5: fill the inbound CV pipeline (S5 classifier + S6 extractor + S7 confidentiality + smart chunking + vectorizer)"
git push origin main
```
