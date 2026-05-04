"""CIS routes — /cis/scope, /cis/select-tools, /cis/run, /cis/interventions/{id}.

Wraps the K_SCOPING / K_TOOL_SELECTOR agents and the dynamic O2 orchestrator.
All routes are stateless except for session rows inserted in /cis/run.
"""

import uuid
import threading
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.agents.cis.k_scoping import ScopingAgent, ScopingState
from api.agents.cis.k_tool_selector import ToolSelectorAgent

router = APIRouter()


# ── Request / Response Models ──────────────────────────────────────────────

class ScopeRequest(BaseModel):
    scoping_state: dict
    user_message: str


class ScopeResponse(BaseModel):
    scoping_state: dict


class SelectToolsRequest(BaseModel):
    scoping_state: dict


class ToolPlanResponse(BaseModel):
    ordered: list[str]
    reasoning: str


class RunRequest(BaseModel):
    scoping_state: dict
    tool_plan: list[str]


class RunResponse(BaseModel):
    session_id: str


class InterventionsResponse(BaseModel):
    interventions: list[dict]


# ── Helper: rebuild ScopingState from dict ────────────────────────────────

def _state_from_dict(d: dict) -> ScopingState:
    """Reconstruct a ScopingState from its __dict__ representation.
    Handles nested ScopingTurn objects stored as dicts."""
    from api.agents.cis.k_scoping import ScopingTurn

    state = ScopingState()
    if not d:
        return state
    state.problem = d.get("problem")
    state.scope = d.get("scope")
    state.requested_outcomes = d.get("requested_outcomes")
    state.role_title = d.get("role_title")
    state.target_kpi = d.get("target_kpi")
    state.confidence = float(d.get("confidence", 0.0))
    state.ready = bool(d.get("ready", False))

    raw_turns = d.get("turns", [])
    for t in raw_turns:
        if isinstance(t, dict):
            state.turns.append(ScopingTurn(
                role=t.get("role", "user"),
                message=t.get("message", ""),
            ))
        elif isinstance(t, ScopingTurn):
            state.turns.append(t)
    return state


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/scope")
async def cis_scope(req: ScopeRequest, request: Request):
    """Run one turn of the conversational scoping agent."""
    llm = request.state.llm
    agent = ScopingAgent(llm)
    state = _state_from_dict(req.scoping_state)

    updated = agent.step(state, req.user_message)
    return ScopeResponse(scoping_state={
        "problem": updated.problem,
        "scope": updated.scope,
        "requested_outcomes": updated.requested_outcomes,
        "role_title": updated.role_title,
        "target_kpi": updated.target_kpi,
        "confidence": updated.confidence,
        "ready": updated.ready,
        "turns": [
            {"role": t.role, "message": t.message}
            for t in updated.turns
        ],
    })


@router.post("/select-tools")
async def cis_select_tools(req: SelectToolsRequest, request: Request):
    """Select the minimal tool subset for a scoped charter."""
    llm = request.state.llm
    selector = ToolSelectorAgent(llm)
    state = _state_from_dict(req.scoping_state)

    plan = selector.select(state)
    return ToolPlanResponse(ordered=plan.ordered, reasoning=plan.reasoning)


@router.post("/run")
async def cis_run(req: RunRequest, request: Request):
    """Run a Kaizen with the selected tool plan. Returns immediately with a
    session_id; SSE events stream on /sessions/{session_id}/stream."""
    if not req.tool_plan:
        raise HTTPException(status_code=400, detail="tool_plan must not be empty")

    supabase = request.state.supabase
    orchestrator = request.state.orchestrator
    state = _state_from_dict(req.scoping_state)

    session_id = str(uuid.uuid4())
    role_title = state.role_title or "Senior Java Developer"
    problem_brief = state.problem or None

    # Insert kaizen_sessions row
    try:
        supabase.table("kaizen_sessions").insert({
            "session_id": session_id,
            "role_title": role_title,
            "problem_brief": problem_brief,
            "status": "running",
            "tool_plan": req.tool_plan,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}")

    # Run in background thread (same pattern as trigger.py)
    def _run():
        try:
            orchestrator.run_full_kaizen(
                session_id=session_id,
                role_title=role_title,
                problem_brief=problem_brief,
                target_kpi=state.target_kpi,
                tool_plan=req.tool_plan,
            )
        except Exception:
            import traceback
            traceback.print_exc()

    threading.Thread(target=_run, daemon=True).start()

    return RunResponse(session_id=session_id)


@router.get("/interventions/{session_id}")
async def cis_interventions(session_id: str, request: Request):
    """Fetch all interventions for a given session."""
    supabase = request.state.supabase
    try:
        resp = supabase.table("interventions").select("*").eq(
            "session_id", session_id
        ).order("priority", desc=False).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    rows = resp.data or []
    return InterventionsResponse(interventions=rows)
