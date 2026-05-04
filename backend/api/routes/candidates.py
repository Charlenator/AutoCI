"""B8: Candidate Search routes — semantic search, CV download, schedule meeting.

Three endpoints on a single APIRouter:
  POST /candidates/search      — semantic search over CV chunks
  GET  /candidates/{id}/cv     — signed Supabase Storage URL (5-min TTL)
  POST /candidates/{id}/schedule — email candidate with cal.com booking links
"""

from __future__ import annotations

import html as html_mod
import json as json_mod
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.agents.specialists.s2_rag import RAGAgent
from api.integrations.resend_client import ResendClient

router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    q: str
    limit: int = 20


class CandidateCard(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    experience_summary: str | None = None
    match_score: float = 0.0
    is_duplicate: bool = False
    missing_fields: list[str] = []
    cv_storage_path: str | None = None
    confidential: bool = False


class SearchResponse(BaseModel):
    results: list[CandidateCard]


class CvSignedUrl(BaseModel):
    url: str
    expires_at: str  # ISO-8601


class SlotEntry(BaseModel):
    start: str
    end: str
    booking_url: str


class ScheduleRequest(BaseModel):
    slots: list[SlotEntry]
    message: str | None = None


class ScheduleResponse(BaseModel):
    resend_id: str
    slots_sent: int


# ---------------------------------------------------------------------------
# POST /candidates/search
# ---------------------------------------------------------------------------


@router.post("/search", response_model=SearchResponse)
async def search_candidates(body: SearchRequest, request: Request):
    """Semantic search over CV corpus via RAG + candidate table lookup."""
    supabase = request.state.supabase
    rag = RAGAgent(supabase)
    result = rag.retrieve(body.q, top_k=body.limit, corpus_filter="cvs")
    chunks = result.chunks or []

    if not chunks:
        return SearchResponse(results=[])

    # Group chunks by candidate_id; keep the highest-similarity chunk per ID.
    best: dict[str, tuple[float, dict]] = {}  # candidate_id -> (similarity, chunk)
    for c in chunks:
        raw_meta = c.get("metadata") or {}
        if isinstance(raw_meta, str):
            try:
                meta = json_mod.loads(raw_meta)
            except (json_mod.JSONDecodeError, TypeError):
                meta = {}
        else:
            meta = raw_meta
        cid = meta.get("candidate_id") if isinstance(meta, dict) else None
        if not cid:
            continue
        sim = float(c.get("similarity") or 0)
        if cid not in best or sim > best[cid][0]:
            best[cid] = (sim, c)

    if not best:
        return SearchResponse(results=[])

    # Sort by similarity descending to get the top N candidate_ids.
    sorted_ids = [cid for cid, _ in sorted(best.items(), key=lambda x: float(x[1][0]), reverse=True)]

    # Fetch full candidate rows from the database.
    try:
        db_resp = (
            supabase.table("candidates")
            .select("*")
            .in_("candidate_id", sorted_ids)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Supabase query failed: {exc}") from exc

    rows = db_resp.data or []
    rows_by_id = {r["candidate_id"]: r for r in rows}

    cards: list[CandidateCard] = []
    for cid in sorted_ids:
        row = rows_by_id.get(cid)
        if row is None:
            continue  # chunk references a deleted candidate

        sim = best[cid][0]
        skills_raw = row.get("skills_json") or []
        if isinstance(skills_raw, list):
            top_skills = skills_raw[:5]
        elif isinstance(skills_raw, str):
            try:
                parsed = json_mod.loads(skills_raw)
                top_skills = (parsed if isinstance(parsed, list) else [])[:5]
            except Exception:
                top_skills = []
        else:
            top_skills = []

        summary = row.get("experience_summary") or ""
        if len(summary) > 160:
            summary = summary[:157] + "..."

        missing = row.get("missing_fields_json") or []
        if isinstance(missing, str):
            try:
                missing = json_mod.loads(missing)
            except Exception:
                missing = []
        if not isinstance(missing, list):
            missing = []

        cards.append(CandidateCard(
            id=cid,
            name=row.get("name"),
            email=row.get("email"),
            phone=row.get("phone"),
            skills=top_skills,
            experience_summary=summary,
            match_score=round(sim, 4),
            is_duplicate=bool(row.get("is_duplicate", False)),
            missing_fields=missing,
            cv_storage_path=row.get("cv_storage_path"),
            confidential=bool(row.get("confidential", False)),
        ))

    return SearchResponse(results=cards)


# ---------------------------------------------------------------------------
# GET /candidates/{candidate_id}/cv
# ---------------------------------------------------------------------------


@router.get("/{candidate_id}/cv", response_model=CvSignedUrl)
async def get_cv_signed_url(candidate_id: str, request: Request):
    """Return a 5-minute Supabase Storage signed URL for the candidate's CV."""
    supabase = request.state.supabase

    try:
        resp = (
            supabase.table("candidates")
            .select("cv_storage_path")
            .eq("candidate_id", candidate_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Supabase query failed: {exc}") from exc

    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Candidate not found")

    path = rows[0].get("cv_storage_path")
    if not path:
        raise HTTPException(status_code=404, detail="Candidate has no CV stored")

    try:
        signed = supabase.storage.from_("cv-attachments").create_signed_url(
            path, expires_in=300
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage signed URL failed: {exc}") from exc

    url = signed.get("signedURL") or ""
    if not url:
        raise HTTPException(status_code=502, detail="Storage returned empty signed URL")

    expires_at = datetime.now(timezone.utc).isoformat()
    return CvSignedUrl(url=url, expires_at=expires_at)


# ---------------------------------------------------------------------------
# POST /candidates/{candidate_id}/schedule
# ---------------------------------------------------------------------------


@router.post("/{candidate_id}/schedule", response_model=ScheduleResponse)
async def schedule_candidate(candidate_id: str, body: ScheduleRequest, request: Request):
    """Send an HTML invite email with booking links for the selected slots."""
    supabase = request.state.supabase

    # Validate slot count
    if not body.slots or len(body.slots) > 3:
        raise HTTPException(
            status_code=400,
            detail="Must provide between 1 and 3 slots",
        )

    # Look up candidate
    try:
        resp = (
            supabase.table("candidates")
            .select("name, email")
            .eq("candidate_id", candidate_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Supabase query failed: {exc}") from exc

    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Candidate not found")

    name = rows[0].get("name") or "Candidate"
    email = rows[0].get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Candidate has no email address")

    # Build the HTML invite
    greeting = html_mod.escape(f"Hi {name},")
    footer = html_mod.escape("AutoCI — Recruitment Analytics Platform")

    recruiter_msg = ""
    if body.message:
        escaped_msg = html_mod.escape(body.message)
        recruiter_msg = f'<p style="margin:12px 0;font-style:italic;">{escaped_msg}</p>'

    slot_rows_html = ""
    for i, slot in enumerate(body.slots):
        # Parse the start timestamp for a human-friendly label
        try:
            dt = datetime.fromisoformat(slot.start.replace("Z", "+00:00"))
            formatted = dt.strftime("%A %B %-d, %I:%M %p")
        except (ValueError, TypeError):
            formatted = slot.start

        slot_rows_html += (
            f'<tr>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">'
            f'<a href="{html_mod.escape(slot.booking_url)}" '
            f'style="display:inline-block;padding:10px 20px;background:#2563eb;'
            f'color:#fff;text-decoration:none;border-radius:6px;font-weight:600;">'
            f'{html_mod.escape(formatted)}</a>'
            f'</td>'
            f'</tr>'
        )

    html_body = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:520px;margin:24px auto;padding:24px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;">
  <p style="font-size:16px;color:#111827;">{greeting}</p>
  <p style="font-size:14px;color:#374151;">A recruiter has invited you to schedule an interview. Please pick a time that works for you:</p>
  {recruiter_msg}
  <table style="width:100%;border-collapse:collapse;margin:16px 0;">
    {slot_rows_html}
  </table>
  <p style="font-size:12px;color:#6b7280;margin-top:24px;">{footer}</p>
</div>
</body>
</html>"""

    # Send via Resend
    try:
        resend = ResendClient()
        result = resend.send_email(
            to=email,
            subject="Interview slots available",
            html=html_body,
            from_email="AutoCI <recruitment@wabi-ai.tech>",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Resend email failed: {exc}") from exc

    resend_id = result.get("id", "")
    return ScheduleResponse(resend_id=resend_id, slots_sent=len(body.slots))
