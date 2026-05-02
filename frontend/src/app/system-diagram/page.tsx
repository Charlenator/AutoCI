"use client";

import React, { useCallback, useMemo, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Node,
  Edge,
} from 'reactflow';
import 'reactflow/dist/base.css';
import './system-diagram.css';

// Custom Node Components
const TierNode = ({ data }: { data: any }) => (
  <div className="tier-node">
    <div className="tier-header" style={{ backgroundColor: data.color }}>
      <span className="tier-icon">{data.icon}</span>
      <span className="tier-title">{data.title}</span>
    </div>
    <div className="tier-content">
      <div className="tier-description">{data.description}</div>
      {data.children && (
        <div className="tier-children">
          {data.children.map((child: any, i: number) => (
            <div key={i} className="tier-child">
              <span className="child-bullet">{child.icon}</span>
              <span className="child-label">{child.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  </div>
);

const ProcessNode = ({ data }: { data: any }) => (
  <div className="process-node">
    <div className="process-icon">{data.icon}</div>
    <div className="process-title">{data.title}</div>
    <div className="process-desc">{data.description}</div>
  </div>
);

const HighlightNode = ({ data }: { data: any }) => (
  <div className="highlight-node">
    <div className="highlight-icon">{data.icon}</div>
    <div className="highlight-title">{data.title}</div>
    <div className="highlight-subtitle">{data.subtitle}</div>
  </div>
);

// Type definitions for node data
interface TierData {
  title: string;
  description: string;
  color: string;
  icon: string;
  children: { icon: string; label: string }[];
}

interface HighlightData {
  icon: string;
  title: string;
  subtitle: string;
}

interface ProcessData {
  icon: string;
  title: string;
  description: string;
}

type NodeData = TierData | HighlightData | ProcessData;

const nodeTypes = {
  tier: TierNode,
  process: ProcessNode,
  highlight: HighlightNode,
};

// Node Definitions
const initialNodes: Node[] = [
  // Tier 3: Meta-Orchestrator
  {
    id: 'tier3',
    type: 'tier',
    position: { x: 400, y: 50 },
    data: {
      title: 'Tier 3 — Meta-Orchestrator',
      description: '"What problems should we be solving?"',
      color: '#7c3aed',
      icon: '⚡',
      children: [
        { icon: '🔍', label: 'Problem Prioritization' },
        { icon: '📊', label: 'Impact Scoring' },
        { icon: '🎯', label: 'Kaizen Launch' },
      ],
    } as TierData,
  },

  // Tier 2: Detection Layer
  {
    id: 'tier2',
    type: 'tier',
    position: { x: 400, y: 250 },
    data: {
      title: 'Tier 2 — Problem Detection',
      description: 'Internal + External Benchmarking + Gap Analysis',
      color: '#d97706',
      icon: '🔍',
      children: [
        { icon: '📈', label: 'Internal Benchmarks' },
        { icon: '🌍', label: 'External Data (Adzuna)' },
        { icon: '⚠️', label: 'Gap Severity Score' },
      ],
    } as TierData,
  },

  // Tier 1: Kaizen Engine
  {
    id: 'tier1',
    type: 'tier',
    position: { x: 400, y: 500 },
    data: {
      title: 'Tier 1 — Kaizen Engine (DMAIC)',
      description: 'Phase-gated. Every step a Durable DBOS workflow',
      color: '#dc2626',
      icon: '🔄',
      children: [
        { icon: '📋', label: 'Define (SIPOC)' },
        { icon: '📏', label: 'Measure (Metrics)' },
        { icon: '🔎', label: 'Analyse (5 Whys)' },
        { icon: '📈', label: 'Improve (Matrix)' },
        { icon: '✅', label: 'Control (Kanban)' },
      ],
    } as TierData,
  },

  // UI Layer - Consolidated
  {
    id: 'ui',
    type: 'tier',
    position: { x: 750, y: 200 },
    data: {
      title: 'UI Control Panel',
      description: 'Single interface, 5 views',
      color: '#2563eb',
      icon: '🌐',
      children: [
        { icon: '💬', label: 'Chat + Queries' },
        { icon: '📊', label: 'Live Graph' },
        { icon: '📄', label: 'Report Builder' },
        { icon: '💰', label: 'Cost Tracker' },
        { icon: '⚙️', label: 'Demo Controls' },
      ],
    } as TierData,
  },

  // Process Highlights
  {
    id: 'fivewhys',
    type: 'highlight',
    position: { x: 650, y: 450 },
    data: {
      icon: '🔢',
      title: 'Five Whys',
      subtitle: '5 atomic sequential calls — no shortcuts',
    } as HighlightData,
  },
  {
    id: 'ishikawa',
    type: 'highlight',
    position: { x: 650, y: 550 },
    data: {
      icon: '🌳',
      title: 'Ishikawa',
      subtitle: '6 parallel branches — root cause mapping',
    } as HighlightData,
  },

  // Key Metrics
  {
    id: 'metrics',
    type: 'process',
    position: { x: 150, y: 350 },
    data: {
      icon: '⚡',
      title: '90 seconds • $0.18',
      description: 'Consulting-grade report, Black Belt readable',
    } as ProcessData,
  },

  // Data Layer
  {
    id: 'data',
    type: 'process',
    position: { x: 150, y: 500 },
    data: {
      icon: '🗄️',
      title: 'Supabase + pgvector',
      description: 'Persistent state, vector search',
    } as ProcessData,
  },
];

// Edge Definitions
const initialEdges: Edge[] = [
  // Main flow: Detection → Orchestration → Kaizen
  { id: 'e-tier2-tier3', source: 'tier2', target: 'tier3', animated: true, style: { stroke: '#d97706', strokeWidth: 3 } },
  { id: 'e-tier1-tier2', source: 'tier1', target: 'tier2', animated: true, style: { stroke: '#dc2626', strokeWidth: 3 } },

  // UI interactions
  { id: 'e-ui-tier3', source: 'ui', target: 'tier3', style: { stroke: '#2563eb', strokeWidth: 2, strokeDasharray: '5,5' } },
  { id: 'e-ui-tier1', source: 'ui', target: 'tier1', style: { stroke: '#2563eb', strokeWidth: 2, strokeDasharray: '5,5' } },

  // Process details
  { id: 'e-tier1-whys', source: 'tier1', target: 'fivewhys', style: { stroke: '#dc2626', strokeWidth: 2 } },
  { id: 'e-tier1-ishikawa', source: 'tier1', target: 'ishikawa', style: { stroke: '#dc2626', strokeWidth: 2 } },

  // Infrastructure
  { id: 'e-tier1-metrics', source: 'tier1', target: 'metrics', style: { stroke: '#6b7280', strokeWidth: 1 } },
  { id: 'e-tier1-data', source: 'tier1', target: 'data', style: { stroke: '#6b7280', strokeWidth: 1 } },
  { id: 'e-tier2-data', source: 'tier2', target: 'data', style: { stroke: '#6b7280', strokeWidth: 1 } },
  { id: 'e-tier3-data', source: 'tier3', target: 'data', style: { stroke: '#6b7280', strokeWidth: 1 } },
];

// Legend
const Legend = () => (
  <div className="legend">
    <h3>System Story</h3>
    <div className="legend-items">
      <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#7c3aed' }} />Meta-Orchestrator</div>
      <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#d97706' }} />Detection</div>
      <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#dc2626' }} />Kaizen Engine</div>
      <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#2563eb' }} />UI Control</div>
    </div>
  </div>
);

// Main Component
export default function SystemDiagram() {
  const [nodes] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="system-diagram-container">
      <header className="diagram-header">
        <div className="header-content">
          <h1>AutoCI System Architecture</h1>
          <p>Six Sigma methodology wired into the architecture — not the prompt</p>
        </div>
      </header>

      <div className="diagram-wrapper">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          minZoom={0.1}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#cbd5e1" gap={20} />
          <Controls />
          <MiniMap 
            style={{ width: 200, height: 150, borderRadius: '8px' }}
            nodeColor={(node) => {
              switch (node.data?.color) {
                case '#7c3aed': return '#7c3aed';
                case '#d97706': return '#d97706';
                case '#dc2626': return '#dc2626';
                case '#2563eb': return '#2563eb';
                default: return '#64748b';
              }
            }}
          />
        </ReactFlow>

        <Legend />
      </div>

      <div className="diagram-footer">
        <div className="footer-content">
          <div className="system-summary">
            <h3>The Architecture Enforces Rigour</h3>
            <p>
              Five Whys runs as <strong>five sequential atomic calls</strong> — each must commit before the next begins. 
              DMAIC phase gates prevent jumping from problem to solution. 
              The model has <em>no path around the logic</em>. 
              Result: Consulting-grade analysis in 90 seconds for $0.18.
            </p>
          </div>
          <div className="key-metrics">
            <div className="metric">
              <span className="metric-value">90s</span>
              <span className="metric-label">Analysis Time</span>
            </div>
            <div className="metric">
              <span className="metric-value">$0.18</span>
              <span className="metric-label">Per Kaizen</span>
            </div>
            <div className="metric">
              <span className="metric-value">Phase-Gated</span>
              <span className="metric-label">No Shortcuts</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}