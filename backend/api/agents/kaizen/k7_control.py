"""K7: Control Agent — Builds an honest Kanban-style control plan.

A fresh Kaizen has produced recommendations but executed nothing yet, so every
item lands in "To Do". The agent calls DeepSeek once with a JSON-output prompt
to derive owner, due_date, and KPI to monitor per intervention; if the LLM
fails or returns invalid JSON we fall back to sensible defaults rather than
inventing data.
"""

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from api.tools.t3_litellm_router import LiteLLMRouter


SYSTEM_PROMPT = """You are a recruiting operations lead turning Kaizen interventions into a control plan.

For each intervention, decide:
- owner: the role most accountable (e.g. "Hiring Manager", "Recruiting Lead", "Compensation Team", "Talent Brand"). Pick the SINGLE best owner — not "Everyone".
- due_offset_days: integer days from today by which the action should be DONE. 30 / 60 / 90 are typical; higher-priority items get 30, structural changes 90.
- kpi_to_monitor: which KPI this intervention is supposed to move. MUST be one of: "Time to Fill", "Applied → Hire Conversion", "Offer Acceptance Rate".

Return ONLY a JSON array, one object per input intervention, in the same order:
[
  {"owner": "...", "due_offset_days": 30, "kpi_to_monitor": "..."}
]

No prose, no markdown fences."""


@dataclass
class ControlItem:
    action: str
    owner: str
    due_date: str  # ISO YYYY-MM-DD
    kpi_to_monitor: str
    status: str = "To Do"


@dataclass
class ControlOutput:
    kanban_board: dict[str, list[ControlItem]]
    control_plan_summary: str


class K7ControlAgent:
    """Translates interventions into a To-Do-only Kanban with realistic owner / due / KPI."""

    DEFAULT_KPI = "Time to Fill"
    DEFAULT_OWNER = "Hiring Team"
    DEFAULT_DUE_OFFSET = 30
    VALID_KPIS = {
        "Time to Fill",
        "Applied → Hire Conversion",
        "Offer Acceptance Rate",
    }

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(self, interventions: list[dict], session_id: str | None = None) -> ControlOutput:
        if not interventions:
            return ControlOutput(
                kanban_board={"To Do": [], "In Progress": [], "Done": []},
                control_plan_summary="No interventions provided.",
            )

        meta = self._derive_metadata(interventions, session_id)

        today = date.today()
        items: list[ControlItem] = []
        for i, intervention in enumerate(interventions):
            m = meta[i] if i < len(meta) else {}
            offset = self._coerce_int(m.get("due_offset_days"), self.DEFAULT_DUE_OFFSET)
            owner = (m.get("owner") or self.DEFAULT_OWNER).strip() or self.DEFAULT_OWNER
            kpi = (m.get("kpi_to_monitor") or self.DEFAULT_KPI).strip()
            if kpi not in self.VALID_KPIS:
                kpi = self.DEFAULT_KPI
            title = intervention.get("title") or intervention.get("name") or f"Intervention {i+1}"
            items.append(ControlItem(
                action=f"Implement '{title}'",
                owner=owner,
                due_date=(today + timedelta(days=offset)).isoformat(),
                kpi_to_monitor=kpi,
                status="To Do",
            ))

        # Honest Kanban: nothing has started, so everything is "To Do".
        # The "In Progress" / "Done" columns exist for the UI and stay empty here —
        # they'll fill in over time as the team executes. Inventing a split would
        # be misleading.
        return ControlOutput(
            kanban_board={"To Do": items, "In Progress": [], "Done": []},
            control_plan_summary=(
                f"{len(items)} actions queued. Default review cadence: weekly until first KPI re-measure."
            ),
        )

    def _derive_metadata(self, interventions: list[dict], session_id: str | None) -> list[dict]:
        """Single LLM call to populate {owner, due_offset_days, kpi_to_monitor}.
        Returns an empty list on failure; callers fall through to defaults."""
        slim = [
            {
                "title": iv.get("title") or iv.get("name") or f"Intervention {i+1}",
                "description": (iv.get("description") or "")[:300],
            }
            for i, iv in enumerate(interventions)
        ]
        try:
            content, _log = self.llm.route(
                "dmaic_narrative",
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(slim, ensure_ascii=False)},
                ],
                session_id=session_id,
                from_agent="k7_control",
                to_agent="t3_llm",
                temperature=0.2,
            )
            parsed = self._parse_json_array(content)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return []

    @staticmethod
    def _coerce_int(val: Any, fallback: int) -> int:
        try:
            n = int(val)
            return n if n > 0 else fallback
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _parse_json_array(content: str) -> Any:
        text = content.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if not text.startswith("["):
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                text = text[start : end + 1]
        return json.loads(text)
