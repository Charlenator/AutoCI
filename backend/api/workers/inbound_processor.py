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

import hashlib
import json
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

    # ---- B5 full pipeline ----
    try:
        _run_b5_pipeline(row, supabase, result)
    except Exception as exc:  # noqa: BLE001
        result.error = f"pipeline error: {exc}"
        result.notes.append(result.error)
        _update_inbound_final(supabase, inbound_id, "error", None,
                              error_log=str(exc), result=result)
        return result

    _update_inbound_final(supabase, inbound_id, result.final_status,
                          result.classified_as_cv, result=result)
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


# ── B5 pipeline steps ──────────────────────────────────────────────────────


def _run_b5_pipeline(row: dict, supabase: Any, result: ProcessResult) -> None:
    """Run the full B5 pipeline steps 1–6, mutating `result` in place.

    The caller handles final update + outer exception catch. We raise on any
    unrecoverable error so the caller sets status='error'.
    """
    inbound_id = row["id"]
    sender = (row.get("sender") or "").strip()
    subject = (row.get("subject") or "").strip()
    body = (row.get("body_text") or "").strip()
    storage_path = row.get("attachment_storage_path") or ""

    # ── Step 1: Download attachment ────────────────────────────────────
    docx_bytes: bytes | None = None
    has_attachment = bool(storage_path)

    if has_attachment:
        try:
            resp = supabase.storage.from_("cv-attachments").download(storage_path)
            docx_bytes = resp
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"storage download failed: {exc}") from exc

    # ── Step 2: Dedup hash ──────────────────────────────────────────────
    hash_source = f"{sender}-{subject}".lower().encode()
    if docx_bytes:
        dedup_hash = hashlib.sha256(hash_source + docx_bytes).hexdigest()
    else:
        dedup_hash = hashlib.sha256(hash_source).hexdigest()

    # Check for existing candidate with same hash
    existing = (
        supabase.table("candidates")
        .select("candidate_id")
        .eq("dedup_hash", dedup_hash)
        .limit(1)
        .execute()
    )
    if existing.data:
        result.candidate_id = existing.data[0]["candidate_id"]
        result.final_status = "processed"
        result.classified_as_cv = True
        result.notes.append("duplicate of existing candidate (dedup hash match)")
        return

    # ── Step 3: Classify ────────────────────────────────────────────────
    from api.agents.specialists.s5_cv_classifier import CVClassifierAgent
    from api.tools.t3_litellm_router import LiteLLMRouter

    llm = LiteLLMRouter(supabase_client=supabase)
    s5 = CVClassifierAgent(llm)

    raw_text_for_classify: str = ""
    is_docx_attachment = False

    if docx_bytes:
        # Extract raw text inline for the classifier (S6 would do it again, but
        # S5 only needs text; we re-extract in S6 for the structured fields).
        try:
            from docx import Document as _Doc
            import io
            _d = _Doc(io.BytesIO(docx_bytes))
            raw_text_for_classify = "\n".join(p.text for p in _d.paragraphs if p.text.strip())
            is_docx_attachment = True
        except Exception as exc:  # noqa: BLE001
            # python-docx parse failure — not a proper docx CV
            raw_text_for_classify = ""
            result.notes.append(f"classifier: docx parse error ({exc}) — treating as not_cv")
    else:
        raw_text_for_classify = body

    s5_result = s5.is_cv(raw_text_for_classify or "")
    result.notes.append(
        f"classifier: is_cv={s5_result['is_cv']} conf={s5_result['confidence']} reason={s5_result.get('reason', '')}"
    )

    if not s5_result["is_cv"]:
        # ── Step 4b: Not-CV path → vectorize email ─────────────────────
        from api.workers.email_vectorizer import vectorize_email
        from api.tools.t4_embeddings import EmbeddingService

        chunks = vectorize_email(subject, body, inbound_id)
        result.notes.append(f"vectorized email into {len(chunks)} chunks (not_cv)")

        if chunks:
            _embed_and_upsert_chunks(chunks, EmbeddingService(), supabase)

        result.classified_as_cv = False
        result.chunk_count = len(chunks)
        result.final_status = "not_cv"
        return

    # ── Step 4a: CV path — extract, confidentiality, upsert ────────────
    from api.agents.specialists.s6_cv_extractor import CVExtractorAgent
    from api.agents.specialists.s7_confidentiality import ConfidentialityAgent
    from api.workers.cv_chunking import chunk_cv
    from api.tools.t4_embeddings import EmbeddingService

    s6 = CVExtractorAgent(llm)
    record = s6.extract(docx_bytes) if docx_bytes else {
        "name": None, "email": None, "phone": None, "summary": None,
        "skills": [], "experience": [], "education": [],
        "missing_fields": ["name", "email", "phone", "summary", "skills",
                           "experience", "education"],
        "raw_text": raw_text_for_classify,
    }
    missing = record.get("missing_fields") or []
    result.notes.append(
        f"extractor: {len(record.get('skills') or [])} skills, "
        f"{len(record.get('experience') or [])} exp items, "
        f"{len(record.get('education') or [])} edu items"
        + (f" (missing: {missing})" if missing else "")
    )

    s7 = ConfidentialityAgent(llm)
    confidentiality = s7.classify(record.get("raw_text") or "")
    result.notes.append(
        f"confidentiality: {confidentiality['confidential']} ({confidentiality.get('reason', '')})"
    )

    # Upsert candidates row
    candidate_payload = {
        "name": record.get("name"),
        "email": record.get("email"),
        "phone": record.get("phone"),
        "experience_summary": record.get("summary"),
        "skills_json": json.dumps(record.get("skills") or []),
        "missing_fields_json": json.dumps(missing) if missing else None,
        "cv_storage_path": storage_path or None,
        "dedup_hash": dedup_hash,
        "confidential": confidentiality["confidential"],
        "source_email_id": inbound_id,
        "source_channel": "email",
        "applied_date": datetime.now(timezone.utc).date().isoformat(),
    }
    cand_resp = (
        supabase.table("candidates")
        .insert(candidate_payload)
        .execute()
    )
    cand_data = cand_resp.data or []
    if not cand_data:
        raise RuntimeError("candidates insert returned no rows")
    candidate_id = cand_data[0]["candidate_id"]
    result.candidate_id = candidate_id

    # Chunk + embed + upsert corpus_chunks
    chunks = chunk_cv(record, candidate_id)
    result.notes.append(f"chunked into {len(chunks)} CV sections")

    if chunks:
        _embed_and_upsert_chunks(chunks, EmbeddingService(), supabase)

    result.classified_as_cv = True
    result.chunk_count = len(chunks)
    result.final_status = "processed"


def _embed_and_upsert_chunks(
    chunks: list[dict],
    embedder: Any,
    supabase: Any,
) -> None:
    """Embed chunk_text and upsert to corpus_chunks with ignore_duplicates."""
    texts = [c["chunk_text"] for c in chunks]
    embeddings = embedder.embed_batch(texts)

    for chunk, emb in zip(chunks, embeddings):
        meta = chunk.get("metadata") or {}
        supabase.table("corpus_chunks").upsert({
            "corpus_name": chunk["corpus_name"],
            "chunk_text": chunk["chunk_text"],
            "metadata": json.dumps(meta),
            "embedding": emb,
            "confidential": meta.get("confidential", True),
        }, on_conflict="content_hash", ignore_duplicates=True).execute()


def _update_inbound_final(
    supabase: Any,
    inbound_id: str,
    final_status: str,
    classified_as_cv: bool | None,
    *,
    error_log: str | None = None,
    result: ProcessResult | None = None,
) -> None:
    """Update the inbound_emails row with final status + timestamps."""
    update_payload: dict[str, Any] = {
        "status": final_status,
        "classified_as_cv": classified_as_cv,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "error_log": error_log,
    }
    if result and result.candidate_id:
        update_payload["candidate_id"] = result.candidate_id

    try:
        supabase.table("inbound_emails").update(update_payload).eq(
            "id", inbound_id
        ).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[inbound_processor] failed final status update: {exc}")
        raise
