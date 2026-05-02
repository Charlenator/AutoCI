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

    def run(self, gap_report: dict, session_id: str = None) -> DefineOutput:
        """Generate Define phase output from Gap Report."""
        messages = [
            {"role": "system", "content": """You are a Lean Six Sigma Black Belt. Based on the gap analysis report, generate a Define phase output.

Return your response as VALID JSON with these exact keys:
{
  "problem_statement": "clear problem statement based on the gap",
  "sipoc": {
    "Suppliers": "list of talent sources",
    "Inputs": "what goes into the process",
    "Process": "the recruitment process steps",
    "Outputs": "what the process produces",
    "Customers": "who receives the output"
  },
  "financial_impact": "estimated cost of the gap in rands or dollars",
  "kpi_target": "measurable target (e.g. Reduce TTF by 30% within 90 days)"
}

Only return valid JSON, no other text."""},
            {"role": "user", "content": f"Gap report:\n{json.dumps(gap_report, indent=2)}\n\nGenerate Define output as JSON."},
        ]
        content, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                      from_agent="k1_define", to_agent="t3_llm")

        # Try to parse JSON from LLM response
        parsed = self._parse_llm_json(content)
        if parsed and all(k in parsed for k in ["problem_statement", "sipoc"]):
            return DefineOutput(
                problem_statement=parsed.get("problem_statement", "Gap detected in recruitment pipeline."),
                sipoc=parsed.get("sipoc", {}),
                financial_impact=parsed.get("financial_impact", str(gap_report.get("flagged_metrics", []))),
                kpi_target=parsed.get("kpi_target", "Reduce TTF by 30% within 90 days"),
            )

        # Fallback: use LLM narrative but extract what we can
        return DefineOutput(
            problem_statement=content[:500] if content else "Gap detected in recruitment pipeline.",
            sipoc={"Suppliers": "LinkedIn, Indeed, Referrals", "Inputs": "Applications",
                   "Process": "Apply→Screen→Interview→Offer", "Outputs": "Hires",
                   "Customers": "Hiring Managers"},
            financial_impact=str(gap_report.get("flagged_metrics", [])),
            kpi_target="Reduce TTF by 30% within 90 days",
        )
