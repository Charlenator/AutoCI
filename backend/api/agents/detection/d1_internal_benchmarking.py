"""D1: Internal Benchmarking Agent — Computes pipeline metrics from seed data."""

from dataclasses import dataclass, field
from api.tools.t1_mcp_analytics import AnalyticsLibrary
from api.tools.t2_validation_interceptor import validate_agent_output
from pydantic import BaseModel

class InternalBenchmarkSchema(BaseModel):
    time_to_fill_days: float
    stage_conversions: dict
    offer_acceptance_rate: float
    source_yields: dict
    kpis: dict
    validity: dict

@dataclass
class InternalBenchmarkResult:
    time_to_fill_days: float
    stage_conversions: dict
    offer_acceptance_rate: float
    source_yields: dict
    kpis: dict           # Clean 3-KPI snapshot: {time_to_fill, conversion_rate, offer_acceptance}
    outlier_warnings: list[str]
    validity: dict

class D1InternalBenchmarkingAgent:
    """Computes internal baseline metrics from raw pipeline data."""

    def __init__(self):
        self.analytics = AnalyticsLibrary()

    @validate_agent_output(schema=InternalBenchmarkSchema, min_sample_size=3)
    def run(self, pipeline_events: list[dict], hires: list[dict],
            candidates: list[dict], offer_outcomes: list[dict]) -> InternalBenchmarkResult:
        """Calculate all baseline metrics."""
        ttf = self.analytics.time_to_fill(pipeline_events, hires)

        stages = ["Applied", "Screening", "Interview 1", "Interview 2", "Offer"]
        stage_conversions = {}
        for s in stages:
            stage_conversions[s] = self.analytics.stage_conversion_rate(pipeline_events, s)

        oar = self.analytics.offer_acceptance_rate(hires, offer_outcomes)
        source_yields = self.analytics.source_yield(pipeline_events, candidates)
        conversion = self.analytics.applied_to_hire_rate(pipeline_events, hires)

        kpis = {
            "time_to_fill": {"value": round(ttf, 1), "unit": "days", "label": "Time to Fill"},
            "conversion_rate": {"value": round(conversion, 4), "unit": "ratio", "label": "Applied → Hire"},
            "offer_acceptance": {"value": round(oar, 4), "unit": "ratio", "label": "Offer Acceptance"},
        }

        return InternalBenchmarkResult(
            time_to_fill_days=ttf,
            stage_conversions=stage_conversions,
            offer_acceptance_rate=oar,
            source_yields=source_yields,
            kpis=kpis,
            outlier_warnings=[],
            validity={"data_points": len(pipeline_events)},
        )
