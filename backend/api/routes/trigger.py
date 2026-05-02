"""A1, A2: Kaizen trigger endpoints — wired to real MetaOrchestrator.
Runs Kaizen as background task so SSE events stream in real-time."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import asyncio

router = APIRouter()


class ManualTrigger(BaseModel):
    role_id: str | None = None
    role_title: str | None = None
    problem_brief: str | None = None
    target_kpi: str | None = None  # one of: time_to_fill, conversion_rate, offer_acceptance


class GoalReviewTrigger(BaseModel):
    role_title: str | None = None  # optional override; default = auto-detect from KPI gaps
    region: str | None = None


class TriggerResponse(BaseModel):
    session_id: str
    status: str
    message: str
    role_title: str | None = None
    target_kpi: str | None = None


def _resolve_role_title(supabase, role_id: str | None, role_title: str | None) -> str:
    """Resolve a role's title from role_id, falling back to provided role_title or default."""
    if role_title:
        return role_title
    if role_id:
        try:
            resp = supabase.table("roles").select("title").eq("role_id", role_id).limit(1).execute()
            if resp.data:
                return resp.data[0]["title"]
        except Exception:
            pass
    return "Senior Java Developer"


@router.post("/manual")
async def trigger_manual(body: ManualTrigger, request: Request) -> TriggerResponse:
    """A1: Launch a full Kaizen with a user-supplied brief or targeted KPI.
    Either `problem_brief` or `target_kpi` (or both) makes the Kaizen proceed even if no gap auto-detected."""
    session_id = str(uuid4())
    orchestrator = request.state.orchestrator
    supabase = request.state.supabase

    role_title = _resolve_role_title(supabase, body.role_id, body.role_title)

    try:
        supabase.table("kaizen_sessions").insert({
            "session_id": session_id,
            "trigger_type": "manual",
            "phase": "detection",
            "status": "running",
            "output_state": {
                "problem_brief": body.problem_brief,
                "target_kpi": body.target_kpi,
            },
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    asyncio.create_task(_run_kaizen_background(
        orchestrator, session_id, role_title,
        problem_brief=body.problem_brief,
        target_kpi=body.target_kpi,
    ))

    return TriggerResponse(
        session_id=session_id,
        status="running",
        message="🚀 Kaizen launched — watch the graph light up.",
        role_title=role_title,
        target_kpi=body.target_kpi,
    )


@router.post("/goal-review")
async def trigger_goal_review(request: Request, body: GoalReviewTrigger | None = None) -> TriggerResponse:
    """A2: Simulate a goal review — picks the role with the worst KPI gap and launches a Kaizen.
    Falls back to the legacy hardcoded role if no benchmark data is available."""
    session_id = str(uuid4())
    orchestrator = request.state.orchestrator
    supabase = request.state.supabase

    body = body or GoalReviewTrigger()
    region = body.region or "South Africa"

    role_title = body.role_title or _pick_worst_role(supabase, region) or "Senior Java Developer"

    try:
        supabase.table("kaizen_sessions").insert({
            "session_id": session_id,
            "trigger_type": "goal_review_simulation",
            "phase": "detection",
            "status": "running",
            "output_state": {"auto_picked_role": role_title, "region": region},
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    asyncio.create_task(_run_kaizen_background(orchestrator, session_id, role_title))

    return TriggerResponse(
        session_id=session_id,
        status="running",
        message=f"🚀 Kaizen launched on {role_title} — auto-picked from KPI gaps.",
        role_title=role_title,
    )


def _pick_worst_role(supabase, region: str) -> str | None:
    """Pick the role with the worst TTF delta vs benchmark.
    Cheap heuristic — full multi-KPI selection happens inside the Kaizen itself."""
    try:
        roles = supabase.table("roles").select("title, target_ttf_days").eq("status", "open").execute().data or []
        benchmarks = supabase.table("industry_benchmarks").select("role_family, median_ttf_days").eq("region", region).execute().data or []
    except Exception:
        return None

    bench_by_role = {b["role_family"]: b["median_ttf_days"] for b in benchmarks if b.get("median_ttf_days")}
    if not bench_by_role:
        return None

    worst_role, worst_delta = None, -1.0
    for r in roles:
        target = r.get("target_ttf_days") or bench_by_role.get(r["title"])
        bench = bench_by_role.get(r["title"])
        if not target or not bench:
            continue
        # Larger target relative to benchmark = more "ambitious" = use that as a proxy for trouble.
        # In a real system D1 would compute actual TTF; we keep this simple to avoid an extra DB roundtrip.
        delta = abs(target - bench) / bench
        if delta > worst_delta:
            worst_delta = delta
            worst_role = r["title"]
    return worst_role


async def _run_kaizen_background(
    orchestrator,
    session_id: str,
    role_title: str,
    problem_brief: str | None = None,
    target_kpi: str | None = None,
):
    """Run Kaizen on a background thread. Updates session status on completion."""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.run_full_kaizen(
                session_id, role_title,
                problem_brief=problem_brief,
                target_kpi=target_kpi,
            ),
        )

        final_status = "completed" if result.phase in ("complete", "detection") else "failed"
        final_phase = result.phase

        def _update():
            orchestrator.supabase.table("kaizen_sessions").update({
                "status": final_status,
                "phase": final_phase,
                "output_state": {
                    "detection": result.detection,
                    "define": result.define,
                    "measure": result.measure,
                    "analyse": result.analyse,
                    "improve": result.improve,
                    "control": result.control,
                    "problem_brief": problem_brief,
                    "target_kpi": target_kpi,
                },
            }).eq("session_id", session_id).execute()

        await loop.run_in_executor(None, _update)

    except Exception as e:
        print(f"Kaizen background task failed for {session_id}: {e}")
        try:
            def _fail():
                orchestrator.supabase.table("kaizen_sessions").update({
                    "status": "failed",
                    "output_state": {"error": str(e)},
                }).eq("session_id", session_id).execute()
            await loop.run_in_executor(None, _fail)
        except Exception:
            pass
