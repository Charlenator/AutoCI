"""A1, A2: Kaizen trigger endpoints — wired to real MetaOrchestrator.
Runs Kaizen as background task so SSE events stream in real-time."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import asyncio
import json

router = APIRouter()


class ManualTrigger(BaseModel):
    role_id: str | None = None
    problem_brief: str | None = None


class GoalReviewResponse(BaseModel):
    session_id: str
    status: str
    message: str


@router.post("/manual")
async def trigger_manual(body: ManualTrigger, request: Request):
    """A1: Launch a full Kaizen via MetaOrchestrator on background thread."""
    session_id = str(uuid4())
    orchestrator = request.state.orchestrator
    supabase = request.state.supabase

    # Insert kaizen_sessions row first (FK target for agent_invocations)
    try:
        supabase.table("kaizen_sessions").insert({
            "session_id": session_id,
            "trigger_type": "manual",
            "phase": "detection",
            "status": "running",
            "output_state": {},
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    # Launch Kaizen as a background task (sync → async via run_in_executor)
    asyncio.create_task(_run_kaizen_background(orchestrator, session_id, body.problem_brief or "Senior Java Developer"))

    return GoalReviewResponse(
        session_id=session_id,
        status="running",
        message="🚀 Kaizen launched! Watch the graph light up.",
    )


@router.post("/goal-review")
async def trigger_goal_review(request: Request):
    """A2: Simulate a KPI miss — runs full detection + Kaizen on background thread."""
    session_id = str(uuid4())
    orchestrator = request.state.orchestrator
    supabase = request.state.supabase

    # Insert kaizen_sessions row first (FK target for agent_invocations)
    try:
        supabase.table("kaizen_sessions").insert({
            "session_id": session_id,
            "trigger_type": "goal_review_simulation",
            "phase": "detection",
            "status": "running",
            "output_state": {},
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    # Launch Kaizen as a background task
    asyncio.create_task(_run_kaizen_background(orchestrator, session_id, "Senior Java Developer"))

    return GoalReviewResponse(
        session_id=session_id,
        status="running",
        message="🚀 Kaizen launched! Watch the graph light up.",
    )


async def _run_kaizen_background(orchestrator, session_id: str, role_title: str):
    """Run Kaizen on a background thread. Updates session status on completion."""
    loop = asyncio.get_event_loop()
    try:
        # run_full_kaizen is synchronous — offload to executor
        result = await loop.run_in_executor(
            None, orchestrator.run_full_kaizen, session_id, role_title
        )

        # Mark session as completed (or failed) in DB
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
