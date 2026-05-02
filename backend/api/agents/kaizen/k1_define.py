"""K1: Define Agent — Problem statement, SIPOC, financial impact."""

import json
import re
from dataclasses import dataclass, asdict
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class DefineOutput:
    problem_statement: str
    sipoc: dict  # Suppliers, Inputs, Process, Outputs, Customers
    financial_impact: str
    kpi_target: str

class K1DefineAgent:
    """Scopes the Kaizen investigation with SIPOC + financial impact."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def _parse_llm_json(self, content: str) -> dict | None:
        """Extract JSON from LLM output with flexible parsing."""
        # Try to find a JSON block in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        # Try to parse the whole thing as JSON
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return None

    def run(
        self,
        gap_report: dict,
        session_id: str = None,
        problem_brief: str | None = None,
        target_kpi: str | None = None,
        role_title: str | None = None,
    ) -> DefineOutput:
        """Generate Define phase output. The framing depends on what was supplied:
            - problem_brief → user-driven investigation (free-text)
            - target_kpi    → KPI-targeted investigation (one of time_to_fill/conversion_rate/offer_acceptance)
            - neither       → gap-driven (use the auto-detected gap report)"""

        # Build the "investigation framing" block injected into the user prompt.
        framing_lines: list[str] = []
        if problem_brief:
            framing_lines.append(f"User-supplied problem brief: {problem_brief}")
        if target_kpi:
            kpi_label = {
                "time_to_fill": "Time to Fill",
                "conversion_rate": "Applied → Hire conversion rate",
                "offer_acceptance": "Offer Acceptance Rate",
            }.get(target_kpi, target_kpi)
            framing_lines.append(f"Targeted KPI: {kpi_label}")
        if role_title:
            framing_lines.append(f"Role family: {role_title}")
        framing = "\n".join(framing_lines) if framing_lines else "(No specific brief — frame the investigation around the largest detected gap.)"

        messages = [
            {"role": "system", "content": """You are a Lean Six Sigma Black Belt. Generate a Define phase output for a recruitment Kaizen.

The investigation may be triggered by EITHER an auto-detected gap, a user-supplied free-text brief, OR a specific KPI the user wants to drill into. Frame the SIPOC and problem statement around whichever framing is provided. If a `problem_brief` is given, the brief takes precedence over the gap report — the gap report is supporting context, not the headline.

Return your response as VALID JSON with these exact keys:
{
  "problem_statement": "concise problem statement reflecting the framing — start with the symptom, not the metric",
  "sipoc": {
    "Suppliers": "...",
    "Inputs": "...",
    "Process": "...",
    "Outputs": "...",
    "Customers": "..."
  },
  "financial_impact": "estimated cost of the problem in rands or dollars (use realistic ranges)",
  "kpi_target": "measurable, time-bound target tied to the framing (e.g. 'Lift offer acceptance from 55% to 80% within 90 days')"
}

Only return valid JSON, no other text."""},
            {"role": "user", "content": (
                f"Investigation framing:\n{framing}\n\n"
                f"Auto-detected gap report (supporting context):\n{json.dumps(gap_report, indent=2)}\n\n"
                "Generate Define output as JSON."
            )},
        ]
        content, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                      from_agent="k1_define", to_agent="t3_llm")

        parsed = self._parse_llm_json(content)
        if parsed and all(k in parsed for k in ["problem_statement", "sipoc"]):
            return DefineOutput(
                problem_statement=parsed.get("problem_statement", "Gap detected in recruitment pipeline."),
                sipoc=parsed.get("sipoc", {}),
                financial_impact=parsed.get("financial_impact", str(gap_report.get("flagged_metrics", []))),
                kpi_target=parsed.get("kpi_target", "Improve target metric by 30% within 90 days"),
            )

        # Fallback: use LLM narrative but extract what we can
        return DefineOutput(
            problem_statement=content[:500] if content else (problem_brief or "Gap detected in recruitment pipeline."),
            sipoc={"Suppliers": "LinkedIn, Indeed, Referrals", "Inputs": "Applications",
                   "Process": "Apply→Screen→Interview→Offer", "Outputs": "Hires",
                   "Customers": "Hiring Managers"},
            financial_impact=str(gap_report.get("flagged_metrics", [])),
            kpi_target="Improve target metric by 30% within 90 days",
        )
