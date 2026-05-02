"""S2: RAG Retrieval Agent — Hybrid semantic search over corpus_chunks.

Uses pgvector `match_chunks` RPC for vector similarity search, with
fallback to PostgreSQL full-text search if the RPC is unavailable."""

from dataclasses import dataclass
from api.tools.t4_embeddings import EmbeddingService

@dataclass
class RAGResult:
    query: str
    chunks: list[dict]
    context_window: str  # concatenated + truncated

class RAGAgent:
    """Retrieves relevant chunks from corpus_chunks table via pgvector."""

    def __init__(self, supabase_client, embed_service: EmbeddingService | None = None):
        self.supabase = supabase_client
        self.embed = embed_service or EmbeddingService()

    def retrieve(self, query: str, top_k: int = 5, corpus_filter: str | None = None) -> RAGResult:
        """Fetch chunks matching query via semantic search.

        Steps:
          1. Embed the query via EmbeddingService
          2. Call match_chunks RPC on Supabase
          3. Fall back to text_search if RPC is missing
        """
        chunks = self._semantic_search(query, top_k, corpus_filter)

        # Fallback: keyword text search
        if not chunks:
            chunks = self._text_search(query, top_k, corpus_filter)

        context = "\n\n".join(
            c.get("chunk_text", c.get("content", "")) for c in chunks
        )[:4000]

        return RAGResult(query=query, chunks=chunks, context_window=context)

    def _semantic_search(self, query: str, top_k: int, corpus_filter: str | None) -> list[dict]:
        """pgvector cosine similarity search via match_chunks RPC."""
        if not self.embed.available:
            return []

        try:
            query_vec = self.embed.embed(query)
            if self.embed.is_zero_vector(query_vec):
                return []

            rpc_params = {
                "query_embedding": query_vec,
                "match_threshold": 0.7,
                "match_count": top_k,
            }
            if corpus_filter:
                rpc_params["corpus_filter"] = corpus_filter

            resp = self.supabase.rpc("match_chunks", rpc_params).execute()
            return resp.data or []
        except Exception as e:
            print(f"[S2] RPC match_chunks failed ({e}), falling back to text search")
            return []

    def _text_search(self, query: str, top_k: int, corpus_filter: str | None) -> list[dict]:
        """PostgreSQL full-text search fallback."""
        try:
            q = self.supabase.table("corpus_chunks").select("*").text_search(
                "chunk_text", query
            ).limit(top_k)
            if corpus_filter:
                q = q.eq("corpus_name", corpus_filter)
            resp = q.execute()
            return resp.data or []
        except Exception:
            return []
