# AutoCI RAG Chat System

## Overview

The chat system (`POST /chat/query`) lets you ask natural-language questions about your recruitment pipeline. It uses a **two-step routing pipeline**:

```
User Query → S1 Translation Agent (classify intent) → either S3 SQL Agent or S2 RAG Agent → Response
```

## How It Works

### Step 1: Intent Classification (S1 Translation Agent)

The Translation Agent analyzes your query and routes it:

| Agent Routed To | Trigger Keywords | Example Query |
|---|---|---|
| `s3_sql` | "time to fill", "conversion", "pipeline", "drop-off", "cost per hire", "source", "yield", "trend", "count", "average" | "What is the time to fill for Senior Java Dev?" |
| `s2_rag` | All other queries — searches knowledge base or falls back to direct LLM | "How does AutoCI handle gap analysis?" |

### Step 2a: SQL Agent (for metric/pipeline queries)

When routed to `s3_sql`, the system:

1. Fetches live data from **6 Supabase tables**: `roles`, `candidates`, `pipeline_events`, `hires`, `offer_outcomes`
2. Computes standard recruitment metrics using the **MCP Analytics Library** (T1): TTF, conversion rates, source yield, cost metrics
3. For novel metrics, generates SQL via **DeepSeek Chat** (T3 LLM) and executes it

### Step 2b: RAG Agent (for knowledge queries)

When routed to `s2_rag`, the system:

1. Searches the `corpus_chunks` table using **pgvector** (or text search fallback)
2. Returns up to 5 matching chunks (truncated to 4000 chars)
3. If no chunks found, falls back to **DeepSeek Chat** with database schema context

## Example Queries

```
# Metric queries (SQL route)
"Time to fill for Senior Java Developer"
"Conversion rate from screening to interview"
"Pipeline drop-off by source"
"Cost per hire for Q1"
"Benchmark comparison for time to fill"

# Knowledge queries (RAG route)
"What is SIPOC?"
"How does Five Whys analysis work?"
"What tables are in the database?"
"How does AutoCI's detection layer work?"
```

## API Reference

### POST /chat/query

**Request:**
```json
{
  "session_id": "optional-uuid",
  "message": "Time to fill for Senior Java Developer",
  "context": {}
}
```

**Response:**
```json
{
  "reply": "Found these metrics: time_to_fill_days: 45, benchmark_days: 38",
  "sources": [
    "Computed from 150 pipeline events, 12 hires"
  ]
}
```

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Query  │ ──► │  S1 Translation  │ ──► │  S3 SQL Agent   │
│  /chat/query │     │  (classifier)     │     │  (metrics/SQL)  │
└──────────────┘     └──────────────────┘     └────────┬────────┘
                           │                           │
                           ▼                           ▼
                    ┌──────────────────┐     ┌─────────────────┐
                    │  S2 RAG Agent    │     │  Supabase DB    │
                    │  (vector search) │     │  (live data)    │
                    └────────┬─────────┘     └─────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  LLM Fallback    │
                    │  (DeepSeek Chat) │
                    └──────────────────┘
```

## Key Features

- **No LLM call for routing** — S1 uses keyword-based classification (fast, zero cost)
- **Live data** — metrics are computed from your actual Supabase pipeline data
- **Hybrid RAG** — pgvector search with text-search fallback
- **LLM fallback** — for queries that don't match any agent's domain
- **Session tracking** — cost logged to `agent_invocations` table per session
