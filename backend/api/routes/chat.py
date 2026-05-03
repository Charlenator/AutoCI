"""Chat endpoint — wired to the Sprint B1 Query Planner + SQL Executor pipeline.

Flow:
    user query
      -> S1 QueryPlanner.plan()       (LLM decides retrieval path; emits envelope)
      -> S3 SQLExecutor.execute()     (if plan.needs_sql; runs templated or freeform SELECT)
      -> S2 RAGAgent.retrieve()       (if plan.needs_rag; vector search)
      -> compose reply + citations    (returned to frontend; includes the plan envelope so the
                                       Query Transformation Card can render it)
"""

from __future__ import annotations

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
            sql_payload = {
                "template_id": result.template_id,
                "sql": result.sql,
                "row_count": result.row_count,
                "rows": preview_rows,
                "error": result.error,
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

        reply = _compose_reply(plan, sql_payload, rag_chunks_payload)
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
# Reply composition
# ---------------------------------------------------------------------------

def _compose_reply(plan, sql_payload: dict | None, rag_chunks: list[dict] | None) -> str:
    """Assemble a human-readable reply. Frontend will progressively replace
    this with the Query Transformation Card (B1) + Citation Drawer (B2)."""

    parts: list[str] = []

    if plan.explanation:
        parts.append(plan.explanation)

    # SQL summary
    if sql_payload:
        if sql_payload.get("error"):
            parts.append(f"SQL execution failed: {sql_payload['error']}")
        else:
            row_count = sql_payload.get("row_count", 0)
            if row_count == 0:
                parts.append("The structured query returned no rows.")
            elif row_count == 1:
                # If single-row, dump key=value for a clean answer.
                only = sql_payload["rows"][0]
                summary = ", ".join(
                    f"{k}={v}" for k, v in only.items() if v is not None
                )
                parts.append(summary)
            else:
                parts.append(f"The structured query returned {row_count} rows.")

    # RAG summary
    if rag_chunks:
        n = len(rag_chunks)
        parts.append(f"Retrieved {n} supporting chunk{'s' if n != 1 else ''} from the knowledge base.")

    if not parts:
        parts.append("No retrieval path produced a result. Try rephrasing the question.")

    return " ".join(parts)


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
