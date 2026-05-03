# Task 03 — B7: cal.com slot lookup wrapper

## Goal

Thin Python client around cal.com's free-tier API. One function: given an
event-type ID, return a 14-day grid of available slots. Used by the Schedule
Meeting flow (Task 04) to render the slot picker and to deep-link booking
URLs in the candidate invite email.

## Files this task touches

- NEW: `backend/api/integrations/cal_com_client.py`
- ADD TESTS: `backend/test_all.py`

## Acceptance criteria

- `get_slots(event_type_id, days=14)` returns a dict keyed by ISO date with
  a list of `{start, end, booking_url}` per date.
- On 4xx/5xx from cal.com, raises `CalComError` with the API message.
- Has a unit test that mocks `httpx` and asserts request shape + response
  parsing.

---

## Sub-tasks

### 03.1 — `cal_com_client.py`

**File**: `backend/api/integrations/cal_com_client.py` (NEW)

**Done when**: Module exposes `class CalComClient` with `get_slots`, plus a
module-level `CalComError` exception. API key + default event-type ID read
from `CAL_COM_API_KEY` and `CAL_COM_DEFAULT_EVENT_TYPE_ID` env vars; cal.com
username read from `CAL_COM_USERNAME`.

**Prompt to paste:**

```
Create backend/api/integrations/cal_com_client.py.

Read first:
  - backend/api/integrations/resend_client.py — match the same shape (sync
    httpx, custom Error class, env-var defaults, no async).

Implement:

  class CalComError(Exception):
      """Raised when cal.com returns a non-2xx response or an unparseable body."""

  class CalComClient:
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
          if not self.api_key:
              raise CalComError("CAL_COM_API_KEY not configured")
          if not self.username:
              raise CalComError("CAL_COM_USERNAME not configured")

      def get_slots(
          self,
          *,
          event_type_id: int | None = None,
          days: int = 14,
          tz: str = "Africa/Johannesburg",
      ) -> dict[str, list[dict]]:
          """Fetch available slots for the next `days` days.

          Returns:
            {
              "2026-05-04": [
                {"start": "2026-05-04T09:00:00+02:00",
                 "end":   "2026-05-04T09:30:00+02:00",
                 "booking_url": "https://cal.com/charle/30min?date=...&slot=..."},
                ...
              ],
              "2026-05-05": [...],
              ...
            }

          Raises CalComError on non-2xx or unparseable body.
          """

Implementation notes:
  - Endpoint: GET https://api.cal.com/v1/slots
  - Query params:
      apiKey={api_key}
      eventTypeId={event_type_id or self.default_event_type_id}
      startTime={now ISO}
      endTime={now+days ISO}
      timeZone={tz}
  - Response shape: {"slots": {"YYYY-MM-DD": [{"time": "ISO"}, ...], ...}}
  - For each slot in each date:
      slot_start = parse the ISO time
      slot_end = slot_start + event.length minutes (cal.com returns event
        length separately; if not present, default to 30 min)
      booking_url = f"https://cal.com/{self.username}/{event_slug}?date={iso_date}&slot={slot_start.isoformat()}"
        (event_slug is part of the cal.com URL path; pass it via env or
        derive from event_type via a separate /v1/event-types call cached
        for 24h. For first pass, hardcode "30min" if env CAL_COM_EVENT_SLUG
        is not set.)
  - Timeout: 10s.
  - If the response has no "slots" key, return {}.

Add tests in backend/test_all.py:
  - monkeypatch httpx to return a fixed slots payload (one date with two
    slots) and assert the parsed dict shape.
  - asserts CalComError when the API returns 401.

Do not modify any other file. Do not add any new dependency.
```

## Definition of done

- 03.1 in KANBAN "Done"
- `python test_all.py 1` passes

## Commit + push

```
git add backend/api/integrations/cal_com_client.py backend/test_all.py CONTEXT/handoff_to_deepseek/KANBAN.md
git commit -m "Sprint B7: cal.com slot lookup wrapper (cal_com_client.py)"
git push origin main
```
