"""Inbound CV processor — Modal-side worker for the decoupled inbound pipeline.

Sprint B4 ships the **scaffold**: the function loads a pending row, sets
status='processing', and (for now) marks it 'processed' with a stub note.
Sprint B5 fills the body with the real pipeline:

  1. Download the attachment from Storage.
  2. Classify (.docx → "is this a CV?") via the S5 classifier.
  3. Extract structured fields via S6 (`python-docx` + DeepSeek).
  4. Confidentiality flag via S7.
  5. Section-based smart-chunking for the CVs corpus + vectorize via T4.
  6. Upsert candidates row + corpus_chunks rows.
  7. Mark inbound_emails row processed (or 'not_cv' / 'error').

The function is designed to run anywhere — locally during dev (called from
`/simulate-inbound` or `/trigger-process`), and on Modal (Sprint D2 will wrap
this in an `@app.function` web endpoint that the Edge Function pings after
queuing a row).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    inbound_id: str
    final_status: str                      # 'processed' | 'not_cv' | 'error'
    classified_as_cv: bool | None = None
    candidate_id: str | None = None
    chunk_count: int = 0
    error: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "inbound_id": self.inbound_id,
            "final_status": self.final_status,
            "classified_as_cv": self.classified_as_cv,
            "candidate_id": self.candidate_id,
            "chunk_count": self.chunk_count,
            "error": self.error,
            "notes": self.notes,
        }


def process_pending_email(
    inbound_id: str,
    supabase=None,
    *,
    force: bool = False,
) -> ProcessResult:
    """Process a single inbound_emails row.

    Args:
        inbound_id: UUID of the row to process.
        supabase: optional supabase client; if None, creates one from env vars.
        force: if True, re-process even if status != 'pending'. Use sparingly.

    Returns a ProcessResult with the final state. Always sets the DB row's
    status before returning, even on failure (status='error' + error_log).
    """
    if supabase is None:
        supabase = _default_supabase()

    result = ProcessResult(inbound_id=inbound_id, final_status="error")

    # ---- Load the row ----
    row_resp = (
        supabase.table("inbound_emails")
        .select("*")
        .eq("id", inbound_id)
        .limit(1)
        .execute()
    )
    rows = row_resp.data or []
    if not rows:
        result.error = f"inbound_emails row {inbound_id} not found"
        result.notes.append(result.error)
        return result
    row = rows[0]

    if row.get("status") not in ("pending", "error") and not force:
        result.final_status = row.get("status") or "error"
        result.error = f"row already in status {row.get('status')}; pass force=True to re-run"
        result.notes.append(result.error)
        return result

    # ---- Mark processing ----
    try:
        supabase.table("inbound_emails").update({"status": "processing"}).eq(
            "id", inbound_id
        ).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[inbound_processor] could not flip to processing: {exc}")

    # ---- B5 placeholder: real classify/extract/confidentiality/vectorize lands here ----
    #
    # For B4, we just inspect what we have and write a stub note. This keeps
    # the row out of 'pending' so polling-based dispatch can move on, and
    # gives us something to see in the Candidate Search tab once it's wired
    # up.
    has_attachment = bool(row.get("attachment_storage_path"))
    attach_mime = row.get("attachment_mime") or ""
    looks_like_docx = attach_mime in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ) or (row.get("attachment_filename") or "").lower().endswith((".docx", ".doc"))

    note = (
        f"[B4 stub] attachment={'yes' if has_attachment else 'no'} "
        f"mime={attach_mime or 'n/a'} looks_like_docx={looks_like_docx}. "
        f"B5 will classify, extract, vectorize."
    )
    result.notes.append(note)

    # Tentative classification just based on extension/MIME (real LLM check is B5).
    tentative_is_cv = bool(has_attachment and looks_like_docx)
    final_status = "processed" if tentative_is_cv else "not_cv"

    update_payload: dict[str, Any] = {
        "status": final_status,
        "classified_as_cv": tentative_is_cv,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "error_log": None,
    }

    try:
        supabase.table("inbound_emails").update(update_payload).eq(
            "id", inbound_id
        ).execute()
    except Exception as exc:  # noqa: BLE001
        result.error = f"failed to mark final status: {exc}"
        result.notes.append(result.error)
        return result

    result.final_status = final_status
    result.classified_as_cv = tentative_is_cv
    return result


def process_all_pending(
    supabase=None,
    *,
    limit: int = 50,
) -> list[ProcessResult]:
    """Drain the pending queue. For local dev / one-shot CLI invocation."""
    if supabase is None:
        supabase = _default_supabase()
    pending_resp = (
        supabase.table("inbound_emails")
        .select("id")
        .eq("status", "pending")
        .order("received_at", desc=False)
        .limit(limit)
        .execute()
    )
    ids = [r["id"] for r in (pending_resp.data or [])]
    return [process_pending_email(i, supabase=supabase) for i in ids]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_supabase():
    import os
    from supabase import create_client

    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )
