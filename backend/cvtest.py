#!/usr/bin/env python3
"""End-to-end smoke test for the B5 inbound CV pipeline.

Purpose: POST a real .docx CV to /inbound/simulate on the deployed Modal endpoint,
verify the full pipeline runs end-to-end, and confirm dedup on re-run.
"""

import base64
import json
import os
import sys
import time

import httpx
from dotenv import load_dotenv
from supabase import create_client

# ── Config ────────────────────────────────────────────────────────────────

MODAL_URL = "https://charlenator--autoci-backend-fastapi-app.modal.run"
CV_DIR = os.path.join(os.path.dirname(__file__), "..", "dev-tools", "cv_generator", "output")
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

# Pick one CV — thabo_mokoena_senior_java_developer is a named person with
# skills, experience, and education that will exercise all chunk types.
CV_FILENAME = "kagiso_sekhoane_data_scientist.docx"
SENDER = "hiring@techco.co.za"
SUBJECT = "CV Submission: Kagiso Sekhoane"

# ── Helpers ───────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
pass_count = 0
fail_count = 0

def ok(name: str):
    global pass_count
    pass_count += 1
    print(f"  {GREEN}✓{RESET} {name}")

def fail(name: str, detail: str = ""):
    global fail_count
    fail_count += 1
    msg = f"  {RED}✗{RESET} {name}"
    if detail:
        msg += f"\n       {RED}{detail}{RESET}"
    print(msg)

def check(name: str, ok_: bool, detail: str = ""):
    if ok_:
        ok(name)
    else:
        fail(name, detail)

# ── Load env ──────────────────────────────────────────────────────────────

load_dotenv(ENV_PATH)
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
if not supabase_url or not supabase_key:
    print(f"{RED}ERROR{RESET}: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

supa = create_client(supabase_url, supabase_key)

# ── Step 1: Read the CV ───────────────────────────────────────────────────

cv_path = os.path.join(CV_DIR, CV_FILENAME)
if not os.path.exists(cv_path):
    print(f"{RED}ERROR{RESET}: CV not found at {cv_path}")
    sys.exit(1)

with open(cv_path, "rb") as f:
    docx_bytes = f.read()

docx_b64 = base64.b64encode(docx_bytes).decode("ascii")
print(f"\n{'='*60}")
print(f"📄 Loaded CV: {CV_FILENAME} ({len(docx_bytes)} bytes)")
print(f"{'='*60}")

# ── Step 2: POST to /inbound/simulate ─────────────────────────────────────

print(f"\n{'─'*60}")
print("🚀 POST /inbound/simulate to Modal")
print(f"{'─'*60}")

payload = {
    "sender": SENDER,
    "recipient": "jobs@charlecoetzee.com",
    "subject": SUBJECT,
    "body_text": "",
    "body_html": "",
    "attachment_filename": CV_FILENAME,
    "attachment_mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "attachment_b64": docx_b64,
    "run_worker": True,
}

try:
    resp = httpx.post(
        f"{MODAL_URL}/inbound/simulate",
        json=payload,
        timeout=120,
    )
    check(f"HTTP 200 (got {resp.status_code})", resp.status_code == 200,
          resp.text[:500] if resp.status_code != 200 else "")

    if resp.status_code == 200:
        data = resp.json()
        worker = data.get("worker", {})
        inbound_id = data.get("inbound_id", "")
        print(f"  inbound_id: {inbound_id}")
        print(f"  attachment_path: {data.get('attachment_path')}")
        print(f"  worker.final_status: {worker.get('final_status')}")
        print(f"  worker.classified_as_cv: {worker.get('classified_as_cv')}")
        print(f"  worker.candidate_id: {worker.get('candidate_id')}")
        print(f"  worker.chunk_count: {worker.get('chunk_count')}")
        print(f"  worker.notes: {json.dumps(worker.get('notes', []), indent=2)}")
        print(f"  worker.error: {worker.get('error')}")

        # Verify worker response
        final_status = worker.get("final_status", "")
        check("final_status = 'processed'", final_status == "processed",
              f"got '{final_status}'")
        check("classified_as_cv = True", worker.get("classified_as_cv") is True,
              f"got {worker.get('classified_as_cv')}")
        check("candidate_id is set", bool(worker.get("candidate_id")),
              f"got candidate_id={worker.get('candidate_id')}")

        chunk_count = worker.get("chunk_count", 0)
        check(f"chunk_count between 5 and 8 (got {chunk_count})",
              5 <= chunk_count <= 8,
              f"got {chunk_count}")
        check("no error", not worker.get("error"),
              f"got error: {worker.get('error')}")

        candidate_id = worker.get("candidate_id", "")

        # ── Step 3: Verify DB rows ────────────────────────────────────
        print(f"\n{'─'*60}")
        print("🗄️  Verifying database rows")
        print(f"{'─'*60}")

        # candidates row
        cand_resp = (
            supa.table("candidates")
            .select("*")
            .eq("candidate_id", candidate_id)
            .execute()
        )
        cand_rows = cand_resp.data or []
        check(f"candidates row exists", len(cand_rows) == 1,
              f"got {len(cand_rows)} rows")

        if cand_rows:
            c = cand_rows[0]
            print(f"  name: {c.get('name')}")
            print(f"  email: {c.get('email')}")
            print(f"  phone: {c.get('phone')}")
            print(f"  skills_json: {c.get('skills_json')}")
            print(f"  experience_summary length: {len(c.get('experience_summary') or '')}")
            print(f"  cv_storage_path: {c.get('cv_storage_path')}")
            print(f"  confidential: {c.get('confidential')}")
            print(f"  dedup_hash: {c.get('dedup_hash')}")
            check("name is populated", bool(c.get("name")),
                  f"got name={c.get('name')}")
            check("email is populated", bool(c.get("email")),
                  f"got email={c.get('email')}")
            check("source_email_id matches", str(c.get("source_email_id")) == inbound_id,
                  f"got {c.get('source_email_id')} expected {inbound_id}")

        # corpus_chunks rows — use metadata->> operator for broadest match
        # (handles both raw dict and double-string-encoded JSONB)
        chunks_resp = (
            supa.table("corpus_chunks")
            .select("*")
            .filter("metadata->>candidate_id", "eq", candidate_id)
            .execute()
        )
        chunk_rows = chunks_resp.data or []
        check(f"corpus_chunks returned (found {len(chunk_rows)})", len(chunk_rows) > 0)
        if chunk_rows:
            chunk_kinds = [c.get("metadata", {}).get("chunk_kind") for c in chunk_rows]
            print(f"  chunk kinds found: {chunk_kinds}")
            has_identity = "identity" in chunk_kinds
            has_skills = "skills" in chunk_kinds
            has_summary = "summary" in chunk_kinds
            has_experience = "experience" in chunk_kinds
            has_education = "education" in chunk_kinds
            check("has 'identity' chunk", has_identity, f"kinds: {chunk_kinds}")
            check("has 'skills' chunk", has_skills, f"kinds: {chunk_kinds}")
            check("has 'summary' chunk", has_summary, f"kinds: {chunk_kinds}")
            check("has 'experience' chunk(s)", has_experience, f"kinds: {chunk_kinds}")
            check("has 'education' chunk", has_education, f"kinds: {chunk_kinds}")

        # inbound_emails row
        inb_resp = (
            supa.table("inbound_emails")
            .select("*")
            .eq("id", inbound_id)
            .execute()
        )
        inb_rows = inb_resp.data or []
        check(f"inbound_emails row exists", len(inb_rows) == 1,
              f"got {len(inb_rows)} rows")
        if inb_rows:
            ie = inb_rows[0]
            print(f"  inbound status: {ie.get('status')}")
            print(f"  inbound processed_at: {ie.get('processed_at')}")
            check("status = 'processed'", ie.get("status") == "processed",
                  f"got '{ie.get('status')}'")
            check("classified_as_cv = True", ie.get("classified_as_cv") is True,
                  f"got {ie.get('classified_as_cv')}")
            check("processed_at is set", bool(ie.get("processed_at")),
                  f"got processed_at={ie.get('processed_at')}")

except httpx.TimeoutException:
    fail("POST timed out after 120s — pipeline may still be running on Modal")
except Exception as exc:
    fail(f"POST failed: {exc}")

# ── Step 4: Re-run to confirm dedup ───────────────────────────────────────

print(f"\n{'─'*60}")
print("🔄 Re-running with same payload (dedup test)")
print(f"{'─'*60}")
time.sleep(2)  # brief pause so timestamps differ

try:
    resp2 = httpx.post(
        f"{MODAL_URL}/inbound/simulate",
        json=payload,
        timeout=120,
    )
    check(f"HTTP 200 on re-run (got {resp2.status_code})", resp2.status_code == 200,
          resp2.text[:500] if resp2.status_code != 200 else "")

    if resp2.status_code == 200:
        data2 = resp2.json()
        worker2 = data2.get("worker", {})
        inbound_id2 = data2.get("inbound_id", "")
        notes2 = worker2.get("notes", [])
        has_dup_note = any("duplicate" in n.lower() for n in notes2)

        print(f"  inbound_id (2nd): {inbound_id2}")
        print(f"  worker.final_status: {worker2.get('final_status')}")
        print(f"  worker.notes: {json.dumps(notes2, indent=2)}")

        check("final_status = 'processed'", worker2.get("final_status") == "processed",
              f"got '{worker2.get('final_status')}'")
        check("notes mention 'duplicate'", has_dup_note,
              f"notes: {notes2}")

        # Verify the second inbound row also got processed
        inb2_resp = (
            supa.table("inbound_emails")
            .select("*")
            .eq("id", inbound_id2)
            .execute()
        )
        inb2_rows = inb2_resp.data or []
        check(f"2nd inbound_emails row exists", len(inb2_rows) == 1)
        if inb2_rows:
            check("2nd row status = 'processed'", inb2_rows[0].get("status") == "processed",
                  f"got '{inb2_rows[0].get('status')}'")

except httpx.TimeoutException:
    fail("Re-run POST timed out after 120s")
except Exception as exc:
    fail(f"Re-run POST failed: {exc}")

# ── Summary ───────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
total = pass_count + fail_count
print(f"{'RESULTS':^60}")
print(f"{'='*60}")
print(f"  {GREEN}{pass_count} passed{RESET}")
if fail_count:
    print(f"  {RED}{fail_count} failed{RESET}")
else:
    print(f"  {GREEN}All checks passed! 🎉{RESET}")

# If there's a candidate_id, print the supabase queries to run manually
if 'candidate_id' in dir() and candidate_id:
    print(f"\n{YELLOW}Quick-verify commands:{RESET}")
    print(f"  Candidate:    candidates?candidate_id=eq.{candidate_id}")
    print(f"  Chunks:       corpus_chunks?metadata->>candidate_id=eq.{candidate_id}")
    print(f"  Inbound row:  inbound_emails?id=eq.{inbound_id}")

sys.exit(0 if fail_count == 0 else 1)
