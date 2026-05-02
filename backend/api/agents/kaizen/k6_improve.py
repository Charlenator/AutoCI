"""K6: Improve Agent — Generates interventions grounded in prior case studies,
prioritised by Impact/Effort.

Phase 4.5 T2.1 (extended to K6, 2026-05-02): retrieves `kaizen_case_studies`
filtered by the root-cause framing so interventions are grounded in what
actually worked in prior Kaizens — not just LLM priors.

Also fixes a pre-existing parsing bug: the previous version assigned
Impact=Medium / Effort=Medium / Priority=55 to every intervention regardless
of what the LLM produced. Now uses a JSON-output prompt (same pattern as K7)
and extracts real impact / effort / priority per intervention."""

import json
from dataclasses import dataclass, field
from typing import Any
from api.tools.t3_litellm_router import LiteLLMRouter


SYSTEM_PROMPT = """You are a Six Sigma improvement specialist generating interventions for a Kaizen.

Inputs you receive:
- The confirmed root causes (from K4 Five Whys + K5 Ishikawa)
- The analysis findings synthesis
- Optionally: relevant case studies from prior Kaizens (cite them by R-ID when an intervention has direct precedent)

Generate 5-8 distinct, executable interventions. For each:
- title: 5-10 words, imperative voice ("Restructure Interview 2 rubric", not "We could possibly look at the rubric")
- description: 1-2 sentences. State what gets done and what changes as a result.
- impact: High | Medium | Low — *expected* effect on the target KPI. Pick the most likely outcome, not the most generous.
- effort: High | Medium | Low — implementation cost in time / coordination / risk.
- evidence_id (optional): the R-ID of a case study that supports this intervention. Omit if none applies — don't invent one.

Output: ONLY a JSON object with one key, "interventions", containing the list. No prose, no markdown fences:
{
  "interventions": [
    {"title": "...", "description": "...", "impact": "High", "effort": "Low", "evidence_id": "R3"},
    ...
  ]
}"""


@dataclass
class Intervention:
    title: str
    description: str
    impact: str  # High | Medium | Low
    effort: str  # High | Medium | Low
    priority_score: int  # 1-100, derived from impact + effort
    evidence_id: str | None = None  # R-ID of the supporting case study, if any


@dataclass
class ImproveOutput:
    interventions: list[Intervention]
    recommendation: str
    rag_citations: list[dict] = field(default_factory=list)
    """R-IDs from kaizen_case_studies retrieved before generating interventions.
    IDs are offset from K3's count so the chain stays globally consistent."""


# Impact × Effort → priority score (1-100). Higher is better.
# High impact + Low effort = obvious wins; Low impact + High effort = avoid.
PRIORITY_MATRIX = {
    ("High", "Low"):    95,
    ("High", "Medium"): 80,
    ("High", "High"):   60,
    ("Medium", "Low"):  70,
    ("Medium", "Medium"): 50,
    ("Medium", "High"): 30,
    ("Low", "Low"):     40,
    ("Low", "Medium"):  25,
    ("Low", "High"):    10,
}
VALID_IMPACT_EFFORT = {"High", "Medium", "Low"}
RAG_TOP_K = 4
RAG_CORPUS = "kaizen_case_studies"


class K6ImproveAgent:
    """Generates interventions, grounded in case studies when available, scored by Impact/Effort."""

    def __init__(self, llm_router: LiteLLMRouter, rag_agent=None):
        self.llm = llm_router
        self.rag = rag_agent

    def run(
        self,
        root_causes: str,
        analysis_findings: str,
        session_id: str | None = None,
        citation_id_offset: int = 0,
    ) -> ImproveOutput:
        """Generate prioritised interventions. `citation_id_offset` shifts R-IDs so they don't
        collide with K4/K5's citations from the analyse phase."""
        rag_block, citations = self._retrieve_case_studies(
            root_causes, analysis_findings, citation_id_offset
        )

        system = SYSTEM_PROMPT + (("\n\n" + rag_block) if rag_block else "")
        user = (
            f"Root causes:\n{root_causes}\n\n"
            f"Analysis findings:\n{analysis_findings}"
        )

        content, _log = self.llm.route(
            "dmaic_narrative",
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            session_id=session_id, from_agent="k6_improve", to_agent="t3_llm",
            temperature=0.3,
        )

        interventions = self._parse_interventions(content)
        if not interventions:
            interventions = self._fallback_intervention()

        # Recommendation = a tight summary of the top 2 picks, not the raw LLM blob.
        top = sorted(interventions, key=lambda i: i.priority_score, reverse=True)[:2]
        recommendation = (
            "Top picks: " +
            "; ".join(f"{iv.title} (Impact={iv.impact}, Effort={iv.effort}, Priority={iv.priority_score})"
                      for iv in top)
        )

        return ImproveOutput(
            interventions=interventions,
            recommendation=recommendation,
            rag_citations=citations,
        )

    def _retrieve_case_studies(
        self, root_causes: str, findings: str, offset: int
    ) -> tuple[str, list[dict]]:
        """One retrieval keyed on root causes — interventions for the same kind of
        problem usually rhyme across organisations."""
        if not self.rag:
            return "", []
        query = f"interventions and improvements for: {root_causes[:400]}"
        try:
            result = self.rag.retrieve(query, top_k=RAG_TOP_K, corpus_filter=RAG_CORPUS)
            chunks = result.chunks or []
        except Exception:
            return "", []

        if not chunks:
            return "", []

        next_id = offset + 1
        lines = ["Relevant prior interventions (cite as evidence_id when applicable):"]
        citations: list[dict] = []
        for chunk in chunks:
            text = (chunk.get("chunk_text") or chunk.get("content") or "").strip()
            snippet = text[:500].replace("\n", " ")
            lines.append(f"  R{next_id}: {snippet}")
            citations.append({
                "id": f"R{next_id}",
                "source": "rag_chunk",
                "corpus": chunk.get("corpus_name", RAG_CORPUS),
                "snippet": text[:300],
                "scope": "improve",
            })
            next_id += 1
        return "\n".join(lines), citations

    @staticmethod
    def _parse_interventions(content: str) -> list[Intervention]:
        """Parse the JSON output. Tolerates markdown fences and stray prose."""
        text = content.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return []

        raw_list = parsed.get("interventions") if isinstance(parsed, dict) else None
        if not isinstance(raw_list, list):
            return []

        interventions: list[Intervention] = []
        for raw in raw_list[:8]:
            if not isinstance(raw, dict):
                continue
            title = (raw.get("title") or "").strip()
            description = (raw.get("description") or "").strip()
            if not title or not description:
                continue
            impact = K6ImproveAgent._normalise_band(raw.get("impact"))
            effort = K6ImproveAgent._normalise_band(raw.get("effort"))
            priority = PRIORITY_MATRIX.get((impact, effort), 50)
            ev = raw.get("evidence_id")
            if isinstance(ev, str) and ev.strip():
                evidence_id = ev.strip()
            else:
                evidence_id = None
            interventions.append(Intervention(
                title=title[:80],
                description=description[:300],
                impact=impact,
                effort=effort,
                priority_score=priority,
                evidence_id=evidence_id,
            ))
        return interventions

    @staticmethod
    def _normalise_band(val: Any) -> str:
        if isinstance(val, str):
            v = val.strip().capitalize()
            if v in VALID_IMPACT_EFFORT:
                return v
        return "Medium"

    @staticmethod
    def _fallback_intervention() -> list[Intervention]:
        return [Intervention(
            title="Standardise interview feedback",
            description="Implement a structured scoring rubric so calibration is consistent across interviewers.",
            impact="High",
            effort="Low",
            priority_score=PRIORITY_MATRIX[("High", "Low")],
            evidence_id=None,
        )]
