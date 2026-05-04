"""K_SCOPING: Conversational scoping agent for Continuous Improvement Suite.

Holds a back-and-forth with the user until the charter is clear,
then emits a structured ScopingState with problem, scope, outcomes, role, KPI, confidence.
"""

from dataclasses import dataclass, field
from typing import Literal
import json
from api.tools.t3_litellm_router import LiteLLMRouter

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ScopingTurn:
    role: Literal["user", "agent"]
    message: str

@dataclass
class ScopingState:
    turns: list[ScopingTurn] = field(default_factory=list)
    problem: str | None = None
    scope: str | None = None
    requested_outcomes: list[str] | None = None
    role_title: str | None = None
    target_kpi: Literal["time_to_fill", "conversion_rate", "offer_acceptance"] | None = None
    confidence: float = 0.0
    ready: bool = False

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are scoping a continuous-improvement initiative. Hold a back-and-forth
with the user until you have enough to write a charter:
   - the problem in one sentence
   - the in/out-of-scope boundary
   - the requested outcomes (1-3 short bullet phrases)
   - the role being improved (e.g. "Senior Java Developer")
   - the primary target KPI (one of: time_to_fill, conversion_rate, offer_acceptance)
   - your confidence that the charter is correct (0..1)

After each user turn, output JSON:
  {
    "agent_message": str,         # the next thing to say to the user
    "ready": bool,                 # true if you have enough
    "problem": str|null,
    "scope": str|null,
    "requested_outcomes": [str]|null,
    "role_title": str|null,
    "target_kpi": str|null,        # one of the allowed values, or null
    "confidence": 0..1
  }

When ready=true, agent_message should be a one-line confirmation rather than another question.
"""

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ScopingAgent:
    """LLM-driven conversational scoping agent."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def step(self, state: ScopingState, user_message: str) -> ScopingState:
        """Append the user message, ask the LLM what to do next, return new state."""
        # Append user turn
        state.turns.append(ScopingTurn(role="user", message=user_message))

        # Build messages for LLM
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        for turn in state.turns:
            messages.append({"role": turn.role, "content": turn.message})

        try:
            content, _log = self.llm.route(
                "k_scoping",
                messages,
                from_agent="k_scoping",
                to_agent="t3_llm",
            )
        except Exception:
            state.turns.append(ScopingTurn(
                role="agent",
                message="Sorry, I didn't catch that. Could you rephrase?",
            ))
            state.ready = False
            state.confidence = 0.0
            return state

        # Parse JSON response
        parsed = _parse_json(content)
        if parsed is None:
            state.turns.append(ScopingTurn(
                role="agent",
                message="Sorry, I didn't catch that. Could you rephrase?",
            ))
            state.ready = False
            state.confidence = 0.0
            return state

        # Update state from parsed JSON
        if parsed.get("problem") is not None:
            state.problem = parsed["problem"]
        if parsed.get("scope") is not None:
            state.scope = parsed["scope"]
        if parsed.get("requested_outcomes") is not None:
            state.requested_outcomes = parsed["requested_outcomes"]
        if parsed.get("role_title") is not None:
            state.role_title = parsed["role_title"]
        if parsed.get("target_kpi") in ("time_to_fill", "conversion_rate", "offer_acceptance"):
            state.target_kpi = parsed["target_kpi"]
        if parsed.get("confidence") is not None:
            try:
                state.confidence = max(0.0, min(1.0, float(parsed["confidence"])))
            except (TypeError, ValueError):
                state.confidence = 0.0
        state.ready = bool(parsed.get("ready", False))

        agent_message = str(parsed.get("agent_message", "Understood."))
        state.turns.append(ScopingTurn(role="agent", message=agent_message))

        return state

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)

def _parse_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    text = raw.strip()
    fence_match = _JSON_FENCE_RE.match(text)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed