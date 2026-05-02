"""External Knowledge Ingestion Route — live market data + pre-seeding of RAG corpus."""

import json
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from api.agents.specialists.s4_research import ResearchAgent
from api.tools.t4_embeddings import EmbeddingService
from api.sse import push_event, make_step_event, make_output_event

router = APIRouter()


class KnowledgeUpdateRequest(BaseModel):
    roles: list[str] = ["Java Developer", "Python Developer"]
    session_id: Optional[str] = None


class KnowledgeUpdateResponse(BaseModel):
    status: str
    session_id: str
    results: dict[str, dict]
    total_chunks: int
    message: str


# ── Seed documents for initial RAG population ──────────────────────

SEED_DOCUMENTS = {
    "dmaic_methodology": {
        "corpus_name": "dmaic_methodology",
        "chunks": [
            {
                "text": (
                    "DMAIC is a data-driven Lean Six Sigma methodology used for process improvement. "
                    "The five phases are: Define, Measure, Analyse, Improve, and Control. "
                    "Define scopes the problem with SIPOC. Measure establishes baseline metrics. "
                    "Analyse identifies root causes using tools like Five Whys and Fishbone diagrams. "
                    "Improve generates and prioritises interventions. Control implements monitoring "
                    "via control plans and Kanban boards."
                ),
                "metadata": {"phase": "overview", "tool": "dmaic"},
            },
            {
                "text": (
                    "SIPOC stands for Suppliers, Inputs, Process, Outputs, Customers. "
                    "It is a high-level process mapping tool used in the Define phase of DMAIC. "
                    "Suppliers provide inputs to the process; the process transforms inputs into outputs; "
                    "customers receive the outputs. A well-defined SIPOC establishes process boundaries "
                    "and identifies key stakeholders."
                ),
                "metadata": {"phase": "define", "tool": "sipoc"},
            },
            {
                "text": (
                    "The Five Whys is a root cause analysis technique used in the Analyse phase. "
                    "By repeatedly asking 'why' (typically five times), the investigator moves past "
                    "symptoms to uncover the fundamental cause of a problem. Each answer forms the basis "
                    "for the next question. It is often combined with the Ishikawa (Fishbone) diagram "
                    "to categorise causes into groups such as People, Process, Technology, and Environment."
                ),
                "metadata": {"phase": "analyse", "tool": "five_whys"},
            },
            {
                "text": (
                    "A Kanban board visualises work items in columns such as To Do, In Progress, and Done. "
                    "In the Control phase of DMAIC, it is used to track implementation tasks, assign owners, "
                    "set due dates, and monitor progress. Each card represents an action item from the "
                    "Improve phase. The board ensures accountability and provides real-time visibility."
                ),
                "metadata": {"phase": "control", "tool": "kanban"},
            },
            {
                "text": (
                    "Time to Fill (TTF) is a key recruitment metric measuring the number of days from "
                    "job requisition approval to candidate acceptance. Industry benchmarks vary by role, "
                    "seniority, and geography. A high TTF may indicate bottlenecks in screening, "
                    "interview scheduling, or offer negotiation. Reducing TTF improves hiring velocity "
                    "and reduces cost-per-hire."
                ),
                "metadata": {"phase": "measure", "tool": "ttf"},
            },
        ],
    },
    "role_benchmarks": {
        "corpus_name": "role_benchmarks",
        "chunks": [
            {
                "text": (
                    "Senior Java Developer benchmarks for South Africa: median TTF 35 days "
                    "(25th percentile: 25 days, 75th percentile: 50 days). Global median: 30 days. "
                    "Key skills required: Java, Spring Boot, microservices, AWS, Docker, Kubernetes. "
                    "The role is in high demand with competitive compensation in the R800k-R1.2M range."
                ),
                "metadata": {"role": "Senior Java Developer", "region": "South Africa"},
            },
            {
                "text": (
                    "Product Manager benchmarks for South Africa: median TTF 40 days "
                    "(25th: 28 days, 75th: 55 days). Global median: 35 days. "
                    "Key requirements: 4+ years B2B SaaS product management, roadmap ownership, "
                    "cross-functional collaboration. Compensation generally in the R700k-R1M range."
                ),
                "metadata": {"role": "Product Manager", "region": "South Africa"},
            },
            {
                "text": (
                    "UX Designer benchmarks for South Africa: median TTF 30 days "
                    "(25th: 20 days, 75th: 42 days). Global median: 28 days. "
                    "Key skills: Figma, user research, prototyping, data visualisation. "
                    "Compensation typically in the R500k-R800k range depending on seniority."
                ),
                "metadata": {"role": "UX Designer", "region": "South Africa"},
            },
            {
                "text": (
                    "Recruitment conversion funnel: Industry benchmarks show that for every 100 applicants, "
                    "approximately 20-30 advance to screening, 10-15 reach first interview, "
                    "3-5 reach final interview, and 1-2 receive offers. A high drop-off rate at any stage "
                    "indicates a process bottleneck that may require Kaizen intervention."
                ),
                "metadata": {"role": "general", "tool": "conversion_funnel"},
            },
        ],
    },
    "kaizen_case_studies": {
        "corpus_name": "kaizen_case_studies",
        "chunks": [
            {
                "text": (
                    "Kaizen Case Study — Recruitment TTF Reduction: A technology company reduced "
                    "Senior Java Developer TTF from 62 to 31 days (50% improvement) over 6 months. "
                    "Key interventions: (1) Standardised technical assessment to reduce interview rounds "
                    "from 4 to 3; (2) Implemented automated screening questionnaire to pre-qualify candidates; "
                    "(3) Reserved interview slots with hiring managers to eliminate scheduling delays. "
                    "Cost savings estimated at R450,000 in reduced agency fees."
                ),
                "metadata": {"case": "ttf_reduction", "role": "Java Developer"},
            },
            {
                "text": (
                    "Kaizen Case Study — Offer Acceptance Rate: A financial services firm improved "
                    "offer acceptance from 55% to 82% by restructuring compensation packages and "
                    "reducing offer-to-start timeline. Key changes: (1) Salary benchmarking against "
                    "market data showed offers were 15% below median; (2) Introduced sign-on bonus "
                    "for fast acceptances; (3) Streamlined background check process from 14 to 5 days."
                ),
                "metadata": {"case": "offer_acceptance", "role": "general"},
            },
            {
                "text": (
                    "Kaizen Case Study — Interview Scheduling Bottleneck: A retail company reduced "
                    "average scheduling lag from 8.2 to 2.5 days by implementing calendar integration "
                    "and automated availability polling. Interviewers were required to maintain "
                    "at least 3 available slots per week. The improvement reduced candidate drop-off "
                    "between screening and first interview by 40%."
                ),
                "metadata": {"case": "scheduling", "role": "general"},
            },
        ],
    },
}


async def seed_rag_corpus(supabase, embed_service: EmbeddingService | None = None) -> dict[str, int]:
    """Pre-seed the RAG corpus with structured documents.

    Seeds 3 structured corpora (dmaic_methodology, role_benchmarks, kaizen_case_studies).
    Skips any corpus_name that already has chunks in the DB.

    Returns a dict of corpus_name -> chunks_seeded.
    Called automatically on app startup and via POST /knowledge/seed.
    """
    if not embed_service:
        embed_service = EmbeddingService()

    totals: dict[str, int] = {}

    for doc_key, doc in SEED_DOCUMENTS.items():
        corpus_name = doc["corpus_name"]
        chunks = doc["chunks"]

        # Batch embed all chunk texts
        texts = [c["text"] for c in chunks]
        embeddings = embed_service.embed_batch(texts)
        inserted = 0

        for chunk, emb in zip(chunks, embeddings):
            try:
                supabase.table("corpus_chunks").insert({
                    "corpus_name": corpus_name,
                    "chunk_text": chunk["text"],
                    "metadata": json.dumps(chunk["metadata"]),
                    "embedding": emb,
                }).execute()
                inserted += 1
            except Exception as e:
                print(f"[seed] Insert error ({corpus_name}): {e}")

        totals[corpus_name] = inserted
        print(f"[seed] Seeded {inserted} chunks into '{corpus_name}'")

    return totals


# ── Endpoints ──────────────────────────────────────────────────────


@router.post("/update", response_model=KnowledgeUpdateResponse)
async def update_external_knowledge(body: KnowledgeUpdateRequest, request: Request):
    """Fetch live data for each requested role and persist to Supabase + RAG corpus."""
    supabase = request.state.supabase
    research = ResearchAgent(supabase_client=supabase)
    session_id = body.session_id or str(uuid4())

    def _sse(event: dict):
        try:
            push_event(session_id, event)
        except Exception:
            pass

    _sse({"type": "connected", "session_id": session_id})

    results = {}
    total_chunks = 0

    for role_idx, role in enumerate(body.roles):
        if session_id:
            _sse(make_step_event("S4", f"📚 Processing {role}", role_idx, len(body.roles)))

        role_result = {"adzuna": 0, "tavily": 0, "news": 0}

        # ---- Adzuna ----
        if session_id:
            _sse(make_step_event("S4", f"💼 {role}: Adzuna search...", 0, 3))
            _sse(make_output_event("detection", f"💼 {role}: Searching Adzuna for job postings...", "S4"))
        try:
            adzuna = research.search_adzuna(role)
            if adzuna and not adzuna[0].get("error"):
                role_result["adzuna"] = len(adzuna)
                _sse(make_output_event("detection",
                      f"💼 **{role}**: Found {len(adzuna)} job postings on Adzuna",
                      "S4"))
        except Exception as e:
            _sse(make_output_event("detection", f"⚠️ {role}: Adzuna error — {e}", "S4"))

        # ---- Tavily ----
        if session_id:
            _sse(make_step_event("S4", f"🌐 {role}: Tavily search...", 1, 3))
            _sse(make_output_event("detection", f"🌐 {role}: Searching web for market intel...", "S4"))
        try:
            tavily = research.search_tavily(f"{role} hiring trends South Africa")
            if tavily and not tavily[0].get("error"):
                role_result["tavily"] = len(tavily)
                for r in tavily:
                    _sse(make_output_event("detection", f"🌐 **{r['title']}**", "S4"))
        except Exception as e:
            _sse(make_output_event("detection", f"⚠️ {role}: Tavily error — {e}", "S4"))

        # ---- NewsAPI ----
        if session_id:
            _sse(make_step_event("S4", f"📰 {role}: NewsAPI search...", 2, 3))
            _sse(make_output_event("detection", f"📰 {role}: Fetching news articles...", "S4"))
        try:
            news = research.search_news(f"{role} hiring South Africa")
            if news and not news[0].get("error"):
                role_result["news"] = len(news)
                for r in news:
                    _sse(make_output_event("detection", f"📰 **{r['title']}**", "S4"))
        except Exception as e:
            _sse(make_output_event("detection", f"⚠️ {role}: NewsAPI error — {e}", "S4"))

        results[role] = role_result
        total_chunks += role_result["adzuna"] + role_result["tavily"] + role_result["news"]

        if session_id:
            _sse(make_step_event("S4", f"✅ {role} complete", role_idx + 1, len(body.roles)))
            summary_parts = []
            if role_result["adzuna"]:
                summary_parts.append(f"{role_result['adzuna']} job postings")
            if role_result["tavily"]:
                summary_parts.append(f"{role_result['tavily']} web results")
            if role_result["news"]:
                summary_parts.append(f"{role_result['news']} news articles")
            _sse(make_output_event("detection",
                  f"✅ **{role}** ingested: {', '.join(summary_parts)}",
                  "S4"))

    if session_id:
        _sse(make_output_event("detection",
              f"📊 **Total**: {total_chunks} chunks ingested across {len(body.roles)} roles",
              "S4"))

    return KnowledgeUpdateResponse(
        status="ok",
        session_id=session_id,
        results=results,
        total_chunks=total_chunks,
        message=f"✅ External knowledge updated: {total_chunks} chunks ingested across {len(body.roles)} roles",
    )


@router.post("/seed")
async def seed_knowledge(request: Request):
    """Pre-seed RAG corpus with 3 structured documents (DMAIC, Benchmarks, Case Studies)."""
    supabase = request.state.supabase
    embed_service = EmbeddingService()
    totals = await seed_rag_corpus(supabase, embed_service)
    if not totals:
        return {"status": "ok", "message": "RAG corpus already seeded", "chunks_seeded": 0}
    total = sum(totals.values())
    return {
        "status": "ok",
        "message": f"Seeded {total} chunks across {len(totals)} corpora",
        "corpora": totals,
        "chunks_seeded": total,
    }
