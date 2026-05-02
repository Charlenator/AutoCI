"""Per-session HITL controls.
`POST /sessions/{id}/respond` lets the user advance, ask a follow-up, or abort
between Kaizen phases. The orchestrator is blocked on the matching HITL queue;
this endpoint just hands it the next move."""

from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.sse import put_hitl_response

router = APIRouter()


class RespondBody(BaseModel):
    decision: Literal["advance", "ask", "abort"]
    message: str | None = Field(
        default=None,
        description="Required when decision == 'ask'. Free-text question routed through the chat agent.",
    )


@router.post("/{session_id}/respond")
async def respond(session_id: str, body: RespondBody) -> dict:
    """Advance, ask, or abort the Kaizen at the current HITL pause.

    - `advance`: orchestrator continues to the next phase.
    - `ask`: orchestrator routes the message through the chat agent (S1 → S2/S3),
      streams the answer back, then waits again for a final advance/abort.
    - `abort`: orchestrator stops and marks the session as aborted.
    """
    if body.decision == "ask" and not body.message:
        raise HTTPException(status_code=400, detail="`message` is required when decision is 'ask'")

    put_hitl_response(session_id, body.model_dump())
    return {"session_id": session_id, "decision": body.decision, "queued": True}
