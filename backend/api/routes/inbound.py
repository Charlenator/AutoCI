"""Local-dev affordances for the inbound CV pipeline.

Two endpoints:

  POST /inbound/simulate
      Fakes a Resend webhook payload (no signature, no Edge Function). Inserts
      directly into inbound_emails, optionally uploads a base64 attachment to
      Storage, then runs the worker synchronously. Useful for testing the full
      pipeline without sending real email.

  POST /inbound/trigger/{inbound_id}
      Re-runs the worker on an existing pending row. Useful after a worker
      bugfix or to dispatch real Resend-queued rows during local dev (until
      Modal is deployed and the Edge Function calls the worker directly).

The Edge Function in supabase/functions/inbound-email/index.ts handles real
Resend webhooks; these routes are only the manual-trigger path.
"""

from __future__ import annotations

import base64
import binascii
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.workers.inbound_processor import process_pending_email

logger = logging.getLogger(__name__)
router = APIRouter()


class SimulateInboundRequest(BaseModel):
    sender: str = "test-sender@example.com"
    recipient: str = "jobs@charlecoetzee.com"
    subject: str = "Simulated inbound"
    body_text: str = ""
    body_html: str = ""
    # Optional attachment
    attachment_filename: str | None = None
    attachment_mime: str | None = None
    attachment_b64: str | None = None
    # If true, also runs the worker synchronously after queuing
    run_worker: bool = True


@router.post("/simulate")
def simulate_inbound(body: SimulateInboundRequest, request: Request):
    """Fake a Resend webhook + queue a row + (optionally) run the worker."""
    supabase = request.state.supabase

    attachment_path: str | None = None
    attachment_size: int | None = None

    if body.attachment_b64 and body.attachment_filename:
        try:
            raw = base64.b64decode(body.attachment_b64)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"invalid base64: {exc}") from exc
        safe_name = body.attachment_filename.replace("/", "_").replace("\\", "_")[:200]
        path = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}/{uuid.uuid4()}_{safe_name}"
        try:
            supabase.storage.from_("cv-attachments").upload(
                path,
                raw,
                {"content-type": body.attachment_mime or "application/octet-stream"},
            )
            attachment_path = path
            attachment_size = len(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[simulate-inbound] storage upload failed: {exc}")
            raise HTTPException(status_code=500, detail=f"storage upload failed: {exc}") from exc

    # Insert the queue row (matches Edge Function shape).
    insert_payload = {
        "svix_id": f"sim-{uuid.uuid4()}",
        "status": "pending",
        "sender": body.sender,
        "recipient": body.recipient,
        "subject": body.subject,
        "body_text": body.body_text,
        "body_html": body.body_html,
        "attachment_filename": body.attachment_filename,
        "attachment_mime": body.attachment_mime,
        "attachment_storage_path": attachment_path,
        "attachment_size": attachment_size,
        "raw_webhook_payload": {"simulated": True, "request": body.dict()},
    }
    insert_resp = supabase.table("inbound_emails").insert(insert_payload).execute()
    rows = insert_resp.data or []
    if not rows:
        raise HTTPException(status_code=500, detail="insert returned no rows")
    inbound_id = rows[0]["id"]

    response: dict = {"queued": True, "inbound_id": inbound_id, "attachment_path": attachment_path}

    if body.run_worker:
        result = process_pending_email(inbound_id, supabase=supabase)
        response["worker"] = result.to_dict()

    return response


@router.post("/trigger/{inbound_id}")
def trigger_processing(inbound_id: str, request: Request, force: bool = False):
    """Re-run the worker on an existing inbound_emails row."""
    supabase = request.state.supabase
    result = process_pending_email(inbound_id, supabase=supabase, force=force)
    return result.to_dict()


@router.post("/drain")
def drain_pending(request: Request, limit: int = 25):
    """Drain up to `limit` pending rows. Local-dev / one-shot tool."""
    from api.workers.inbound_processor import process_all_pending

    supabase = request.state.supabase
    results = process_all_pending(supabase=supabase, limit=limit)
    return {"processed": len(results), "results": [r.to_dict() for r in results]}
