# Task 02 — B6: Resend send wrapper

## Goal

Thin Python client around the Resend send API. Used by the Schedule Meeting
flow (Task 04) to email candidates a 14-day cal.com slot grid. Nothing
fancy — one function, validated inputs, real errors surfaced.

## Files this task touches

- NEW: `backend/api/integrations/resend_client.py`
- ADD TESTS: `backend/test_all.py`

## Acceptance criteria

- `send_email(to, subject, html, ...)` returns `{"id": str}` on success.
- On 4xx/5xx from Resend, raises `ResendError` with the API's error message
  preserved.
- Has a unit test that mocks `httpx` and asserts the request shape.

---

## Sub-tasks

### 02.1 — `resend_client.py`

**File**: `backend/api/integrations/resend_client.py` (NEW)

**Done when**: Module exposes `class ResendClient` with `send_email`,
`send_email_text`, and a module-level `ResendError` exception. API key
read from `RESEND_API_KEY` env var.

**Prompt to paste:**

```
Create backend/api/integrations/resend_client.py.

Read first:
  - backend/api/agents/specialists/s4_research.py — note the httpx.Client
    usage pattern (sync, with timeout, raise_for_status, return shaped
    dict on success / dict with "error" on failure).

Implement (synchronous, httpx-based, matches the rest of the codebase):

  class ResendError(Exception):
      """Raised when the Resend API returns a non-2xx response."""

  class ResendClient:
      def __init__(self, api_key: str | None = None, default_from: str | None = None):
          self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
          self.default_from = default_from or os.getenv("RESEND_FROM_EMAIL", "")
          if not self.api_key:
              raise ResendError("RESEND_API_KEY not configured")

      def send_email(
          self,
          *,
          to: str | list[str],
          subject: str,
          html: str,
          from_email: str | None = None,
          reply_to: str | None = None,
          text: str | None = None,        # optional plain-text fallback
      ) -> dict:
          """POST https://api.resend.com/emails. Returns {'id': '<resend-id>'}.

          Raises ResendError on non-2xx, with the API error message preserved.
          """

      def send_email_text(self, *, to, subject, body, from_email=None, reply_to=None) -> dict:
          """Convenience: wraps send_email with a basic text-to-html conversion
          (escape HTML, replace \\n with <br>, wrap in a single <div>)."""

Implementation notes:
  - Endpoint: POST https://api.resend.com/emails
  - Headers: Authorization: Bearer {api_key}, Content-Type: application/json
  - Body: {"from": from_email or self.default_from, "to": to (list or str),
           "subject": subject, "html": html, "text": text|None,
           "reply_to": reply_to|None}
  - Drop None-valued keys before sending.
  - Timeout: 15s.
  - On non-2xx: parse the JSON body for an "error" or "message" field; raise
    ResendError(f"Resend {status}: {message}").

Add a test in backend/test_all.py inside level1_unit() that:
  - monkeypatches httpx.Client to return a 200 response with body {"id": "abc"}
  - constructs ResendClient(api_key="test") and calls send_email(to="x@y.com",
    subject="hi", html="<p>hi</p>", from_email="me@example.com")
  - asserts the result is {"id": "abc"}
  - asserts the request body had the expected keys
You can use a tiny inline FakeClient class instead of monkeypatching if that's
easier; the goal is just to exercise the request-shaping logic.

Do not modify any other file. Do not add any new dependency.
```

## Definition of done

- 02.1 in KANBAN "Done"
- `python test_all.py 1` passes

## Commit + push

```
git add backend/api/integrations/resend_client.py backend/test_all.py CONTEXT/handoff_to_deepseek/KANBAN.md
git commit -m "Sprint B6: Resend send wrapper (resend_client.py)"
git push origin main
```
