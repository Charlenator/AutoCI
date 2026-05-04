#!/usr/bin/env python3
"""Dig deeper into the metadata format mismatch."""
import json, os, sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("/Users/MAC/Desktop/VSC/TCN/AutoCI/backend/.env")
supa = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

# Check what the metadata looks like in the raw DB
r = supa.table("corpus_chunks").select("chunk_id, metadata, chunk_text").order("created_at", desc=True).limit(5).execute()
for row in r.data:
    meta = row.get("metadata")
    print(f"  chunk_id={row['chunk_id'][:8]}...")
    print(f"    metadata type={type(meta).__name__} value={meta}")
    print(f"    chunk_text={row.get('chunk_text','')[:50]}")
    
    # Try the contains on this row
    r2 = supa.table("corpus_chunks").select("chunk_id").contains("metadata", meta).execute()
    print(f"    contains(self.metadata): {len(r2.data)} rows")

# Now try to query with the exact format
r3 = supa.table("corpus_chunks").select("chunk_id", "metadata", count="exact").execute()
print(f"\nTotal rows: {r3.count if hasattr(r3, 'count') else len(r3.data)}")
print(f"Sample metadata from first row: {r3.data[0].get('metadata') if r3.data else 'N/A'}")

# Check if metadata is stored as a string vs JSONB
if r3.data:
    meta_type = type(r3.data[0].get("metadata"))
    print(f"metadata type: {meta_type}")
