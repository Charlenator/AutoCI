"""B7: Thin synchronous cal.com v2 slot-lookup wrapper.

Cal.com deprecated v1 in mid-2025.  This module targets the v2 API::

    GET https://api.cal.com/v2/slots
        ?eventTypeId=N
        &start=YYYY-MM-DD
        &end=YYYY-MM-DD
        &timeZone=Africa/Johannesburg

Auth is via the ``cal-api-key`` HTTP header.

The v2 response shape (confirmed live)::

    {
      "status": "success",
      "data": {
        "2026-05-04": [{"start": "2026-05-04T08:00:00.000Z"}, ...],
        "2026-05-05": [{"start": "2026-05-05T08:00:00.000Z"}, ...],
      }
    }

Note: ``data`` IS the slots dict — there is no ``data.slots`` wrapper.
Each entry has a ``start`` key (not ``time``).
"""

import os
from datetime import datetime, timedelta, timezone

import httpx

CAL_COM_V2_URL = "https://api.cal.com/v2/slots"
CAL_COM_API_VERSION = "2024-09-04"
DEFAULT_TIMEOUT = 10
DEFAULT_EVENT_LENGTH_MIN = 30
DEFAULT_EVENT_SLUG = "30min"
DEFAULT_TZ = "Africa/Johannesburg"


def _parse_iso(iso_str: str) -> datetime | None:
    """Parse an ISO-8601 string, tolerating trailing ``Z``."""
    try:
        cleaned = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


def _format_date(dt: datetime) -> str:
    """Return ``YYYY-MM-DD`` — cal.com v2 expects date-only for start/end."""
    return dt.strftime("%Y-%m-%d")


class CalComError(Exception):
    """Raised when cal.com returns a non-2xx response or an unparseable body."""


class CalComClient:
    """Synchronous HTTP client for the cal.com v2 slots API.

    Usage::
        client = CalComClient()
        slots = client.get_slots(event_type_id=5572588, days=3)
    """

    def __init__(
        self,
        api_key: str | None = None,
        username: str | None = None,
        default_event_type_id: int | None = None,
    ):
        self.api_key = api_key or os.getenv("CAL_COM_API_KEY", "")
        self.username = username or os.getenv("CAL_COM_USERNAME", "")
        self.default_event_type_id = default_event_type_id or int(
            os.getenv("CAL_COM_DEFAULT_EVENT_TYPE_ID", "0") or 0
        )
        self.event_slug = os.getenv("CAL_COM_EVENT_SLUG", DEFAULT_EVENT_SLUG)
        if not self.api_key:
            raise CalComError("CAL_COM_API_KEY not configured")
        if not self.username:
            raise CalComError("CAL_COM_USERNAME not configured")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_slots(
        self,
        *,
        event_type_id: int | None = None,
        days: int = 14,
        tz: str = DEFAULT_TZ,
    ) -> dict[str, list[dict]]:
        """Fetch available slots for the next *days* days via v2 API.

        Returns a dict keyed by ISO date (``YYYY-MM-DD``), each value a list
        of slot dicts::

            {
              "2026-05-04": [
                {"start": "2026-05-04T08:00:00.000Z",
                 "end":   "2026-05-04T08:30:00.000Z",
                 "booking_url": "https://cal.com/charle/30min?date=...&slot=..."},
              ],
              ...
            }

        Raises ``CalComError`` on non-2xx or an unparseable response body.
        """
        eid = event_type_id or self.default_event_type_id
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)

        params: dict[str, str] = {
            "eventTypeId": str(eid),
            "start": _format_date(now),
            "end": _format_date(end),
            "timeZone": tz,
        }
        headers: dict[str, str] = {
            "cal-api-key": self.api_key,
            "cal-api-version": CAL_COM_API_VERSION,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.get(
                    CAL_COM_V2_URL,
                    params=params,
                    headers=headers,
                )
                if not resp.is_success:
                    try:
                        err_body = resp.json()
                        msg = (
                            err_body.get("error")
                            or err_body.get("message")
                            or resp.text
                        )
                    except Exception:
                        msg = resp.text
                    raise CalComError(f"Cal.com {resp.status_code}: {msg}")

                raw = resp.json()

        except httpx.TimeoutException:
            raise CalComError("Cal.com request timed out")
        except httpx.RequestError as e:
            raise CalComError(f"Cal.com request failed: {e}")

        # v2 response: data IS the slots dict (not data.slots)
        data: dict = raw.get("data", {}) if isinstance(raw, dict) else {}
        if not data or not isinstance(data, dict):
            return {}

        event_length = DEFAULT_EVENT_LENGTH_MIN

        result: dict[str, list[dict]] = {}
        for date_str, slot_list in data.items():
            if not isinstance(slot_list, list):
                continue
            parsed_slots: list[dict] = []
            for entry in slot_list:
                if not isinstance(entry, dict):
                    continue
                raw_start = entry.get("start")  # v2 field is `start`, not `time`
                if not raw_start:
                    continue
                slot_start = _parse_iso(raw_start)
                if slot_start is None:
                    continue
                slot_end = slot_start + timedelta(minutes=event_length)

                booking_url = (
                    f"https://cal.com/{self.username}/{self.event_slug}"
                    f"?date={date_str}&slot={slot_start.isoformat()}"
                )

                parsed_slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                    "booking_url": booking_url,
                })
            if parsed_slots:
                result[date_str] = parsed_slots

        return result
