"""K3: Analyse Host — Root cause orchestration.
Initiates K4 Five Whys (sequential, 3 perspectives × 5 levels) then K5 Ishikawa
(6 sequential branches), then synthesises both into a single findings summary.

Phase 4.5 T2.1: forwards an optional RAGAgent down to K4 and K5 so each agent
can pull `kaizen_case_studies` chunks before its LLM calls. Citations bubble up
into AnalyseOutput.rag_citations so the writeup agent can reference them as R-IDs."""

from dataclasses import dataclass, field
from typing import Callable, Optional
from api.tools.t3_litellm_router import LiteLLMRouter
from api.agents.kaizen.k4_five_whys import K4FiveWhysAgent
from api.agents.kaizen.k5_ishikawa import K5IshikawaAgent


@dataclass
class AnalyseOutput:
    root_causes: list[dict]
    ishikawa_factors: dict
    synthesised_findings: str
    rag_citations: list[dict] = field(default_factory=list)
    """Aggregated R-ID citations from K4 (case studies) + K5 (branch case studies)."""


class K3AnalyseHostAgent:
    """Orchestrates K4 sequentially, then K5 sequentially, then synthesises."""

    def __init__(self, llm_router: LiteLLMRouter, rag_agent=None):
        self.llm = llm_router
        self.five_whys = K4FiveWhysAgent(llm_router, rag_agent=rag_agent)
        self.ishikawa = K5IshikawaAgent(llm_router, rag_agent=rag_agent)

    def run(self, problem_statement: str, session_id: str | None = None,
            on_step: Optional[Callable[[str, str, int, int], None]] = None) -> AnalyseOutput:
        """Execute K4, then K5, with per-step callbacks. Aggregate RAG citations."""

        if on_step:
            on_step("K4", "Starting Five Whys (3 perspectives × 5 levels)", 0, 15)
        k4_result = self.five_whys.run(problem_statement, session_id=session_id, on_step=on_step)

        # Offset K5 citation IDs by the count of K4 citations so we don't collide.
        k4_citation_count = len(k4_result.rag_citations)

        if on_step:
            on_step("K5", "Starting Ishikawa (6 branches)", 0, 6)
        k5_result = self.ishikawa.run(
            problem_statement, session_id=session_id, on_step=on_step,
            citation_id_offset=k4_citation_count,
        )

        # Synthesis prompt — pass the structured chains + branches and let DeepSeek
        # weave them together.
        why_chains_text = "\n".join(
            f"  Perspective: {c.perspective}\n    Q→A: " +
            " → ".join(f"{q.split(': ')[-1]} → {a}" for q, a in zip(c.question_chain, c.answer_chain))
            for c in k4_result.chains
        )
        ishikawa_text = "\n".join(
            f"  {cat}: {', '.join(causes)}"
            for cat, causes in k5_result.branches.items()
        )
        rag_summary = ""
        all_citations = k4_result.rag_citations + k5_result.rag_citations
        if all_citations:
            rag_summary = (
                "\n\nReference case studies cited above (you may reference them inline as R-IDs):\n"
                + "\n".join(f"  {c['id']}: {c['snippet'][:200]}" for c in all_citations)
            )

        if on_step:
            on_step("K3", "Synthesising root cause findings...", 1, 1)

        synthesis, _log = self.llm.route(
            "dmaic_narrative",
            [
                {"role": "system", "content": (
                    "Synthesise root cause findings from Five Whys and Ishikawa analysis "
                    "into a concise findings summary. Cite case study R-IDs inline when they "
                    "support a finding."
                )},
                {"role": "user", "content": (
                    f"Problem: {problem_statement}\n\n"
                    f"Five Whys (3 perspectives):\n{why_chains_text}\n\n"
                    f"Ishikawa (6 branches):\n{ishikawa_text}"
                    f"{rag_summary}"
                )},
            ],
            session_id=session_id, from_agent="k3_analyse_host", to_agent="t3_llm",
        )

        root_causes = [
            {
                "perspective": chain.perspective,
                "why_chain": chain.question_chain,
                "answer_chain": chain.answer_chain,
                "causal_factors": chain.causal_factors,
            }
            for chain in k4_result.chains
        ]

        return AnalyseOutput(
            root_causes=root_causes,
            ishikawa_factors=k5_result.branches,
            synthesised_findings=synthesis.strip(),
            rag_citations=all_citations,
        )
