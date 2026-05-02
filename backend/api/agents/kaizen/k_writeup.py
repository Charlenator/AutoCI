"""K_WRITEUP: Amazon-narrative writeup agent.
Runs after each DMAIC phase. Single DeepSeek call. Produces a structured
0.5-1 page narrative the user can read in the chat panel and approve / question."""

import json
from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel, Field

from api.tools.t3_litellm_router import LiteLLMRouter


SYSTEM_PROMPT = """You are an Amazon-style narrative writer for a Six Sigma Kaizen investigation.

Your job: turn a phase's structured analytical output into a tight, evidence-anchored doc — the kind of one-pager an L7 leader would actually read.

Style rules (non-negotiable):
- TL;DR is one sentence. State the answer, not the topic.
- Key findings are NOT a paraphrase of the JSON. Each finding must combine 2+ data points or contrast against prior phases / industry benchmark / live market intel.
- Hypothesis must be falsifiable — "X drives Y because Z" — and pick a side, even if confidence is moderate.
- Cite every quantitative claim. Available citation IDs:
    • kaizen_node IDs from this Kaizen (e.g. D1, D2, K2, K4)
    • salary_signal ID `S1` — D2's computed median-salary comparison vs Adzuna (single composite signal, not a raw posting)
    • adzuna_posting IDs (e.g. A1, A2) — live competitor job postings with salary
    • tavily IDs (e.g. T1, T2) — web research results
    • news IDs (e.g. N1, N2) — recent industry news articles
    • rag_chunk IDs (e.g. R1, R2) — relevant prior-Kaizen case studies retrieved by K4/K5; surfaced in `analyse.rag_citations`. Cite an R-ID when a finding has precedent in a past investigation.
- When the salary_signal (S1) is present, use IT for pay-comparison claims rather than citing individual A-postings — it's the median of many, less noisy.
- When market data CONTRADICTS or REINFORCES the internal data, name it explicitly. "Our offers at R175k are R30k below the Adzuna median (A2) — pay is the likely driver" beats a generic "compensation may matter".
- No corporate filler ("synergize", "leverage", "going forward"). No bullet-padding.
- "Open questions" are things the user could meaningfully answer in 30 seconds — not research projects.

Output format: return ONLY a JSON object matching this schema. No prose, no markdown fences:
{
  "headline": "<10 words max — what changed or what we learned>",
  "tl_dr": "<one sentence — the answer>",
  "key_findings": ["<finding 1>", "<finding 2>", "<finding 3>"],
  "hypothesis": "<falsifiable causal claim>",
  "evidence_citations": [
    {"source": "kaizen_node|adzuna_posting|tavily|news|rag_chunk", "id": "<the ID — D1, A2, T1, N1, etc.>", "snippet": "<the data point you're citing>"}
  ],
  "next_step": "<one sentence — what should happen next in the Kaizen>",
  "open_questions": ["<question for the user>"]
}"""


class EvidenceCitation(BaseModel):
    source: str = Field(description="kaizen_node | rag_chunk | adzuna_posting | news | tavily")
    id: str
    snippet: str


class WriteupSchema(BaseModel):
    headline: str
    tl_dr: str
    key_findings: list[str]
    hypothesis: str
    evidence_citations: list[EvidenceCitation] = Field(default_factory=list)
    next_step: str
    open_questions: list[str] = Field(default_factory=list)


@dataclass
class WriteupResult:
    phase: str
    headline: str
    tl_dr: str
    key_findings: list[str]
    hypothesis: str
    evidence_citations: list[dict]
    next_step: str
    open_questions: list[str]

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "headline": self.headline,
            "tl_dr": self.tl_dr,
            "key_findings": self.key_findings,
            "hypothesis": self.hypothesis,
            "evidence_citations": self.evidence_citations,
            "next_step": self.next_step,
            "open_questions": self.open_questions,
        }


class WriteupAgent:
    """Generates Amazon-narrative writeups for each DMAIC phase.

    A single call per phase keeps cost bounded and lets the writeup focus on
    synthesis rather than re-doing the analytical work. The agent receives:
      - the phase's structured JSON output
      - all prior writeups in this Kaizen (for narrative continuity)
      - the role + problem brief context
    """

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def run(
        self,
        phase: str,
        phase_output: Any,
        prior_writeups: list[dict],
        role_title: str,
        problem_brief: str | None = None,
        session_id: str | None = None,
        market_data: dict | None = None,
    ) -> WriteupResult:
        """Generate a writeup for a single completed phase.

        `market_data` (when provided) carries the S4 fetch results — Adzuna postings,
        Tavily web results, NewsAPI articles. The agent formats them with stable IDs
        (A1/A2 for Adzuna, T1/T2 for Tavily, N1/N2 for news) so the LLM can cite
        them in `evidence_citations`. Without it, writeups can still reference
        kaizen_node outputs.
        """
        prior_summary = ""
        if prior_writeups:
            lines = [f"  - {w['phase']}: {w['headline']} → {w['tl_dr']}" for w in prior_writeups]
            prior_summary = "Prior phase writeups:\n" + "\n".join(lines)

        brief_line = f"User-supplied investigation brief: {problem_brief}" if problem_brief else ""

        market_block = self._format_market_data(market_data)

        user_prompt = f"""Role under investigation: {role_title}
{brief_line}

Phase just completed: {phase.upper()}

Phase output (structured JSON):
{json.dumps(self._serialize(phase_output), indent=2, default=str)[:6000]}

{prior_summary}

{market_block}

Write the {phase.upper()} phase writeup."""

        content, _log = self.llm.route(
            "dmaic_narrative",
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            session_id=session_id,
            from_agent="K_WRITEUP",
            to_agent="t3_llm",
            temperature=0.3,
        )

        parsed = self._parse_json(content)
        validated = WriteupSchema(**parsed)
        return WriteupResult(
            phase=phase,
            headline=validated.headline,
            tl_dr=validated.tl_dr,
            key_findings=validated.key_findings,
            hypothesis=validated.hypothesis,
            evidence_citations=[c.model_dump() for c in validated.evidence_citations],
            next_step=validated.next_step,
            open_questions=validated.open_questions,
        )

    @staticmethod
    def _format_market_data(market_data: dict | None) -> str:
        """Render Adzuna / Tavily / News results as a stable-ID block the LLM can cite.

        Empty / missing market_data returns an empty string so we don't bloat the
        prompt with "no data" noise. Each entry is capped to keep the prompt tight.
        """
        if not market_data:
            return ""

        sections: list[str] = []

        # Computed signal first — this is the highest-value item, derived by D2.
        sig = market_data.get("salary_signal")
        if sig:
            status = sig.get("status")
            if status == "insufficient_data":
                sections.append(
                    f"Salary vs live market (D2-computed):\n"
                    f"  S1: insufficient data to compare — {sig.get('reason', '')}. "
                    f"Cite this gap if pay is part of your hypothesis: we cannot quantify "
                    f"market positioning without disclosed competitor salaries."
                )
            else:
                conf = " — LOW CONFIDENCE, small sample" if status == "low_confidence" else ""
                sections.append(
                    f"Salary vs live market (D2-computed){conf}:\n"
                    f"  S1: our accepted-hire median R{sig['internal_median']:,.0f} (n={sig['internal_n']}) "
                    f"vs Adzuna median R{sig['adzuna_median']:,.0f} (n={sig['adzuna_n']}) — "
                    f"{sig['delta_pct']:+.1f}% [{sig['severity']}]"
                )

        adzuna = [r for r in (market_data.get("adzuna_results") or []) if not r.get("error")][:6]
        if adzuna:
            lines = ["Live competitor postings (Adzuna):"]
            for i, r in enumerate(adzuna, start=1):
                title = (r.get("title") or "Untitled posting")[:90]
                company = r.get("company") or "Unknown company"
                smin = r.get("salary_min")
                smax = r.get("salary_max")
                if smin or smax:
                    salary = f"R{smin or '?'}–R{smax or '?'}"
                else:
                    salary = "salary not disclosed"
                lines.append(f"  A{i}: {title} @ {company} ({salary})")
            sections.append("\n".join(lines))

        tavily = [r for r in (market_data.get("tavily_results") or []) if not r.get("error")][:4]
        if tavily:
            lines = ["Web research (Tavily):"]
            for i, r in enumerate(tavily, start=1):
                title = (r.get("title") or "Untitled")[:80]
                snippet = (r.get("content") or "").strip()[:160].replace("\n", " ")
                lines.append(f"  T{i}: {title} — {snippet}")
            sections.append("\n".join(lines))

        news = [r for r in (market_data.get("news_results") or []) if not r.get("error")][:4]
        if news:
            lines = ["Recent industry news (NewsAPI):"]
            for i, r in enumerate(news, start=1):
                title = (r.get("title") or "Untitled")[:80]
                date = (r.get("publishedAt") or "")[:10]
                lines.append(f"  N{i}: ({date}) {title}")
            sections.append("\n".join(lines))

        if not sections:
            return ""
        return "Market intelligence — cite as A1/T1/N1 etc. when relevant:\n\n" + "\n\n".join(sections)

    @staticmethod
    def _serialize(obj: Any) -> Any:
        """Best-effort serialization for dataclasses + Pydantic + raw dicts."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return {k: WriteupAgent._serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
        if isinstance(obj, dict):
            return {k: WriteupAgent._serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [WriteupAgent._serialize(v) for v in obj]
        return obj

    @staticmethod
    def _parse_json(content: str) -> dict:
        """Extract the JSON object from the LLM response, tolerating markdown fences."""
        text = content.strip()
        if text.startswith("```"):
            # Strip ```json ... ``` fences
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        # First/last brace fallback for stray prose
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]
        return json.loads(text)
