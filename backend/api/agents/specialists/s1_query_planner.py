"""S1 Query Planner — Sprint B1.

Replaces the keyword-based TranslationAgent. The Planner is an LLM-driven,
schema-aware agent that decides on a *plan* for any incoming chat query:
how to retrieve the answer (SQL template, freeform SELECT, vector RAG, or a
combination) and what to surface in the UI's Query Transformation Card.

Output schema (QueryPlan dataclass):
  - needs_sql / needs_rag         — which retrieval paths to run
  - sql_template_id / sql_template_params — preferred path: a pre-validated template
  - sql_freeform                  — fallback when no template fits
  - rag_query / rag_corpus_filter — vector retrieval params
  - explanation                   — one human-readable line for the Card
  - confidence                    — planner's self-rating, 0..1

The planner does NOT execute the plan. The chat route + the orchestrator's
`_handle_ask` hand the plan to the SQL Executor and/or the RAG Agent.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from api.agents.specialists.sql_templates import (
    TEMPLATE_REGISTRY,
    planner_template_summary,
)
from api.tools.t3_litellm_router import LiteLLMRouter


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

_LIVE_SEARCH_SOURCES = {"tavily", "news", "adzuna"}


@dataclass
class QueryPlan:
    """Structured plan for how to answer a chat query."""
    original_query: str

    needs_sql: bool = False
    sql_template_id: str | None = None
    sql_template_params: dict | None = None
    sql_freeform: str | None = None

    needs_rag: bool = False
    rag_query: str | None = None
    rag_corpus_filter: str | None = None

    # B-aug: live web/news/jobs augmentation. When set, chat.py calls S4 with
    # the listed sources, persists the results into corpus_chunks (upsert with
    # ignore_duplicates so migration 007's UNIQUE content_hash holds), then
    # re-retrieves via S2 against the freshly-augmented corpus.
    needs_live_search: bool = False
    live_search_sources: list[str] = field(default_factory=list)
    live_search_topic: str | None = None

    explanation: str = ""
    confidence: float = 0.0

    # Filled by the planner only on parse failure / fallback
    fallback_reason: str | None = None

    def to_envelope(self) -> dict:
        """JSON-serialisable form, used by the SSE `query_transformation` event."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Schema summary the LLM sees
# ---------------------------------------------------------------------------

_SCHEMA_SUMMARY = """
Tables (Postgres on Supabase):
- roles(role_id, title, department, target_ttf_days, target_conversion_rate, target_offer_acceptance_rate, opened_date, status)
- candidates(candidate_id, role_id, source_channel, applied_date, name, email, phone, skills_json, experience_summary, cv_storage_path, dedup_hash, is_duplicate, missing_fields_json, confidential, source_email_id, created_at)
- pipeline_events(event_id, candidate_id, stage, event_date, outcome, interviewer_id) -- stages: Applied | Screening | Interview 1 | Interview 2 | Offer | Hired
- hires(hire_id, candidate_id, role_id, offer_date, start_date, salary, accepted)
- offer_outcomes(offer_id, candidate_id, role_id, outcome, decline_reason)
- industry_benchmarks(role_family, region, median_ttf_days, p25_ttf_days, p75_ttf_days, conversion_rate_median, offer_acceptance_median, source_yield_median, sample_size, data_source)
- adzuna_postings(id, role_title, company, salary_min, salary_max, location, posted_date, redirect_url)
- corpus_chunks(chunk_id, corpus_name, chunk_text, metadata, embedding, confidential, created_at)
- inbound_emails(id, status, sender, subject, attachment_storage_path, classified_as_cv, candidate_id, received_at)
- kaizen_sessions, kaizen_nodes, agent_invocations -- kaizen run + cost trace tables.

Available RAG corpora (in corpus_chunks.corpus_name):
- 'dmaic_methodology'    -- Six Sigma DMAIC reference docs
- 'role_benchmarks'      -- benchmark notes per role family
- 'kaizen_case_studies'  -- prior-Kaizen case studies (use this for 'why' / root-cause questions)
- 'market_intel'         -- Tavily web search results
- 'industry_news'        -- NewsAPI articles
- 'cvs'                  -- CV chunks (CONFIDENTIAL by default; only retrievable if confidential filter is bypassed)
- 'jds'                  -- job description chunks
"""

_SYSTEM_PROMPT_TEMPLATE = """You are the Query Planner for AutoCI, a recruitment-analytics platform.
For every user message, you decide *how* the answer should be retrieved.

You have three retrieval paths:
1. **SQL templates** (preferred for any numeric/factual question). Pick a template by id and supply its params.
2. **Freeform SELECT** (use only if no template fits). Emit a single read-only SELECT statement.
3. **RAG vector retrieval** (for definitional, methodological, qualitative questions; or for searching CV / case-study text).

Use **both** SQL and RAG when the question wants a number AND context (e.g. "what's our offer acceptance and why is it low?").

You can also flag **live search**:
- Set `needs_live_search: true` when the question implies *current / recent* external information that the existing corpora are unlikely to have — e.g. "what are current market salaries", "any recent industry news on attrition", "what jobs are currently advertised for X". Otherwise leave it false.
- `live_search_sources` is a list picked from {{"tavily", "news", "adzuna"}}. Use:
    - "adzuna"  for current job postings / salary signals
    - "news"    for recent articles / events
    - "tavily"  for general web search (definitions, opinions, reports)
- `live_search_topic` is the search string (typically a 2-5 word phrase). Default to the role title or topic word if unsure.
- When you set `needs_live_search: true`, also set `needs_rag: true` so the augmented corpus is searched after fetch.

Rules — strict:
- Only emit SELECT (or WITH-CTE) statements in `sql_freeform`. Never INSERT/UPDATE/DELETE/DDL.
- Prefer templates over freeform whenever a template fits.
- Map natural-language role names to substring filters: "Java dev" -> role_title="Java Dev", "UX" -> role_title="UX Designer".
- Set confidence honestly: 0.9+ when a template fits cleanly; 0.5-0.8 if you had to interpret; <0.5 if the question is vague.
- `explanation` is one sentence in plain English describing what you did (used in the user-facing Query Transformation Card).

Schema:
{schema}

Available SQL templates:
{templates}

Output a single JSON object exactly matching this shape (no markdown fences, no extra text):
{{
  "needs_sql": bool,
  "sql_template_id": string | null,
  "sql_template_params": object | null,
  "sql_freeform": string | null,
  "needs_rag": bool,
  "rag_query": string | null,
  "rag_corpus_filter": string | null,
  "needs_live_search": bool,
  "live_search_sources": string[],
  "live_search_topic": string | null,
  "explanation": string,
  "confidence": number
}}

Examples:
User: "What's our average time to fill for Java Developers?"
{{"needs_sql": true, "sql_template_id": "time_to_fill", "sql_template_params": {{"role_title": "Java Developer"}}, "sql_freeform": null, "needs_rag": false, "rag_query": null, "rag_corpus_filter": null, "needs_live_search": false, "live_search_sources": [], "live_search_topic": null, "explanation": "Looked up the average time-to-fill metric, filtered to roles matching 'Java Developer'.", "confidence": 0.95}}

User: "What is DMAIC and how does it apply here?"
{{"needs_sql": false, "sql_template_id": null, "sql_template_params": null, "sql_freeform": null, "needs_rag": true, "rag_query": "DMAIC methodology explanation", "rag_corpus_filter": "dmaic_methodology", "needs_live_search": false, "live_search_sources": [], "live_search_topic": null, "explanation": "Routed to the DMAIC methodology corpus for a definitional answer.", "confidence": 0.9}}

User: "Why are UX candidates declining offers and what's our acceptance rate?"
{{"needs_sql": true, "sql_template_id": "offer_acceptance_rate", "sql_template_params": {{"role_title": "UX"}}, "sql_freeform": null, "needs_rag": true, "rag_query": "candidates declining offers root cause", "rag_corpus_filter": "kaizen_case_studies", "needs_live_search": false, "live_search_sources": [], "live_search_topic": null, "explanation": "Pulled the UX offer-acceptance metric and searched prior-Kaizen case studies for declining-offer root causes.", "confidence": 0.85}}

User: "What are current market salaries for senior Java developers in Cape Town?"
{{"needs_sql": false, "sql_template_id": null, "sql_template_params": null, "sql_freeform": null, "needs_rag": true, "rag_query": "senior Java developer salary Cape Town", "rag_corpus_filter": null, "needs_live_search": true, "live_search_sources": ["adzuna", "tavily"], "live_search_topic": "Senior Java Developer", "explanation": "Question asks for current external market salary data; pulling fresh Adzuna postings and a Tavily web search, then re-retrieving against the augmented corpus.", "confidence": 0.85}}
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class QueryPlannerAgent:
    """LLM-driven, schema-aware query planner. Single DeepSeek call per query."""

    def __init__(self, llm_router: LiteLLMRouter):
        self.llm = llm_router

    def plan(self, query: str, session_id: str | None = None) -> QueryPlan:
        """Produce a QueryPlan for the given user query. Falls back gracefully on LLM error or invalid JSON."""
        if not query or not query.strip():
            return _fallback(query, "empty query", route="rag")

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            schema=_SCHEMA_SUMMARY.strip(),
            templates=planner_template_summary(),
        )

        try:
            content, _log = self.llm.route(
                "translation",
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                session_id=session_id,
                from_agent="s1_query_planner",
                to_agent="t3_llm",
            )
        except Exception as exc:  # noqa: BLE001 -- LLM router can throw anything
            return _fallback(query, f"LLM error: {exc}", route="rag")

        envelope = _parse_json(content)
        if envelope is None:
            return _fallback(query, "could not parse planner JSON", route="rag")

        plan = _envelope_to_plan(query, envelope)
        plan = _sanitize_plan(plan)
        return plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _envelope_to_plan(query: str, env: dict) -> QueryPlan:
    return QueryPlan(
        original_query=query,
        needs_sql=bool(env.get("needs_sql", False)),
        sql_template_id=env.get("sql_template_id") or None,
        sql_template_params=env.get("sql_template_params") or None,
        sql_freeform=env.get("sql_freeform") or None,
        needs_rag=bool(env.get("needs_rag", False)),
        rag_query=env.get("rag_query") or None,
        rag_corpus_filter=env.get("rag_corpus_filter") or None,
        needs_live_search=bool(env.get("needs_live_search", False)),
        live_search_sources=_clean_live_sources(env.get("live_search_sources")),
        live_search_topic=(env.get("live_search_topic") or None) or None,
        explanation=str(env.get("explanation") or "").strip(),
        confidence=_clamp_confidence(env.get("confidence")),
    )


def _clean_live_sources(raw) -> list[str]:
    """Coerce the planner's `live_search_sources` field to a clean list of allowed names."""
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        name = item.strip().lower()
        if name in _LIVE_SEARCH_SOURCES and name not in out:
            out.append(name)
    return out


def _clamp_confidence(value) -> float:
    try:
        v = float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return v


def _sanitize_plan(plan: QueryPlan) -> QueryPlan:
    """Strip nonsense the LLM might emit + ensure at least one retrieval path is set."""
    # An unknown template id falls back to RAG with the original query
    if plan.sql_template_id and plan.sql_template_id not in TEMPLATE_REGISTRY:
        plan.fallback_reason = f"unknown template '{plan.sql_template_id}'; routing to RAG"
        plan.sql_template_id = None
        plan.sql_template_params = None
        plan.needs_sql = False
        plan.needs_rag = True
        plan.rag_query = plan.rag_query or plan.original_query

    # Freeform SQL must be SELECT-only — anything else gets dropped (defense in depth before the executor's regex)
    if plan.sql_freeform:
        if not _looks_like_select(plan.sql_freeform):
            plan.fallback_reason = "freeform SQL was not a SELECT; dropped"
            plan.sql_freeform = None
            if not plan.sql_template_id:
                plan.needs_sql = False

    # Final guard: if neither path is set, fall back to RAG with the original query
    if not plan.needs_sql and not plan.needs_rag:
        plan.needs_rag = True
        plan.rag_query = plan.rag_query or plan.original_query
        plan.fallback_reason = plan.fallback_reason or "no retrieval path picked; defaulted to RAG"

    if plan.needs_rag and not plan.rag_query:
        plan.rag_query = plan.original_query

    # B-aug: live-search post-conditions
    if plan.needs_live_search:
        # Default to all three sources if the planner forgot to populate the list
        if not plan.live_search_sources:
            plan.live_search_sources = ["tavily", "news", "adzuna"]
        # Default the topic to the original query when missing
        if not plan.live_search_topic:
            plan.live_search_topic = plan.original_query
        # Fetching new content is pointless unless we then retrieve it
        if not plan.needs_rag:
            plan.needs_rag = True
            plan.rag_query = plan.rag_query or plan.original_query

    return plan


_SELECT_PREFIX = re.compile(r"^\s*(SELECT|WITH)\s", re.IGNORECASE)
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(DROP|INSERT|UPDATE|DELETE|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|REPLACE|MERGE|VACUUM|REINDEX|COPY|EXECUTE|CALL)\b",
    re.IGNORECASE,
)


def _looks_like_select(sql: str) -> bool:
    if not _SELECT_PREFIX.match(sql):
        return False
    if _FORBIDDEN_KEYWORDS.search(sql):
        return False
    return True


def _fallback(query: str, reason: str, route: str = "rag") -> QueryPlan:
    plan = QueryPlan(
        original_query=query,
        needs_rag=(route == "rag"),
        rag_query=query if route == "rag" else None,
        explanation=f"Fell back to vector retrieval: {reason}.",
        confidence=0.2,
        fallback_reason=reason,
    )
    return plan


