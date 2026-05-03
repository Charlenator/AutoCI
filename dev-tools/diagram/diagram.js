// AutoCI Dev Progress — React Flow standalone diagram.
// View with VS Code Live Server (right-click index.html → Open with Live Server).
// Update node statuses by editing NODES_RAW below or CONTEXT/dev-progress-diagram.md.
// Update CHANGELOG below whenever a meaningful node moves status (most-recent first).

import React from 'https://esm.sh/react@18';
import { createRoot } from 'https://esm.sh/react-dom@18/client';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
} from 'https://esm.sh/reactflow@11.10.4?deps=react@18,react-dom@18';

// ---------- "Right now" panel ----------
// Update each time work shifts. Keep both sides in sync — Charle should always
// know what (if anything) is blocking him.
const NOW = {
  claude: "B-evidence shipped: SQL templates with aggregate output now expose an optional build_evidence() that returns the underlying source rows (e.g. the 3 hires behind a TTF average). ExecutorResult carries evidence_sql + evidence_rows; Citation Drawer renders 'Source records (N)' as an expandable section with its own Source SQL toggle. 5 templates wired (time_to_fill, offer_acceptance_rate, conversion_rate, kpis_for_role, pipeline_volume_by_stage); record-level templates (candidate_search_by_skill etc.) intentionally have no evidence. Next: B-aug live-search augmentation, then B5 Modal worker fill.",
  charle: "Two optional parallel tasks (non-blocking): (1) Set RESEND_WEBHOOK_SECRET on Supabase Edge Function secrets (Step 5 below). (2) Generate more CV variety if you want edge cases to test. Otherwise just chill until next session — fresh context, clean state.",
};

// ---------- Charle's full checklist (rich HTML in `body`) ----------
// Update `done: true` as steps complete so Charle can track progress. Set to
// null to hide the panel entirely.
const CHARLE_CHECKLIST = {
  title: "Open parallel tasks",
  status: "1 small task",
  intro: "Modal setup done ✓. One small new task popped up — see Step 5 below.",
  steps: [
    {
      title: "Step 1 — Account + CLI auth",
      meta: "5 min",
      done: true,
      body: `
        <p>Activate the project venv, then authenticate the Modal CLI. Browser tab opens for sign-in / sign-up.</p>
        <pre><code># activate venv
& "C:/autoci-venv/Scripts/Activate.ps1"

# confirm modal CLI is installed (already in requirements.txt; if not):
pip install modal

# auth — opens browser
modal token new</code></pre>
        <p>The token gets stashed in <code>~/.modal.toml</code>. No further wiring needed.</p>
      `,
    },
    {
      title: "Step 2 — Create the Modal Secret",
      meta: "10 min",
      done: true,
      body: `
        <p>Modal stores env vars in named "Secret" objects. Create <strong>one</strong> Secret called <code>autoci-secrets</code> with every key our backend needs. Pick whichever path is easier:</p>
        <p><strong>Option A — via the web dashboard</strong> (recommended first time):</p>
        <ol>
          <li>Go to <a href="https://modal.com/secrets" target="_blank" rel="noopener">modal.com/secrets</a></li>
          <li>Click <em>New Secret</em> → <em>Custom</em></li>
          <li>Name: <code>autoci-secrets</code></li>
          <li>Paste each key/value pair from your local <code>backend/.env</code>:</li>
        </ol>
        <pre><code>SUPABASE_URL
SUPABASE_SERVICE_KEY
DEEPSEEK_API_KEY
OPENAI_API_KEY
ADZUNA_APP_ID
ADZUNA_API_KEY
TAVILY_API_KEY
NEWSAPI_KEY
RESEND_API_KEY
RESEND_WEBHOOK_SECRET
CAL_COM_API_KEY
CAL_COM_DEFAULT_EVENT_TYPE_ID
CAL_COM_USERNAME</code></pre>
        <p><strong>Option B — via CLI</strong> (faster, more typing):</p>
        <pre><code>modal secret create autoci-secrets \`
  SUPABASE_URL=https://orxdunrevazwpyzkoaob.supabase.co \`
  SUPABASE_SERVICE_KEY=&lt;value from backend/.env&gt; \`
  DEEPSEEK_API_KEY=&lt;value from backend/.env&gt; \`
  OPENAI_API_KEY=&lt;value or placeholder&gt; \`
  ADZUNA_APP_ID=6febb622 \`
  ADZUNA_API_KEY=&lt;value from backend/.env&gt; \`
  TAVILY_API_KEY=&lt;value from backend/.env&gt; \`
  NEWSAPI_KEY=&lt;value from backend/.env&gt; \`
  RESEND_API_KEY=&lt;value from backend/.env&gt; \`
  RESEND_WEBHOOK_SECRET=&lt;value from backend/.env&gt; \`
  CAL_COM_API_KEY=&lt;value from backend/.env&gt; \`
  CAL_COM_DEFAULT_EVENT_TYPE_ID=5572588 \`
  CAL_COM_USERNAME=charle-coetzee-b2wbir</code></pre>
      `,
    },
    {
      title: "Step 3 — (Optional but worth it) Real OpenAI key for embeddings",
      meta: "5 min · ~$5",
      done: true,
      body: `
        <p>Your current <code>OPENAI_API_KEY</code> is a placeholder, which means the embeddings tool falls back to zero-vectors. The 213 corpus chunks already in Supabase were generated with a real key — new chunks (CV chunks once B5 lands, plus any B3 retrieval test) need the same vector space to match.</p>
        <p>Generate a key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">platform.openai.com/api-keys</a>, then update <strong>both</strong>:</p>
        <ul>
          <li>Local <code>backend/.env</code> — replace <code>MISSING_NEEDED_FOR_T4_EMBEDDINGS</code> with the real key</li>
          <li>Modal Secret <code>autoci-secrets</code> — same key</li>
        </ul>
        <div class="checklist-callout">~$5 of credit covers the entire demo. Skip if budget is tight; vector search will silently return zero-similarity results (RAG path becomes near-useless but the pipeline still runs).</div>
      `,
    },
    {
      title: "Step 4 — Confirm + report back",
      meta: "30 sec",
      done: true,
      body: `
        <p>Verify the secret is reachable:</p>
        <pre><code>modal secret list</code></pre>
        <p>You should see <code>autoci-secrets</code> with 13 keys (12 if you skipped the OpenAI step).</p>
        <p>Reply in chat with "Modal ready" or paste the <code>modal secret list</code> output. Claude will then reference the <code>autoci-secrets</code> name in <code>modal_config.py</code> when Sprint D2 starts.</p>
      `,
    },
    {
      title: "Step 5 (NEW) — Set RESEND_WEBHOOK_SECRET on Supabase Edge Functions",
      meta: "2 min · optional",
      done: false,
      body: `
        <p>The Edge Function (Supabase) needs the Resend webhook signing secret to verify inbound webhooks. Without this, signature verification is skipped (logged as a warning) — works for testing, fails closed for production.</p>
        <p><strong>Option A — via Supabase dashboard</strong>:</p>
        <ol>
          <li>Go to <a href="https://supabase.com/dashboard/project/orxdunrevazwpyzkoaob/settings/edge-functions" target="_blank" rel="noopener">Project Settings → Edge Functions → Secrets</a></li>
          <li>Add a secret named <code>RESEND_WEBHOOK_SECRET</code> with the value <code>whsec_uUNBFija+ogyvI9AgUqXZehpDureNVo+</code></li>
          <li>Save. Existing function picks it up on next invocation.</li>
        </ol>
        <p><strong>Option B — via the Supabase CLI</strong> (if installed):</p>
        <pre><code>supabase secrets set RESEND_WEBHOOK_SECRET=whsec_uUNBFija+ogyvI9AgUqXZehpDureNVo+ \\
  --project-ref orxdunrevazwpyzkoaob</code></pre>
        <p>Once set, the Edge Function logs will show <code>signature OK svix-id=...</code> on each verified inbound; if a real Resend webhook fails verification it'll return 401.</p>
        <div class="checklist-callout">Skippable for now — local dev and the simulate-inbound endpoint don't need it. Worth doing before the live Resend round-trip in the demo.</div>
      `,
    },
  ],
};

// ---------- Sprint progress ----------
// status: 'done' | 'in_progress' | 'pending'
// progress: 0..1 (how far through the sprint we are)
const SPRINTS = [
  {
    id: "A",
    label: "Foundation",
    status: "done",
    progress: 1,
    substeps: [
      { id: "A1", label: "Migration 004 applied", status: "done" },
      { id: "A2", label: "3-tab shell skeleton + nav + drawer", status: "done" },
    ],
  },
  {
    id: "B",
    label: "Brief-required closures",
    status: "in_progress",
    progress: 0.6,
    substeps: [
      { id: "B1", label: "Query Planner + sql_templates + SQL exec + 4-layer safety", status: "done" },
      { id: "B2", label: "Citation chip system + CitationDrawer + QueryTransformationCard + ChatPanel", status: "done" },
      { id: "B-emb", label: "(slot-in) Embedding switch: OpenAI ada-002 (1536-d) → bge-small-en-v1.5 (384-d). Free, local. Migration 006 applied; 213 chunks re-embedded; RAG smoke test passes.", status: "done" },
      { id: "B3", label: "Knowledge Sources Panel + /sources route", status: "done" },
      { id: "B4", label: "Edge Function v2 + Modal worker scaffold + /inbound/simulate + /inbound/trigger + /inbound/drain", status: "done" },
      { id: "B-evidence", label: "Source-record evidence in Citation Drawer — templates emit optional build_evidence(); ExecutorResult carries evidence_rows/sql; UI renders aggregate + expandable Source Records.", status: "done" },
      { id: "B-aug", label: "Live-search augmentation in chat path (planner needs_live_search → S4 → upsert into corpus_chunks → re-retrieve)", status: "pending" },
      { id: "B5", label: "Modal worker filling — classifier + extractor + confidentiality + vectorizer", status: "pending" },
      { id: "B6", label: "Resend send wrapper", status: "pending" },
      { id: "B7", label: "cal.com slot wrapper", status: "pending" },
      { id: "B8", label: "CandidateSearch interface + Schedule Meeting flow", status: "pending" },
    ],
  },
  {
    id: "C",
    label: "Core nice-to-haves",
    status: "pending",
    progress: 0,
    substeps: [
      { id: "C1", label: "CIS rebrand: K_SCOPING + K_TOOL_SELECTOR + dynamic O2", status: "pending" },
      { id: "C2", label: "K6 update + retire K7 + interventions table", status: "pending" },
      { id: "C3", label: "FMEA tool", status: "pending" },
      { id: "C4", label: "Findings + Impact/Effort tables", status: "pending" },
      { id: "C5", label: "React Flow drawer in frontend (cumulative lighting)", status: "pending" },
    ],
  },
  {
    id: "D",
    label: "Deploy + submit",
    status: "pending",
    progress: 0,
    substeps: [
      { id: "D1", label: "Vercel frontend deploy (auto on push)", status: "in_progress" },
      { id: "D2", label: "Modal backend deploy", status: "pending" },
      { id: "D3", label: "Edge Function deploy + Resend webhook URL", status: "done" },
      { id: "D4", label: "Prod smoke test", status: "pending" },
      { id: "D5", label: "Submission deliverables", status: "pending" },
    ],
  },
];

// ---------- Changelog (most recent first) ----------
// kind: 'shipped' | 'progress' | 'cut' | 'decision' | 'infra'
const CHANGELOG = [
  { date: "2026-05-03", kind: "shipped", text: "B-evidence shipped — SQLTemplate gains optional build_evidence(); ExecutorResult carries evidence_sql + evidence_rows + evidence_error; chat.py forwards them; Citation drawer renders an expandable 'Source records (N)' section under the aggregate, with its own Source SQL toggle. Wired for time_to_fill, offer_acceptance_rate, conversion_rate, kpis_for_role, pipeline_volume_by_stage. Already-record-level templates (candidate_search_by_skill, candidate_by_email, industry_benchmark_for_role) intentionally have no evidence path. Unit-test coverage added in test_all.py. Closes Charle's last ask before the prior handoff." },
  { date: "2026-05-03", kind: "decision", text: "B-evidence added to plan (next-session priority): templates get an optional build_evidence() that returns the *underlying source rows* (the 3 hires that produced the 83.3-day average), not just the aggregate. Citation Drawer renders both. Stronger 'source traceability' demo." },
  { date: "2026-05-03", kind: "decision", text: "B-aug added to plan: live-search augmentation in chat path. Currently S4 is Kaizen-only; chat questions about current market data get stale answers. Next session item." },
  { date: "2026-05-03", kind: "shipped", text: "Migration 007: dedup corpus_chunks (213 → 79 rows; 134 dupes from re-vectorization on every Kaizen run) + UNIQUE content_hash index to block future dupes. CV chunks remain per-candidate distinguishable via metadata->>'candidate_id' in the dedup key." },
  { date: "2026-05-03", kind: "shipped", text: "B2 polish: chat reply now LLM-rewritten into natural language, Query Transformation Card collapsed-by-default with three labelled blocks (Your query / What we ran / Exact query)." },
  { date: "2026-05-03", kind: "shipped", text: "Sprint B4 done — Edge Function v2 deployed (signature verify + svix-id dedup + Storage upload + queue insert), Modal worker scaffold (process_pending_email) verified end-to-end, /inbound/simulate + /inbound/trigger + /inbound/drain routes for local-dev testing." },
  { date: "2026-05-03", kind: "shipped", text: "Sprint B3 done — /sources route + KnowledgeSourcesPanel modal. Live data: 6 corpora, 213 chunks, 10 surfaced SQL tables, ~830+ rows. Closes the '≥3 structured documents visibility' brief requirement." },
  { date: "2026-05-03", kind: "shipped", text: "CONTEXT/presentation_prep.md seeded — Q&A pre-emption doc with the LangChain framing, embedding choice, DeepSeek choice, pgvector choice, SQL injection answer, HITL rationale. Grow as more decisions land." },
  { date: "2026-05-03", kind: "shipped", text: "Embedding switch complete: 213 chunks re-embedded with bge-small-en-v1.5 in 51.7s, zero failures. End-to-end RAG smoke test: 'What is DMAIC?' matches the overview chunk at 0.749 similarity." },
  { date: "2026-05-03", kind: "decision", text: "CV smart-chunking strategy locked for Sprint B5: section-based chunking (identity / skills / summary / per-job / education), not paragraph. Other corpora keep paragraph chunking. Closes the brief's 'understanding of chunking' angle." },
  { date: "2026-05-03", kind: "decision", text: "Skipping LangChain/LangGraph. Reasons in chat — short version: we've already built the orchestration primitives, the DMAIC-as-architecture story is a strength, and direct LiteLLM calls give predictable latency." },
  { date: "2026-05-03", kind: "decision", text: "Embeddings: switched to BAAI/bge-small-en-v1.5 (384-d, local sentence-transformers) — free, no API key, comparable retrieval quality. Migration 006 applied; T4 rewritten." },
  { date: "2026-05-03", kind: "infra", text: "Modal Secret 'autoci-secrets' confirmed (13 keys). modal_config.py expansion deferred to Sprint D2." },
  { date: "2026-05-03", kind: "shipped", text: "Sprint B2 done — Chat tab is live. ChatPanel + CitationChip + Citation + CitationDrawer + QueryTransformationCard components shipped, wired to POST /chat/query. Plain Tailwind per the simplicity rule; design pass will repaint." },
  { date: "2026-05-03", kind: "decision", text: "UI components stay simple + flexible until the dedicated design sprint. New project memory rule." },
  { date: "2026-05-03", kind: "shipped", text: "Dev diagram: added Charle's-checklist panel with rich HTML + verbose Modal setup steps. Sidebar widened to 33vw + drag-resizable." },
  { date: "2026-05-03", kind: "shipped", text: "Sprint B1 done — Query Planner (LLM, schema-aware) + 8 validated SQL templates + thin SQL Executor + 4-layer SQL safety. Verified end-to-end: real TTF query returns 83.3 days for Senior Java Developer; DROP rejected at the DB by run_select_query." },
  { date: "2026-05-03", kind: "decision", text: "No emojis in user-facing UI. Existing nav + page placeholders rewritten to text-only." },
  { date: "2026-05-03", kind: "shipped", text: "Dev diagram: added Right-now panel + Sprint progress tracker (A/B/C/D with sub-step status)." },
  { date: "2026-05-03", kind: "infra", text: "Migration 005 applied: run_select_query RPC (Postgres-level SELECT-only enforcement, layer 4 of SQL safety)." },
  { date: "2026-05-03", kind: "progress", text: "Sprint B1 in flight: Query Planner + sql_templates + S3 SQL Executor + 4-layer SQL safety." },
  { date: "2026-05-03", kind: "shipped", text: "Sprint A2 — 3-tab shell skeleton: TopNav, RightDrawer, /, /candidates, /cis routes." },
  { date: "2026-05-03", kind: "infra", text: "CV generator tooling shipped: dev-tools/cv_generator/make_cvs.py + LLM prompt. First 20 .docx CVs generated locally." },
  { date: "2026-05-03", kind: "shipped", text: "Sprint A1 — Migration 004 applied via Supabase MCP: inbound_emails table, candidates extended, corpus_chunks.confidential, match_chunks RPC updated, cv-attachments bucket." },
  { date: "2026-05-03", kind: "decision", text: "Unified corpus_chunks design: CVs/JDs/email summaries all live in one table, distinguished by corpus_name + metadata." },
  { date: "2026-05-03", kind: "infra", text: "Edge Function inbound-email stub deployed (returns 200 so Resend webhook validation passes). Real handler lands in Sprint B4." },
  { date: "2026-05-03", kind: "infra", text: "Resend webhook configured (signing secret + API key in backend/.env). cal.com slot-lookup API verified." },
  { date: "2026-05-03", kind: "decision", text: "Inbound architecture: Edge Function = dumb pipe; Modal Python worker = heavy processing. .docx-only POC." },
  { date: "2026-05-03", kind: "cut", text: "Cuts moved to ROADMAP: RACI, Pareto, cross-Kaizen view, system_logs middleware, JD-paste fan-out." },
  { date: "2026-05-03", kind: "decision", text: "Plan pivot 2026-05-03: 3-interface shell + Resend + cal.com + CIS rebrand. Old plan archived." },
];

// ---------- Layout config ----------
const NODE_W = 230;
const NODE_H = 78;
const NODE_GAP_X = 22;
const NODE_GAP_Y = 16;
const GROUP_PAD_TOP = 44;
const GROUP_PAD_BOTTOM = 16;
const GROUP_PAD_X = 16;

// ---------- Group definitions ----------
// cols = how many node columns inside the group
const GROUPS = [
  { id: 'frontend',    label: '🖥️ Frontend (Next.js)',           x: 0,    y: 0,    cols: 4 },
  { id: 'routes',      label: '🛣️ Backend Routes',                x: 0,    y: 700,  cols: 4 },
  { id: 'specialists', label: '🧠 Backend Specialists',           x: 0,    y: 1300, cols: 2 },
  { id: 'detection',   label: '🔎 Detection',                     x: 580,  y: 1300, cols: 1 },
  { id: 'cis',         label: '🛠️ CIS Tools',                     x: 880,  y: 1300, cols: 2 },
  { id: 'tools',       label: '🔧 Tools / Middleware',            x: 0,    y: 2050, cols: 4 },
  { id: 'workflow',    label: '🎼 Workflow / Orchestrator',       x: 0,    y: 2350, cols: 3 },
  { id: 'edge',        label: '⚡ Supabase Edge (dumb pipe)',     x: 850,  y: 2350, cols: 1 },
  { id: 'worker',      label: '🐍 Modal Python Worker',           x: 1170, y: 2350, cols: 2 },
  { id: 'db',          label: '🗄️ Supabase Tables',               x: 0,    y: 2750, cols: 5 },
  { id: 'storage',     label: '📦 Storage',                       x: 0,    y: 3450, cols: 1 },
  { id: 'external',    label: '🌐 External APIs',                 x: 320,  y: 3450, cols: 4 },
  { id: 'deploy',      label: '🚀 Deployment',                    x: 1480, y: 3450, cols: 2 },
];

// ---------- Node definitions ----------
// [groupId, id, label, status, effort, phase]
// status: 'done' | 'wip' | 'todo' | 'todoBig' | 'retire'
const NODES_RAW = [
  // FRONTEND
  ['frontend', 'fe_shell',     '3-tab shell + nav',                'todo',    'M',  '5'],
  ['frontend', 'fe_drawer',    'Right drawer (React Flow)',        'todo',    'M',  '5'],
  ['frontend', 'fe_chat',      'Chat tab',                         'todo',    'S',  '5'],
  ['frontend', 'fe_qtc',       'QueryTransformationCard',          'todo',    'S',  '5'],
  ['frontend', 'fe_citdr',     'CitationDrawer',                   'todo',    'M',  '5'],
  ['frontend', 'fe_ksp',       'KnowledgeSourcesPanel',            'todo',    'S',  '5'],
  ['frontend', 'fe_csearch',   'CandidateSearch tab',              'todo',    'M',  '6'],
  ['frontend', 'fe_slot',      'SlotGrid (cal.com)',               'todo',    'M',  '6'],
  ['frontend', 'fe_cis',       'CIS tab',                          'todo',    'M',  '7'],
  ['frontend', 'fe_intv',      'InterventionsTable',               'todo',    'S',  '7'],
  ['frontend', 'fe_kpi',       'KPI tile row',                     'done',    '',   '2'],
  ['frontend', 'fe_writeup',   'Writeup card + chips',             'done',    '',   '4'],
  ['frontend', 'fe_ask',       'Ask-mode UI',                      'done',    '',   '4'],
  ['frontend', 'fe_sse',       'SSE client',                       'done',    '',   '4'],
  ['frontend', 'fe_ret_kan',   'Kanban (retire)',                  'retire',  'XS', '7'],
  ['frontend', 'fe_ret_sd',    '/system-diagram page (retire)',    'retire',  'XS', '5'],

  // ROUTES
  ['routes', 'r_chat',     '/chat/query',                          'done',    '',   '—'],
  ['routes', 'r_trig',     '/trigger/manual + goal-review',        'done',    '',   '3'],
  ['routes', 'r_stream',   '/sessions/{id}/stream',                'done',    '',   '4'],
  ['routes', 'r_respond',  '/sessions/{id}/respond',               'done',    '',   '4'],
  ['routes', 'r_metrics',  '/metrics/cost + /metrics/kpis',        'done',    '',   '1+2'],
  ['routes', 'r_know',     '/knowledge/seed + update',             'done',    '',   '—'],
  ['routes', 'r_rag',      '/rag/ingest',                          'done',    '',   '—'],
  ['routes', 'r_health',   '/health',                              'done',    '',   '—'],
  ['routes', 'r_sources',  '/sources',                             'done',    '',   'B3'],
  ['routes', 'r_cand',     '/candidates/*',                        'todo',    'M',  '6'],
  ['routes', 'r_cis',      '/cis/scope + /cis/run',                'todo',    'M',  '7'],
  ['routes', 'r_intv',     '/interventions',                       'todo',    'S',  '7'],
  ['routes', 'r_inbound',  '/inbound/simulate + trigger + drain',  'done',    '',   'B4'],

  // SPECIALISTS
  ['specialists', 's1_new',   'S1 QueryPlanner',                  'done',    '',   'B1'],
  ['specialists', 's2',       'S2 RAGAgent',                      'done',    '',   '—'],
  ['specialists', 's3_new',   'S3 SQLExecutor',                   'done',    '',   'B1'],
  ['specialists', 'sql_tpl',  'sql_templates dict (8 templates)', 'done',    '',   'B1'],
  ['specialists', 's4',       'S4 ResearchAgent',                 'done',    '',   '—'],

  // DETECTION
  ['detection', 'd1', 'D1 InternalBenchmarking',                  'done',    '',   '2'],
  ['detection', 'd2', 'D2 ExternalBenchmarking',                  'done',    '',   '4.5'],
  ['detection', 'd3', 'D3 GapAnalysis',                           'done',    '',   '2'],

  // CIS
  ['cis', 'k_scope',  'K_SCOPING',                                'todo',    'M',  '7'],
  ['cis', 'k_sel',    'K_TOOL_SELECTOR',                          'todo',    'S',  '7'],
  ['cis', 'k1',       'K1 Define',                                'done',    '',   '3'],
  ['cis', 'k2',       'K2 Measure',                               'done',    '',   '—'],
  ['cis', 'k3',       'K3 AnalyseHost',                           'done',    '',   '—'],
  ['cis', 'k4',       'K4 FiveWhys (RAG)',                        'done',    '',   '4.5'],
  ['cis', 'k5',       'K5 Ishikawa (RAG)',                        'done',    '',   '4.5'],
  ['cis', 'k6',       'K6 Improve (+linked_root_cause)',          'wip',     'XS', '7'],
  ['cis', 'k7_ret',   'K7 Control / Kanban (retire)',             'retire',  'XS', '7'],
  ['cis', 'k_write',  'K_WRITEUP',                                'done',    '',   '4'],
  ['cis', 'k_fmea',   'FMEA',                                     'todo',    'M',  '7'],

  // TOOLS
  ['tools', 't1', 'T1 MCP Analytics',                              'done',    '',   '—'],
  ['tools', 't2', 'T2 Validation Interceptor',                     'done',    '',   '—'],
  ['tools', 't3', 'T3 LiteLLM Router',                             'done',    '',   '1'],
  ['tools', 't4', 'T4 Embeddings',                                 'done',    '',   '—'],

  // WORKFLOW
  ['workflow', 'o2_old',    'O2 run_full_kaizen (refactor)',      'done',    '',   '—'],
  ['workflow', 'o2_new',    'O2 dynamic tool runner',             'todo',    'M',  '7'],
  ['workflow', 'sse_infra', 'SSE infra + HITL queue',             'done',    '',   '4'],

  // EDGE
  ['edge', 'ef_inbound',    'inbound-email receiver (dumb pipe)', 'done',    '',   'B4'],

  // WORKER
  ['worker', 'w_processor', 'inbound_processor.py (B4 scaffold)', 'wip',     'M',  'B5'],
  ['worker', 'w_cv_cls',    'S5 CV classifier (.docx)',           'todo',    'S',  '6'],
  ['worker', 'w_cv_ext',    'S6 CV extractor (python-docx)',      'todo',    'M',  '6'],
  ['worker', 'w_conf',      'S7 Confidentiality classifier',      'todo',    'S',  '6'],
  ['worker', 'w_vec',       'Email vectorizer',                   'todo',    'S',  '6'],

  // DB TABLES — unified corpus design: CVs/JDs/email summaries all live in corpus_chunks
  ['db', 'db_roles',         'roles',                             'done',    '',   '—'],
  ['db', 'db_intvw',         'interviewers',                      'done',    '',   '—'],
  ['db', 'db_cand',          'candidates (+CV cols)',             'done',    '',   '6'],
  ['db', 'db_pipe',          'pipeline_events',                   'done',    '',   '—'],
  ['db', 'db_hires',         'hires',                             'done',    '',   '—'],
  ['db', 'db_off',           'offer_outcomes',                    'done',    '',   '—'],
  ['db', 'db_bench',         'industry_benchmarks',               'done',    '',   '—'],
  ['db', 'db_adz',           'adzuna_postings',                   'done',    '',   '—'],
  ['db', 'db_sess',          'kaizen_sessions',                   'done',    '',   '—'],
  ['db', 'db_nodes',         'kaizen_nodes',                      'done',    '',   '—'],
  ['db', 'db_inv',           'agent_invocations',                 'done',    '',   '—'],
  ['db', 'db_chunks',        'corpus_chunks (+confidential)',     'done',    '',   '6'],
  ['db', 'db_inbox',         'inbound_emails',                    'done',    '',   '6'],
  ['db', 'db_intv_tbl',      'interventions',                     'todo',    'S',  '7'],
  ['db', 'db_rpc',           'match_chunks RPC (+filter)',        'done',    '',   '6'],

  // STORAGE
  ['storage', 'st_cv', 'cv-attachments bucket',                   'done',    '',   '6'],

  // EXTERNAL
  ['external', 'e_ds',     'DeepSeek (LiteLLM)',                  'done',    '',   '—'],
  ['external', 'e_oai',    'OpenAI embeddings',                   'done',    '',   '—'],
  ['external', 'e_adz',    'Adzuna',                              'done',    '',   '—'],
  ['external', 'e_tav',    'Tavily',                              'done',    '',   '—'],
  ['external', 'e_news',   'NewsAPI',                             'done',    '',   '—'],
  ['external', 'e_resend', 'Resend (send + inbound)',             'todo',    'S',  '6'],
  ['external', 'e_cal',    'cal.com (slots)',                     'todo',    'S',  '6'],

  // DEPLOY
  ['deploy', 'dep_vercel',  'Vercel (frontend)',                  'todo',    'S',  '8'],
  ['deploy', 'dep_modal',   'Modal (backend)',                    'todo',    'M',  '8'],
  ['deploy', 'dep_edge',    'Edge Function deploy',               'todo',    'S',  '8'],
  ['deploy', 'dep_subm',    'Submission deliverables',            'todo',    'S',  '9'],
];

// ---------- Edges (high-signal flow only — keeps the diagram readable) ----------
const EDGES_RAW = [
  // Chat path: user -> chat tab -> route -> S1_NEW -> SQL/RAG -> DB
  ['fe_chat', 'r_chat'],
  ['r_chat', 's1_new'],
  ['s1_new', 'sql_tpl'],
  ['s1_new', 's3_new'],
  ['s1_new', 's2'],
  ['s2', 'db_rpc'],
  ['s3_new', 'db_rpc'],
  ['sql_tpl', 's3_new'],

  // Candidate Search path: search -> route -> RAG / cal.com / Resend
  ['fe_csearch', 'r_cand'],
  ['r_cand', 's2'],
  ['r_cand', 'e_cal'],
  ['r_cand', 'e_resend'],
  ['fe_slot', 'e_cal'],

  // CIS path: tab -> route -> scoping -> selector -> orchestrator -> tools
  ['fe_cis', 'r_cis'],
  ['r_cis', 'k_scope'],
  ['k_scope', 'k_sel'],
  ['k_sel', 'o2_new'],
  ['o2_new', 'd1'],
  ['o2_new', 'k1'],
  ['o2_new', 'k_fmea'],

  // Inbound pipeline (decoupled): Resend -> Edge -> Storage + queue -> Worker -> agents -> DB
  ['e_resend', 'ef_inbound'],
  ['ef_inbound', 'st_cv'],
  ['ef_inbound', 'db_inbox'],
  ['db_inbox', 'w_processor'],
  ['w_processor', 'w_cv_cls'],
  ['w_processor', 'w_cv_ext'],
  ['w_processor', 'w_conf'],
  ['w_processor', 'w_vec'],
  ['w_processor', 'db_cand'],
  ['w_processor', 'db_chunks'],

  // Simulated inbound -> same Edge function
  ['r_inbound', 'ef_inbound'],

  // SSE + HITL infra
  ['r_stream', 'sse_infra'],
  ['r_respond', 'sse_infra'],
  ['o2_new', 'sse_infra'],
];

// ---------- Layout generator ----------
function buildLayout() {
  // Group nodes by groupId
  const byGroup = {};
  for (const [g, ...rest] of NODES_RAW) {
    (byGroup[g] = byGroup[g] || []).push(rest);
  }

  const nodes = [];
  const edges = [];

  for (const grp of GROUPS) {
    const childRows = byGroup[grp.id] || [];
    const cols = grp.cols;
    const rows = Math.ceil(childRows.length / cols);
    const innerW = cols * NODE_W + (cols - 1) * NODE_GAP_X;
    const innerH = rows * NODE_H + (rows - 1) * NODE_GAP_Y;
    const groupW = innerW + GROUP_PAD_X * 2;
    const groupH = innerH + GROUP_PAD_TOP + GROUP_PAD_BOTTOM;

    // Group container
    nodes.push({
      id: grp.id,
      type: 'groupNode',
      position: { x: grp.x, y: grp.y },
      data: { label: grp.label },
      style: { width: groupW, height: groupH },
      draggable: false,
      selectable: false,
    });

    // Children
    childRows.forEach(([id, label, status, effort, phase], i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      nodes.push({
        id,
        type: 'statusNode',
        parentNode: grp.id,
        extent: 'parent',
        position: {
          x: GROUP_PAD_X + col * (NODE_W + NODE_GAP_X),
          y: GROUP_PAD_TOP + row * (NODE_H + NODE_GAP_Y),
        },
        data: { label, status, effort, phase },
        className: `status-${status}`,
        draggable: false,
      });
    });
  }

  for (const [from, to] of EDGES_RAW) {
    edges.push({
      id: `${from}->${to}`,
      source: from,
      target: to,
      type: 'smoothstep',
      animated: false,
      style: { stroke: '#64748b', strokeWidth: 1.5, opacity: 0.7 },
    });
  }

  return { nodes, edges };
}

// ---------- Custom node types ----------
const StatusNode = ({ data }) => {
  return React.createElement(
    'div',
    {
      className: `react-flow__node-statusNode status-${data.status}`,
      style: { width: NODE_W - 4, height: NODE_H - 4 },
    },
    React.createElement(Handle, { type: 'target', position: Position.Top, style: { background: '#64748b' } }),
    React.createElement('div', { className: 'node-label' }, data.label),
    React.createElement('div', { className: 'node-meta' },
      React.createElement('span', null, data.phase ? `Phase ${data.phase}` : ''),
      React.createElement('span', { className: 'node-effort' }, data.effort ? `[${data.effort}]` : '')
    ),
    React.createElement(Handle, { type: 'source', position: Position.Bottom, style: { background: '#64748b' } })
  );
};

const GroupNode = ({ data }) => {
  return React.createElement(
    React.Fragment,
    null,
    React.createElement('div', { className: 'group-label' }, data.label)
  );
};

const nodeTypes = {
  statusNode: StatusNode,
  groupNode: GroupNode,
};

// ---------- App ----------
const App = () => {
  const { nodes, edges } = React.useMemo(() => buildLayout(), []);
  return React.createElement(
    ReactFlow,
    {
      nodes,
      edges,
      nodeTypes,
      fitView: true,
      fitViewOptions: { padding: 0.1 },
      minZoom: 0.15,
      maxZoom: 2,
      proOptions: { hideAttribution: true },
      defaultEdgeOptions: { type: 'smoothstep' },
    },
    React.createElement(Background, { color: '#1e293b', gap: 24 }),
    React.createElement(Controls, { showInteractive: false }),
    React.createElement(MiniMap, {
      pannable: true,
      zoomable: true,
      nodeColor: (n) => {
        if (n.type === 'groupNode') return 'transparent';
        const s = n.data?.status;
        if (s === 'done') return '#22c55e';
        if (s === 'wip') return '#fbbf24';
        if (s === 'todoBig') return '#ef4444';
        if (s === 'retire') return '#475569';
        return '#94a3b8';
      },
      maskColor: 'rgba(15, 23, 42, 0.7)',
    })
  );
};

const container = document.getElementById('root');
const root = createRoot(container);
root.render(React.createElement(App));

// ---------- Render sidebar panels (vanilla DOM, no React needed) ----------
function renderNow() {
  const claude = document.getElementById('now-claude');
  const charle = document.getElementById('now-charle');
  if (claude) claude.textContent = NOW.claude;
  if (charle) charle.textContent = NOW.charle;
}

function renderChecklist() {
  const intro = document.getElementById('checklist-intro');
  const steps = document.getElementById('checklist-steps');
  const status = document.getElementById('checklist-status');
  const panel = document.getElementById('checklist-panel');

  if (!CHARLE_CHECKLIST || !panel) {
    if (panel) panel.style.display = 'none';
    return;
  }
  panel.style.display = '';

  if (intro) intro.innerHTML = CHARLE_CHECKLIST.intro || '';
  if (status) status.textContent = CHARLE_CHECKLIST.status || '';
  if (!steps) return;
  steps.innerHTML = (CHARLE_CHECKLIST.steps || []).map((step, i) => `
    <div class="checklist-step">
      <div class="checklist-step-header">
        <span class="checklist-step-title">${step.done ? '✓ ' : ''}${step.title}</span>
        <span class="checklist-step-meta">${step.meta || ''}</span>
      </div>
      <div class="checklist-step-body">${step.body}</div>
    </div>
  `).join('');
}

function renderSprints() {
  const list = document.getElementById('sprint-list');
  if (!list) return;
  list.innerHTML = SPRINTS.map((sprint) => {
    const fillWidth = `${Math.round(sprint.progress * 100)}%`;
    const statusLabel = {
      done: "done",
      in_progress: "in progress",
      pending: "pending",
    }[sprint.status] || sprint.status;
    const subSteps = (sprint.substeps || [])
      .map(
        (s) => `<li class="${s.status}"><strong>${s.id}</strong> ${s.label}</li>`
      )
      .join("");
    return `
      <li>
        <span class="sprint-id">${sprint.id} ${sprint.label}</span>
        <span class="sprint-bar ${sprint.status}"><span class="sprint-bar-fill" style="width:${fillWidth}"></span></span>
        <span class="sprint-status ${sprint.status}">${statusLabel}</span>
        <ul class="sprint-substeps">${subSteps}</ul>
      </li>
    `;
  }).join('');
}

function renderChangelog() {
  const list = document.getElementById('changelog-list');
  if (!list) return;
  list.innerHTML = CHANGELOG.map((entry) => {
    const tagLabel = {
      shipped: 'shipped',
      progress: 'in progress',
      cut: 'cut',
      decision: 'decision',
      infra: 'infra',
    }[entry.kind] || entry.kind;
    return `
      <li class="kind-${entry.kind}">
        <div class="changelog-meta">
          <span>${entry.date}</span>
          <span class="changelog-tag tag-${entry.kind}">${tagLabel}</span>
        </div>
        <div class="changelog-text">${entry.text}</div>
      </li>
    `;
  }).join('');
}

renderNow();
renderChecklist();
renderSprints();
renderChangelog();
