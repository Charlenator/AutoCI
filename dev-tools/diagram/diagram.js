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
  claude: "Sprint B1 — Query Planner + sql_templates + SQL executor + 4-layer SQL safety. Migration 005 (run_select_query RPC) applied.",
  charle: "Nothing blocking. Optional: keep generating CV batches if you want richer test data — the pipeline can ingest them once Sprint B5 lands.",
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
    progress: 0.05,
    substeps: [
      { id: "B1", label: "Query Planner + sql_templates + SQL exec + 4-layer safety", status: "in_progress" },
      { id: "B2", label: "Citation chip system + CitationDrawer", status: "pending" },
      { id: "B3", label: "Knowledge Sources Panel + /sources route", status: "pending" },
      { id: "B4", label: "Edge Function (dumb pipe) + Modal worker scaffold", status: "pending" },
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
  ['routes', 'r_sources',  '/sources',                             'todo',    'S',  '5'],
  ['routes', 'r_cand',     '/candidates/*',                        'todo',    'M',  '6'],
  ['routes', 'r_cis',      '/cis/scope + /cis/run',                'todo',    'M',  '7'],
  ['routes', 'r_intv',     '/interventions',                       'todo',    'S',  '7'],
  ['routes', 'r_inbound',  '/simulate-inbound',                    'todo',    'S',  '6'],

  // SPECIALISTS
  ['specialists', 's1_old',   'S1 TranslationAgent (replace)',    'done',    '',   '—'],
  ['specialists', 's1_new',   'S1 QueryPlanner',                  'todoBig', 'L',  '5'],
  ['specialists', 's2',       'S2 RAGAgent',                      'done',    '',   '—'],
  ['specialists', 's3_old',   'S3 SQLAgent (refactor)',           'done',    '',   '—'],
  ['specialists', 's3_new',   'S3 SQLExecutor',                   'todo',    'S',  '5'],
  ['specialists', 'sql_tpl',  'sql_templates dict',               'todo',    'S',  '5'],
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
  ['edge', 'ef_inbound',    'inbound-email receiver (dumb pipe)', 'todo',    'M',  '6'],

  // WORKER
  ['worker', 'w_processor', 'inbound_processor.py',               'todo',    'M',  '6'],
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
renderSprints();
renderChangelog();
