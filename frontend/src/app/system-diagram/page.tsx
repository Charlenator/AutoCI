"use client";

import React from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Position,
  Node,
  Edge,
  MarkerType,
  Handle,
} from "reactflow";
import "reactflow/dist/base.css";
import "./system-diagram.css";

/* ───────────────────────────────────────────────────────────────
 * AutoCI System Diagram — full agent + API map.
 * Visual only. Planned components have a dashed border + lower opacity.
 * Lanes (top → bottom): Frontend, API Gateway, Orchestrator, Detection,
 * Kaizen, Specialists, Tools, Database, External APIs.
 * ─────────────────────────────────────────────────────────────── */

type Family =
  | "frontend"
  | "api"
  | "orchestrator"
  | "detection"
  | "kaizen"
  | "specialist"
  | "tool"
  | "database"
  | "external"
  | "planned";

const FAMILY: Record<Family, { color: string; bg: string; label: string; icon: string }> = {
  frontend:     { color: "#2563eb", bg: "#dbeafe", label: "Frontend",       icon: "🌐" },
  api:          { color: "#7c3aed", bg: "#ede9fe", label: "API Gateway",    icon: "🔌" },
  orchestrator: { color: "#ea580c", bg: "#ffedd5", label: "Orchestrator",   icon: "⚡" },
  detection:    { color: "#ca8a04", bg: "#fef9c3", label: "Detection",      icon: "🔍" },
  kaizen:       { color: "#dc2626", bg: "#fee2e2", label: "Kaizen (DMAIC)", icon: "🔄" },
  specialist:   { color: "#0d9488", bg: "#ccfbf1", label: "Specialists",    icon: "🧠" },
  tool:         { color: "#475569", bg: "#e2e8f0", label: "Tools",          icon: "🛠" },
  database:     { color: "#059669", bg: "#d1fae5", label: "Database",       icon: "🗄" },
  external:     { color: "#be185d", bg: "#fce7f3", label: "External APIs",  icon: "🌍" },
  planned:      { color: "#6b7280", bg: "#f1f5f9", label: "Planned",        icon: "📋" },
};

interface ServiceNodeData {
  id: string;        // short ID like D1, K_WRITEUP
  title: string;     // human label
  desc: string;      // one-line description
  family: Family;
  planned?: boolean;
}

const ServiceNode = ({ data }: { data: ServiceNodeData }) => {
  const fam = FAMILY[data.family];
  return (
    <div
      className={`service-node ${data.planned ? "planned" : ""}`}
      style={{
        borderColor: fam.color,
        background: fam.bg,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: fam.color, width: 8, height: 8 }} />
      <div className="service-id" style={{ background: fam.color }}>
        {data.id}
      </div>
      <div className="service-title">{data.title}</div>
      <div className="service-desc">{data.desc}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: fam.color, width: 8, height: 8 }} />
    </div>
  );
};

const nodeTypes = { service: ServiceNode };

/* ── Layout grid (x,y in pixels) ────────────────────────────────
 * Each "lane" is a horizontal row spaced 180px apart vertically.
 * Within a lane, nodes are spaced ~220px apart horizontally.
 */

const LANE_Y = {
  frontend: 0,
  api: 180,
  orch: 380,
  detection: 580,
  kaizen: 580,
  specialist: 580,
  kaizenSub: 760, // K4/K5 under K3, K_WRITEUP after K7
  tool: 940,
  db: 1120,
  external: 1300,
};

const initialNodes: Node[] = [
  // ── FRONTEND (top) ────────────────────────────────────────────
  {
    id: "F1", type: "service", position: { x: 880, y: LANE_Y.frontend },
    data: {
      id: "F1", title: "Dashboard UI",
      desc: "Next.js + SSE — KPI tiles, chat, timeline, HITL gates, writeup cards",
      family: "frontend",
    } as ServiceNodeData,
  },

  // ── API GATEWAY ────────────────────────────────────────────────
  { id: "A1",  type: "service", position: { x: 100,  y: LANE_Y.api },
    data: { id: "A1",  title: "POST /trigger/manual",       desc: "Launch Kaizen with custom brief", family: "api" } as ServiceNodeData },
  { id: "A2",  type: "service", position: { x: 340,  y: LANE_Y.api },
    data: { id: "A2",  title: "POST /trigger/goal-review",  desc: "Auto-pick worst KPI gap",         family: "api" } as ServiceNodeData },
  { id: "A3",  type: "service", position: { x: 580,  y: LANE_Y.api },
    data: { id: "A3",  title: "GET /sessions/:id/stream",   desc: "SSE event stream",                family: "api" } as ServiceNodeData },
  { id: "A4",  type: "service", position: { x: 820,  y: LANE_Y.api },
    data: { id: "A4",  title: "POST /sessions/:id/respond", desc: "HITL: advance / ask / abort",     family: "api" } as ServiceNodeData },
  { id: "A5",  type: "service", position: { x: 1060, y: LANE_Y.api },
    data: { id: "A5",  title: "POST /chat/query",           desc: "S1 → S2/S3 routing",              family: "api" } as ServiceNodeData },
  { id: "A6",  type: "service", position: { x: 1300, y: LANE_Y.api },
    data: { id: "A6",  title: "GET /metrics/kpis",          desc: "3 KPI tiles, role-scoped",        family: "api" } as ServiceNodeData },
  { id: "A7",  type: "service", position: { x: 1540, y: LANE_Y.api },
    data: { id: "A7",  title: "GET /metrics/cost",          desc: "USD + tokens (cached / uncached)", family: "api" } as ServiceNodeData },
  { id: "A8",  type: "service", position: { x: 1780, y: LANE_Y.api },
    data: { id: "A8",  title: "POST /knowledge/{seed,update}", desc: "Seed corpora + live API ingest", family: "api" } as ServiceNodeData },

  // ── ORCHESTRATOR ───────────────────────────────────────────────
  { id: "O2",  type: "service", position: { x: 880, y: LANE_Y.orch },
    data: { id: "O2",  title: "MetaOrchestrator",
      desc: "Phase-gated DMAIC; HITL queue.Queue; SSE pump",
      family: "orchestrator" } as ServiceNodeData },

  // ── DETECTION (left cluster, lane 4) ───────────────────────────
  { id: "D1", type: "service", position: { x: 100, y: LANE_Y.detection },
    data: { id: "D1", title: "Internal Benchmarking", desc: "Compute TTF, conversion, OAR (role-scoped)", family: "detection" } as ServiceNodeData },
  { id: "D2", type: "service", position: { x: 340, y: LANE_Y.detection },
    data: { id: "D2", title: "External Benchmarking", desc: "industry_benchmarks + live Adzuna salary (S1)", family: "detection" } as ServiceNodeData },
  { id: "D3", type: "service", position: { x: 580, y: LANE_Y.detection },
    data: { id: "D3", title: "Gap Analysis", desc: "Severity per KPI, kaizen_required gate", family: "detection" } as ServiceNodeData },

  // ── KAIZEN (centre cluster) ────────────────────────────────────
  { id: "K1", type: "service", position: { x: 820,  y: LANE_Y.kaizen },
    data: { id: "K1", title: "Define (SIPOC)",       desc: "Brief / KPI / gap framing", family: "kaizen" } as ServiceNodeData },
  { id: "K2", type: "service", position: { x: 1060, y: LANE_Y.kaizen },
    data: { id: "K2", title: "Measure",              desc: "Baseline KPIs", family: "kaizen" } as ServiceNodeData },
  { id: "K3", type: "service", position: { x: 1300, y: LANE_Y.kaizen },
    data: { id: "K3", title: "Analyse Host",         desc: "Spawns K4 + K5; aggregates citations", family: "kaizen" } as ServiceNodeData },

  // ── KAIZEN sub-row (K4, K5 under K3; K6, K7, K_WRITEUP after) ──
  { id: "K4", type: "service", position: { x: 1180, y: LANE_Y.kaizenSub },
    data: { id: "K4", title: "Five Whys", desc: "5 × 3 perspectives, RAG-grounded", family: "kaizen" } as ServiceNodeData },
  { id: "K5", type: "service", position: { x: 1420, y: LANE_Y.kaizenSub },
    data: { id: "K5", title: "Ishikawa", desc: "6 branches, per-branch RAG", family: "kaizen" } as ServiceNodeData },
  { id: "K6", type: "service", position: { x: 820,  y: LANE_Y.kaizenSub },
    data: { id: "K6", title: "Improve", desc: "Interventions + Impact/Effort matrix, RAG-grounded", family: "kaizen" } as ServiceNodeData },
  { id: "K7", type: "service", position: { x: 1060, y: LANE_Y.kaizenSub },
    data: { id: "K7", title: "Control", desc: "Kanban (To Do only) + owner / due / KPI", family: "kaizen" } as ServiceNodeData },
  { id: "KW", type: "service", position: { x: 580,  y: LANE_Y.kaizenSub },
    data: { id: "K_WRITEUP", title: "Amazon-Narrative Writeup",
      desc: "1 DeepSeek call/phase: headline, TL;DR, findings, citations",
      family: "kaizen" } as ServiceNodeData },
  { id: "KD", type: "service", position: { x: 340,  y: LANE_Y.kaizenSub },
    data: { id: "K_DEBRIEF", title: "Email Debrief",
      desc: "Compiles all writeups → Markdown → Gmail send",
      family: "kaizen", planned: true } as ServiceNodeData },

  // ── SPECIALISTS (right cluster) ────────────────────────────────
  { id: "S1", type: "service", position: { x: 1660, y: LANE_Y.specialist },
    data: { id: "S1", title: "Translation (Intent)", desc: "Routes user query → S2 or S3", family: "specialist" } as ServiceNodeData },
  { id: "S2", type: "service", position: { x: 1660, y: LANE_Y.kaizenSub },
    data: { id: "S2", title: "RAG Retrieval", desc: "match_chunks RPC + corpus filter", family: "specialist" } as ServiceNodeData },
  { id: "S3", type: "service", position: { x: 1900, y: LANE_Y.specialist },
    data: { id: "S3", title: "SQL Agent", desc: "T1 analytics formulas + LLM-generated SQL", family: "specialist" } as ServiceNodeData },
  { id: "S4", type: "service", position: { x: 1900, y: LANE_Y.kaizenSub },
    data: { id: "S4", title: "Research", desc: "Tavily + NewsAPI + Adzuna calls + persist", family: "specialist" } as ServiceNodeData },
  { id: "S5", type: "service", position: { x: 2140, y: LANE_Y.specialist },
    data: { id: "S5", title: "Interview Prep", desc: "CV → JD fit + Calendar slots", family: "specialist", planned: true } as ServiceNodeData },

  // ── TOOLS ──────────────────────────────────────────────────────
  { id: "T1", type: "service", position: { x: 340,  y: LANE_Y.tool },
    data: { id: "T1", title: "Analytics Library", desc: "TTF, conversion, OAR, source yield (no LLM)", family: "tool" } as ServiceNodeData },
  { id: "T2", type: "service", position: { x: 580,  y: LANE_Y.tool },
    data: { id: "T2", title: "Validation Interceptor", desc: "Pydantic + sample size + z-score outliers", family: "tool" } as ServiceNodeData },
  { id: "T3", type: "service", position: { x: 820,  y: LANE_Y.tool },
    data: { id: "T3", title: "LiteLLM Router", desc: "Single-model DeepSeek; computes USD from tokens", family: "tool" } as ServiceNodeData },
  { id: "T4", type: "service", position: { x: 1060, y: LANE_Y.tool },
    data: { id: "T4", title: "Embeddings", desc: "OpenAI ada-002 → 1536-d vectors", family: "tool" } as ServiceNodeData },

  // ── DATABASE ───────────────────────────────────────────────────
  { id: "DB_TABLES", type: "service", position: { x: 580, y: LANE_Y.db },
    data: { id: "Supabase Tables",
      title: "Pipeline + Sessions",
      desc: "roles · candidates · pipeline_events · hires · offer_outcomes · industry_benchmarks · kaizen_sessions · agent_invocations · adzuna_postings",
      family: "database" } as ServiceNodeData },
  { id: "DB_RAG", type: "service", position: { x: 1060, y: LANE_Y.db },
    data: { id: "corpus_chunks",
      title: "RAG (pgvector)",
      desc: "6 corpora · ivfflat index · match_chunks RPC",
      family: "database" } as ServiceNodeData },

  // ── EXTERNAL APIs ──────────────────────────────────────────────
  { id: "E1", type: "service", position: { x: 100,  y: LANE_Y.external },
    data: { id: "E1", title: "DeepSeek", desc: "Sole LLM provider — chat completion", family: "external" } as ServiceNodeData },
  { id: "E2", type: "service", position: { x: 340,  y: LANE_Y.external },
    data: { id: "E2", title: "Adzuna", desc: "Live job postings + salary", family: "external" } as ServiceNodeData },
  { id: "E3", type: "service", position: { x: 580,  y: LANE_Y.external },
    data: { id: "E3", title: "Tavily", desc: "Web research", family: "external" } as ServiceNodeData },
  { id: "E4", type: "service", position: { x: 820,  y: LANE_Y.external },
    data: { id: "E4", title: "NewsAPI", desc: "Industry news", family: "external" } as ServiceNodeData },
  { id: "E5", type: "service", position: { x: 1060, y: LANE_Y.external },
    data: { id: "E5", title: "OpenAI Embeddings", desc: "ada-002 → 1536-d vectors", family: "external" } as ServiceNodeData },
  { id: "E6", type: "service", position: { x: 1300, y: LANE_Y.external },
    data: { id: "E6", title: "Google Calendar", desc: "Free/busy + slot proposal", family: "external", planned: true } as ServiceNodeData },
  { id: "E7", type: "service", position: { x: 1540, y: LANE_Y.external },
    data: { id: "E7", title: "Gmail API", desc: "Send Kaizen debrief + draft invites", family: "external", planned: true } as ServiceNodeData },
];

/* ── Edges ──────────────────────────────────────────────────────
 * Conventions:
 * - Solid lines: data flow at runtime
 * - Dashed lines: utility / cross-cutting (SSE pump, logging, persistence)
 * - Animated: hot path during a Kaizen
 */
const edge = (
  id: string, source: string, target: string,
  opts: { color?: string; dashed?: boolean; animated?: boolean; label?: string } = {}
): Edge => ({
  id, source, target,
  animated: opts.animated,
  label: opts.label,
  labelStyle: { fontSize: 10, fontWeight: 500, fill: "#475569" },
  labelBgStyle: { fill: "#fff", fillOpacity: 0.85 },
  labelBgPadding: [3, 5],
  labelBgBorderRadius: 4,
  style: {
    stroke: opts.color || "#94a3b8",
    strokeWidth: 2,
    strokeDasharray: opts.dashed ? "5 4" : undefined,
  },
  markerEnd: { type: MarkerType.ArrowClosed, color: opts.color || "#94a3b8", width: 16, height: 16 },
});

const initialEdges: Edge[] = [
  // Frontend → API Gateway
  edge("e-F1-A1", "F1", "A1", { color: FAMILY.api.color }),
  edge("e-F1-A2", "F1", "A2", { color: FAMILY.api.color }),
  edge("e-F1-A3", "F1", "A3", { color: FAMILY.api.color, animated: true, label: "SSE" }),
  edge("e-F1-A4", "F1", "A4", { color: FAMILY.api.color }),
  edge("e-F1-A5", "F1", "A5", { color: FAMILY.api.color }),
  edge("e-F1-A6", "F1", "A6", { color: FAMILY.api.color }),
  edge("e-F1-A7", "F1", "A7", { color: FAMILY.api.color, dashed: true }),
  edge("e-F1-A8", "F1", "A8", { color: FAMILY.api.color, dashed: true }),

  // API Gateway → Orchestrator
  edge("e-A1-O2", "A1", "O2", { color: FAMILY.orchestrator.color, animated: true }),
  edge("e-A2-O2", "A2", "O2", { color: FAMILY.orchestrator.color, animated: true }),
  edge("e-A3-O2", "A3", "O2", { color: FAMILY.orchestrator.color, dashed: true, label: "drains queue" }),
  edge("e-A4-O2", "A4", "O2", { color: FAMILY.orchestrator.color, label: "HITL" }),

  // /chat/query → S1 (NOT through orchestrator)
  edge("e-A5-S1", "A5", "S1", { color: FAMILY.specialist.color, animated: true }),

  // Orchestrator → Detection (sequential)
  edge("e-O2-D1", "O2", "D1", { color: FAMILY.detection.color, animated: true }),
  edge("e-O2-D2", "O2", "D2", { color: FAMILY.detection.color, animated: true }),
  edge("e-O2-D3", "O2", "D3", { color: FAMILY.detection.color, animated: true }),

  // Orchestrator → Kaizen phases
  edge("e-O2-K1", "O2", "K1", { color: FAMILY.kaizen.color, animated: true }),
  edge("e-O2-K2", "O2", "K2", { color: FAMILY.kaizen.color, animated: true }),
  edge("e-O2-K3", "O2", "K3", { color: FAMILY.kaizen.color, animated: true }),
  edge("e-O2-K6", "O2", "K6", { color: FAMILY.kaizen.color, animated: true }),
  edge("e-O2-K7", "O2", "K7", { color: FAMILY.kaizen.color, animated: true }),
  edge("e-O2-KW", "O2", "KW", { color: FAMILY.kaizen.color, label: "after each phase" }),
  edge("e-O2-KD", "O2", "KD", { color: FAMILY.kaizen.color, dashed: true, label: "post-Kaizen" }),

  // K3 → K4 + K5 (sub-orchestration)
  edge("e-K3-K4", "K3", "K4", { color: FAMILY.kaizen.color }),
  edge("e-K3-K5", "K3", "K5", { color: FAMILY.kaizen.color }),

  // Orchestrator → Specialists (research path + ask handler)
  edge("e-O2-S4", "O2", "S4", { color: FAMILY.specialist.color, label: "fetch market_data" }),
  edge("e-O2-S2", "O2", "S2", { color: FAMILY.specialist.color, dashed: true, label: "ask path" }),
  edge("e-O2-S3", "O2", "S3", { color: FAMILY.specialist.color, dashed: true, label: "ask path" }),

  // S1 routes to S2/S3
  edge("e-S1-S2", "S1", "S2", { color: FAMILY.specialist.color }),
  edge("e-S1-S3", "S1", "S3", { color: FAMILY.specialist.color }),

  // K4/K5/K6 use S2 (RAG) for case studies — Phase 4.5 T2.1
  edge("e-K4-S2", "K4", "S2", { color: FAMILY.specialist.color, dashed: true, label: "case studies" }),
  edge("e-K5-S2", "K5", "S2", { color: FAMILY.specialist.color, dashed: true }),
  edge("e-K6-S2", "K6", "S2", { color: FAMILY.specialist.color, dashed: true }),

  // Detection → Tools
  edge("e-D1-T1", "D1", "T1", { color: FAMILY.tool.color }),
  edge("e-D2-T1", "D2", "T1", { color: FAMILY.tool.color }),

  // All LLM-using agents → T3 (LiteLLM)
  edge("e-D3-T3",  "D3", "T3", { color: FAMILY.tool.color }),
  edge("e-K1-T3",  "K1", "T3", { color: FAMILY.tool.color }),
  edge("e-K2-T3",  "K2", "T3", { color: FAMILY.tool.color }),
  edge("e-K3-T3",  "K3", "T3", { color: FAMILY.tool.color }),
  edge("e-K4-T3",  "K4", "T3", { color: FAMILY.tool.color }),
  edge("e-K5-T3",  "K5", "T3", { color: FAMILY.tool.color }),
  edge("e-K6-T3",  "K6", "T3", { color: FAMILY.tool.color }),
  edge("e-K7-T3",  "K7", "T3", { color: FAMILY.tool.color }),
  edge("e-KW-T3",  "KW", "T3", { color: FAMILY.tool.color }),
  edge("e-S1-T3",  "S1", "T3", { color: FAMILY.tool.color, dashed: true }),
  edge("e-S3-T3",  "S3", "T3", { color: FAMILY.tool.color }),

  // T3 → DeepSeek (sole LLM provider)
  edge("e-T3-E1", "T3", "E1", { color: FAMILY.external.color, animated: true }),

  // S2 → T4 (embed query) → OpenAI; S2 → DB_RAG (match_chunks)
  edge("e-S2-T4", "S2", "T4", { color: FAMILY.tool.color }),
  edge("e-T4-E5", "T4", "E5", { color: FAMILY.external.color }),
  edge("e-S2-DBRAG", "S2", "DB_RAG", { color: FAMILY.database.color, label: "match_chunks" }),

  // S4 → External live APIs
  edge("e-S4-E2", "S4", "E2", { color: FAMILY.external.color }),
  edge("e-S4-E3", "S4", "E3", { color: FAMILY.external.color }),
  edge("e-S4-E4", "S4", "E4", { color: FAMILY.external.color }),
  edge("e-S4-T4",  "S4", "T4", { color: FAMILY.tool.color, dashed: true, label: "embed → corpus" }),

  // T2 wraps every agent (validation interceptor) — represented as one cross-edge
  edge("e-T2-O2",  "T2", "O2", { color: FAMILY.tool.color, dashed: true, label: "validates" }),

  // Persistence: all agents write to Supabase tables; sample edges
  edge("e-O2-DBT", "O2", "DB_TABLES", { color: FAMILY.database.color, label: "kaizen_sessions" }),
  edge("e-T3-DBT", "T3", "DB_TABLES", { color: FAMILY.database.color, dashed: true, label: "agent_invocations" }),
  edge("e-S4-DBT", "S4", "DB_TABLES", { color: FAMILY.database.color, dashed: true, label: "adzuna_postings" }),
  edge("e-S4-DBRAG","S4","DB_RAG",   { color: FAMILY.database.color, dashed: true, label: "embed → chunks" }),
  edge("e-D1-DBT", "D1", "DB_TABLES", { color: FAMILY.database.color, dashed: true }),
  edge("e-D2-DBT", "D2", "DB_TABLES", { color: FAMILY.database.color, dashed: true }),
  edge("e-S3-DBT", "S3", "DB_TABLES", { color: FAMILY.database.color, dashed: true }),

  // Planned: K_DEBRIEF + S5 → Google APIs
  edge("e-KD-E7", "KD", "E7", { color: FAMILY.external.color, dashed: true }),
  edge("e-S5-E6", "S5", "E6", { color: FAMILY.external.color, dashed: true }),
  edge("e-S5-E7", "S5", "E7", { color: FAMILY.external.color, dashed: true }),
];

const Legend = () => (
  <div className="legend">
    <h3>Components</h3>
    <div className="legend-items">
      {Object.entries(FAMILY).map(([key, fam]) => (
        <div key={key} className="legend-item">
          <div className="legend-color" style={{ background: fam.color }} />
          <span>{fam.icon} {fam.label}</span>
        </div>
      ))}
    </div>
    <div className="legend-divider" />
    <div className="legend-edge-key">
      <div className="legend-edge"><span className="line solid" /> Runtime data flow</div>
      <div className="legend-edge"><span className="line dashed" /> Utility / persistence</div>
      <div className="legend-edge"><span className="line animated" /> Hot path during Kaizen</div>
    </div>
  </div>
);

export default function SystemDiagram() {
  return (
    <div className="system-diagram-container">
      <header className="diagram-header">
        <div className="header-content">
          <h1>AutoCI System Architecture</h1>
          <p>Full agent + API map — frontend ➜ orchestrator ➜ DMAIC ➜ data + external APIs</p>
        </div>
      </header>

      <div className="diagram-wrapper">
        <ReactFlow
          nodes={initialNodes}
          edges={initialEdges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.2}
          maxZoom={1.6}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable
        >
          <Background color="#cbd5e1" gap={24} />
          <Controls />
          <MiniMap
            style={{ width: 220, height: 160, borderRadius: 8 }}
            nodeColor={(n) => {
              const fam = (n.data as ServiceNodeData)?.family;
              return fam ? FAMILY[fam].color : "#94a3b8";
            }}
          />
        </ReactFlow>

        <Legend />
      </div>
    </div>
  );
}
