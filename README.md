# RAGcruitment Platform: Agentic Intelligence & Recruitment Operations


RAGcruitment is an intelligence platform built for modern recruitment teams who need to move faster than the market. It replaces manual screening and static spreadsheets with A fleet of smart knowledgeable AI agents connected directly to your email, calendar, internal databases, and external information. The system handles everything from inbound CV ingestion to real-time market benchmarking. By combining deep "Reasoning" capabilities with structured data verification, RAGcruitment Helps recruiters make smart decisions backed by data.

---

## 1. The Multi-Agent Orchestration Layer
The core of RAGcruitment Platform is not a single prompt, but a sophisticated **Orchestration Mesh**. Depending on the complexity of the user's request, a specialized **Router Agent** analyzes the intent and delegates tasks to a fleet of specialized sub-agents:

| Agent                           | Description                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Query Planner**              | LLM-driven planner that analyzes chat queries and decides the retrieval strategy — SQL template, freeform SELECT, RAG search, or live web augmentation. |
| **RAG Agent**                  | Hybrid semantic search over `corpus_chunks` via pgvector (cosine similarity) with full-text fallback. |
| **SQL Template Executor**               | Pre-validated SQL execution against Supabase via `run_select_query` RPC. Used by the RAG chatbot.                                                    |
| **Ad-hoc SQL Query Executor**               | when no SQL template matches, the planner generates a raw read-only SELECT statement. Re-validated by a safety-check regex before reaching the DB.
| **Research Agent**             | Fetches market intel from Tavily, NewsAPI, and Adzuna and persists to `corpus_chunks`. Used by the chat "live augmentation" path.                       |
| **CV Classifier**              | LLM-driven classifier that judges whether extracted text is a CV/resume. Used in the inbound email pipeline for candidate search.                       |
| **CV Extractor**               | Extracts structured fields (name, email, skills, experience, education) from `.docx` CVs via python-docx + LLM.                                         |
| **Confidentiality Classifier** | Classifies text as containing personal/confidential data. Defaults to `confidential=True` to prevent leakage.                                           |
| **Internal Benchmarking**      | Computes internal pipeline KPIs (TTF, stage conversions, offer acceptance rate). Only used in the Kaizen detection phase.                               |


```text 
                    ┌─────────────────────────────────────────────────────────┐
                    |   RAGcruitment Platform FRONTEND (Next.js 15)           │
                    │  ┌───────────────┬──────────────────┬────────────────┐  │
                    │  │ Hybrid Chat   │ Candidate Search │ CI Dashboard   │  │
                    │  │ (RAG + Trace) │ (SQL Analytics)  │ (DMAIC Vision) │  │
                    │  └───────────────┴──────────────────┴────────────────┘  │
                    │        Observability: Live React Flow Reasoning Graph   │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │             MODAL ORCHESTRATION MESH (FastAPI)          │
                    │  ┌───────────────────────────────────────────────────┐  │
                    │  │                 INTENT ROUTER AGENT               │  │
                    │  └──────────┬──────────────┬───────────────┬─────────┘  │
                    │             │              │               │            │
             ┌──────▼──────┐      ▼              ▼               ▼            │
             │   HYBRID    │  ┌─────────┐  ┌───────────┐  ┌──────────────┐    │
             │    QUERY    │  │ DYNAMIC │  │ SEMANTIC  │  │ TRANSLATION  │    │
             │   PLANNER   │  │ SQL GEN │  │ RAG AGENT │  │  API AGENT   │    │
             │ (Templates) │  └────┬────┘  └─────┬─────┘  └──────┬───────┘    │
             └──────┬──────┘       │             │               │            │
                    └──────────────┼───────┬─────┴───────────────┘            │
                                   │       │                                  │
                    ┌──────────────▼───────▼──────────────────────────────────┐
                    │           SUPABASE PERSISTENCE & DATA FABRIC            │
                    │  • Postgres: Relational Core (Candidates, KPIs, Logs)   │
                    │  • pgvector: Knowledge Mesh (DMAIC, Market Intel, CVs)  │
                    │  • Storage: Document Store (.docx/.pdf attachments)     │
                    └──────────────────────────────▲──────────────────────────┘
                                                   │
                                                   |                                                  
          ┌────────────────────────────────────────┴──────────────────────────┐
          │               INGESTION & EXTERNAL INTEGRATION                    │
          │  • Inbound Pipeline: Resend Webhook ──▶ Edge Function ──▶ Modal   │
          │  • Market Context: Tavily (Web) | Adzuna (Job) | NewsAPI (Trends) │
          │  • Logistics: Cal.com (Scheduling) | Resend (Outbound Comms)      │
          │  • Intelligence: DeepSeek-V3 / GPT-4o-mini                        │
          └───────────────────────────────────────────────────────────────────┘
```
---

## 2. The Hybrid Knowledge Mesh
RAGcruitment Platform operates across a dual-layer knowledge base, allowing the agents to "reason" across both structured databases and unstructured document chunks.

### **A. Structured SQL Intelligence (Postgres)**
The system maintains a high-integrity relational layer for precise analytical queries:

*   **Recruitment Pipeline:** Deep visibility into `candidates` (Structured table populated whenever a new CV is received via our inbound email webhook. ), `pipeline_events`, `hires`, and `offer_outcomes`.
*   **Market Benchmarking:** `industry_benchmarks` (TTF/OAR by region) and `adzuna_postings` for real-time salary/skill parity.
*   **Observability:** Every action is logged in `agent_invocations` (500+ traces), tracking cost, token usage, and latency for full system transparency.
*   **Automation Queue:** `inbound_emails` table manages the state of the CV processing pipeline (Pending → Processed).

### **B. Unstructured Vector Corpora (BAAI/bge-small-en-v1.5)**

For semantic depth, RAGcruitment Platform utilizes a 384-dimensional vector space:

*   **Market & News:** Real-time API calls and Cached `market_intel` and `industry_news` snippets for trend analysis.
*   **Six Sigma Core:** `dmaic_methodology` reference docs (SIPOC, Five Whys, Kanban) used to ground agent reasoning in continuous improvement principles.
*   **Institutional Memory:** `kaizen_case_studies` allowing the agent to use prior "Root Cause Analyses" as precedent for new problem-solving sessions.
*   **Role Context:** `role_benchmarks` containing deep-dive requirements for specific tech stacks (Java, Data Engineering, etc.).
*   **Applicant CV Contents** `cvs` In addition to inbound CVs' key info being stored in the structured Postgres tables, the remaining CV content is also chunked and stored in the vector database for more general semantic searches. 
      
---

## 3. Technical Stack
*   **Orchestration & Logic:** FastAPI hosted on **Modal** (Serverless Python). **LiteLLM** for provider-agnostic LLM handling. **Supabase** edge functions for CV inestion pipeline trigger. 
*   **Database & Vector:** **Supabase** (Postgres + pgvector).
*   **Frontend & Ingestion:** **Next.js 15** (Vercel) with **Resend** for email-driven triggers.
*   **Agent Intelligence:** DeepSeek-V4 via optimized system prompts and tool-calling schemas. Self-hosted **text-embedding-ada-002** model for corpus embedding (RAG). 