#!/usr/bin/env python3
"""seed_cvs.py — Bulk-seed CVs into AutoCI via /inbound/simulate.

Reads every .docx from dev-tools/cv_generator/output/ and POSTs each one
to the deployed /inbound/simulate endpoint. This triggers the full B5
pipeline synchronously per file:

    1. Upload .docx to cv-attachments Storage bucket
    2. Insert inbound_emails row (status pending → processing → processed)
    3. S5 classifier (is this a CV?)
    4. S6 extractor (name, email, phone, skills, experience, education)
    5. S7 confidentiality flag
    6. Chunk CV into 5-8 corpus_chunks rows
    7. Embed each chunk via bge-small-en-v1.5 (384-d)
    8. Upsert to candidates + corpus_chunks tables
    9. Mark inbound_emails row processed

Usage:
    # Point at the deployed Modal backend:
    API_BASE=https://charlenator--autoci-backend-fastapi-app.modal.run \
        python dev-tools/seed_cvs.py

    # Or point at a local dev server:
    API_BASE=http://127.0.0.1:8000 \
        python dev-tools/seed_cvs.py

The script will skip the LLM-dependent steps if the API key isn't set (falls
back to "not_cv" classification). Run it after you've changed the LLM provider.

Requires: pip install httpx
"""

from __future__ import annotations

import base64
import os
import sys
import time
from pathlib import Path

import httpx

# ── Config ────────────────────────────────────────────────────────────────────
CV_FOLDER = Path(__file__).resolve().parent / "cv_generator" / "output"
API_BASE  = os.environ.get("API_BASE", "https://charlenator--autoci-backend-fastapi-app.modal.run")
TIMEOUT   = 60  # LLM calls can take a while per CV
# ───────────────────────────────────────────────────────────────────────────────


def seed_one(client: httpx.Client, docx_path: Path) -> dict:
    """POST a single .docx to /inbound/simulate and return the response JSON."""
    raw_bytes = docx_path.read_bytes()
    b64 = base64.b64encode(raw_bytes).decode()

    payload = {
        "sender": "seeder@autoci.local",
        "recipient": "jobs@wabi-ai.tech",
        "subject": f"Application: {docx_path.stem}",
        "body_text": f"Please find attached my CV ({docx_path.name}).",
        "attachment_filename": docx_path.name,
        "attachment_mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "attachment_b64": b64,
        "run_worker": True,
    }

    resp = client.post(f"{API_BASE}/inbound/simulate", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    files = sorted(CV_FOLDER.glob("*.docx"))
    total = len(files)
    if total == 0:
        print(f"No .docx files found in {CV_FOLDER}")
        sys.exit(1)

    print(f"Found {total} CVs to seed via {API_BASE}\n")

    stats: dict[str, int] = {"processed": 0, "not_cv": 0, "error": 0, "skip": 0}
    start = time.time()

    with httpx.Client() as client:
        for i, cv in enumerate(files, 1):
            label = f"[{i:>2}/{total}]"
            try:
                data = seed_one(client, cv)
            except httpx.TimeoutException:
                print(f"{label} ⏱ TIMEOUT  {cv.name}  (LLM call took >{TIMEOUT}s)")
                stats["error"] += 1
                continue
            except httpx.HTTPStatusError as exc:
                print(f"{label} ✗ FAIL     {cv.name}  HTTP {exc.response.status_code}")
                stats["error"] += 1
                continue
            except Exception as exc:
                print(f"{label} ✗ FAIL     {cv.name}  {exc}")
                stats["error"] += 1
                continue

            worker = data.get("worker") or {}
            status = worker.get("final_status", "unknown")

            if status == "processed":
                cid = worker.get("candidate_id", "?")[:8]
                chunks = worker.get("chunk_count", 0)
                print(f"{label} ✓          {cv.name}  candidate={cid}… chunks={chunks}")
                stats["processed"] += 1
            elif status == "not_cv":
                print(f"{label} ⚠ NOT_CV   {cv.name}")
                stats["not_cv"] += 1
            else:
                err = worker.get("error", "unknown error")
                print(f"{label} ✗ {status.upper():8s} {cv.name}  {err}")
                stats["error"] += 1

    elapsed = time.time() - start
    ok = stats["processed"]
    print(f"\n{'─' * 50}")
    print(f"Done  {total} files  ({elapsed:.0f}s)")
    print(f"  ✓ processed: {ok}")
    print(f"  ⚠ not_cv:    {stats['not_cv']}")
    print(f"  ✗ errors:    {stats['error']}")
    if ok < total:
        print(f"\nRe-run to retry errors — the pipeline respects dedup hashes so")
        print(f"already-processed CVs will be skipped (candidate_id returned).")
    print()


if __name__ == "__main__":
    main()
