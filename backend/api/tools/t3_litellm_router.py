"""T3: LiteLLM cost-aware model router.
Routes LLM calls to optimal model with cost logging to agent_invocations."""

import os
import time
import json
from typing import Literal
from litellm import completion
from dataclasses import dataclass, asdict

ModelName = Literal["deepseek-chat"]

TASK_ROUTING = {
    # Single-model pipeline: every task routes to DeepSeek.
    "five_whys": "deepseek-chat",
    "sql_generation": "deepseek-chat",
    "orchestration": "deepseek-chat",
    "dmaic_narrative": "deepseek-chat",
    "translation": "deepseek-chat",
    "research_synthesis": "deepseek-chat",
    "tagging": "deepseek-chat",
    "extraction": "deepseek-chat",
    "parsing": "deepseek-chat",
}

MODEL_CONFIG = {
    "deepseek-chat": {
        "model": "deepseek/deepseek-chat",
        "max_tokens": 4096,
    },
}

# Per-1M-token rates for client-side cost calculation. LiteLLM's `_cost` field
# returns 0.0 for `deepseek-chat` because the OpenAI-compat path we use doesn't
# trigger LiteLLM's pricing table — we compute it ourselves from the usage
# counts. Cached input is ~50% cheaper than uncached.
#
# Rates locked by Donna 2026-05-02 — keep these explicit so the dashboard cost
# ticker is predictable. Update here if DeepSeek's pricing changes.
MODEL_PRICING_USD_PER_1M = {
    "deepseek-chat": {
        "input_uncached": 0.14,
        "input_cached":   0.07,
        "output":         0.28,
    },
}


def compute_cost_usd(model_name: str, input_tokens: int, cached_tokens: int, output_tokens: int) -> float:
    """Compute the USD cost for a single LLM call from token counts.

    Returns 0.0 if the model has no pricing entry, so callers can still log the
    invocation. Cached tokens are billed at the cache-hit rate; the rest of
    input is billed at the cache-miss rate.
    """
    rates = MODEL_PRICING_USD_PER_1M.get(model_name)
    if not rates:
        return 0.0
    uncached = max(input_tokens - cached_tokens, 0)
    return (
        uncached * rates["input_uncached"]
        + cached_tokens * rates["input_cached"]
        + output_tokens * rates["output"]
    ) / 1_000_000.0

@dataclass
class InvocationLog:
    session_id: str | None
    from_agent: str
    to_agent: str
    tool_used: str = "llm"
    model_used: str = ""
    input_summary: str = ""
    output_summary: str = ""
    cost_usd: float = 0.0
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

class LiteLLMRouter:
    """Routes LLM calls based on task type with cost tracking."""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    def route(self, task: str, messages: list[dict], session_id: str | None = None,
              from_agent: str = "", to_agent: str = "", **kwargs) -> tuple[str, InvocationLog]:
        """Execute an LLM call with automatic routing and cost logging."""
        model_name = TASK_ROUTING.get(task, "deepseek-chat")
        config = MODEL_CONFIG[model_name].copy()
        config.update(kwargs)

        start = time.time()
        response = completion(messages=messages, **config)
        duration_ms = int((time.time() - start) * 1000)

        content = response.choices[0].message.content or ""
        litellm_cost = float(getattr(response, "_cost", 0.0) or 0.0)

        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
        prompt_details = getattr(usage, "prompt_tokens_details", None) if usage else None
        cached_tokens = int(getattr(prompt_details, "cached_tokens", 0) or 0) if prompt_details else 0

        # If LiteLLM didn't price the call (returns 0.0 for deepseek-chat in our setup),
        # fall back to our own per-1M rates. Don't double-count when LiteLLM does compute it.
        if litellm_cost > 0:
            cost = litellm_cost
        else:
            cost = compute_cost_usd(model_name, input_tokens, cached_tokens, output_tokens)

        log = InvocationLog(
            session_id=session_id,
            from_agent=from_agent,
            to_agent=to_agent,
            model_used=model_name,
            input_summary=json.dumps(messages)[:200],
            output_summary=content[:200],
            cost_usd=cost,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )

        if self.supabase:
            self._persist_log(log)

        return content, log

    def _persist_log(self, log: InvocationLog):
        """Write invocation log to agent_invocations table."""
        try:
            self.supabase.table("agent_invocations").insert(asdict(log)).execute()
        except Exception as e:
            print(f"Failed to persist invocation log: {e}")
