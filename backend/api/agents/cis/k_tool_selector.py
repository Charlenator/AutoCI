"""K_TOOL_SELECTOR: Picks the subset of CIS tools needed per charter."""

from dataclasses import dataclass
from api.tools.t3_litellm_router import LiteLLMRouter

# ---------------------------------------------------------------------------
# Tool catalog
# ---------------------------------------------------------------------------

TOOL_CATALOG = {
    "D1": "Internal benchmarking — pull the KPI from our pipeline data.",
    "D2": "External benchmarking — Adzuna market signal.",
    "D3": "Gap analysis — quantify the delta against benchmarks.",
    "K1": "Define — frame the problem statement formally.",
    "K2": "Measure — confirm the metric definition + sample size.",
    "K3": "Analyse-host — meta-step that introduces analyse phase.",
    "K4": "Five Whys — root-cause iterative drilldown (RAG-grounded).",
    "K5": "Ishikawa — fishbone categorical cause map (RAG-grounded).",
    "K6": "Improve — generate interventions.",
    "FMEA": "FMEA — Severity × Occurrence × Detection on candidate failure modes.",
    "K_WRITEUP": "Writeup agent — runs after every multi-phase step.",
}

# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class ToolPlan:
    ordered: list[str]            # subset of TOOL_CATALOG keys, in order
    reasoning: str                 # one paragraph rendered in the UI

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are the tool selector for AutoCI's Continuous Improvement Suite.
Given the scoped charter, pick the minimal subset of tools needed to address the problem.
Return a JSON object with:
  - "ordered": a list of tool keys from the catalog, in execution order
  - "reasoning": one paragraph explaining your choice.

Heuristics:
- If target_kpi exists, ALWAYS include D1.
- If the problem mentions market / salary / candidates / current trends, include D2.
- If both D1 and D2 are present, include D3.
- K1 and K2 are cheap and almost always belong (Define + Measure).
- K3 only if the user explicitly asks for analysis OR the next step is K4/K5.
- K4 OR K5 (or both) if root-cause is the goal.
- K6 if the user wants interventions.
- FMEA if the user mentions risk / failure modes / critical paths.
- K_WRITEUP is appended after every multi-phase tool — the orchestrator handles that, not you.

Tool Catalog:
{tool_catalog}

Output ONLY the JSON object, no markdown fences:
{{
  "ordered": ["D1", "K1", ...],
  "reasoning": "..."
}}
"""

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ToolSelectorAgent:
    """Selects the right CIS tools for a given charter."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def select(self, scoping_state: "ScopingState") -> ToolPlan:
        """Pick tools based on the scoped charter."""
        import json

        # Build context from scoping state
        ctx_parts = []
        if scoping_state.problem:
            ctx_parts.append(f"Problem: {scoping_state.problem}")
        if scoping_state.scope:
            ctx_parts.append(f"Scope: {scoping_state.scope}")
        if scoping_state.requested_outcomes:
            ctx_parts.append(f"Outcomes: {', '.join(scoping_state.requested_outcomes)}")
        if scoping_state.role_title:
            ctx_parts.append(f"Role: {scoping_state.role_title}")
        if scoping_state.target_kpi:
            ctx_parts.append(f"Target KPI: {scoping_state.target_kpi}")
        if scoping_state.confidence:
            ctx_parts.append(f"Confidence: {scoping_state.confidence:.2f}")

        context = "\n".join(ctx_parts)

        # Format tool catalog for prompt
        catalog_str = "\n".join(f"  {k}: {v}" for k, v in TOOL_CATALOG.items())

        system_prompt = _SYSTEM_PROMPT.format(tool_catalog=catalog_str)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ]

        try:
            content, _log = self.llm.route(
                "k_tool_selector",
                messages,
                from_agent="k_tool_selector",
                to_agent="t3_llm",
            )
        except Exception:
            return ToolPlan(ordered=["D1", "K1", "K2", "K4", "K6"], reasoning="LLM error, using fallback.")

        # Parse JSON
        parsed = _parse_json(content)
        if not parsed:
            return ToolPlan(ordered=["D1", "K1", "K2", "K4", "K6"], reasoning="Parse error, using fallback.")

        raw_list = parsed.get("ordered", [])
        reasoning = str(parsed.get("reasoning", ""))

        # Validate: drop unknown keys, deduplicate preserving order
        seen = set()
        ordered = []
        for key in raw_list:
            if not isinstance(key, str):
                continue
            key = key.strip().upper()
            if key in TOOL_CATALOG and key not in seen:
                seen.add(key)
                ordered.append(key)

        if not ordered:
            ordered = ["D1", "K1", "K2", "K4", "K6"]
            reasoning = "Empty tool list, using default fallback."

        return ToolPlan(ordered=ordered, reasoning=reasoning)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re
import json
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)

def _parse_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    text = raw.strip()
    fence_match = _JSON_FENCE_RE.match(text)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed
