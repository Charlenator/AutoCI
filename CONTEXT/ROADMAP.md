# AutoCI — Roadmap (post-MVP)

> **Purpose**: a living "what I'd add with more time and resources" document. Doubles as the source for the presentation's future-work slide.
>
> **Rules**:
> - Items move here from `plan-of-record.md` when we deliberately cut them from current scope.
> - New ideas go here when they appear during build but don't strictly enhance the current product or close a brief requirement.
> - Each item is sized (relative effort) so we can pull items back into scope opportunistically if Phase 5/6/7/8/9 finish ahead of plan.
> - Categorized by theme for easy presentation use.

---

## Communication & Workflow

### RACI matrix tool *(cut from Phase 7)*
**Effort**: S
**What**: Per-intervention agent that emits a Responsible / Accountable / Consulted / Informed table for each owner. Frontend renders as a mini-table inside the Interventions row.
**Why valuable**: makes the Control phase output usable as-is by any change-management practitioner. Maps interventions directly to org accountability.
**Why cut**: not in the brief; CIS already has Pareto/FMEA-class tools to demo "right tool for the job." RACI adds another mini-tool surface without closing a requirement.

### JD-paste fan-out search *(cut from Phase 6)*
**Effort**: S
**What**: Pasted job description gets parsed by a translation agent that extracts 3-5 key requirements, each fired as a separate semantic query against `cv_chunks`, then results merged + ranked.
**Why valuable**: makes Candidate Search smarter than a single embedding lookup. A JD asking for "Java 17 + AWS + Kubernetes + 5 years" has multiple distinct concept clusters; one embedding flattens them.
**Why cut**: free-text semantic search alone meets the "verified output / search" requirement. Fan-out is a sophistication win, not a needed one.

### Slack / Teams notifications
**Effort**: M
**What**: When a high-priority candidate arrives via inbound email (or a Kaizen completes), push a Slack/Teams message to the recruiter with a deep-link.
**Why valuable**: closes the loop on the "agent acts autonomously, you find out about it later" UX. Recruiters live in Slack, not in the AutoCI app.

### ATS integrations (Greenhouse, Lever, Workday)
**Effort**: L (per ATS)
**What**: Bidirectional sync — pipeline events flow from ATS into AutoCI; AutoCI's verified-output candidate records flow back to ATS as new applicants.
**Why valuable**: makes AutoCI deployable inside an existing recruiter workflow without forcing them to abandon their ATS.

### Email-driven Kaizen triggers
**Effort**: M
**What**: A leader emails the system (e.g. `kaizen@yourdomain`) describing a process problem; the inbound pipeline routes it directly into K_SCOPING.
**Why valuable**: pure ergonomic win — Kaizens can be triggered by leadership without anyone opening the app.

---

## Quality & Reliability

### Three-layer RAG self-check *(cut from earlier plan)*
**Effort**: M
**What**: Two additional self-check layers beyond citations:
1. **Confidence-gated retry**: LLM emits `confidence: low|med|high`; on `low`, S1/S2 reformulate query and retrieve once more (cap at 1 retry).
2. **Numeric reasonableness check**: numeric outputs validated against bounds defined per-metric (TTF ∈ [1, 365], OAR ∈ [0, 1]); out-of-range → re-verify or flag.
**Why valuable**: catches LLM-fabricated numbers and weak retrievals before they reach the user.
**Why cut**: validated SQL templates path covers numeric accuracy in practice. Citations cover RAG traceability. The retry/sanity layers add complexity for diminishing returns at MVP.

### PDF CV ingestion *(deferred from Phase 6 POC)*
**Effort**: M
**What**: Add PDF parsing alongside the POC's `.docx`-only extraction. Modal worker calls `pypdf` (or `pdfplumber` for tables/multi-column) to extract text, then runs the same DeepSeek extraction prompt as the `.docx` path.
**Why valuable**: real recruiters receive a mix of `.docx` and `.pdf` CVs (probably 60/40 in favour of PDF). POC ships `.docx` only to keep the extraction loop simple; PDF closes the gap.
**Why cut**: extraction quality varies wildly across PDF generators (Word-exported PDFs are easy; scanned/OCRd ones are hard). Sized M because handling the long tail of bad PDFs takes iteration. POC demo can use `.docx` candidates without this.

### T2.2 Evidence Selector *(deferred from Phase 4.5)*
**Effort**: M
**What**: Thin DeepSeek call before each K phase that takes (role, KPI, phase) and returns `{chunk_ids, postings_filter}`. K agents consume only the curated slice.
**Why valuable**: stops irrelevant news articles from polluting Five Whys context when corpora grow.
**Why cut**: writeups already cite well with current retrieval; no demonstrated need yet. Worth revisiting once corpora cross ~500 chunks.

### FMEA expansion to broader risk register
**Effort**: M
**What**: Today FMEA scores interventions. Expand to score the entire pipeline (every stage, every tool, every external API dependency) so the system maintains a live risk dashboard.
**Why valuable**: makes the "Six Sigma rigour as architecture" claim deeper than just per-Kaizen output.

### Server-side cal.com booking
**Effort**: M
**What**: Use `/v2/bookings` to create the booking server-side from AutoCI when the candidate clicks a slot in the invite email. Eliminates the trust step where the candidate could pick a different time.
**Why valuable**: tightens the candidate UX; closes a small abuse vector (candidate ignores the slots we offered and books over our dentist appointment).
**Why cut**: free-tier deep-link approach is good enough for the demo. The trust assumption is reasonable in a recruiting context.

### Process map / SIPOC visual diagram
**Effort**: M
**What**: Render existing SIPOC text output as a swim-lane diagram via React Flow.
**Why valuable**: another LSS artefact that pairs with Pareto charts and the system diagram.
**Why cut**: visually competes with the global system flow drawer; SIPOC text alone reads fine.

---

## Visualizations & Analytics

### Pareto analysis tool *(cut from Phase 7)*
**Effort**: S
**What**: 80/20 root-cause analysis as a CIS tool. Bar chart by frequency × impact.
**Why valuable**: visually compelling; classic Six Sigma tool that pairs with Five Whys + Ishikawa.
**Why cut**: brief doesn't require it; CIS already demos "right tool for the job" with K_SCOPING + K_TOOL_SELECTOR + FMEA.

### Cross-Kaizen interventions view *(cut from Phase 7)*
**Effort**: S
**What**: A historical aggregation view across all Kaizen sessions: "every intervention ever proposed, filterable by role / KPI / status / owner."
**Why valuable**: turns single-session outputs into a portfolio-wide CI ledger; managers can see what's been tried and what's worked.
**Why cut**: per-Kaizen interventions table closes the "replace Kanban" requirement. Cross-Kaizen aggregation is portfolio-polish — defer to post-deploy.

### Real-time hiring dashboard
**Effort**: M
**What**: Auto-refreshing dashboard showing pipeline KPIs as new events stream in. Subscribes to Supabase Realtime channels on `pipeline_events`.
**Why valuable**: makes AutoCI useful as an always-on monitor, not just a query/Kaizen tool.

### Sankey diagram of pipeline flow
**Effort**: S
**What**: Visualize candidate flow stage-by-stage (Applied → Screening → Interview → Offer → Hire → Decline) as a Sankey diagram, colored by source channel.
**Why valuable**: instantly readable view of where in the funnel candidates are dropping.

---

## Observability & Operations

### system_logs middleware *(cut from Phase 5)*
**Effort**: S
**What**: Centralized request/response/agent-call log table separate from `agent_invocations`. Captures route hits, error states, timing.
**Why valuable**: better debugging story than relying on Modal logs.
**Why cut**: `agent_invocations` already captures the LLM side; we can extend it for non-LLM events when needed. Don't build a parallel logging layer pre-emptively.

### Long-term log archival to S3
**Effort**: M
**What**: Nightly job to ship `agent_invocations` + `system_logs` rows older than 90 days to S3 (Parquet) and prune from Supabase.
**Why valuable**: keeps Supabase fast as the system runs longer; preserves audit trail at low cost.

### DBOS durability for orchestrator
**Effort**: L
**What**: Replace the worker-thread orchestrator with DBOS-backed durable workflows. Crash-resumable Kaizens.
**Why valuable**: production-grade reliability. A Kaizen that crashes mid-flight today loses state; with DBOS it picks up where it left off.

---

## Multi-User & Authentication

### Authentication + multi-recruiter isolation
**Effort**: L
**What**: Supabase Auth + RLS policies so each recruiter sees only their own scheduled meetings, drafted emails, and run history. Shared corpora and KPIs.
**Why valuable**: required for any real deployment. Removes the "single demo user" assumption.

### cal.com OAuth Managed Users
**Effort**: M
**What**: Each recruiter authenticates AutoCI to their own cal.com account via OAuth. AutoCI books slots on each recruiter's calendar.
**Why valuable**: pairs with multi-user auth above. Today every "Schedule Meeting" call hits Charle's cal.com.

---

## Scale & Reliability

### Mobile-responsive UI
**Effort**: M
**What**: Tailwind breakpoints + component refactors for phone/tablet.
**Why valuable**: recruiters increasingly work on the move.

### Multi-language CV support
**Effort**: M
**What**: Detect CV language, extract fields per language, normalize to English in the structured store. Vector search across languages via multilingual embeddings.
**Why valuable**: South African recruitment is multilingual; English-only is a hard limit.

### Embedded vector store outside Supabase
**Effort**: L
**What**: Migrate `corpus_chunks` to a dedicated vector DB (Pinecone, Qdrant, or Weaviate) for performance at scale.
**Why valuable**: pgvector is fine to ~1M chunks; beyond that a dedicated store is faster.
**When**: not until corpus crosses ~500K chunks.

---

## Live data & retrieval upgrades

### `corpus_chunks.metadata`-filtered retrieval
**Effort**: XS
**What**: Use the existing `{role, source, topic}` metadata JSONB to filter `match_chunks` results. Already populated, just not consumed.
**Why valuable**: tighter retrieval; less off-topic noise.
**Why cut**: can revisit when corpora grow.

### Adzuna posting freshness filter
**Effort**: XS
**What**: Filter `adzuna_postings` by `expired_date` so only currently-active postings shape benchmarks. Drop `is_repost` / `original_posting_id` if still unused.
**Why valuable**: stops stale postings (sometimes 6+ months old) from skewing live-market signals.

---

## Process / Methodology improvements

### Automated reference checks
**Effort**: L
**What**: Cross-reference candidate LinkedIn (via web scraping or LinkedIn API) against CV claims; flag inconsistencies.
**Why valuable**: closes the cleanse → verify loop with an external truth source.

### Scheduled Kaizen runs (cron)
**Effort**: S
**What**: APScheduler or Modal cron triggers a goal-review Kaizen weekly/monthly without human kickoff.
**Why valuable**: AutoCI becomes an "always watching" monitor.

### Email debrief for completed Kaizens
**Effort**: S
**What**: After a Kaizen finishes, compile a Markdown summary email and send via Resend to the trigger user. Re-uses existing K_WRITEUP outputs.
**Why valuable**: leadership engagement without anyone opening the app.

---

## Notes for the presentation slide

When pitching the future-work view, group items by audience:
- **For recruiters**: Slack notifications, ATS integrations, mobile UI, multi-language CV support.
- **For leadership**: real-time dashboard, scheduled Kaizens, email debriefs, Sankey flow.
- **For engineering rigour**: DBOS durability, three-layer self-check, FMEA risk register, log archival.
- **For multi-tenant deployment**: auth + RLS, cal.com OAuth Managed Users, embedded vector DB.

The narrative arc: *"AutoCI today is a one-recruiter demo with a battle-tested core; here's how it scales out."*
