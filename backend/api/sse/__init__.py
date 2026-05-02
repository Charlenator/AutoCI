"""SSE event system — pushes real-time state transitions to frontend EventSource.
Works from both sync and async callers via put_nowait."""
import asyncio
import json
from collections import deque

# In-memory event queues per session (thread-safe deques)
_session_queues: dict[str, deque] = {}

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

def make_cost_event(total_usd: float, session_id: str = None) -> dict:
    """Create a cost update event."""
    return {
        "type": "cost",
        "total_usd": round(total_usd, 6),
        "session_id": session_id,
    }
