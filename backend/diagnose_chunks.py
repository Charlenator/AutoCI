#!/usr/bin/env python3
"""Diagnose why corpus_chunks upsert returns 0 rows despite pipeline claiming 7 chunks.

Possible causes to narrow down:
1. Embedding format (list[float] → supabase-py serialization issue with VECTOR(384))
2. RLS / service key issue
3. on_conflict/content_hash issue  
4. Exception swallowed silently
"""

import json
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv("/Users/MAC/Desktop/VSC/TCN/AutoCI/backend/.env")
url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not url or not key:
    print("ERROR: Missing Supabase credentials")
    sys.exit(1)

supa = create_client(url, key)

candidate_id = "6b13ac0f-d370-4c8e-b1fb-b4988d33d442"

print("=" * 60)
print("1. Direct query: what chunks exist for this candidate_id?")
print("=" * 60)

try:
    # Try different query methods
    r1 = supa.table("corpus_chunks").select("*").contains(
        "metadata", json.dumps({"candidate_id": candidate_id})
    ).execute()
    print(f"  .contains() query: {len(r1.data)} rows")

    # Also search by metadata->>candidate_id text extraction
    r2 = supa.table("corpus_chunks").select("*").filter(
        "metadata->>candidate_id", "eq", candidate_id
    ).execute()
    print(f"  metadata->> filter: {len(r2.data)} rows")

    # Count total rows
    r3 = supa.table("corpus_chunks").select("chunk_id", count="exact").execute()
    print(f"  Total corpus_chunks rows: {r3.count if hasattr(r3, 'count') else len(r3.data)}")
    
except Exception as e:
    print(f"  Query failed: {e}")

print()
print("=" * 60)
print("2. Try a direct insert with minimal fields (no embedding)")
print("=" * 60)

try:
    test_payload = {
        "corpus_name": "cvs",
        "chunk_text": "diagnostic test chunk",
        "metadata": json.dumps({"candidate_id": candidate_id, "chunk_kind": "test", "confidential": True}),
        "confidential": True,
    }
    r4 = supa.table("corpus_chunks").insert(test_payload).execute()
    print(f"  Insert (no embedding): {len(r4.data)} rows returned")
    if r4.data:
        print(f"  chunk_id: {r4.data[0].get('chunk_id')}")
        print(f"  content_hash: {r4.data[0].get('content_hash')}")
except Exception as e:
    print(f"  Insert FAILED: {e}")

print()
print("=" * 60)
print("3. Try insert with zero vector embedding (C-style list)")
print("=" * 60)

try:
    test_payload2 = {
        "corpus_name": "cvs",
        "chunk_text": "diagnostic test chunk with embedding",
        "metadata": json.dumps({"candidate_id": candidate_id, "chunk_kind": "test_emb", "confidential": True}),
        "embedding": [0.0] * 384,
        "confidential": True,
    }
    r5 = supa.table("corpus_chunks").insert(test_payload2).execute()
    print(f"  Insert (with zero embedding): {len(r5.data)} rows returned")
    if r5.data:
        print(f"  chunk_id: {r5.data[0].get('chunk_id')}")
except Exception as e:
    print(f"  Insert with embedding FAILED: {e}")

print()
print("=" * 60)
print("4. Try upsert with on_conflict=content_hash")
print("=" * 60)

try:
    test_payload3 = {
        "corpus_name": "cvs",
        "chunk_text": "diagnostic test chunk upsert",
        "metadata": json.dumps({"candidate_id": candidate_id, "chunk_kind": "test_upsert", "confidential": True}),
        "embedding": [0.0] * 384,
        "confidential": True,
    }
    r6 = supa.table("corpus_chunks").upsert(
        test_payload3,
        on_conflict="content_hash",
        ignore_duplicates=True,
    ).execute()
    print(f"  Upsert: {len(r6.data)} rows returned")
    print(f"  Response keys: {r6.data[0].keys() if r6.data else 'no data'}")
    if r6.data:
        print(f"  chunk_id: {r6.data[0].get('chunk_id')}")
except Exception as e:
    print(f"  Upsert FAILED: {e}")

print()
print("=" * 60)
print("5. Re-query to see what landed")
print("=" * 60)

try:
    r7 = supa.table("corpus_chunks").select("*").contains(
        "metadata", json.dumps({"candidate_id": candidate_id})
    ).execute()
    print(f"  .contains() query now: {len(r7.data)} rows")
    for row in r7.data[:10]:
        meta = row.get("metadata", {})
        print(f"    [{meta.get('chunk_kind', '?')}] {row.get('chunk_text', '')[:60]}... content_hash={row.get('content_hash', 'N/A')[:16]}")
except Exception as e:
    print(f"  Re-query failed: {e}")

print()
print("Done.")
