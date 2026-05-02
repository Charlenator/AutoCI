"""K4: Five Whys Agent — 5 sequential atomic LLM calls, each building on the last.
Emits per-step progress via optional on_step callback."""

from dataclasses import dataclass, field
from typing import Callable, Optional
from api.tools.t3_litellm_router import LiteLLMRouter

@dataclass
class WhyChain:
    question_chain: list[str]
    answer_chain: list[str]
    causal_factors: list[str]

class K4FiveWhysAgent:
    """Executes 5 sequential why questions, each dep on previous answer."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(self, problem: str, depth: int = 5, session_id: str = None,
            on_step: Optional[Callable[[str, int, int, str], None]] = None) -> list[WhyChain]:
        """Run sequential Five Whys on the problem.
        on_step(agent_id, label, progress, total) is called after each call."""
        chains = []
        total_calls = depth * 3  # 3 perspectives × depth
        call_count = 0

        for perspective in ["process", "people", "data"]:
            q_chain, a_chain = [], []
            context = problem

            for i in range(depth):
                call_count += 1
                q = f"Why ({perspective}, #{i+1}): {context}"
                messages = [
                    {"role": "system", "content": "Answer the 'Why' question concisely based on recruitment pipeline context."},
                    {"role": "user", "content": q},
                ]
                answer, log = self.llm.route("five_whys", messages, session_id=session_id,
                                             from_agent="k4_five_whys", to_agent="t3_llm")
                q_chain.append(q)
                a_chain.append(answer.strip())
                context = answer

                if on_step:
                    on_step("K4", f"Why {i+1}/{depth} ({perspective})", call_count, total_calls)

            chains.append(WhyChain(question_chain=q_chain, answer_chain=a_chain,
                                   causal_factors=[a.split(".")[0] for a in a_chain[-2:]]))

        return chains
