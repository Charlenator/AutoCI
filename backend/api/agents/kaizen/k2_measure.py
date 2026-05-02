"""K2: Measure Agent — Current-state metrics + data quality assessment."""

from dataclasses import dataclass
from api.tools.t1_mcp_analytics import AnalyticsLibrary
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class MeasureOutput:
    current_state_metrics: dict
    data_quality_flags: list[str]
    baseline_summary: str

class K2MeasureAgent:
    """Establishes baseline KPIs and data quality."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.analytics = AnalyticsLibrary()
        self.llm = llm_router

    def run(self, pipeline_events: list[dict], hires: list[dict],
            candidates: list[dict], offer_outcomes: list[dict],
            session_id: str = None) -> MeasureOutput:
        """Compute baseline and flag data issues."""
        ttf = self.analytics.time_to_fill(pipeline_events, hires)
        oar = self.analytics.offer_acceptance_rate(hires, offer_outcomes)
        source_yields = self.analytics.source_yield(pipeline_events, candidates)

        metrics = {
            "time_to_fill_days": round(ttf, 1),
            "offer_acceptance_rate": round(oar, 2),
            "source_yields": source_yields,
            "total_candidates": len(candidates),
            "total_offers": len(offer_outcomes),
        }

        messages = [
            {"role": "system", "content": "Summarise current-state metrics for a Kaizen report."},
            {"role": "user", "content": f"Metrics: {metrics}"},
        ]
        summary, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                      from_agent="k2_measure", to_agent="t3_llm")

        return MeasureOutput(
            current_state_metrics=metrics,
            data_quality_flags=[],
            baseline_summary=summary.strip(),
        )
