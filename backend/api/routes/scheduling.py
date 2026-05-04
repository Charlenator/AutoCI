"""Scheduling route — wraps CalComClient slot lookup.

GET /scheduling/slots?days=14
  Returns a flattened, sorted list of available slots for the given window.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from api.integrations.cal_com_client import CalComClient

router = APIRouter()


@router.get("/slots")
async def get_slots(
    days: int = Query(14, ge=1, le=31, description="Number of days to fetch slots for"),
):
    """Return a flattened, sorted list of available cal.com slots.

    Each slot has ``start``, ``end``, and ``booking_url``.
    Results are sorted by start time ascending.
    """
    try:
        client = CalComClient()
        slots_by_date = client.get_slots(days=days)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cal.com error: {exc}") from exc

    # Flatten the date-grouped dict into a single sorted list.
    flat: list[dict] = []
    for date_str, slot_list in slots_by_date.items():
        flat.extend(slot_list)

    flat.sort(key=lambda s: s.get("start", ""))

    return {"slots": flat}
