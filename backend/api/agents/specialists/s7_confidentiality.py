"""S7 Confidentiality Classifier — Sprint B5.

Classifies extracted text as confidential (containing personal data) or not.
Defaults to confidential=True on any uncertainty: we'd rather over-flag a
personal CV than leak.

Output shape: {"confidential": bool, "reason": str}
"""

from __future__ import annotations

import json
import re

from api.tools.t3_litellm_router import LiteLLMRouter


_SYSTEM_PROMPT = """You are a confidentiality classifier for a recruitment-analytics platform.
Your job is to judge whether a piece of text contains personal or confidential
information.

Personal/confidential data includes:
- Names, email addresses, phone numbers, physical addresses
- Salary expectations, compensation details
- References (names and contact details of referees)
- Work histories tied to identifiable people
- Any information that could identify a specific individual

Non-confidential content is clearly generic:
- A public job posting
- A Wikipedia article or public research
- A benchmark study or industry report
- Sample data or anonymised statistics

Respond with a single JSON object — no markdown fences, no extra text:
{"confidential": true|false, "reason": "<one sentence>"}

Default to confidential=True on any uncertainty. We'd rather over-flag than leak."""

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _parse_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    text = raw.strip()
    fence_match = _JSON_FENCE_RE.match(text)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


class ConfidentialityAgent:
    """Classifies text as confidential (personal data) or not."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def classify(self, text: str, *, session_id: str | None = None) -> dict:
        """Returns {"confidential": bool, "reason": str}.

        Defaults to confidential=True on any uncertainty. Edge cases:
        - Empty text → confidential=True, reason="empty input"
        - LLM error → confidential=True, reason="LLM error: <exc>"
        """
        if not text or not text.strip():
            return {"confidential": True, "reason": "empty input"}

        try:
            content, _log = self.llm.route(
                "translation",
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                session_id=session_id,
                from_agent="s7_confidentiality",
                to_agent="t3_llm",
            )
        except Exception as exc:
            return {"confidential": True, "reason": f"LLM error: {exc}"}

        parsed = _parse_json(content)
        if parsed is None:
            return {"confidential": True, "reason": "LLM error: non-JSON response"}

        confidential = bool(parsed.get("confidential", True))
        reason = str(parsed.get("reason") or "")

        # Default to True on uncertainty
        if not reason:
            reason = "defaulted to confidential (no reason from LLM)"

        return {"confidential": confidential, "reason": reason}
