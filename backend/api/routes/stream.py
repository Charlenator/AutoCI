"""A3: SSE endpoint for real-time session updates — uses api/sse module."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from api.sse import event_generator

router = APIRouter()

@router.get("/{session_id}/stream")
async def stream_session(session_id: str):
    """A3: SSE stream for session state transitions."""
    return StreamingResponse(
        event_generator(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
