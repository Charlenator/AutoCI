'use client'

/**
 * RAGcruitment — Technical Architecture Brief
 * Route: /brief
 *
 * Dependencies (add to package.json if not already present):
 *   npm install reactflow
 *
 * Place this file at: app/brief/page.tsx
 * Create app/brief/layout.tsx to strip the global nav for this route (see bottom of file).
 */

import { useMemo } from 'react'
import ReactFlow, {
  Background,
  BackgroundVariant,
  Handle,
  Position,
  type Node,
  type Edge,
  type NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'

/* ─────────────────────────────────────────────────────────────────────────────
   DESIGN TOKENS
   Mirrors globals.css :root. Inline so this page is fully portable.
───────────────────────────────────────────────────────────────────────────── */
const C = {
  bg:        '#FAFAF7',
  paper:     '#FFFFFF',
  ink:       '#153243',
  ink2:      '#284B63',
  accent:    '#C44536',
  sageTint:  '#E5E7DF',
  sageWash:  '#F1F2EC',
  line:      '#E1E2DA',
  lineStr:   '#C8CCC0',
  text:      '#1F2A30',
  textSoft:  '#4A5760',
  muted:     '#6B7470',
  // QTC dark surface — used for the flow canvas only
  dbBg:      '#0E1B22',
  dbSurf:    '#111D25',
  dbLine:    '#1F343F',
  dbText:    '#C4D5DE',
  dbMute:    '#6B8593',
  dbAccent:  '#E8B563',
  dbGreen:   '#4A9A7A',
} as const

const MONO = 'var(--font-mono, ui-monospace, "SF Mono", monospace)'
const SANS = 'var(--font-sans, -apple-system, "Segoe UI", sans-serif)'

/* ─────────────────────────────────────────────────────────────────────────────
   REACT FLOW — CUSTOM NODE TYPES
───────────────────────────────────────────────────────────────────────────── */

/** Wide container node — Frontend and Ingestion layers */
function LayerNode({ data }: { data: { eyebrow: string; slots: string[]; variant?: 'top' | 'bottom' } }) {
  const isTop = data.variant !== 'bottom'
  return (
    <div style={{
      width: 580,
      background: isTop ? '#101E28' : '#070E14',
      border: `1px solid ${isTop ? '#223344' : C.dbLine}`,
      borderRadius: 8,
      overflow: 'hidden',
      fontFamily: MONO,
    }}>
      {!isTop && <Handle type="target" position={Position.Top} style={hStyle} />}
      <div style={{
        padding: '7px 14px',
        borderBottom: `1px solid ${C.dbLine}`,
        background: isTop ? 'rgba(232,181,99,0.06)' : 'rgba(255,255,255,0.02)',
      }}>
        <span style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: isTop ? C.dbAccent : C.dbMute }}>
          {data.eyebrow}
        </span>
      </div>
      <div style={{ display: 'flex', gap: 6, padding: '10px 10px' }}>
        {data.slots.map(s => (
          <div key={s} style={{
            flex: 1,
            padding: '8px 10px',
            background: 'rgba(255,255,255,0.025)',
            border: `1px solid ${C.dbLine}`,
            borderRadius: 5,
            color: C.dbText,
            fontSize: 10,
            textAlign: 'center',
            lineHeight: 1.5,
          }}>
            {s}
          </div>
        ))}
      </div>
      {isTop && <Handle type="source" position={Position.Bottom} style={hStyle} />}
    </div>
  )
}

/** The central router — ink-coloured focal point */
function RouterNode({ data }: { data: { label: string } }) {
  return (
    <div style={{
      background: C.ink,
      border: `1px solid ${C.ink2}`,
      borderRadius: 6,
      padding: '11px 24px',
      textAlign: 'center',
      color: '#fff',
      minWidth: 220,
      fontFamily: MONO,
      position: 'relative',
    }}>
      <Handle type="target" position={Position.Top} style={hStyle} />
      <div style={{ fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.38)', marginBottom: 5 }}>
        ORCHESTRATOR
      </div>
      <div style={{ fontSize: 12.5, fontWeight: 600, letterSpacing: '0.03em', color: '#fff' }}>
        {data.label}
      </div>
      <Handle type="source" position={Position.Bottom} style={hStyle} />
    </div>
  )
}

/** Individual specialised agent */
function AgentNode({ data }: { data: { label: string; desc: string } }) {
  return (
    <div style={{
      background: C.dbSurf,
      border: `1px solid ${C.dbLine}`,
      borderRadius: 6,
      padding: '10px 13px',
      width: 152,
      fontFamily: MONO,
    }}>
      <Handle type="target" position={Position.Top} style={hStyle} />
      <div style={{ fontSize: 8.5, letterSpacing: '0.16em', textTransform: 'uppercase', color: C.dbAccent, marginBottom: 5 }}>
        AGENT
      </div>
      <div style={{ fontSize: 10.5, color: C.dbText, lineHeight: 1.45, fontWeight: 500, marginBottom: 4 }}>
        {data.label}
      </div>
      <div style={{ fontSize: 9.5, color: C.dbMute, lineHeight: 1.4 }}>
        {data.desc}
      </div>
      <Handle type="source" position={Position.Bottom} style={hStyle} />
    </div>
  )
}

/** Supabase persistence layer */
function PersistenceNode({ data }: { data: { rows: { name: string; desc: string }[] } }) {
  return (
    <div style={{
      width: 580,
      background: '#0A1820',
      border: `1px solid #2A4858`,
      borderRadius: 8,
      overflow: 'hidden',
      fontFamily: MONO,
    }}>
      <Handle type="target" position={Position.Top} style={hStyle} />
      <Handle type="source" position={Position.Bottom} style={hStyle} />
      <div style={{ padding: '7px 14px', borderBottom: `1px solid ${C.dbLine}` }}>
        <span style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.dbGreen }}>
          Supabase Persistence &amp; Data Fabric
        </span>
      </div>
      <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 5 }}>
        {data.rows.map(r => (
          <div key={r.name} style={{
            display: 'flex', alignItems: 'baseline', gap: 10,
            padding: '6px 10px',
            background: 'rgba(74,154,122,0.05)',
            border: `1px solid rgba(74,154,122,0.12)`,
            borderRadius: 4,
          }}>
            <span style={{ fontSize: 10, color: C.dbGreen, minWidth: 8 }}>•</span>
            <div>
              <span style={{ fontSize: 10.5, color: C.dbText, fontWeight: 600 }}>{r.name}:</span>
              <span style={{ fontSize: 9.5, color: C.dbMute, marginLeft: 8 }}>{r.desc}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const hStyle: React.CSSProperties = {
  background: C.dbAccent,
  border: 'none',
  width: 8,
  height: 8,
}

/* ─────────────────────────────────────────────────────────────────────────────
   FLOW DATA
───────────────────────────────────────────────────────────────────────────── */

const NODES: Node[] = [
  {
    id: 'frontend',
    type: 'layer',
    position: { x: 50, y: 20 },
    data: {
      eyebrow: 'RAGcruitment Platform Frontend (Next.js 15)',
      slots: ['Hybrid Chat\n(RAG + Trace)', 'Candidate Search\n(SQL Analytics)', 'CI Dashboard\n(DMAIC Vision)'],
      variant: 'top',
    },
  },
  {
    id: 'router',
    type: 'router',
    position: { x: 230, y: 175 },
    data: { label: 'Intent Router Agent' },
  },
  {
    id: 'planner',
    type: 'agent',
    position: { x: 18, y: 310 },
    data: { label: 'Hybrid Query Planner', desc: 'SQL Templates' },
  },
  {
    id: 'sqlgen',
    type: 'agent',
    position: { x: 184, y: 310 },
    data: { label: 'Dynamic SQL Generator', desc: 'Ad-hoc SELECT' },
  },
  {
    id: 'rag',
    type: 'agent',
    position: { x: 350, y: 310 },
    data: { label: 'Semantic RAG Agent', desc: 'pgvector cosine' },
  },
  {
    id: 'translation',
    type: 'agent',
    position: { x: 512, y: 310 },
    data: { label: 'Translation API Agent', desc: 'Market Intel' },
  },
  {
    id: 'supabase',
    type: 'persistence',
    position: { x: 50, y: 455 },
    data: {
      rows: [
        { name: 'Postgres', desc: 'Relational core — candidates, pipeline_events, hires, offer_outcomes, agent_invocations' },
        { name: 'pgvector', desc: 'Knowledge mesh — DMAIC docs, market intel, kaizen cases, CV chunks (384-dim)' },
        { name: 'Storage', desc: 'Document store — .docx / .pdf CV attachments from inbound email pipeline' },
      ],
    },
  },
  {
    id: 'ingestion',
    type: 'layer',
    position: { x: 50, y: 622 },
    data: {
      eyebrow: 'Ingestion & External Integration',
      slots: ['Resend Webhook\n→ Edge Fn → Modal', 'Tavily · Adzuna\nNewsAPI', 'Cal.com\nResend Outbound', 'DeepSeek-V3\nGPT-4o-mini'],
      variant: 'bottom',
    },
  },
]

const eStyle = { stroke: C.dbAccent, strokeWidth: 1.5, strokeOpacity: 0.55 }
const eStyleSolid = { stroke: C.dbGreen, strokeWidth: 1.5, strokeOpacity: 0.45 }

const EDGES: Edge[] = [
  { id: 'f-r',   source: 'frontend',     target: 'router',    animated: true,  style: eStyle },
  { id: 'r-p',   source: 'router',       target: 'planner',   animated: true,  style: eStyle },
  { id: 'r-s',   source: 'router',       target: 'sqlgen',    animated: true,  style: eStyle },
  { id: 'r-ra',  source: 'router',       target: 'rag',       animated: true,  style: eStyle },
  { id: 'r-t',   source: 'router',       target: 'translation', animated: true, style: eStyle },
  { id: 'p-db',  source: 'planner',      target: 'supabase',  style: eStyleSolid },
  { id: 's-db',  source: 'sqlgen',       target: 'supabase',  style: eStyleSolid },
  { id: 'ra-db', source: 'rag',          target: 'supabase',  style: eStyleSolid },
  { id: 't-db',  source: 'translation',  target: 'supabase',  style: eStyleSolid },
  { id: 'db-i',  source: 'supabase',     target: 'ingestion', animated: true,
    style: { stroke: C.dbMute, strokeWidth: 1.5, strokeDasharray: '5 3' } },
]

/* ─────────────────────────────────────────────────────────────────────────────
   SUB-COMPONENTS
───────────────────────────────────────────────────────────────────────────── */

function SectionHeader({ num, title }: { num: string; title: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 24,
      paddingBottom: 16, borderBottom: `1px solid ${C.line}`,
    }}>
      <span style={{
        fontFamily: MONO, fontSize: 9.5, color: C.ink2, letterSpacing: '0.14em',
        padding: '3px 9px', border: `1px solid ${C.line}`, borderRadius: 4,
      }}>
        {num}
      </span>
      <h2 style={{ fontFamily: SANS, fontSize: 22, fontWeight: 650, color: C.ink, letterSpacing: '-0.02em', margin: 0 }}>
        {title}
      </h2>
    </div>
  )
}

const AGENTS_DATA = [
  { name: 'Query Planner',             desc: 'LLM-driven planner that analyses chat queries and selects the retrieval strategy — SQL template, freeform SELECT, RAG search, or live web augmentation.' },
  { name: 'RAG Agent',                 desc: 'Hybrid semantic search over corpus_chunks via pgvector (cosine similarity) with full-text fallback.' },
  { name: 'SQL Template Executor',     desc: 'Pre-validated SQL execution against Supabase via run_select_query RPC. Used by the RAG chatbot for structured analytics.' },
  { name: 'Ad-hoc SQL Executor',       desc: 'When no SQL template matches, the planner generates a raw read-only SELECT. Re-validated by a safety-check regex before reaching the DB.' },
  { name: 'Research Agent',            desc: 'Fetches market intelligence from Tavily, NewsAPI, and Adzuna. Persists results to corpus_chunks for the live augmentation path.' },
  { name: 'CV Classifier',             desc: 'LLM-driven classifier that judges whether extracted text is a CV/résumé. First gate in the inbound email pipeline.' },
  { name: 'CV Extractor',              desc: 'Extracts structured fields — name, email, skills, experience, education — from .docx CVs via python-docx + LLM.' },
  { name: 'Confidentiality Classifier',desc: 'Classifies text as containing personal or confidential data. Defaults to confidential=True to prevent accidental leakage.' },
  { name: 'Internal Benchmarking',     desc: 'Computes internal pipeline KPIs — TTF, stage conversions, offer acceptance rate. Used exclusively in the Kaizen detection phase.' },
]

function AgentTable() {
  return (
    <div style={{ border: `1px solid ${C.line}`, borderRadius: 8, overflow: 'hidden', background: C.paper }}>
      {/* Header */}
      <div style={{ display: 'grid', gridTemplateColumns: '196px 1fr', background: C.sageWash, borderBottom: `1px solid ${C.line}` }}>
        <div style={{ padding: '8px 16px', fontFamily: MONO, fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase' as const, color: C.muted }}>Agent</div>
        <div style={{ padding: '8px 18px', fontFamily: MONO, fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase' as const, color: C.muted, borderLeft: `1px solid ${C.line}` }}>Responsibility</div>
      </div>
      {AGENTS_DATA.map((agent, i) => (
        <div
          key={agent.name}
          style={{
            display: 'grid', gridTemplateColumns: '196px 1fr',
            borderBottom: i < AGENTS_DATA.length - 1 ? `1px solid ${C.line}` : 'none',
          }}
        >
          <div style={{
            padding: '12px 16px', fontFamily: MONO, fontSize: 11, fontWeight: 600,
            color: C.ink, display: 'flex', alignItems: 'center',
          }}>
            {agent.name}
          </div>
          <div style={{
            padding: '12px 18px', fontSize: 12.5, color: C.textSoft, lineHeight: 1.65,
            borderLeft: `1px solid ${C.line}`, display: 'flex', alignItems: 'center', fontWeight: 300,
          }}>
            {agent.desc}
          </div>
        </div>
      ))}
    </div>
  )
}

function KnowledgeCard({ title, accent, items }: {
  title: string
  accent: string
  items: { label: string; desc: string }[]
}) {
  return (
    <div style={{
      background: C.paper, border: `1px solid ${C.line}`, borderRadius: 10,
      padding: 22, position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${accent}, transparent)` }} />
      <h3 style={{
        fontFamily: MONO, fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase' as const,
        color: accent, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 10, margin: '0 0 18px',
      }}>
        {title}
        <span style={{ flex: 1, height: 1, background: C.line, display: 'block' }} />
      </h3>
      {items.map(item => (
        <div key={item.label} style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'flex-start' }}>
          <span style={{ color: accent, fontFamily: MONO, fontSize: 11, flexShrink: 0, marginTop: 1 }}>→</span>
          <div>
            <strong style={{ fontFamily: MONO, fontSize: 10.5, fontWeight: 600, color: C.text, display: 'block', marginBottom: 2 }}>
              {item.label}
            </strong>
            <span style={{ fontSize: 12.5, color: C.textSoft, lineHeight: 1.6 }}>{item.desc}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

const STACK_ITEMS = [
  { label: 'Orchestration',  value: 'FastAPI · Modal (Serverless)' },
  { label: 'LLM Routing',   value: 'LiteLLM (provider-agnostic)' },
  { label: 'Database',       value: 'Supabase · Postgres' },
  { label: 'Vector Store',   value: 'pgvector (384-dim)' },
  { label: 'Embedding',      value: 'BAAI/bge-small-en-v1.5' },
  { label: 'Frontend',       value: 'Next.js 15 · Vercel' },
  { label: 'Email',          value: 'Resend · Inbound Webhook' },
  { label: 'Scheduling',     value: 'Cal.com' },
  { label: 'Web Intel',      value: 'Tavily · NewsAPI · Adzuna' },
  { label: 'Trigger Layer',  value: 'Supabase Edge Functions' },
  { label: 'Intelligence',   value: 'DeepSeek-V3 · GPT-4o-mini' },
  { label: 'CV Parsing',     value: 'python-docx · LLM extraction' },
]

/* ─────────────────────────────────────────────────────────────────────────────
   PAGE ROOT
───────────────────────────────────────────────────────────────────────────── */

export default function BriefPage() {
  const nodeTypes = useMemo<NodeTypes>(() => ({
    layer:       LayerNode,
    router:      RouterNode,
    agent:       AgentNode,
    persistence: PersistenceNode,
  }), [])

  return (
    <div style={{ background: C.bg, minHeight: '100vh', fontFamily: SANS, WebkitFontSmoothing: 'antialiased' }}>

      {/* ── HERO ── */}
      <div style={{ background: C.ink, color: '#fff', padding: '72px 0 64px', borderBottom: `3px solid ${C.dbAccent}` }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 40px' }}>

          {/* eyebrow */}
          <div style={{
            fontFamily: MONO, fontSize: 10, letterSpacing: '0.22em', textTransform: 'uppercase',
            color: C.dbAccent, marginBottom: 22, display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <span style={{ width: 28, height: 1, background: C.dbAccent, display: 'inline-block' }} />
            Technical Architecture Brief
          </div>

          {/* heading */}
          <h1 style={{ fontSize: 'clamp(40px, 5.5vw, 62px)', fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1.08, margin: '0 0 22px', color: '#fff' }}>
            RAGcruitment
            <br />
            <span style={{ color: C.dbAccent, fontWeight: 400, fontStyle: 'italic' }}>Intelligence Platform</span>
          </h1>

          {/* sub */}
          <p style={{ fontSize: 15, color: 'rgba(196,213,222,0.7)', maxWidth: 580, lineHeight: 1.8, margin: '0 0 40px', fontWeight: 300 }}>
            An agentic recruitment operations platform that replaces manual screening with a mesh of specialised AI agents — wired directly to email, calendar, structured databases, and live market intelligence feeds.
          </p>

          {/* chips */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['Multi-Agent Orchestration', 'Hybrid RAG + SQL', 'pgvector · Supabase · Modal', 'Next.js 15 · FastAPI'].map(label => (
              <span key={label} style={{
                fontFamily: MONO, fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase',
                color: 'rgba(196,213,222,0.5)', border: '1px solid rgba(196,213,222,0.14)',
                padding: '5px 13px', borderRadius: 4,
              }}>
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── CONTENT ── */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 40px 100px' }}>

        {/* ── SECTION 01 — ORCHESTRATION ── */}
        <section style={{ paddingTop: 60 }}>
          <SectionHeader num="01" title="The Multi-Agent Orchestration Layer" />
          <p style={{ color: C.textSoft, fontSize: 14, lineHeight: 1.8, marginBottom: 32, maxWidth: 700 }}>
            The core of RAGcruitment is not a single prompt — it is a sophisticated{' '}
            <strong style={{ color: C.ink, fontWeight: 600 }}>Orchestration Mesh</strong>. A specialised Router
            Agent analyses the intent of every request and delegates to a fleet of purpose-built sub-agents,
            each with a tightly scoped responsibility.
          </p>

          <AgentTable />

          {/* React Flow diagram */}
          <div style={{ marginTop: 44 }}>
            <div style={{
              fontFamily: MONO, fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase',
              color: C.muted, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <span style={{ width: 16, height: 1, background: C.lineStr, display: 'inline-block' }} />
              System Architecture — Interactive
            </div>

            {/* Canvas */}
            <div style={{
              height: 780,
              borderRadius: 10,
              overflow: 'hidden',
              border: `1px solid ${C.dbLine}`,
              background: C.dbBg,
            }}>
              <ReactFlow
                nodes={NODES}
                edges={EDGES}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.14 }}
                proOptions={{ hideAttribution: true }}
                minZoom={0.35}
                maxZoom={2}
                defaultEdgeOptions={{ type: 'smoothstep' }}
              >
                <Background
                  color={C.dbLine}
                  variant={BackgroundVariant.Dots}
                  gap={22}
                  size={1.2}
                />
              </ReactFlow>
            </div>
            <p style={{ fontFamily: MONO, fontSize: 10.5, color: C.muted, marginTop: 10 }}>
              Scroll to zoom · drag to pan
            </p>
          </div>
        </section>

        {/* ── SECTION 02 — KNOWLEDGE MESH ── */}
        <section style={{ paddingTop: 64 }}>
          <SectionHeader num="02" title="The Hybrid Knowledge Mesh" />
          <p style={{ color: C.textSoft, fontSize: 14, lineHeight: 1.8, marginBottom: 28, maxWidth: 700 }}>
            RAGcruitment operates across a dual-layer knowledge base, enabling agents to reason across both
            structured relational data and unstructured document corpora simultaneously.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <KnowledgeCard
              title="A — Structured SQL (Postgres)"
              accent={C.ink2}
              items={[
                { label: 'Recruitment Pipeline',   desc: 'Full visibility into candidates, pipeline_events, hires, and offer_outcomes.' },
                { label: 'Market Benchmarking',    desc: 'industry_benchmarks (TTF/OAR by region) and adzuna_postings for real-time salary parity.' },
                { label: 'Observability',          desc: '500+ traces in agent_invocations tracking cost, token usage, and latency per request.' },
                { label: 'Automation Queue',       desc: 'inbound_emails manages CV pipeline state from Pending → Processed.' },
              ]}
            />
            <KnowledgeCard
              title="B — Vector Corpora (pgvector)"
              accent={C.dbGreen}
              items={[
                { label: 'Market & News',          desc: 'Cached market_intel and industry_news snippets from live Tavily and NewsAPI calls.' },
                { label: 'Six Sigma Core',         desc: 'dmaic_methodology reference docs — SIPOC, Five Whys, Kanban — for CI grounding.' },
                { label: 'Institutional Memory',   desc: 'kaizen_case_studies — prior Root Cause Analyses used as precedent for new problems.' },
                { label: 'Applicant CVs',          desc: 'CV text chunked and embedded for semantic candidate search beyond structured fields.' },
              ]}
            />
          </div>

          <div style={{
            marginTop: 16, padding: '12px 18px', fontFamily: MONO, fontSize: 11, color: C.muted,
            background: C.sageWash, border: `1px solid ${C.line}`, borderRadius: 6,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <span style={{ color: C.dbGreen }}>◆</span>
            Embeddings: BAAI/bge-small-en-v1.5 · 384 dimensions · Cosine similarity retrieval with full-text fallback
          </div>
        </section>

        {/* ── SECTION 03 — TECHNICAL STACK ── */}
        <section style={{ paddingTop: 64 }}>
          <SectionHeader num="03" title="Technical Stack" />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {STACK_ITEMS.map(item => (
              <div
                key={item.label}
                style={{
                  background: C.paper,
                  border: `1px solid ${C.line}`,
                  borderRadius: 6,
                  padding: '14px 16px',
                }}
              >
                <div style={{ fontFamily: MONO, fontSize: 9, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.14em', marginBottom: 5 }}>
                  {item.label}
                </div>
                <div style={{ fontFamily: MONO, fontSize: 12, color: C.ink, fontWeight: 600 }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* ── FOOTER ── */}
      <div style={{
        borderTop: `1px solid ${C.line}`, padding: '22px 40px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        maxWidth: 900, margin: '0 auto',
      }}>
        <span style={{ fontFamily: MONO, fontSize: 10, color: C.muted, letterSpacing: '0.08em' }}>
          Confidential · Technical Architecture Brief · 2025
        </span>
        <span style={{ fontFamily: MONO, fontSize: 13, color: C.ink, fontWeight: 700, letterSpacing: '-0.02em' }}>
          RAGcruitment
        </span>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────────────────
   LAYOUT SHIM
   Save this separately as:  app/brief/layout.tsx
   Strips the global nav/sidebar so the brief renders full-screen.
─────────────────────────────────────────────────────────────────────────────

export default function BriefLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

*/