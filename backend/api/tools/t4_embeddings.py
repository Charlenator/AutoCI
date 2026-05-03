"""T4: Embedding Service — local sentence-transformers, no external API.

Migration 006 (2026-05-03) switched from OpenAI text-embedding-ada-002 (1536-d)
to BAAI/bge-small-en-v1.5 (384-d). The new model is free, runs locally, and is
roughly competitive on retrieval benchmarks.

The model is loaded lazily and cached at module level so a single process
(FastAPI server, Modal worker, re-embed script) loads it exactly once. First
call on a cold start pays ~30s; every call after is ~10ms per batch.

Usage:
    svc = EmbeddingService()
    vec = svc.embed("some text")          # -> list[float] of length 384
    vecs = svc.embed_batch(["a", "b"])     # -> list[list[float]]
"""

from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

# bge-small recommends prefixing the *query* (not docs) with a short instruction
# for retrieval tasks. We keep things simple: no prefix on docs, optional prefix
# on queries via embed_query(). Cosine similarity expects normalized vectors,
# which sentence-transformers can do for us.
QUERY_INSTRUCTION = "Represent this query for searching relevant passages: "

ZERO_EMBEDDING: list[float] = [0.0] * EMBEDDING_DIM

# Module-level singleton + load lock so concurrent first-callers don't all try
# to load the model. Subsequent calls hit the cache.
_model: Any | None = None
_model_lock = Lock()


def _load_model():
    """Lazily import sentence-transformers and load the model once per process."""
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            logger.warning(
                "[T4] sentence-transformers not installed; embeddings will be zero-vectors. "
                "Run `pip install sentence-transformers` (~500MB with torch)."
            )
            return None
        try:
            cache_dir = os.getenv("BGE_CACHE_DIR")
            kwargs = {}
            if cache_dir:
                kwargs["cache_folder"] = cache_dir
            logger.info(f"[T4] Loading {EMBEDDING_MODEL_NAME} ...")
            model = SentenceTransformer(EMBEDDING_MODEL_NAME, **kwargs)
            _model = model
            logger.info(f"[T4] Embedding model loaded ({EMBEDDING_DIM}-d).")
            return _model
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[T4] Failed to load embedding model: {exc}")
            return None


class EmbeddingService:
    """Generates 384-d normalized embeddings via BAAI/bge-small-en-v1.5.

    Falls back to zero-vectors if sentence-transformers fails to load — keeps
    downstream code from breaking. Production paths should warn loudly when
    `available=False`.
    """

    def __init__(self):
        self._model = _load_model()
        self._available = self._model is not None

    @property
    def available(self) -> bool:
        return self._available

    @property
    def dim(self) -> int:
        return EMBEDDING_DIM

    # ── Public API ──────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        """Embed a single text. Returns a 384-d vector (or zero-vector on failure)."""
        if not self._available or not text or not text.strip():
            return ZERO_EMBEDDING
        return self.embed_batch([text])[0]

    def embed_query(self, text: str) -> list[float]:
        """Embed a *query* string for retrieval. bge-small recommends a short
        instruction prefix on queries (not on indexed docs)."""
        if not self._available or not text or not text.strip():
            return ZERO_EMBEDDING
        return self.embed_batch([QUERY_INSTRUCTION + text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed many texts in one model call. Returns a list of 384-d vectors."""
        if not self._available or not texts:
            return [ZERO_EMBEDDING] * len(texts) if texts else []
        # Replace empty strings with placeholder so the model doesn't choke;
        # we'll zero them out below.
        cleaned = [(t if t and t.strip() else "[empty]") for t in texts]
        try:
            arr = self._model.encode(
                cleaned,
                normalize_embeddings=True,  # for cosine similarity
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[T4] Batch embedding failed: {exc}")
            return [ZERO_EMBEDDING] * len(texts)

        out: list[list[float]] = []
        for i, t in enumerate(texts):
            if not t or not t.strip():
                out.append(ZERO_EMBEDDING)
            else:
                out.append(arr[i].tolist())
        return out

    def is_zero_vector(self, vec: list[float]) -> bool:
        """Check if a vector is the zero placeholder."""
        return all(v == 0.0 for v in vec)
