"""T3: LiteLLM cost-aware model router.
Routes LLM calls to optimal model with cost logging to agent_invocations."""

import os
import time
import json
from typing import Literal
from litellm import completion
from dataclasses import dataclass, asdict

ModelName = Literal["claude-opus-4-7-thinking", "claude-sonnet-4-6", "deepseek-chat"]

TASK_ROUTING = {
    # All tasks → DeepSeek (single API key for full pipeline)
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
    "claude-opus-4-7-thinking": {
        "model": "anthropic/claude-opus-4-7-thinking",
        "max_tokens": 4096,
        "thinking": True,
    },
    "claude-sonnet-4-6": {
        "model": "anthropic/claude-sonnet-4-6",
        "max_tokens": 2048,
    },
    "deepseek-chat": {
        "model": "deepseek/deepseek-chat",
        "max_tokens": 4096,
    },
}

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

class LiteLLMRouter:
    """Routes LLM calls based on task type with cost tracking."""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    def route(self, task: str, messages: list[dict], session_id: str | None = None,
              from_agent: str = "", to_agent: str = "", **kwargs) -> tuple[str, InvocationLog]:
        """Execute an LLM call with automatic routing and cost logging."""
        model_name = TASK_ROUTING.get(task, "claude-sonnet-4-6")
        config = MODEL_CONFIG[model_name].copy()
        config.update(kwargs)

        start = time.time()
        response = completion(messages=messages, **config)
        duration_ms = int((time.time() - start) * 1000)

        content = response.choices[0].message.content or ""
        cost = getattr(response, "_cost", 0.0) or 0.0

        log = InvocationLog(
            session_id=session_id,
            from_agent=from_agent,
            to_agent=to_agent,
            model_used=model_name,
            input_summary=json.dumps(messages)[:200],
            output_summary=content[:200],
            cost_usd=cost,
            duration_ms=duration_ms,
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
