"""S5 CV Classifier — Sprint B5.

Classifies extracted text as a candidate's CV (or not). Designed to be called
by the inbound worker (inbound_processor.py) before extraction/vectorization.

Output shape: {"is_cv": bool, "confidence": float, "reason": str}
"""

from __future__ import annotations

import json
import re

from api.tools.t3_litellm_router import LiteLLMRouter


_SYSTEM_PROMPT = """You are a CV classifier for a recruitment-analytics platform.
Your job is to judge whether a given piece of extracted text is a candidate's CV
(resume) — NOT a cover letter, NOT a marketing PDF, NOT a job posting, NOT a
generic article.

A CV typically contains:
- Personal details (name, email, phone, address)
- Work experience (roles, companies, dates, responsibilities)
- Education history (schools, degrees, years)
- Skills (technical, professional, language)
- A career summary or objective statement

A cover letter is typically a short, personal letter addressed to a hiring
manager. A job posting lists requirements and responsibilities for an open
role. A marketing PDF promotes a product or service.

Respond with a single JSON object — no markdown fences, no extra text:
{"is_cv": true|false, "confidence": 0..1, "reason": "<one sentence>"}

Set confidence high (>=0.9) when the text clearly contains CV-like structure
and content. Set confidence low (<0.5) when the text is ambiguous or too short."""

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


class CVClassifierAgent:
    """Classifies text as a candidate's CV (or not)."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def is_cv(self, text: str, *, session_id: str | None = None) -> dict:
        """Returns {"is_cv": bool, "confidence": float (0..1), "reason": str}.

        Edge cases:
        - Empty/whitespace text -> return is_cv=False, confidence=0.0
          without calling the LLM.
        - LLM error or non-JSON response -> return is_cv=False, confidence=0.0
          with reason="LLM error: <exc>".
        """
        if not text or not text.strip():
            return {"is_cv": False, "confidence": 0.0, "reason": "empty input"}

        try:
            content, _log = self.llm.route(
                "translation",
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                session_id=session_id,
                from_agent="s5_cv_classifier",
                to_agent="t3_llm",
            )
        except Exception as exc:
            return {"is_cv": False, "confidence": 0.0, "reason": f"LLM error: {exc}"}

        parsed = _parse_json(content)
        if parsed is None:
            return {
                "is_cv": False,
                "confidence": 0.0,
                "reason": "LLM error: non-JSON response",
            }

        is_cv = bool(parsed.get("is_cv", False))
        confidence = _clamp_confidence(parsed.get("confidence"))
        reason = str(parsed.get("reason") or "")

        return {"is_cv": is_cv, "confidence": confidence, "reason": reason}


def _clamp_confidence(value) -> float:
    try:
        v = float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return v
