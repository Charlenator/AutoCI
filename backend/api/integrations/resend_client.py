"""B6: Thin synchronous Resend send wrapper — matches httpx pattern in s4_research.py."""

import os
import json
import httpx
import html as html_mod

RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_TIMEOUT = 15


class ResendError(Exception):
    """Raised when the Resend API returns a non-2xx response."""


class ResendClient:
    """Synchronous HTTP client for the Resend send API.

    Usage:
        client = ResendClient()
        resp = client.send_email(
            to="candidate@example.com",
            subject="Interview invitation",
            html="<p>Please pick a slot</p>",
        )
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_from: str | None = None,
    ):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self.default_from = default_from or os.getenv("RESEND_FROM_EMAIL", "")
        if not self.api_key:
            raise ResendError("RESEND_API_KEY not configured")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_email(
        self,
        *,
        to: str | list[str],
        subject: str,
        html: str,
        from_email: str | None = None,
        reply_to: str | None = None,
        text: str | None = None,
    ) -> dict:
        """POST to Resend's /emails endpoint.

        Returns ``{"id": "<resend-message-id>"}`` on success.
        Raises ``ResendError`` on non-2xx, preserving the API's error message.
        """
        body: dict[str, object] = {
            "from": from_email or self.default_from,
            "to": to if isinstance(to, list) else [to],
            "subject": subject,
            "html": html,
        }
        if text is not None:
            body["text"] = text
        if reply_to is not None:
            body["reply_to"] = reply_to

        # Drop keys whose values are None (avoids Resend rejecting null fields).
        body = {k: v for k, v in body.items() if v is not None}

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.post(
                    RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.is_success:
                    return dict(resp.json())  # {"id": "..."}

                # Try to extract a meaningful error message.
                try:
                    err_body = resp.json()
                    msg = err_body.get("error") or err_body.get("message") or resp.text
                except Exception:
                    msg = resp.text
                raise ResendError(f"Resend {resp.status_code}: {msg}")

        except httpx.TimeoutException:
            raise ResendError("Resend request timed out")
        except httpx.RequestError as e:
            raise ResendError(f"Resend request failed: {e}")

    def send_email_text(
        self,
        *,
        to: str | list[str],
        subject: str,
        body: str,
        from_email: str | None = None,
        reply_to: str | None = None,
    ) -> dict:
        """Convenience wrapper — converts plain text to a minimal HTML body."""
        escaped = html_mod.escape(body, quote=True)
        wrapped = f"<div>{escaped.replace(chr(10), '<br>')}</div>"
        return self.send_email(
            to=to,
            subject=subject,
            html=wrapped,
            from_email=from_email,
            reply_to=reply_to,
            text=body,
        )
