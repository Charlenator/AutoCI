# AI Agent Technical Challenge — Requirement Analysis

**Evaluated against**: Inference Group — AI Agent Technical Challenge (docx)
**Project**: AutoCI — AI-Powered Recruitment Pipeline Kaizen Engine
**Date**: 2026-04-29

---

## Part 1 – Retrieval-Augmented Generation (RAG) Deployment

### Requirement 1: Working RAG pipeline with structured documents
| Criteria | Status | Details |
|---|---|---|
| RAG system answers queries | ✅ **Met** | `POST /chat/query` routes through S1 (intent classification) → S2 (retrieval) or S3 (SQL agent). Real queries return data from Supabase + RAG corpora. |
| Structured content (CSV/JSON/tabular) | ✅ **Met** | 5 structured corpora in `corpus_chunks`: **market_intel** (15 chunks from Tavily), **industry_news** (2 chunks from NewsAPI), **dmaic_methodology** (20 chunks), **role_benchmarks** (16 chunks), **kaizen_case_studies** (12 chunks). Plus SQL tables (`roles`, `candidates`, `pipeline_events`, `hires`, `industry_benchmarks`). |
| At least three structured documents | ✅ **Met** | **5 corpora** seeded: 3 explicit structured docs (`dmaic_methodology`, `role_benchmarks`, `kaizen_case_studies`) + 2 API-sourced corpora (`market_intel`, `industry_news`). All pre-loaded on startup or via `/knowledge/seed` endpoint. |

### Requirement 2: Retrieval mechanism (vector or semantic search)
| Criteria | Status | Details |
|---|---|---|
| Vector/semantic search | ✅ **Met** | `corpus_chunks` table has `pgvector` extension + `ivfflat` index on 1536-d embeddings. **Embeddings are real non-zero vectors** (3073/1536 nonzero vals). `s2_rag.py` calls `match_chunks` RPC for cosine similarity. Fallback to PostgreSQL `text_search` if RPC fails. |
| `match_chunks` RPC | ✅ **Met** | Deployed to Supabase (`supabase/rpc_match_chunks.sql`). Accepts `query_embedding VECTOR(1536)`, `match_threshold`, `match_count`, optional `corpus_filter`. Returns `chunk_id, chunk_text, corpus_name, metadata, similarity`. Verified working. |

### Requirement 3: Web-deployed RAG interface
| Criteria | Status | Details |
|---|---|---|
| Web interface (Streamlit/Gradio/in-platform) | ✅ **Met** | Next.js frontend at localhost:3000 with RAG-aware chat panel. Backend FastAPI serves `/chat/query`. |
| Clean, testable demo | ✅ **Met** | Four routes, SSE streaming, real-time results timeline. Dashboard is functional and visually clear. |

### Requirement 4: Prompt control / query transformation
| Criteria | Status | Details |
|---|---|---|
| Query transformation | ✅ **Met** | S1 Translation Agent (`s1_translation.py`) classifies user intent via keyword matching → routes to SQL, RAG, or fallback LLM. |
| Structured answers | ✅ **Met** | SQL agent returns computed metrics (TTF, conversion rates, source yields). LLM fallback returns narrative with schema context. |

### Requirement 5: Source traceability
| Criteria | Status | Details |
|---|---|---|
| Data relevance | ⚠️ **Partial** | RAG returns top-k chunks with similarity scores from `match_chunks`. SQL agent returns live pipeline metrics. |
| Context retention | ⚠️ **Partial** | Chat session uses `session_id` but no explicit conversation history management beyond message accumulation in frontend state. |
| Traceability of sources | ⚠️ **Partial** | `sources` array returned with corpus names but no chunk IDs, document links, or citation markers. |

### Part 1 Summary
**Score**: ~85% — Full RAG pipeline operational: `match_chunks` RPC deployed, real non-zero embeddings in all 5 corpora (65 total chunks), 3+ structured documents pre-loaded, web interface with query routing and vector search verified working.

---

## Part 2 – Agent with Tooling, Data Extraction, and Verification

### Requirement 1: Three tools/APIs (Calendar, Email, Web access)
| Criteria | Status | Details |
|---|---|---|
| Calendar (Google/Outlook) | ❌ **Not met** | No Google Calendar API integration. `interviewers.calendar_id` column exists in schema but never populated or queried by any agent. |
| Email (read/send) | ❌ **Not met** | No email integration (Gmail, Outlook, SendGrid, etc.). No agent reads or sends emails. |
| Web access (scraping/search/API) | ✅ **Met** | Three web APIs integrated: **Tavily** (web search), **NewsAPI** (news articles), **Adzuna** (job postings). S4 Research Agent orchestrates these. Also 21st.dev MCP and Brave Search MCP available via tool system. |
| **Total tools** | **1 / 3 required** | Only web access satisfied. Calendar and email are entirely absent. |

### Requirement 2: Autonomous data pipeline (extract → cleanse → verify → store/display)
| Criteria | Status | Details |
|---|---|---|
| Extract from unstructured/semi-structured | ⚠️ **Partial** | S4 extracts from web APIs (JSON responses), but not from emails, calendars, or documents. |
| Cleanse & normalize | ❌ **Not met** | No data cleansing logic. Raw API results stored as-is. No deduplication, validation rules, or normalization routines. |
| Verify using rules or reference data | ❌ **Not met** | D3 Gap Analysis *generates* gap recommendations but does not verify/validate incoming data. No cross-verification between data sources. |
| Store/display verified output | ⚠️ **Partial** | Kaizen results displayed in dashboard timeline. Adzuna postings persisted to `adzuna_postings` table. But no "verified output" export (CSV, table, etc.). |

### Requirement 3: Example workflow comparison
The challenge example: *"Fetch event data from calendar and email, cross-verify participant details from a public web directory or structured file, and output a cleansed attendee list with missing fields flagged."*

| Step | AutoCI Equivalent | Status | Gap |
|---|---|---|---|
| Fetch calendar events | None | ❌ | No calendar API connected |
| Fetch email data | None | ❌ | No email API connected |
| Cross-verify from web directory | S4 web search | ⚠️ | Can search web but no cross-verification logic |
| Cleansed output with flagged fields | None | ❌ | No data quality/cleansing step |

### Part 2 Summary
**Score**: ~20% — Only the "web access" tool requirement is met. Calendar and email are entirely missing. The autonomous data pipeline (extract → cleanse → verify → display) is not implemented. The project focuses on a different use case (Six Sigma Kaizen for recruitment) rather than the challenge-specified data pipeline task.

---

## Overall Evaluation

> **Updated 2026-05-02**: Phase 1-3 of the post-submission iteration are complete. Tool integration and data pipeline scores unchanged (Calendar/Email work targeted for Phase 6). Multi-KPI detection, token-level cost tracking, and generic Kaizen triggering improve traceability + analytics depth.

| Dimension | Score | Comments |
|---|---|---|
| **Architecture & Design** | ✅ 92% | Clean agent architecture, SSE event system, Supabase persistence. Detection layer now multi-KPI (Phase 2). Generic Kaizen triggers (Phase 3). |
| **RAG Pipeline** | ✅ 85% | Full pipeline operational: `match_chunks` RPC + real embeddings + 5 corpora (65 chunks) + 3 structured documents. *Phase 5 will add citations + confidence-gated retry + numeric sanity checks.* |
| **Tool Integration** | ❌ 20% | Still 1/3 required tools. Calendar + Email targeted for Phase 6 (Interview Prep app). |
| **Data Pipeline** | ❌ 15% | Extraction exists; cleanse/verify/export still absent. Phase 6 CV-parsing pipeline addresses this. |
| **Deployment & Demo** | ✅ 85% | Localhost only. KPI tile row + token-level cost tracking added to dashboard (Phase 1+2). |
| **Traceability** | ⚠️ 55% | Token-level cost tracking added (Phase 1) — input/output/cached tokens persisted per call. Source citations still pending (Phase 5). |

**Overall**: ~58% — Detection + cost-tracking + generic-Kaizen improvements landed. Largest remaining gaps unchanged: Calendar/Email tools and the extract→cleanse→verify pipeline (both targeted by Phase 6).

---

## Priority Remediation Recommendations

### High (necessary to meet core requirements):
1. ✅ ~~Implement real pgvector embeddings~~ — **DONE**: `match_chunks` RPC deployed, real non-zero embeddings in all corpora.
2. ✅ ~~Pre-ingest at least 3 structured documents~~ — **DONE**: 5 structured corpora (65 chunks) seeded on startup.
3. ❌ **Add email tool** — Connect Gmail API (read inbox, extract structured data). Simplest path: IMAP + python's `imaplib` or a Gmail MCP server.
4. ❌ **Add calendar tool** — Connect Google Calendar API. Could use the existing `google-calendar` MCP server pattern to read events from interviewers' calendars.

### Medium (addresses data pipeline requirement):
5. ❌ **Build a data pipeline agent** — Create a new specialist agent (e.g. S5) that extracts → cleanses → normalizes → verifies data, with a new dashboard tab showing the "verified output" as a table with flagged fields.
6. ❌ **Add cross-verification logic** — Compare Adzuna salary data against industry_benchmarks table and flag outliers. Cross-check calendar availability against interview scheduling lag.

### Low (polish):
7. ❌ **Cloud deployment** — Deploy frontend to Vercel, backend to Modal.
8. ❌ **Source citations in RAG** — Return chunk IDs with links, show which corpus/doc a fact came from.
9. ❌ **CSV export** — Add download button for pipeline data, Kaizen results, or verified dataset.
