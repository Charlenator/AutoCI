"""GET /sources — Knowledge Sources Panel inventory (Sprint B3).

Returns the full list of structured-content sources AutoCI can answer from:
  - RAG corpora (rows in corpus_chunks, grouped by corpus_name)
  - Queryable SQL tables (the tables the Query Planner exposes)

The frontend Knowledge Sources Panel renders this so reviewers can see at a
glance that AutoCI uses well past the brief's "≥3 structured documents"
requirement.

Cached for 60s so panel opens are cheap.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


# Hardcoded human-readable metadata. Kept here (not in the DB) so it can be
# tuned for the demo without a migration. The truth-of-record for *what
# exists* still comes from live SQL queries below.
CORPUS_DESCRIPTIONS: dict[str, str] = {
    "dmaic_methodology": "Six Sigma DMAIC reference docs (overview, SIPOC, Five Whys, Kanban, TTF). Used for definitional questions.",
    "role_benchmarks": "Per-role benchmark notes (Java Developer, Product Manager, UX Designer, Data Engineer).",
    "kaizen_case_studies": "Prior-Kaizen case studies — used by K4 Five Whys and K5 Ishikawa to ground root-cause analysis in precedent.",
    "market_intel": "Tavily web search snippets cached during Kaizen runs.",
    "industry_news": "NewsAPI articles fetched during Kaizen runs.",
    "adzuna_postings": "Live job-posting bodies from Adzuna for salary/skill benchmarking.",
    "cvs": "Section-chunked candidate CVs from the inbound email pipeline. Confidential by default. (Sprint B5+)",
    "jds": "Section-chunked job descriptions. (Roadmap)",
    "inbound_emails": "Vectorized email-body summaries for non-CV inbound mail.",
    "event_summaries": "Cal.com event summaries vectorized for retrieval.",
}

# The SQL tables we surface to the Knowledge Sources Panel. This is the same
# set the Query Planner can (in principle) query against. Order matters for
# panel readability: most demo-relevant first.
TABLES: list[dict[str, str]] = [
    {"name": "roles", "description": "Job roles being recruited, with KPI targets per role."},
    {"name": "candidates", "description": "Applicants — synthetic pipeline candidates plus CV-driven applicants from the inbound pipeline."},
    {"name": "pipeline_events", "description": "Stage transitions for each candidate (Applied → Screening → Interview 1/2 → Offer → Hired)."},
    {"name": "hires", "description": "Successful hires with offer / start dates and salaries."},
    {"name": "offer_outcomes", "description": "Offer outcomes including decline reasons."},
    {"name": "industry_benchmarks", "description": "External-market benchmark medians (TTF, conversion, OAR) by role family + region."},
    {"name": "adzuna_postings", "description": "Live job postings from Adzuna with salary ranges + redirect URLs."},
    {"name": "kaizen_sessions", "description": "Kaizen run history with structured output state."},
    {"name": "agent_invocations", "description": "Per-LLM-call cost trace with token counts."},
    {"name": "inbound_emails", "description": "Queue table for the inbound CV pipeline (status: pending / processing / processed / not_cv / error)."},
]


# ---------------------------------------------------------------------------
# 60-second cache (single-process; that's fine for our scale)
# ---------------------------------------------------------------------------

_CACHE: dict[str, Any] = {"data": None, "ts": 0.0}
_CACHE_TTL_SEC = 60.0


def _cache_get() -> dict | None:
    if _CACHE["data"] is None:
        return None
    if time.time() - _CACHE["ts"] > _CACHE_TTL_SEC:
        return None
    return _CACHE["data"]


def _cache_put(data: dict) -> None:
    _CACHE["data"] = data
    _CACHE["ts"] = time.time()


# ---------------------------------------------------------------------------
# Inventory builders
# ---------------------------------------------------------------------------

def _build_corpus_inventory(supabase) -> list[dict]:
    """One row per distinct corpus_name; uses the run_select_query RPC for a
    fast aggregate scan, then a bounded sample per corpus."""
    counts_sql = """
        SELECT corpus_name,
               COUNT(*) AS chunk_count,
               COUNT(*) FILTER (WHERE confidential = true) AS confidential_count,
               COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded_count
        FROM corpus_chunks
        GROUP BY corpus_name
        ORDER BY chunk_count DESC
    """
    try:
        resp = supabase.rpc("run_select_query", {"sql_text": counts_sql}).execute()
        rows = resp.data or []
    except Exception:
        rows = []

    corpora: list[dict] = []
    for row in rows:
        name = row.get("corpus_name", "?")
        # Pull a sample of up to 3 non-confidential chunks for this corpus.
        sample_sql = f"""
            SELECT chunk_id, chunk_text, metadata
            FROM corpus_chunks
            WHERE corpus_name = '{name.replace("'", "''")}'
              AND confidential = false
            ORDER BY created_at DESC NULLS LAST
            LIMIT 3
        """
        sample_rows: list[dict] = []
        try:
            sresp = supabase.rpc("run_select_query", {"sql_text": sample_sql}).execute()
            sample_rows = sresp.data or []
        except Exception:
            sample_rows = []

        # Trim long sample text for payload size.
        for s in sample_rows:
            txt = s.get("chunk_text") or ""
            if len(txt) > 280:
                s["chunk_text"] = txt[:280] + "..."

        corpora.append({
            "name": name,
            "description": CORPUS_DESCRIPTIONS.get(name, ""),
            "chunk_count": row.get("chunk_count", 0),
            "confidential_count": row.get("confidential_count", 0),
            "embedded_count": row.get("embedded_count", 0),
            "samples": sample_rows,
        })
    return corpora


def _build_table_inventory(supabase) -> list[dict]:
    """One entry per surfaced table — row count, columns, up to 3 sample rows."""
    out: list[dict] = []
    for entry in TABLES:
        name = entry["name"]
        # Row count
        count_sql = f"SELECT COUNT(*) AS n FROM {name}"
        row_count = 0
        try:
            cresp = supabase.rpc("run_select_query", {"sql_text": count_sql}).execute()
            data = cresp.data or []
            if data:
                row_count = data[0].get("n", 0)
        except Exception:
            row_count = 0

        # Columns
        cols_sql = f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = '{name}'
            ORDER BY ordinal_position
        """
        cols: list[dict] = []
        try:
            cresp = supabase.rpc("run_select_query", {"sql_text": cols_sql}).execute()
            cols = cresp.data or []
        except Exception:
            cols = []

        # Sample rows — cap to 3 for payload size.
        sample_sql = f"SELECT * FROM {name} LIMIT 3"
        samples: list[dict] = []
        try:
            sresp = supabase.rpc("run_select_query", {"sql_text": sample_sql}).execute()
            samples = sresp.data or []
        except Exception:
            samples = []

        # Trim any string field longer than 200 chars in samples to keep the payload small.
        for s in samples:
            for k, v in list(s.items()):
                if isinstance(v, str) and len(v) > 200:
                    s[k] = v[:200] + "..."

        out.append({
            "name": name,
            "description": entry["description"],
            "row_count": row_count,
            "columns": cols,
            "samples": samples,
        })
    return out


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get("/")
def get_sources(request: Request, refresh: bool = False) -> dict:
    """Return the inventory of corpora + queryable tables.

    Cached for 60s; pass ?refresh=true to force a fresh scan.
    """
    if not refresh:
        cached = _cache_get()
        if cached is not None:
            return cached

    supabase = request.state.supabase
    payload = {
        "corpora": _build_corpus_inventory(supabase),
        "tables": _build_table_inventory(supabase),
        "as_of": int(time.time()),
        "summary": {},
    }
    payload["summary"] = {
        "corpora_count": len(payload["corpora"]),
        "tables_count": len(payload["tables"]),
        "total_chunks": sum(c.get("chunk_count", 0) for c in payload["corpora"]),
        "total_table_rows": sum(t.get("row_count", 0) for t in payload["tables"]),
    }
    _cache_put(payload)
    return payload
