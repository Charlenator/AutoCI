"""FMEA Agent — Failure Mode & Effects Analysis for CIS."""

from dataclasses import dataclass, field
from api.tools.t3_litellm_router import LiteLLMRouter

# ---------------------------------------------------------------------------
# Typed containers
# ---------------------------------------------------------------------------

@dataclass
class FMEAEntry:
    failure_mode: str
    effect: str
    cause: str
    severity: int       # 1-10
    occurrence: int     # 1-10
    detection: int      # 1-10

    @property
    def rpn(self) -> int:
        return self.severity * self.occurrence * self.detection


@dataclass
class FMEAOutput:
    entries: list[FMEAEntry]
    headline: str = ""

    @property
    def average_rpn(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.rpn for e in self.entries) / len(self.entries)

    @property
    def top_risk(self) -> FMEAEntry | None:
        if not self.entries:
            return None
        return max(self.entries, key=lambda e: e.rpn)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are the FMEA specialist for AutoCI's Continuous Improvement Suite.
Given a problem statement and role title, perform a Failure Mode & Effects Analysis.

Return ONLY valid JSON (no markdown fences):
{
  "headline": "One-line summary of the FMEA result",
  "entries": [
    {
      "failure_mode": "What could go wrong",
      "effect": "Impact if it happens",
      "cause": "Why it might happen",
      "severity": <1-10>,
      "occurrence": <1-10>,
      "detection": <1-10>
    }
  ]
}

Guidelines:
- Generate 3-8 failure mode entries.
- Severity: 1 (negligible) to 10 (catastrophic).
- Occurrence: 1 (almost never) to 10 (almost certain).
- Detection: 1 (always detected) to 10 (undetectable).
- RPN = S × O × D
- Focus on the recruitment / talent acquisition domain tied to the role.
"""

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class FMEAAgent:
    """Performs FMEA for a given problem."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(self, problem: str, role_title: str = "", session_id: str | None = None) -> FMEAOutput:
        import json

        user_prompt = f"Problem: {problem}\n"
        if role_title:
            user_prompt += f"Role: {role_title}\n"

        try:
            content, _log = self.llm.route(
                "cis_fmea",
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                from_agent="cis_fmea",
                to_agent="t3_llm",
            )
        except Exception:
            return FMEAOutput(entries=[], headline="FMEA failed (LLM error)")

        parsed = _parse_json(content)
        if not parsed:
            return FMEAOutput(entries=[], headline="FMEA failed (parse error)")

        headline = str(parsed.get("headline", ""))
        raw_entries = parsed.get("entries", [])
        entries = [
            FMEAEntry(
                failure_mode=str(e.get("failure_mode", "")),
                effect=str(e.get("effect", "")),
                cause=str(e.get("cause", "")),
                severity=_clamp(int(e.get("severity", 1))),
                occurrence=_clamp(int(e.get("occurrence", 1))),
                detection=_clamp(int(e.get("detection", 1))),
            )
            for e in raw_entries if isinstance(e, dict)
        ]

        return FMEAOutput(entries=entries, headline=headline)


def _clamp(v: int, lo: int = 1, hi: int = 10) -> int:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re
import json
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
