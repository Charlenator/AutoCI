"""S6 CV Extractor — Sprint B5.

Extracts structured fields from a .docx CV using python-docx + an LLM call.
Returns a normalized record with name, email, phone, summary, skills,
experience, and education.

Designed to be called by the inbound worker after S5 classifies the text as CV.
"""

from __future__ import annotations

import json
import re

from api.tools.t3_litellm_router import LiteLLMRouter


_SYSTEM_PROMPT = """You are a CV field extractor for a recruitment-analytics platform.
Given the raw text of a candidate's CV, extract the following fields as a JSON
object — no markdown fences, no extra text:

{
  "name": string | null,
  "email": string | null,
  "phone": string | null,
  "summary": string | null,
  "skills": [string],
  "experience": [
    {
      "role": string,
      "company": string,
      "start_date": string | null,
      "end_date": string | null,
      "description": string
    }
  ],
  "education": [
    {
      "school": string,
      "degree": string,
      "year": string | null
    }
  ]
}

Rules:
- If a field is not present in the text, set it to null (or [] for lists).
- Extract skills as individual strings in lowercase (e.g. "python", "project management").
- For experience, list each distinct role in chronological order.
- For education, list each entry in chronological order.
- Use null for dates that are not clearly stated.
- Keep descriptions concise but faithful to the original text."""

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)

_NORMAL_FIELDS = ["name", "email", "phone", "summary"]
_LIST_FIELDS = ["skills", "experience", "education"]

_MAX_TEXT_CHARS = 8000


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


def _normalize_record(record: dict, raw_text: str) -> dict:
    """Normalize and validate the extracted record.

    - Lowercase email, strip whitespace from all strings.
    - Lowercase + dedupe skills.
    - Compute missing_fields for any null/empty top-level key.
    """
    out = {
        "name": _clean_str(record.get("name")),
        "email": _clean_str(record.get("email")),
        "phone": _clean_str(record.get("phone")),
        "summary": _clean_str(record.get("summary")),
        "skills": _normalize_skills(record.get("skills")),
        "experience": record.get("experience") or [],
        "education": record.get("education") or [],
        "raw_text": raw_text,
    }

    # Lowercase email if present
    if out["email"]:
        out["email"] = out["email"].strip().lower()

    # Normalize experience items
    out["experience"] = [
        {
            "role": _clean_str(e.get("role")),
            "company": _clean_str(e.get("company")),
            "start_date": _clean_str(e.get("start_date")),
            "end_date": _clean_str(e.get("end_date")),
            "description": _clean_str(e.get("description")),
        }
        for e in out["experience"]
        if isinstance(e, dict)
    ]

    # Normalize education items
    out["education"] = [
        {
            "school": _clean_str(e.get("school")),
            "degree": _clean_str(e.get("degree")),
            "year": _clean_str(e.get("year")),
        }
        for e in out["education"]
        if isinstance(e, dict)
    ]

    # Compute missing fields
    missing = []
    for field in _NORMAL_FIELDS:
        if not out[field]:
            missing.append(field)
    for field in _LIST_FIELDS:
        if not out[field]:
            missing.append(field)

    out["missing_fields"] = missing
    return out


def _fallback_record(raw_text: str, error_reason: str | None = None) -> dict:
    return {
        "name": None,
        "email": None,
        "phone": None,
        "summary": None,
        "skills": [],
        "experience": [],
        "education": [],
        "missing_fields": ["name", "email", "phone", "summary", "skills",
                           "experience", "education"],
        "raw_text": raw_text,
    }


def _clean_str(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _normalize_skills(raw_skills) -> list[str]:
    if not raw_skills:
        return []
    if not isinstance(raw_skills, list):
        raw_skills = [str(raw_skills)]
    seen: set[str] = set()
    out: list[str] = []
    for s in raw_skills:
        if not isinstance(s, str):
            continue
        cleaned = s.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


class CVExtractorAgent:
    """Extracts structured fields from a .docx CV."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def extract(self, docx_bytes: bytes, *, session_id: str | None = None) -> dict:
        """Returns a normalized CV record (see module docstring)."""
        # Step 1: Extract raw text from .docx via python-docx
        try:
            from docx import Document  # type: ignore[import-untyped]
            import io
            doc = Document(io.BytesIO(docx_bytes))
            raw_text = "\n".join(
                p.text for p in doc.paragraphs if p.text.strip()
            )
        except Exception as exc:
            return _fallback_record("", f"python-docx error: {exc}")

        if not raw_text.strip():
            return _fallback_record(raw_text, "empty document")

        # Step 2: Send to LLM (cap at _MAX_TEXT_CHARS)
        llm_input = raw_text[: _MAX_TEXT_CHARS]

        try:
            content, _log = self.llm.route(
                "translation",
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": llm_input},
                ],
                session_id=session_id,
                from_agent="s6_cv_extractor",
                to_agent="t3_llm",
            )
        except Exception as exc:
            return _fallback_record(raw_text, f"LLM error: {exc}")

        parsed = _parse_json(content)
        if parsed is None:
            return _fallback_record(raw_text, "non-JSON LLM response")

        # Step 3-4: Normalize + compute missing fields
        return _normalize_record(parsed, raw_text)
