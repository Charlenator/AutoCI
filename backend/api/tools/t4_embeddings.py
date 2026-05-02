"""T4: Embedding Service — real pgvector embeddings via OpenAI text-embedding-ada-002."""

import os
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Dimension matching corpus_chunks.embedding VECTOR(1536)
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIM = 1536

# Sentinel to detect zero/placeholder embeddings
ZERO_EMBEDDING: list[float] = [0.0] * EMBEDDING_DIM


class EmbeddingService:
    """Generates embeddings for RAG retrieval.

    Uses OpenAI text-embedding-ada-002. Falls back to zero-vector if API key
    is missing, so downstream code never breaks.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        if key:
            self.client = OpenAI(api_key=key)
            self._available = True
        else:
            self.client = None
            self._available = False
            logger.warning("[T4] OPENAI_API_KEY not set — embeddings will be zero-vectors")

    @property
    def available(self) -> bool:
        return self._available

    # ── Public API ──────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns 1536-d vector."""
        if not self._available or not text.strip():
            return ZERO_EMBEDDING
        try:
            resp = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text[:8000],  # safety truncate (ada-002 max ~8191 tokens)
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"[T4] Embedding failed: {e}")
            return ZERO_EMBEDDING

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single API call.

        Returns a list of 1536-d vectors, one per input text.
        Falls back to calling embed() individually if batch fails.
        """
        if not self._available or not texts:
            return [ZERO_EMBEDDING] * len(texts) if texts else []

        truncated = [t[:8000] for t in texts]
        valid_texts = [t for t in truncated if t.strip()]
        if not valid_texts:
            return [ZERO_EMBEDDING] * len(texts)

        try:
            resp = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=valid_texts,
            )
            # Map back to original order — mapby index in response
            result_map: dict[int, list[float]] = {}
            for idx, data in enumerate(resp.data):
                result_map[data.index] = data.embedding

            embeddings: list[list[float]] = []
            for i in range(len(texts)):
                if truncated[i].strip() and i in result_map:
                    embeddings.append(result_map[i])
                else:
                    embeddings.append(ZERO_EMBEDDING)
            return embeddings
        except Exception as e:
            logger.warning(f"[T4] Batch embedding failed ({e}), falling back to per-item")
            return [self.embed(t) for t in texts]

    def is_zero_vector(self, vec: list[float]) -> bool:
        """Check if a vector is the zero placeholder."""
        return all(v == 0.0 for v in vec)
