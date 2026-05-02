"""T1: MCP Analytics Library — Hard-coded recruitment formulas aligned with data schema.
Eliminates hallucinations in the data analysis layer."""

from datetime import date, datetime
from typing import Any
import statistics

class AnalyticsLibrary:
    """Hard-coded recruitment analytics formulas.
    All methods operate on pre-fetched data — no LLM involvement."""

    @staticmethod
    def _parse_date(val: Any) -> date | None:
        """Parse a date from string, date, or datetime."""
        if isinstance(val, (date, datetime)):
            return val if isinstance(val, date) else val.date()
        if isinstance(val, str):
            # Handle ISO format strings like "2025-01-15" or "2025-01-15T00:00:00"
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def time_to_fill(pipeline_events: list[dict], hires: list[dict]) -> float:
        """Average days from Applied to Hire for filled roles."""
        hire_candidates = {h["candidate_id"]: h for h in hires if h.get("accepted")}
        applied_times = {}
        hired_times = {}
        for ev in pipeline_events:
            if ev["stage"] == "Applied" and ev["outcome"] == "Advanced":
                applied_times[ev["candidate_id"]] = ev["event_date"]
            if ev["stage"] == "Offer" and ev["candidate_id"] in hire_candidates:
                hired_times[ev["candidate_id"]] = ev["event_date"]

        ttfs = []
        for cid in hire_candidates:
            if cid in applied_times and cid in hired_times:
                d1 = AnalyticsLibrary._parse_date(applied_times[cid])
                d2 = AnalyticsLibrary._parse_date(hired_times[cid])
                if d1 and d2:
                    delta = (d2 - d1).days
                    ttfs.append(delta)
        return float(sum(ttfs) / len(ttfs)) if ttfs else 0.0

    @staticmethod
    def stage_conversion_rate(pipeline_events: list[dict], stage: str) -> float:
        """Percentage of candidates who advance from this stage."""
        at_stage = [e for e in pipeline_events if e["stage"] == stage]
        if not at_stage:
            return 0.0
        advanced = sum(1 for e in at_stage if e.get("outcome") == "Advanced")
        return advanced / len(at_stage)

    @staticmethod
    def stage_dropoff_rate(pipeline_events: list[dict], stage: str) -> float:
        """Percentage of candidates rejected at this stage."""
        return 1.0 - AnalyticsLibrary.stage_conversion_rate(pipeline_events, stage)

    @staticmethod
    def offer_acceptance_rate(hires: list[dict], offer_outcomes: list[dict]) -> float:
        """Accepted offers / total offers."""
        accepted = sum(1 for o in offer_outcomes if o.get("outcome") == "Accepted")
        total = len(offer_outcomes)
        return accepted / total if total > 0 else 0.0

    @staticmethod
    def source_yield(pipeline_events: list[dict], candidates: list[dict]) -> dict:
        """Hires per source channel."""
        source_map = {c["candidate_id"]: c["source_channel"] for c in candidates}
        hired_ids = set()
        for ev in pipeline_events:
            if ev["stage"] == "Offer" and ev.get("outcome") == "Offer Extended":
                hired_ids.add(ev["candidate_id"])
        yield_by_source = {}
        for cid in hired_ids:
            src = source_map.get(cid, "Unknown")
            yield_by_source[src] = yield_by_source.get(src, 0) + 1
        return yield_by_source

    @staticmethod
    def outlier_detection(values: list[float], threshold: float = 3.0) -> list[int]:
        """Return indices of values with z-score > threshold."""
        if len(values) < 3:
            return []
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        std = var ** 0.5
        if std == 0:
            return []
        return [i for i, x in enumerate(values) if abs(x - mean) / std > threshold]

    @staticmethod
    def benchmark_comparison(internal_value: float, benchmark_median: float) -> dict:
        """Compare internal metric against industry benchmark."""
        if benchmark_median == 0:
            return {"delta_pct": 0, "direction": "unknown", "severity": "green"}
        delta_pct = ((internal_value - benchmark_median) / benchmark_median) * 100
        severity = "green"
        if delta_pct > 50:
            severity = "red"
        elif delta_pct > 20:
            severity = "amber"
        return {
            "delta_pct": round(delta_pct, 1),
            "direction": "above" if delta_pct > 0 else "below",
            "severity": severity,
        }
