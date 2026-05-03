"""Modal deployment configuration for AutoCI.

Two Modal entry-points live in this file:

  1. **fastapi_app** — wraps backend/main.py:app as an `asgi_app`. Public URL,
     reachable from the Vercel frontend via `NEXT_PUBLIC_API_URL`.

  2. **drain_inbound_queue** — scheduled job (every 2 minutes) that drains the
     pending `inbound_emails` rows through
     `api.workers.inbound_processor.process_all_pending`. The B4 stub already
     advances rows to processed/not_cv based on MIME type; B5 will fill the
     real classifier + .docx extractor + confidentiality + smart-chunking
     bodies. Either way, this scheduled function is the prod trigger that
     turns Resend → Edge Function → row inserts into actual processing.

Deploy command (run from the `backend/` directory so `requirements.txt` and
the `main` / `api` Python sources resolve):

    cd backend
    modal deploy modal_config.py

A single Modal Secret `autoci-secrets` carries every env var main.py + the
routes need at runtime (Supabase, DeepSeek, Adzuna, Tavily, NewsAPI, Resend,
cal.com). Verify with `modal secret list` before deploying. Re-deploys after
secret changes are no-cost and instant; the heavy step is the first image
build (~5-10 min for torch + sentence-transformers + the model bake below).
"""

import modal
from modal import App, Image, Secret, asgi_app

# ---------------------------------------------------------------------------
# Image: deps + bake the embedding weights so cold starts don't re-download.
# ---------------------------------------------------------------------------
# Without the run_commands bake step, every cold container pays a ~30-60s
# weight download + load before the first chat query is served. Baking the
# weights into the image at build time means cold starts are just torch
# import + model load from local disk (~5-10s).
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

image = (
    Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .run_commands(
        f"python -c 'from sentence_transformers import SentenceTransformer; "
        f"SentenceTransformer(\"{EMBEDDING_MODEL}\")'"
    )
    # main.py and the api/ package are added as importable Python source.
    # Resolved relative to the deploy cwd, so the deploy command above must
    # be run from backend/ (where main.py and api/ live as siblings).
    .add_local_python_source("main", "api")
)

app = App("autoci-backend", image=image)

# Single Modal Secret containing all 13 env vars (see module docstring).
SECRETS = [Secret.from_name("autoci-secrets")]


# ---------------------------------------------------------------------------
# 1. FastAPI app (public URL for the Vercel frontend)
# ---------------------------------------------------------------------------

@app.function(
    secrets=SECRETS,
    allow_concurrent_inputs=10,
    container_idle_timeout=300,
    timeout=600,
)
@asgi_app()
def fastapi_app():
    """Serve backend/main.py:app as a public Modal asgi_app."""
    from main import app as fastapi  # late import: runs inside the container
    return fastapi


# ---------------------------------------------------------------------------
# 2. Scheduled inbound-queue drainer
# ---------------------------------------------------------------------------

@app.function(
    secrets=SECRETS,
    schedule=modal.Period(minutes=2),
    timeout=600,
)
def drain_inbound_queue() -> dict:
    """Drain the pending inbound_emails queue every 2 minutes.

    Resend → Supabase Edge Function → INSERT inbound_emails(status='pending')
    is the upstream half of the inbound flow. This function is the downstream
    half on prod: it pulls every pending row through the inbound_processor
    and flips the status to processed / not_cv / error.
    """
    from api.workers.inbound_processor import process_all_pending

    results = process_all_pending(limit=50)
    summary = {
        "processed": sum(1 for r in results if r.final_status == "processed"),
        "not_cv":    sum(1 for r in results if r.final_status == "not_cv"),
        "errors":    sum(1 for r in results if r.final_status == "error"),
        "total":     len(results),
    }
    # Visible in the Modal dashboard logs.
    print(
        f"[drain_inbound_queue] total={summary['total']} "
        f"processed={summary['processed']} "
        f"not_cv={summary['not_cv']} "
        f"errors={summary['errors']}"
    )
    return summary
