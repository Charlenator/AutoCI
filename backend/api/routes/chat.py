"""A4: Strategic discovery chatbot — wired to real agents."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from api.agents.specialists.s1_translation import TranslationAgent
from api.agents.specialists.s3_sql import SQLAgent
from api.agents.specialists.s2_rag import RAGAgent
from api.tools.t4_embeddings import EmbeddingService

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    context: dict = {}


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []


@router.post("/query", response_model=ChatResponse)
async def chat_query(body: ChatRequest, request: Request):
    """A4: Natural language query about recruitment pipeline."""
    try:
        llm = request.state.llm
        supabase = request.state.supabase

        # Step 1: Classify intent via S1 Translation (keyword-based, no LLM needed)
        translator = TranslationAgent()
        classification = translator.classify(body.message)

        reply = ""
        sources = []

        if classification.agent_routed_to == "s3_sql":
            # Step 2a: SQL Agent — fetch pipeline data and compute metrics
            sql_agent = SQLAgent(supabase, llm)

            # Fetch real pipeline data from Supabase
            roles = (supabase.table("roles").select("*").execute().data or [])
            candidates = (supabase.table("candidates").select("*").execute().data or [])
            pipeline_events = (supabase.table("pipeline_events").select("*").execute().data or [])
            hires = (supabase.table("hires").select("*").execute().data or [])
            offer_outcomes = (supabase.table("offer_outcomes").select("*").execute().data or [])

            sql_result = sql_agent.execute(
                body.message,
                session_id=body.session_id,
                pipeline_events=pipeline_events,
                hires=hires,
                candidates=candidates,
                offer_outcomes=offer_outcomes,
            )

            # Format response
            if sql_result.computed_metrics:
                metrics_str = ", ".join(f"{k}: {v}" for k, v in sql_result.computed_metrics.items())
                reply = f"Found these metrics: {metrics_str}"
                sources = [f"Computed from {len(pipeline_events)} pipeline events, {len(hires)} hires"]
            elif sql_result.sql:
                reply = f"SQL query returned {len(sql_result.data)} rows"
                sources = [f"SQL: {sql_result.sql[:200]}..."]
            else:
                reply = "I couldn't find matching metrics for that query."

        elif classification.agent_routed_to == "s2_rag":
            # Step 2b: RAG Agent — search knowledge base
            rag_agent = RAGAgent(supabase)
            rag_result = rag_agent.retrieve(body.message, top_k=5)

            if rag_result.chunks:
                reply = rag_result.context_window[:2000]
                sources = [c.get("corpus_name", "knowledge_base") for c in rag_result.chunks[:3]]
            else:
                # Fallback: direct LLM with schema context
                schema_hint = (
                    "The AutoCI recruitment database has tables: "
                    "roles, candidates, pipeline_events, hires, offer_outcomes, "
                    "keywords, industry_benchmarks, job_descriptions, posting_keywords, "
                    "interviewers, kaizen_sessions, agent_invocations, adzuna_postings, corpus_chunks. "
                    "The system runs Six Sigma DMAIC Kaizen investigations for recruitment pipeline gaps."
                )
                content, log = llm.route(
                    "dmaic_narrative",
                    [
                        {"role": "system", "content": f"You are an AutoCI analytics assistant. {schema_hint}"},
                        {"role": "user", "content": body.message},
                    ],
                    session_id=body.session_id,
                    from_agent="chat_query", to_agent="t3_llm",
                )
                reply = content

        return ChatResponse(reply=reply, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
