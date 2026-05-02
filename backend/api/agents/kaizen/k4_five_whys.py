"""K4: Five Whys Agent — 5 sequential atomic LLM calls per perspective, each
building on the last.

Phase 4.5 T2.1: optionally retrieves prior Kaizen case studies from RAG once
per run() and injects them into each why-question's system prompt so the LLM
has precedent to anchor against. Citations surface as R1/R2/... and are
returned alongside the why-chains for downstream writeup citation."""

from dataclasses import dataclass, field
from typing import Callable, Optional
from api.tools.t3_litellm_router import LiteLLMRouter


@dataclass
class WhyChain:
    perspective: str
    question_chain: list[str]
    answer_chain: list[str]
    causal_factors: list[str]


@dataclass
class K4Result:
    chains: list[WhyChain]
    rag_citations: list[dict] = field(default_factory=list)
    """Each entry: {id: 'R1', source: 'rag_chunk', snippet: '...', corpus: 'kaizen_case_studies'}"""


class K4FiveWhysAgent:
    """Executes 5 sequential why questions per perspective, each dep on previous answer."""

    PERSPECTIVES = ("process", "people", "data")
    DEFAULT_DEPTH = 5
    RAG_TOP_K = 4
    RAG_CORPUS = "kaizen_case_studies"

    def __init__(self, llm_router: LiteLLMRouter, rag_agent=None):
        self.llm = llm_router
        self.rag = rag_agent  # optional — gracefully degrade if missing

    def run(self, problem: str, depth: int = DEFAULT_DEPTH, session_id: str | None = None,
            on_step: Optional[Callable[[str, str, int, int], None]] = None) -> K4Result:
        """Run sequential Five Whys × 3 perspectives.

        on_step(agent_id, label, progress, total) is called after each LLM call.
        """
        rag_block, citations = self._retrieve_case_studies(problem)

        chains: list[WhyChain] = []
        total_calls = depth * len(self.PERSPECTIVES)
        call_count = 0

        for perspective in self.PERSPECTIVES:
            q_chain, a_chain = [], []
            context = problem

            for i in range(depth):
                call_count += 1
                q = f"Why ({perspective}, #{i+1}): {context}"
                system = (
                    "Answer the 'Why' question concisely based on recruitment pipeline context. "
                    "If the case studies below are relevant, cite them inline using their R-ID "
                    "(e.g. 'similar to R2'). If none are relevant, ignore them."
                    + (("\n\n" + rag_block) if rag_block else "")
                )
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": q},
                ]
                answer, _log = self.llm.route(
                    "five_whys", messages, session_id=session_id,
                    from_agent="k4_five_whys", to_agent="t3_llm",
                )
                q_chain.append(q)
                a_chain.append(answer.strip())
                context = answer

                if on_step:
                    on_step("K4", f"Why {i+1}/{depth} ({perspective})", call_count, total_calls)

            chains.append(WhyChain(
                perspective=perspective,
                question_chain=q_chain,
                answer_chain=a_chain,
                causal_factors=[a.split(".")[0] for a in a_chain[-2:]],
            ))

        return K4Result(chains=chains, rag_citations=citations)

    def _retrieve_case_studies(self, problem: str) -> tuple[str, list[dict]]:
        """One RAG retrieval up front. Same chunks fed to all 3 perspectives."""
        if not self.rag:
            return "", []
        try:
            result = self.rag.retrieve(problem, top_k=self.RAG_TOP_K, corpus_filter=self.RAG_CORPUS)
            chunks = result.chunks or []
        except Exception:
            return "", []

        if not chunks:
            return "", []

        lines = ["Relevant prior case studies (cite as R1, R2, ... when applicable):"]
        citations: list[dict] = []
        for i, chunk in enumerate(chunks, start=1):
            text = (chunk.get("chunk_text") or chunk.get("content") or "").strip()
            snippet = text[:500].replace("\n", " ")
            lines.append(f"  R{i}: {snippet}")
            citations.append({
                "id": f"R{i}",
                "source": "rag_chunk",
                "corpus": chunk.get("corpus_name", self.RAG_CORPUS),
                "snippet": text[:300],
            })
        return "\n".join(lines), citations
