"""S4: Research Agent — Fetches market intel from Tavily, NewsAPI, and Adzuna.
Rewritten as fully synchronous + persists to Supabase (adzuna_postings + corpus_chunks)."""

from dataclasses import dataclass
import os
import json
import httpx
import uuid
from typing import Callable, Optional
from api.tools.t4_embeddings import EmbeddingService, ZERO_EMBEDDING

@dataclass
class ResearchResult:
    tavily_results: list[dict]
    news_results: list[dict]
    adzuna_results: list[dict]


class ResearchAgent:
    """Multi-source research for market context (benches, trends, salary data).
    Runs synchronously — compatible with background thread executor in MetaOrchestrator."""

    def __init__(self, supabase_client=None, embed_service: EmbeddingService | None = None):
        self.supabase = supabase_client
        self.embed = embed_service or EmbeddingService()
        self.tavily_key = os.getenv("TAVILY_API_KEY", "")
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID", "default")
        self.adzuna_api_key = os.getenv("ADZUNA_API_KEY", "")

    # ── All-in-one (convenience) ──────────────────────────────

    def research(self, topic: str, role_title: str = None) -> ResearchResult:
        """Run all 3 queries synchronously."""
        query = role_title or topic
        tavily_r = self.search_tavily(query)
        news_r = self.search_news(query)
        adzuna_r = self.search_adzuna(role_title or topic)

        return ResearchResult(
            tavily_results=tavily_r if not isinstance(tavily_r, Exception) else [],
            news_results=news_r if not isinstance(news_r, Exception) else [],
            adzuna_results=adzuna_r if not isinstance(adzuna_r, Exception) else [],
        )

    # ── Individual per-API public methods (persist + return) ───

    def search_tavily(self, query: str) -> list[dict]:
        """Sync web search via Tavily API. Persists results to corpus_chunks."""
        results = self._tavily_search(query)
        if self.supabase and results and not results[0].get("error"):
            self._persist_chunks(results, corpus_name="market_intel",
                                 metadata={"source": "tavily", "topic": query})
        return results

    def search_news(self, query: str) -> list[dict]:
        """Sync news search via NewsAPI. Persists results to corpus_chunks."""
        results = self._news_search(query)
        if self.supabase and results and not results[0].get("error"):
            self._persist_chunks(results, corpus_name="industry_news",
                                 metadata={"source": "newsapi", "topic": query})
        return results

    def search_adzuna(self, role_title: str) -> list[dict]:
        """Sync job search via Adzuna. Persists to adzuna_postings + corpus_chunks."""
        results = self._adzuna_search(role_title)
        if self.supabase and results and not results[0].get("error"):
            self._persist_adzuna(results)
            self._persist_chunks(results, corpus_name="adzuna_postings",
                                 metadata={"source": "adzuna", "role": role_title})
        return results

    # ── Internal API implementations ──────────────────────────

    def _tavily_search(self, query: str) -> list[dict]:
        """Sync web search via Tavily API."""
        if not self.tavily_key:
            return [{"error": "TAVILY_API_KEY not set"}]
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": self.tavily_key, "query": query, "max_results": 5},
                )
                resp.raise_for_status()
                data = resp.json()
                return [{"title": r["title"], "url": r["url"], "content": r["content"][:200]}
                        for r in data.get("results", [])]
        except Exception as e:
            return [{"error": f"Tavily failed: {e}"}]

    def _news_search(self, query: str) -> list[dict]:
        """Sync news search via NewsAPI."""
        if not self.newsapi_key:
            return [{"error": "NEWSAPI_KEY not set"}]
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    "https://newsapi.org/v2/everything",
                    params={"q": query, "apiKey": self.newsapi_key, "pageSize": 5},
                )
                resp.raise_for_status()
                data = resp.json()
                return [{"title": a["title"], "url": a["url"], "publishedAt": a["publishedAt"],
                         "content": a.get("description", a.get("content", ""))[:200]}
                        for a in data.get("articles", [])]
        except Exception as e:
            return [{"error": f"NewsAPI failed: {e}"}]

    def _adzuna_search(self, role_title: str) -> list[dict]:
        """Sync job search via Adzuna API (South Africa region)."""
        if not (self.adzuna_app_id and self.adzuna_api_key):
            return [{"error": "ADZUNA keys not set"}]
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    "https://api.adzuna.com/v1/api/jobs/za/search/1",
                    params={
                        "app_id": self.adzuna_app_id,
                        "app_key": self.adzuna_api_key,
                        "what": role_title,
                        "results_per_page": 10,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return [{
                    "adzuna_id": str(r.get("id", "")),
                    "title": r["title"],
                    "company": r.get("company", {}).get("display_name"),
                    "location": r.get("location", {}).get("display_name"),
                    "salary_min": r.get("salary_min"),
                    "salary_max": r.get("salary_max"),
                    "salary_currency": r.get("salary_is_predicted") and "predicted" or "actual",
                    "posted_date": r.get("created"),
                    "description": r.get("description", "")[:500],
                } for r in data.get("results", [])]
        except Exception as e:
            return [{"error": f"Adzuna failed: {e}"}]

    # ── Persistence ──────────────────────────────────────────

    def _persist_adzuna(self, results: list[dict]):
        """Upsert Adzuna postings into adzuna_postings table with real embeddings."""
        # Pre-compute embeddings for all items that need inserting
        to_insert = []
        for r in results:
            if r.get("error"):
                continue
            try:
                existing = self.supabase.table("adzuna_postings") \
                    .select("posting_id").eq("adzuna_id", r["adzuna_id"]).execute()
                if existing.data:
                    continue
                to_insert.append(r)
            except Exception as e:
                print(f"[S4] Adzuna dedup error: {e}")

        if not to_insert:
            return

        # Build texts to embed
        embed_texts = []
        for r in to_insert:
            text = f"{r['title']} {r.get('company', '')} {r.get('description', '')}".strip()
            embed_texts.append(text[:8000] if text else r["title"])

        embeddings = self.embed.embed_batch(embed_texts)

        for r, emb in zip(to_insert, embeddings):
            try:
                self.supabase.table("adzuna_postings").insert({
                    "adzuna_id": r["adzuna_id"],
                    "title": r["title"],
                    "company": r.get("company"),
                    "location": r.get("location"),
                    "salary_min": r.get("salary_min"),
                    "salary_max": r.get("salary_max"),
                    "posted_date": (r.get("posted_date") or "2025-01-01")[:10],
                    "embedding": emb,
                }).execute()
            except Exception as e:
                print(f"[S4] Adzuna persist error: {e}")

    def _persist_chunks(self, results: list[dict], corpus_name: str, metadata: dict):
        """Chunk each result item into corpus_chunks for RAG retrieval with real embeddings."""
        to_insert = []
        for r in results:
            if r.get("error"):
                continue
            title = r.get("title", "")
            content = r.get("content", "") or r.get("description", "") or ""
            url = r.get("url", "")
            chunk_text = f"**{title}**\n{content}\n{'' if not url else f'Source: {url}'}"
            if not chunk_text.strip():
                continue
            to_insert.append((r, chunk_text[:2000]))

        if not to_insert:
            return

        # Batch embed all chunk texts
        texts = [t for _, t in to_insert]
        embeddings = self.embed.embed_batch(texts)

        for (r, chunk_text), emb in zip(to_insert, embeddings):
            try:
                title = r.get("title", "")
                self.supabase.table("corpus_chunks").insert({
                    "corpus_name": corpus_name,
                    "chunk_text": chunk_text,
                    "metadata": json.dumps({**metadata, "title": title}),
                    "embedding": emb,
                }).execute()
            except Exception as e:
                print(f"[S4] Chunk persist error ({corpus_name}): {e}")
