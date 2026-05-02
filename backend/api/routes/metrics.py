"""A5: Cost and metrics aggregation — wired to real agent_invocations table."""
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

router = APIRouter()


class CostSummary(BaseModel):
    total_cost_usd: float
    session_count: int
    avg_cost_per_session: float
    model_breakdown: dict = {}
    recent_invocations: list[dict] = []


@router.get("/cost")
async def get_cost_metrics(limit: int = Query(default=10, ge=1, le=100), request: Request = None):
    """A5: Aggregate cost from agent_invocations table."""
    supabase = request.state.supabase

    try:
        # Fetch all cost-session pairs for aggregation
        resp = supabase.table("agent_invocations").select(
            "session_id, cost_usd, model_used, from_agent, to_agent, duration_ms, created_at"
        ).execute()
        rows = resp.data or []

        total = sum(r.get("cost_usd", 0) for r in rows)
        sessions = set(r.get("session_id") for r in rows if r.get("session_id"))
        session_count = len(sessions)
        avg_cost = total / session_count if session_count > 0 else 0

        # Model breakdown
        breakdown = {}
        for r in rows:
            m = r.get("model_used", "unknown")
            breakdown[m] = breakdown.get(m, 0) + r.get("cost_usd", 0)

        # Most recent
        recent = sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)[:limit]

        return CostSummary(
            total_cost_usd=round(total, 6),
            session_count=session_count,
            avg_cost_per_session=round(avg_cost, 6),
            model_breakdown={k: round(v, 6) for k, v in breakdown.items()},
            recent_invocations=recent,
        )
    except Exception as e:
        return CostSummary(
            total_cost_usd=0.0,
            session_count=0,
            avg_cost_per_session=0.0,
            model_breakdown={},
            recent_invocations=[],
        )
