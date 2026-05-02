"""A5: Cost and metrics aggregation — wired to real agent_invocations table."""
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from api.agents.detection.d1_internal_benchmarking import D1InternalBenchmarkingAgent
from api.agents.detection.d2_external_benchmarking import D2ExternalBenchmarkingAgent

router = APIRouter()


class CostSummary(BaseModel):
    total_cost_usd: float
    session_count: int
    avg_cost_per_session: float
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    model_breakdown: dict = {}
    recent_invocations: list[dict] = []


def _agg(rows: list[dict], key: str) -> float:
    return sum(r.get(key, 0) or 0 for r in rows)


@router.get("/cost")
async def get_cost_metrics(
    limit: int = Query(default=10, ge=1, le=100),
    session_id: str | None = Query(default=None),
    request: Request = None,
):
    """A5: Aggregate cost + tokens from agent_invocations table.
    Pass `session_id` to filter to a single Kaizen session."""
    supabase = request.state.supabase

    try:
        query = supabase.table("agent_invocations").select(
            "session_id, cost_usd, model_used, from_agent, to_agent, duration_ms, "
            "input_tokens, output_tokens, cached_tokens, created_at"
        )
        if session_id:
            query = query.eq("session_id", session_id)
        rows = query.execute().data or []

        total_cost = _agg(rows, "cost_usd")
        sessions = set(r.get("session_id") for r in rows if r.get("session_id"))
        session_count = len(sessions)
        avg_cost = total_cost / session_count if session_count > 0 else 0

        # Per-model breakdown: {model: {cost, input_tokens, output_tokens}}
        breakdown: dict[str, dict] = {}
        for r in rows:
            m = r.get("model_used", "unknown")
            entry = breakdown.setdefault(m, {"cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "calls": 0})
            entry["cost_usd"] += r.get("cost_usd", 0) or 0
            entry["input_tokens"] += r.get("input_tokens", 0) or 0
            entry["output_tokens"] += r.get("output_tokens", 0) or 0
            entry["cached_tokens"] += r.get("cached_tokens", 0) or 0
            entry["calls"] += 1
        for m, entry in breakdown.items():
            entry["cost_usd"] = round(entry["cost_usd"], 6)

        recent = sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)[:limit]

        return CostSummary(
            total_cost_usd=round(total_cost, 6),
            session_count=session_count,
            avg_cost_per_session=round(avg_cost, 6),
            total_input_tokens=int(_agg(rows, "input_tokens")),
            total_output_tokens=int(_agg(rows, "output_tokens")),
            total_cached_tokens=int(_agg(rows, "cached_tokens")),
            model_breakdown=breakdown,
            recent_invocations=recent,
        )
    except Exception:
        return CostSummary(
            total_cost_usd=0.0,
            session_count=0,
            avg_cost_per_session=0.0,
        )


def _kpi_status(kpi_key: str, our_value: float, target: float | None, benchmark: float | None) -> dict:
    """Resolve a KPI tile's traffic-light status and the threshold that drove it.
    Lower-is-better for time_to_fill; higher-is-better for the rest."""
    direction = "lower_better" if kpi_key == "time_to_fill" else "higher_better"
    primary = target if target is not None else benchmark
    if primary is None or primary == 0:
        return {"status": "unknown", "delta_pct": 0, "primary_target": None, "direction": direction}

    delta_pct = (our_value - primary) / primary * 100
    unfavourable_pct = delta_pct if direction == "lower_better" else -delta_pct
    if unfavourable_pct > 25:
        status = "red"
    elif unfavourable_pct > 10:
        status = "amber"
    else:
        status = "green"
    return {
        "status": status,
        "delta_pct": round(delta_pct, 1),
        "primary_target": primary,
        "direction": direction,
    }


@router.get("/kpis")
async def get_kpis(
    role_title: str = Query(default="Senior Java Developer"),
    region: str = Query(default="South Africa"),
    request: Request = None,
):
    """Return current KPI snapshot (TTF, conversion, OAR) with target + benchmark + status.
    Used by the dashboard's KPI tile row WITHOUT triggering a Kaizen."""
    supabase = request.state.supabase

    # Pull pipeline data, scoped to the requested role.
    try:
        roles = supabase.table("roles").select("*").eq("title", role_title).execute().data or []
        if not roles:
            return {"role_title": role_title, "region": region, "kpis": [], "data_points": 0,
                    "error": f"role '{role_title}' not found"}
        role_id = roles[0]["role_id"]
        candidates = supabase.table("candidates").select("*").eq("role_id", role_id).execute().data or []
        cand_ids = [c["candidate_id"] for c in candidates]
        if cand_ids:
            pipeline_events = supabase.table("pipeline_events").select("*").in_(
                "candidate_id", cand_ids
            ).execute().data or []
        else:
            pipeline_events = []
        hires = supabase.table("hires").select("*").eq("role_id", role_id).execute().data or []
        offers = supabase.table("offer_outcomes").select("*").eq("role_id", role_id).execute().data or []
    except Exception as e:
        return {"error": f"data fetch failed: {e}"}

    d1 = D1InternalBenchmarkingAgent()
    internal = d1.run(pipeline_events, hires, candidates, offers)
    if isinstance(internal, tuple):
        internal = internal[0]

    role = roles[0] if roles else {}

    # Per-KPI targets (pulled from roles row, with sensible defaults)
    targets = {
        "time_to_fill": role.get("target_ttf_days"),
        "conversion_rate": role.get("target_conversion_rate"),
        "offer_acceptance": role.get("target_offer_acceptance_rate"),
    }

    # Pull benchmark row for the role/region
    try:
        bench_resp = supabase.table("industry_benchmarks").select("*").eq(
            "role_family", role_title
        ).eq("region", region).execute()
        bench_row = (bench_resp.data or [{}])[0]
    except Exception:
        bench_row = {}

    benchmarks = {
        "time_to_fill": bench_row.get("median_ttf_days"),
        "conversion_rate": bench_row.get("conversion_rate_median"),
        "offer_acceptance": bench_row.get("offer_acceptance_median"),
    }

    tiles = []
    for kpi_key, kpi in internal.kpis.items():
        status = _kpi_status(kpi_key, kpi["value"], targets.get(kpi_key), benchmarks.get(kpi_key))
        tiles.append({
            "kpi": kpi_key,
            "label": kpi["label"],
            "unit": kpi["unit"],
            "value": kpi["value"],
            "target": targets.get(kpi_key),
            "benchmark": benchmarks.get(kpi_key),
            **status,
        })

    return {
        "role_title": role_title,
        "region": region,
        "kpis": tiles,
        "data_points": internal.validity.get("data_points", 0),
    }
