"""K5: Ishikawa Agent — 6 synchronous branch analyses (Man, Machine, Method, etc).
Emits per-step progress via optional on_step callback.
Fully synchronous — no asyncio, works from any thread."""

from dataclasses import dataclass
from typing import Callable, Optional
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class IshikawaBranch:
    category: str
    causes: list[str]

class K5IshikawaAgent:
    """Executes 6 Ishikawa branch analyses sequentially (no asyncio)."""

    BRANCHES = ["Man (People)", "Machine (Tools)", "Method (Process)",
                "Measurement (Data)", "Mother Nature (Environment)", "Materials (Inputs)"]

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(self, problem: str, session_id: str = None,
            on_step: Optional[Callable[[str, int, int, str], None]] = None) -> dict[str, list[str]]:
        """Execute all 6 branches sequentially — no asyncio.
        Calls on_step(agent_id, label, progress, total) after each branch."""
        branches = {}

        for idx, category in enumerate(self.BRANCHES):
            messages = [
                {"role": "system", "content": f"Identify root causes in the '{category}' category for the problem. Return a comma-separated list of 2-4 causes."},
                {"role": "user", "content": f"Problem: {problem}"},
            ]
            content, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                          from_agent="k5_ishikawa", to_agent="t3_llm")
            causes = [c.strip() for c in content.split(",")]
            branches[category] = causes

            if on_step:
                on_step("K5", f"{category} analysed → {len(causes)} causes", idx + 1, len(self.BRANCHES))

        return branches
