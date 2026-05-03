"""One-off: re-embed every chunk in corpus_chunks using the new T4 model.

Run after Migration 006 (the embedding column was reset to NULL when the
dimensionality changed from 1536 to 384). Idempotent — only updates rows
whose embedding is currently NULL unless --all is passed.

Usage:
    cd backend
    & "C:/autoci-venv/Scripts/Activate.ps1"
    python scripts/reembed_corpus.py            # re-embed only NULL rows
    python scripts/reembed_corpus.py --all      # force re-embed every row
    python scripts/reembed_corpus.py --batch 64 # tune batch size

Reads SUPABASE_URL + SUPABASE_SERVICE_KEY from backend/.env (auto-loaded).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Make `api.tools.t4_embeddings` importable when run as a script.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from api.tools.t4_embeddings import EmbeddingService  # noqa: E402


def get_supabase():
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Force re-embed every row, not just NULL ones.")
    parser.add_argument("--batch", type=int, default=32, help="Batch size sent to the embedding model.")
    parser.add_argument("--limit", type=int, default=None, help="Cap total rows processed (for testing).")
    args = parser.parse_args()

    print(f"[reembed] Loading embedding model (~30s on cold start) ...")
    svc = EmbeddingService()
    if not svc.available:
        print("[reembed] FATAL: embedding model failed to load. "
              "Check that sentence-transformers is installed in this venv.")
        return 1
    print(f"[reembed] Model ready. Dim={svc.dim}")

    supa = get_supabase()

    # Fetch chunks needing embeddings.
    query = supa.table("corpus_chunks").select("chunk_id,chunk_text,embedding")
    if not args.all:
        query = query.is_("embedding", "null")
    if args.limit:
        query = query.limit(args.limit)

    resp = query.execute()
    rows = resp.data or []
    print(f"[reembed] {len(rows)} chunks to process (--all={args.all}, --limit={args.limit}).")
    if not rows:
        print("[reembed] Nothing to do.")
        return 0

    total = len(rows)
    embedded = 0
    failures = 0
    t0 = time.time()

    for batch_start in range(0, total, args.batch):
        batch = rows[batch_start : batch_start + args.batch]
        texts = [r["chunk_text"] or "" for r in batch]
        vecs = svc.embed_batch(texts)
        for r, vec in zip(batch, vecs):
            if all(v == 0.0 for v in vec):
                failures += 1
                continue
            try:
                supa.table("corpus_chunks").update({"embedding": vec}).eq("chunk_id", r["chunk_id"]).execute()
                embedded += 1
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"[reembed] WARN failed to update {r['chunk_id']}: {exc}")
        elapsed = time.time() - t0
        rate = (batch_start + len(batch)) / max(elapsed, 0.001)
        print(
            f"[reembed] progress {batch_start + len(batch)}/{total} "
            f"(embedded={embedded}, failed={failures}, {rate:.1f}/s)"
        )

    print(
        f"[reembed] done in {time.time() - t0:.1f}s — "
        f"{embedded}/{total} embedded, {failures} failed."
    )
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
