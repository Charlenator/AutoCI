"""K7: Control Agent — Builds a Kanban-style control plan with monitoring."""

from dataclasses import dataclass
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class ControlItem:
    action: str
    owner: str
    due_date: str
    kpi_to_monitor: str
    status: str = "To Do"

@dataclass
class ControlOutput:
    kanban_board: dict[str, list[ControlItem]]  # "To Do" | "In Progress" | "Done"
    control_plan_summary: str

class K7ControlAgent:
    """Generates a control plan and Kanban board for sustained improvement."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(self, interventions: list[dict], session_id: str = None) -> ControlOutput:
        """Translate interventions into a control plan with Kanban items."""
        messages = [
            {"role": "system", "content": "Create a control plan with action items, owners, due dates, KPIs. Return as a structured list."},
            {"role": "user", "content": f"Interventions: {interventions}"},
        ]
        content, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                      from_agent="k7_control", to_agent="t3_llm")

        items = [ControlItem(
            action=f"Implement '{i.get('title', 'Improvement')}'",
            owner="Hiring Team",
            due_date="30 days",
            kpi_to_monitor="Time to Fill",
        ) for i in interventions[:5]]

        return ControlOutput(
            kanban_board={
                "To Do": items[:2],
                "In Progress": items[2:4] if len(items) > 3 else [],
                "Done": items[4:] if len(items) > 4 else [],
            },
            control_plan_summary=content[:500],
        )
