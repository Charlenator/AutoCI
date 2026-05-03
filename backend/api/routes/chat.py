"""Chat endpoint — wired to the Sprint B1 Query Planner + SQL Executor pipeline.

Flow:
    user query
      -> S1 QueryPlanner.plan()       (LLM decides retrieval path; emits envelope)
      -> S3 SQLExecutor.execute()     (if plan.needs_sql; runs templated or freeform SELECT)
      -> S2 RAGAgent.retrieve()       (if plan.needs_rag; vector search)
      -> _natural_reply()             (LLM rewrites the structured results into a
                                       human-readable answer; B2 follow-up)
      -> compose response             (returned to frontend; includes the plan envelope so the
                                       Query Transformation Card can render it)
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.agents.specialists.s1_query_planner import QueryPlannerAgent
from api.agents.specialists.s2_rag import RAGAgent
from api.agents.specialists.s3_sql_executor import SQLExecutor

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    context: dict = {}


class ChatResponse(BaseModel):
    reply: str
    plan: dict | None = None
    sql_result: dict | None = None
    rag_chunks: list[dict] | None = None
    sources: list[str] = []  # legacy field kept for back-compat with current dashboard code


# Cap how many SQL rows / RAG chunks we send back so a single API call can't
# accidentally ship megabytes of data.
_SQL_ROW_PREVIEW_LIMIT = 50
_EVIDENCE_ROW_PREVIEW_LIMIT = 100
_RAG_CHUNK_LIMIT = 5


@router.post("/query", response_model=ChatResponse)
async def chat_query(body: ChatRequest, request: Request):
    """Natural-language query endpoint. Returns the planner envelope + retrieval results."""
    try:
        llm = request.state.llm
        supabase = request.state.supabase

        planner = QueryPlannerAgent(llm)
        plan = planner.plan(body.message, session_id=body.session_id)

        sql_payload: dict | None = None
        rag_chunks_payload: list[dict] | None = None

        # ---- SQL path ----
        if plan.needs_sql:
            executor = SQLExecutor(supabase)
            result = executor.execute(plan)
            preview_rows = result.rows[:_SQL_ROW_PREVIEW_LIMIT]
            evidence_preview = result.evidence_rows[:_EVIDENCE_ROW_PREVIEW_LIMIT]
            sql_payload = {
                "template_id": result.template_id,
                "sql": result.sql,
                "row_count": result.row_count,
                "rows": preview_rows,
                "error": result.error,
                "evidence_sql": result.evidence_sql,
                "evidence_rows": evidence_preview,
                "evidence_row_count": result.evidence_row_count,
                "evidence_error": result.evidence_error,
            }

        # ---- RAG path ----
        if plan.needs_rag:
            rag_agent = RAGAgent(supabase)
            rag_query = plan.rag_query or body.message
            rag_result = rag_agent.retrieve(rag_query, top_k=_RAG_CHUNK_LIMIT)
            chunks = getattr(rag_result, "chunks", None) or []
            rag_chunks_payload = [
                {
                    "chunk_id": c.get("chunk_id"),
                    "corpus_name": c.get("corpus_name"),
                    "chunk_text": c.get("chunk_text"),
                    "similarity": c.get("similarity"),
                    "metadata": c.get("metadata"),
                }
                for c in chunks
            ]

        reply = _natural_reply(
            llm,
            user_query=body.message,
            plan=plan,
            sql_payload=sql_payload,
            rag_chunks=rag_chunks_payload,
            session_id=body.session_id,
        )
        legacy_sources = _legacy_sources(sql_payload, rag_chunks_payload)

        return ChatResponse(
            reply=reply,
            plan=plan.to_envelope(),
            sql_result=sql_payload,
            rag_chunks=rag_chunks_payload,
            sources=legacy_sources,
        )

    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Chat error: {exc}") from exc


# ---------------------------------------------------------------------------
# Reply composition — natural-language wrapper over the structured results
# ---------------------------------------------------------------------------

_NATURAL_REPLY_SYSTEM_PROMPT = """You are a recruitment-analytics assistant. The user asked a question. The structured retrieval results that answer it are below.

Write a concise, natural-language answer that:
- States the actual numbers from the results, with units (days / %% / ZAR / count).
- Phrases the answer as if speaking to a recruiter — not as a SQL recap.
- Stays 1-3 sentences unless the data legitimately needs more.
- Does NOT explain methodology, mention SQL, mention "templates", or speculate beyond the data.
- If the result is empty or errored, says so plainly without making up information.
- Does NOT include a leading sentence like "Here is the answer:" — just give the answer.
- Does NOT add inline citation markers like [1] or [2] — the frontend renders citation chips separately.
"""


def _natural_reply(
    llm,
    *,
    user_query: str,
    plan,
    sql_payload: dict | None,
    rag_chunks: list[dict] | None,
    session_id: str | None,
) -> str:
    """Ask the LLM to phrase the structured results as a human answer.

    Falls back to a deterministic compose if the LLM call fails — the user
    still gets *something*, even if it's the older key=value style.
    """
    formatted = _format_results_for_llm(sql_payload, rag_chunks)
    if not formatted.strip():
        if plan.fallback_reason:
            return f"I couldn't find anything relevant ({plan.fallback_reason})."
        return "I couldn't find anything relevant. Try rephrasing the question."

    user_block = (
        f"User question:\n{user_query}\n\n"
        f"Retrieval results:\n{formatted}\n\n"
        "Natural-language answer:"
    )

    try:
        content, _log = llm.route(
            "dmaic_narrative",
            [
                {"role": "system", "content": _NATURAL_REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_block},
            ],
            session_id=session_id,
            from_agent="chat_query",
            to_agent="t3_llm",
        )
        text = (content or "").strip()
        if text:
            return text
    except Exception:
        # fall through to deterministic compose
        pass

    return _deterministic_compose(plan, sql_payload, rag_chunks)


def _format_results_for_llm(
    sql_payload: dict | None,
    rag_chunks: list[dict] | None,
) -> str:
    """Compact, prompt-friendly summary of the structured results."""
    parts: list[str] = []

    if sql_payload:
        if sql_payload.get("error"):
            parts.append(f"SQL execution failed: {sql_payload['error']}")
        else:
            template_id = sql_payload.get("template_id")
            label = f"validated template '{template_id}'" if template_id else "freeform SELECT"
            row_count = sql_payload.get("row_count", 0)
            rows = sql_payload.get("rows", [])
            if row_count == 0:
                parts.append(f"SQL ({label}) returned 0 rows.")
            else:
                preview = rows[: min(10, row_count)]
                rows_json = json.dumps(preview, default=str, indent=None)
                parts.append(
                    f"SQL ({label}) returned {row_count} row{'s' if row_count != 1 else ''}: {rows_json}"
                )

    if rag_chunks:
        for i, c in enumerate(rag_chunks, start=1):
            corpus = c.get("corpus_name", "knowledge")
            text = (c.get("chunk_text") or "")[:400]
            sim = c.get("similarity")
            sim_s = f" sim={sim:.2f}" if isinstance(sim, (float, int)) else ""
            parts.append(f"[RAG #{i} {corpus}{sim_s}] {text}")

    return "\n\n".join(parts)


def _deterministic_compose(
    plan,
    sql_payload: dict | None,
    rag_chunks: list[dict] | None,
) -> str:
    """Last-resort reply when the LLM call fails."""
    bits: list[str] = []
    if plan.explanation:
        bits.append(plan.explanation)
    if sql_payload and not sql_payload.get("error"):
        rc = sql_payload.get("row_count", 0)
        bits.append(f"({rc} structured row{'s' if rc != 1 else ''} returned)")
    if rag_chunks:
        bits.append(f"({len(rag_chunks)} knowledge chunk{'s' if len(rag_chunks) != 1 else ''} retrieved)")
    return " ".join(bits) if bits else "No retrieval path produced a result."


def _legacy_sources(sql_payload: dict | None, rag_chunks: list[dict] | None) -> list[str]:
    """Backwards-compatible string list of sources for the existing dashboard UI."""
    sources: list[str] = []
    if sql_payload and sql_payload.get("template_id"):
        sources.append(f"SQL template: {sql_payload['template_id']}")
    elif sql_payload and sql_payload.get("sql"):
        sql = sql_payload["sql"].strip().replace("\n", " ")
        sources.append(f"SQL: {sql[:160]}{'...' if len(sql) > 160 else ''}")
    for chunk in rag_chunks or []:
        corpus = chunk.get("corpus_name", "knowledge")
        sources.append(f"RAG: {corpus}")
    return sources
