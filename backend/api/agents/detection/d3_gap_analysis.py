"""D3: Gap Analysis Agent — Flags deviations from benchmarks and generates anomaly reports."""

from dataclasses import dataclass
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class GapReport:
    flagged_metrics: list[dict]  # metric_name, our_value, benchmark_value, severity
    recommendation: str  # T3-generated narrative
    kaizen_required: bool

class D3GapAnalysisAgent:
    """Synthesises D1 + D2 output + live market intel, flags gaps, recommends Kaizen."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def analyze(self, internal: dict, external: list[dict],
                session_id: str = None, market_context: str = "") -> GapReport:
        """Compare internal vs external and flag gaps, enriched with live market intel."""
        flagged = []

        for ext in external:
            if abs(ext["delta_pct"]) > 20:
                flagged.append({
                    "metric": "time_to_fill",
                    "our_value": ext["our_ttf"],
                    "benchmark_value": ext["benchmark_median"],
                    "delta_pct": ext["delta_pct"],
                    "severity": "red" if abs(ext["delta_pct"]) > 50 else "amber",
                })

        # Also check stage dropoff patterns
        if internal.get("stage_conversions"):
            for stage, rate in internal["stage_conversions"].items():
                if rate < 0.5:
                    flagged.append({
                        "metric": f"{stage}_conversion",
                        "our_value": rate,
                        "benchmark_value": 0.65,
                        "delta_pct": round(((rate - 0.65) / 0.65) * 100, 1),
                        "severity": "amber",
                    })

        # Generate recommendation via T3 — include market_context for richer analysis
        context = (
            f"Internal benchmarks: {internal}\n"
            f"External benchmarks: {external}\n"
            f"Flagged gaps: {flagged}\n"
            f"Live market intelligence: {market_context[:1500]}"
            if market_context else
            f"Internal benchmarks: {internal}\n"
            f"External benchmarks: {external}\n"
            f"Flagged gaps: {flagged}"
        )
        messages = [
            {"role": "system", "content": "You are a recruitment analytics advisor. Based on gap analysis AND live market data, recommend whether a Kaizen investigation is needed. Be concise and reference any relevant market intel (salary trends, hiring news, web search findings)."},
            {"role": "user", "content": f"Analyse these gaps and recommend action:\n\n{context}"},
        ]
        recommendation, log = self.llm.route(
            "research_synthesis", messages,
            session_id=session_id, from_agent="d3_gap", to_agent="t3_llm",
        )

        kaizen_required = any(f["severity"] == "red" for f in flagged)

        return GapReport(
            flagged_metrics=flagged,
            recommendation=recommendation.strip(),
            kaizen_required=kaizen_required,
        )
