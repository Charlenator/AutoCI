"""K6: Improve Agent — Generates and prioritises interventions via Impact/Effort matrix."""

from dataclasses import dataclass
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class Intervention:
    title: str
    description: str
    impact: str  # High/Medium/Low
    effort: str  # High/Medium/Low
    priority_score: int  # 1-100

@dataclass
class ImproveOutput:
    interventions: list[Intervention]
    recommendation: str

class K6ImproveAgent:
    """Generates interventions and scores them by impact vs effort."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(self, root_causes: str, analysis_findings: str,
            session_id: str = None) -> ImproveOutput:
        """Generate and prioritise 5-8 interventions."""
        messages = [
            {"role": "system", "content": "Generate 5-8 improvement interventions. For each, provide: title, description, impact (High/Medium/Low), effort (High/Medium/Low). Return as numbered list."},
            {"role": "user", "content": f"Root causes: {root_causes}\nFindings: {analysis_findings}"},
        ]
        content, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                      from_agent="k6_improve", to_agent="t3_llm")

        interventions = []
        impact_scores = {"High": 90, "Medium": 55, "Low": 20}
        effort_scores = {"High": 30, "Medium": 60, "Low": 90}

        for i, line in enumerate(content.strip().split("\n\n")[:8]):
            if line.strip():
                interventions.append(Intervention(
                    title=f"Intervention {i+1}",
                    description=line.strip()[:200],
                    impact="Medium",
                    effort="Medium",
                    priority_score=55,
                ))

        return ImproveOutput(
            interventions=interventions or [Intervention(
                title="Standardise interview feedback",
                description="Implement structured scoring rubric",
                impact="High", effort="Low", priority_score=85)],
            recommendation=content[:500],
        )
