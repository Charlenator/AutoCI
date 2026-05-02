"""K5: Ishikawa Agent — 6 sequential branch analyses (Man, Machine, Method, etc).

Phase 4.5 T2.1: each branch gets its own RAG retrieval from kaizen_case_studies
filtered by the branch's category, since 'People' issues differ structurally
from 'Process' or 'Tech' issues. Citations are returned per-branch and
aggregated into K3's output for downstream writeup citation."""

from dataclasses import dataclass, field
from typing import Callable, Optional
from api.tools.t3_litellm_router import LiteLLMRouter


@dataclass
class IshikawaBranch:
    category: str
    causes: list[str]


@dataclass
class K5Result:
    branches: dict[str, list[str]]
    rag_citations: list[dict] = field(default_factory=list)
    """Each: {id: 'R5', source: 'rag_chunk', snippet: '...', corpus: 'kaizen_case_studies', branch: 'Method (Process)'}"""


class K5IshikawaAgent:
    """Executes 6 Ishikawa branch analyses sequentially (no asyncio)."""

    BRANCHES = (
        "Man (People)", "Machine (Tools)", "Method (Process)",
        "Measurement (Data)", "Mother Nature (Environment)", "Materials (Inputs)",
    )
    RAG_TOP_K = 2
    RAG_CORPUS = "kaizen_case_studies"

    def __init__(self, llm_router: LiteLLMRouter, rag_agent=None):
        self.llm = llm_router
        self.rag = rag_agent

    def run(self, problem: str, session_id: str | None = None,
            on_step: Optional[Callable[[str, str, int, int], None]] = None,
            citation_id_offset: int = 0) -> K5Result:
        """Execute all 6 branches sequentially. `citation_id_offset` shifts the R-IDs
        so they don't collide with K4's citations when both are surfaced together."""
        branches: dict[str, list[str]] = {}
        all_citations: list[dict] = []
        next_rag_id = citation_id_offset + 1

        for idx, category in enumerate(self.BRANCHES):
            rag_block, branch_citations, next_rag_id = self._retrieve_branch_chunks(
                category, problem, next_rag_id
            )
            all_citations.extend(branch_citations)

            system = (
                f"Identify root causes in the '{category}' category for the problem. "
                "Return a comma-separated list of 2-4 causes. "
                "If the case studies below show similar causes in this category, cite them inline using R-IDs."
                + (("\n\n" + rag_block) if rag_block else "")
            )
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Problem: {problem}"},
            ]
            content, _log = self.llm.route(
                "dmaic_narrative", messages, session_id=session_id,
                from_agent="k5_ishikawa", to_agent="t3_llm",
            )
            causes = [c.strip() for c in content.split(",") if c.strip()]
            branches[category] = causes

            if on_step:
                on_step("K5", f"{category} analysed → {len(causes)} causes", idx + 1, len(self.BRANCHES))

        return K5Result(branches=branches, rag_citations=all_citations)

    def _retrieve_branch_chunks(
        self, category: str, problem: str, next_id: int
    ) -> tuple[str, list[dict], int]:
        """Retrieve top-K case studies for a single branch. Returns
        (formatted_block, citations, next_id_for_subsequent_branch)."""
        if not self.rag:
            return "", [], next_id
        query = f"{category} root causes: {problem}"
        try:
            result = self.rag.retrieve(query, top_k=self.RAG_TOP_K, corpus_filter=self.RAG_CORPUS)
            chunks = result.chunks or []
        except Exception:
            return "", [], next_id

        if not chunks:
            return "", [], next_id

        lines = [f"Relevant case studies for the {category} branch (cite as R{next_id}+):"]
        citations: list[dict] = []
        for chunk in chunks:
            text = (chunk.get("chunk_text") or chunk.get("content") or "").strip()
            snippet = text[:400].replace("\n", " ")
            lines.append(f"  R{next_id}: {snippet}")
            citations.append({
                "id": f"R{next_id}",
                "source": "rag_chunk",
                "corpus": chunk.get("corpus_name", self.RAG_CORPUS),
                "snippet": text[:300],
                "branch": category,
            })
            next_id += 1
        return "\n".join(lines), citations, next_id
