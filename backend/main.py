"""AutoCI FastAPI application entry point."""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from api.tools.t3_litellm_router import LiteLLMRouter
from api.workflows.o2_meta_orchestrator import MetaOrchestrator
from api.tools.t4_embeddings import EmbeddingService
from api.routes import trigger, stream, chat, metrics, rag, knowledge, sessions, sources
from api.routes.knowledge import seed_rag_corpus

load_dotenv()

app = FastAPI(title="AutoCI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared dependencies
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)
llm = LiteLLMRouter(supabase_client=supabase)
orchestrator = MetaOrchestrator(supabase, llm)


@app.on_event("startup")
async def startup():
    """Verify Supabase connectivity and pre-seed RAG corpus on startup."""
    try:
        resp = supabase.table("industry_benchmarks").select("*").limit(1).execute()
        print(f"[startup] Supabase connected — {len(resp.data)} benchmarks found")
    except Exception as e:
        print(f"[startup] WARNING: Supabase error: {e}")

    # Pre-seed RAG corpus with 3 structured documents (DMAIC, Benchmarks, Case Studies)
    try:
        embed_svc = EmbeddingService()
        seeded = await seed_rag_corpus(supabase, embed_svc)
        if seeded:
            total = sum(seeded.values())
            print(f"[startup] Seeded RAG corpus: {total} chunks across {len(seeded)} corpora")
        else:
            print("[startup] RAG corpus already seeded — skipping")
    except Exception as e:
        print(f"[startup] WARNING: RAG seed error: {e}")


# Make dependencies available to routes via app.state
@app.middleware("http")
async def inject_deps(request, call_next):
    request.state.supabase = supabase
    request.state.llm = llm
    request.state.orchestrator = orchestrator
    response = await call_next(request)
    return response


app.include_router(trigger.router, prefix="/trigger", tags=["Trigger"])
app.include_router(stream.router, prefix="/sessions", tags=["SSE"])
app.include_router(sessions.router, prefix="/sessions", tags=["HITL"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
app.include_router(sources.router, prefix="/sources", tags=["Sources"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "AutoCI"}
