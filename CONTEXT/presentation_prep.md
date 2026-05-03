# Presentation Prep — Q&A pre-emption

Living document for the eventual demo / submission walk-through. Each entry is a question reviewers are likely to ask + the framing we'll use to answer it. Add to this as more "expect-this-question" moments come up during the build.

When Sprint D5 (submission deliverables) lands, the README and screen-record narration will pull talking points from this file.

---

## Q: "Why didn't you use LangChain or LangGraph?"

**Short version (30s)**:
> We deliberately built the orchestration layer from primitives — direct LiteLLM calls, Pydantic dataclasses, an asyncio-driven state machine. LangChain and LangGraph are useful frameworks, but for a system whose core narrative is *"Six Sigma rigour wired into the architecture"*, framework abstractions would obscure the very thing we want reviewers to see. We have all the pieces a framework would give us — orchestrator, retrievers, output parsers, callbacks — implemented explicitly so each one is auditable.

**Longer version (talking points if pressed)**:

1. **The DMAIC backbone is the architectural value.** LangChain assumes a generic ReAct or function-calling loop. Retrofitting Six Sigma phase gates onto its abstractions would be more work than implementing them directly, and would weaken the demo narrative. The fact that *Five Whys is five sequential atomic LLM calls* — not a prompt — is the whole point.

2. **Determinism for reviewer scrutiny.** Direct prompts in plain Python make every agent's behaviour inspectable in 30 seconds. LangChain's middleware (retry policies, prompt templating, callback handlers) introduces magic that's harder to defend on the spot.

3. **Latency budget.** Direct LiteLLM calls minimize per-step overhead. Across six DMAIC phases that compounds.

4. **Equivalent custom pieces we already have**:
   - LangGraph state machine → `O2._handle_phase` + phase enum + HITL queue
   - LangChain Memory → `kaizen_sessions` JSONB + per-session `agent_invocations`
   - LangChain Retrievers → S2 RAG agent + `match_chunks` Postgres RPC
   - LangChain Tools → our specialist agents (S1-S4, K-tools, D-tools)
   - LangChain Output Parsers → Pydantic dataclasses + JSON envelopes (e.g. QueryPlan)
   - LangChain Callbacks → SSE event builders

5. **When we'd reach for them**: a *specific* feature gap (a battle-tested chunker, a particularly good loader). We'd grab the one utility, not adopt the framework wholesale.

**Posture**: not "we hate frameworks" — "we made an explicit, defensible choice for this specific project's narrative."

---

## Q: "Why use a smaller embedding model (bge-small) instead of OpenAI?"

**Short version**:
> Cost discipline and architecture independence. `bge-small-en-v1.5` runs on CPU inside our own Modal containers — no API key, no rate limits, no recurring cost. Retrieval quality is competitive with OpenAI ada-002 on standard benchmarks, especially for short technical queries (skills, role names) which is our core workload. The 384-d vectors are also faster to index and search than 1536-d.

**Talking points**:
- bge-small ranks well on MTEB retrieval benchmarks; the gap to ada-002 is small for our use case.
- Free + local means we can re-embed test corpora at zero marginal cost during dev (we did this once during the build).
- The whole stack stays inside our Modal app, including the embedding model — no third-party API in the hot path of a chat query.
- If retrieval quality issues surface later, swapping models is a one-line change in T4 + a re-embed migration.

---

## Q: "Why DeepSeek instead of GPT-4 / Claude / Gemini?"

**Short version**:
> Cost-to-quality on agentic tasks specifically. DeepSeek-Chat is ~$0.14/M input and ~$0.28/M output — an order of magnitude cheaper than GPT-4-class models with strong instruction-following. Six DMAIC phases plus per-step writeups across multiple Kaizens would be cost-prohibitive on the premium models. LiteLLM (T3) abstracts the router so swapping is a single config change.

**Talking points**:
- A full Kaizen costs around $0.18 in DeepSeek tokens. That's the headline number from the README.
- LiteLLM means we're not locked in. If a specific agent benefits from Claude or GPT-4 reasoning later, the router can route per-task.
- DeepSeek prompt caching kicks in unexpectedly well for our writeup agent's repeated system prompts — incidentally another ~30% savings.

---

## Q: "Why pgvector inside Supabase instead of Pinecone / Qdrant / Weaviate?"

**Short version**:
> Single source of truth. Our structured data (candidates, pipeline events, hires) and our vector data live in the same Postgres database, so a single SQL query can join semantic-search results with hires data without round-tripping between two stores. pgvector handles our scale comfortably (213 chunks today, projected ~500-1000 with CV ingestion).

**Talking points**:
- A dedicated vector DB earns its keep above ~1M chunks. Below that, the cross-store join cost dominates.
- Same auth, same backups, same observability story.
- If we hit pgvector's ceiling, the migration to a dedicated store is mostly a T4 rewrite — most of the surrounding code (chunking, retrieval, RAG agent) doesn't care.

---

## Q: "How do you prevent SQL injection in the LLM-generated SQL path?"

**Short version**:
> Four layers. 1) The Query Planner prefers validated templates (parameterized SQL with strict per-param validation) over freeform SELECTs. 2) Any freeform SQL the LLM does emit is regex-validated in Python before transit. 3) The LLM's system prompt explicitly forbids non-SELECT statements. 4) The database-side `run_select_query` RPC rejects any non-SELECT or stacked-statement at the boundary. Even if the first three layers were bypassed, the database itself refuses to execute writes.

**Talking points**:
- Verified during the build: a `DROP TABLE candidates` query is rejected by the RPC with a clear error.
- The validated-templates path is the *primary* path; freeform is the fallback for novel questions. Most actual queries hit a template.

---

## Q: "What about hallucination on the numeric metrics?"

**Short version**:
> The validated-templates path means numeric answers come from a hand-checked SQL query against the actual database, not from the LLM's interpretation. The Citation Drawer surfaces the SQL that produced the answer plus the rows it returned, so reviewers can verify on the spot. The LLM is responsible for routing and explaining; the numbers come from Postgres.

---

## Q: "What happens when a user asks about *current* market conditions — how do you avoid stale answers?"

**Short version**:
> The Query Planner is taught to recognise "current / recent / today / market" cues in the question and emits a `needs_live_search` flag plus a list of relevant sources (Adzuna for postings, NewsAPI for articles, Tavily for general web). When that flag is set, the chat endpoint runs a pre-RAG step that fetches from those sources and *upserts* the results into the same `corpus_chunks` table everything else lives in — using `ignore_duplicates=True` against migration 007's unique `content_hash` constraint, so re-runs are no-ops. After the upsert, the existing S2 RAG agent retrieves from the now-augmented corpus, so the live-fetched material flows through the same citation + drawer path as everything else.

**Why this is the right shape**:
- One retrieval surface, not two. There's no "live search results" separate UI; fresh chunks just become part of the corpus and surface as normal RAG citations.
- The unique-content-hash constraint means no duplicate ingestion, even if the user asks the same question twice in a row or different users hit overlapping topics.
- The planner is the only piece that's allowed to *decide* when to fire — not a regex on the user's text — so it stays adjustable via prompting rather than a brittle heuristic.

**What it *doesn't* do**:
- No streaming "Searching the web…" indicator yet. The endpoint blocks until the augmentation finishes; the chat UI's "Thinking…" indicator covers that latency. SSE-streamed progress is in ROADMAP.

---

## Q: "How does the system handle source traceability for an aggregated number — like 'average time to fill is 83.3 days'?"

**Short version**:
> Every aggregate-result template carries a sibling `build_evidence` query that returns the underlying source rows that produced the aggregate. The Citation drawer renders the aggregate up top, then expands to a "Source records (N)" table — for the 83.3-day TTF answer, reviewers see the three actual hires (candidate, role, applied date, start date, days-to-fill) that the AVG was computed over. The evidence query goes through the same SQL allowlist as everything else, and a failure in the evidence path is isolated so the main answer still renders.

**Why this matters for the brief**:
- "Source traceability" is a literal Part 1 requirement. Showing the SQL is good; showing the SQL *and* the actual records that produced the number is stronger — it removes the "trust the SQL" leap entirely.
- It's the same architectural shape used everywhere else (clickable citation chips → drawer with full provenance), just one layer deeper for SQL.
- Templates whose primary result is already record-level (candidate-by-skill, candidate-by-email, industry-benchmark-for-role) deliberately skip the evidence path — adding a duplicate evidence query for a record-level result would be cargo-culted.

---

## Q: "Why HITL between phases instead of letting the agents run autonomously?"

**Short version**:
> Trust calibration for a methodology-driven tool. A Six Sigma practitioner reviewing an autonomous Kaizen would want to interrogate findings between phases anyway. HITL gates surface that interrogation as a first-class affordance instead of a post-hoc audit. The Ask path during a gate also showcases that the same RAG infrastructure powers in-flight investigation, not just the chat tab.

---

## (Add as we go)

When a design decision lands that a reviewer might question, add the Q&A here. Easier to write while context is fresh than to reconstruct during submission week.
