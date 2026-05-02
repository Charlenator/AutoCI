"""K3+K4: Analyse Host — Root cause orchestration.
Initiates K4 Five Whys sequentially, then K5 Ishikawa branches in parallel.
Passes on_step callback for per-step SSE granularity."""

from dataclasses import dataclass
from typing import Callable, Optional
from api.tools.t3_litellm_router import LiteLLMRouter
from api.agents.kaizen.k4_five_whys import K4FiveWhysAgent
from api.agents.kaizen.k5_ishikawa import K5IshikawaAgent

@dataclass
class AnalyseOutput:
    root_causes: list[dict]
    ishikawa_factors: dict
    synthesised_findings: str

class K3AnalyseHostAgent:
    """Orchestrates K4 (sequential) then K5 (parallel), then synthesises."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router
        self.five_whys = K4FiveWhysAgent(llm_router)
        self.ishikawa = K5IshikawaAgent(llm_router)

    def run(self, problem_statement: str, session_id: str = None,
            on_step: Optional[Callable[[str, int, int, str], None]] = None) -> AnalyseOutput:
        """Execute K4 sequentially, then K5 parallel branches, with per-step callbacks."""
        # K4: Sequential Five Whys
        if on_step:
            on_step("K4", "Starting Five Whys (3 perspectives × 5 levels)", 0, 15)
        why_chains = self.five_whys.run(problem_statement, session_id=session_id, on_step=on_step)

        # K5: Parallel Ishikawa
        if on_step:
            on_step("K5", "Starting Ishikawa (6 parallel branches)", 0, 6)
        ishikawa_factors = self.ishikawa.run(problem_statement, session_id=session_id, on_step=on_step)

        # Synthesis
        context = f"Five Whys: {why_chains}\nIshikawa: {ishikawa_factors}"
        messages = [
            {"role": "system", "content": "Synthesise root cause findings from Five Whys and Ishikawa analysis into a concise findings summary."},
            {"role": "user", "content": context},
        ]
        if on_step:
            on_step("K3", "Synthesising root cause findings...", 1, 1)
        synthesis, log = self.llm.route("dmaic_narrative", messages, session_id=session_id,
                                        from_agent="k3_analyse_host", to_agent="t3_llm")

        root_causes = [
            {"why_chain": chain.question_chain, "causal_factors": chain.causal_factors}
            for chain in why_chains
        ]

        return AnalyseOutput(
            root_causes=root_causes,
            ishikawa_factors=ishikawa_factors,
            synthesised_findings=synthesis.strip(),
        )
