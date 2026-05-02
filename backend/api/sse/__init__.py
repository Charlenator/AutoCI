"""SSE event system — pushes real-time state transitions to frontend EventSource.
Works from both sync and async callers via put_nowait.

Also hosts the HITL response queue used by the orchestrator: between phases the
orchestrator blocks on `get_hitl_response()` (with a 30s timeout); the
`POST /sessions/:id/respond` endpoint feeds responses in via `put_hitl_response()`.
We use `queue.Queue` (thread-safe) because the orchestrator runs on a worker
thread via `run_in_executor`, while the FastAPI endpoint runs on the event loop —
asyncio.Queue would not be safe across that boundary."""
import asyncio
import json
import queue
from collections import deque

# In-memory event queues per session (thread-safe deques)
_session_queues: dict[str, deque] = {}
# HITL response queues — one per session, fed by the respond endpoint, drained by
# the orchestrator between DMAIC phases.
_hitl_queues: dict[str, "queue.Queue"] = {}

def get_queue(session_id: str) -> deque:
    """Get or create an event queue for a session."""
    if session_id not in _session_queues:
        _session_queues[session_id] = deque()
    return _session_queues[session_id]

def push_event(session_id: str, event: dict):
    """Push an event to a session's stream queue. Works from sync or async code."""
    queue = get_queue(session_id)
    queue.append(event)

async def event_generator(session_id: str):
    """Async generator yielding SSE-formatted events for a session."""
    queue = get_queue(session_id)
    # Send initial connection event
    yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"
    try:
        while True:
            # Poll for events with a small sleep to avoid busy-wait
            if queue:
                event = queue.popleft()
                yield f"data: {json.dumps(event)}\n\n"
            else:
                try:
                    await asyncio.wait_for(_wait_for_event(queue), timeout=30)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
    except asyncio.CancelledError:
        pass

async def _wait_for_event(queue: deque):
    """Wait until there's an event in the queue (polling with sleep)."""
    while not queue:
        await asyncio.sleep(0.1)

def make_node_event(agent_id: str, status: str, label: str = None, data: dict = None) -> dict:
    """Create a standard node_status event."""
    return {
        "type": "node_status",
        "agent_id": agent_id,
        "status": status,
        "label": label or agent_id,
        "data": data or {},
    }

def make_phase_event(phase: str, status: str, data: dict = None) -> dict:
    """Create a phase_transition event."""
    return {
        "type": "phase_transition",
        "phase": phase,
        "status": status,
        "data": data or {},
    }

def make_output_event(phase: str, content: str, agent_id: str = None) -> dict:
    """Create an output_delta event for progressive drawer updates."""
    return {
        "type": "output_delta",
        "phase": phase,
        "agent_id": agent_id,
        "content": content,
    }

def make_step_event(agent_id: str, step_label: str, progress: int = 1, total: int = 1) -> dict:
    """Create a per-step granular progress event for fine-grained agent activity."""
    return {
        "type": "step_progress",
        "agent_id": agent_id,
        "step": step_label,
        "progress": progress,
        "total": total,
    }

def make_cost_event(
    total_usd: float,
    session_id: str = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0,
) -> dict:
    """Create a cost update event with token breakdown."""
    return {
        "type": "cost",
        "total_usd": round(total_usd, 6),
        "session_id": session_id,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "cached_tokens": int(cached_tokens),
    }

def make_phase_writeup_event(phase: str, writeup: dict) -> dict:
    """Create a phase_writeup event carrying the Amazon-narrative writeup JSON."""
    return {
        "type": "phase_writeup",
        "phase": phase,
        "writeup": writeup,
    }


# ── HITL queue API ────────────────────────────────────────────────────────────
# Used by the orchestrator (worker thread) and `POST /sessions/:id/respond`
# (event loop). queue.Queue is thread-safe; asyncio.Queue is not.

def get_hitl_queue(session_id: str) -> "queue.Queue":
    """Get or create the HITL response queue for a session."""
    if session_id not in _hitl_queues:
        _hitl_queues[session_id] = queue.Queue()
    return _hitl_queues[session_id]

def put_hitl_response(session_id: str, response: dict) -> None:
    """Push a HITL response onto the session's queue. Called by the respond endpoint."""
    get_hitl_queue(session_id).put_nowait(response)

def wait_for_hitl_response(session_id: str, timeout_seconds: float = 30.0) -> dict | None:
    """Block until a HITL response arrives or the timeout elapses.
    Returns None on timeout (interpreted as auto-advance by the orchestrator)."""
    try:
        return get_hitl_queue(session_id).get(timeout=timeout_seconds)
    except queue.Empty:
        return None

def clear_hitl_queue(session_id: str) -> None:
    """Drop the HITL queue when a session ends, so memory doesn't accumulate."""
    _hitl_queues.pop(session_id, None)
