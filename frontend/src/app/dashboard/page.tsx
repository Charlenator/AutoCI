"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { connectSSE, SSEEvent } from "@/lib/sse";

/* ─── Types ─── */
interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

interface OutputEntry {
  agent_id: string;
  content: string;
}

interface StepEntry {
  agent_id: string;
  step: string;
  progress: number;
  total: number;
  timestamp: number;
}

/* ─── Phase config ─── */
const PHASE_ORDER = ["detection", "define", "measure", "analyse", "improve", "control"] as const;
type Phase = (typeof PHASE_ORDER)[number];

const PHASE_LABELS: Record<Phase, { icon: string; label: string }> = {
  detection: { icon: "🔍", label: "Detection (Benchmarking)" },
  define: { icon: "📋", label: "Define (SIPOC)" },
  measure: { icon: "📏", label: "Measure (Metrics)" },
  analyse: { icon: "🔬", label: "Analyse (Root Cause)" },
  improve: { icon: "💡", label: "Improve (Interventions)" },
  control: { icon: "📊", label: "Control (Sustain)" },
};

const AGENT_COLORS: Record<string, string> = {
  D1: "#3b82f6",
  D2: "#8b5cf6",
  D3: "#f59e0b",
  S4: "#a855f7",
  K1: "#10b981",
  K2: "#06b6d4",
  K3: "#ef4444",
  K4: "#f97316",
  K5: "#84cc16",
  K6: "#6366f1",
  K7: "#ec4899",
};

/* ─── Main Dashboard ─── */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Welcome to AutoCI. Click **Run Kaizen** to launch a full DMAIC investigation, or ask a question about your pipeline." },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [cost, setCost] = useState(0);
  const [phaseStatus, setPhaseStatus] = useState<Record<Phase, "idle" | "active" | "complete">>({
    detection: "idle", define: "idle", measure: "idle",
    analyse: "idle", improve: "idle", control: "idle",
  });
  const [phaseOutputs, setPhaseOutputs] = useState<Record<Phase, OutputEntry[]>>({
    detection: [], define: [], measure: [],
    analyse: [], improve: [], control: [],
  });
  const [currentPhase, setCurrentPhase] = useState<Phase | null>(null);
  const [stepLog, setStepLog] = useState<StepEntry[]>([]);
  const [knowledgeStatus, setKnowledgeStatus] = useState<"idle" | "fetching" | "done">("idle");
  const [knowledgeSummary, setKnowledgeSummary] = useState<string | null>(null);
  const [seedStatus, setSeedStatus] = useState<"idle" | "seeding" | "done">("idle");
  const timelineRef = useRef<HTMLDivElement>(null);
  const sseRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const stepLogEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll timeline to active phase
  useEffect(() => {
    if (currentPhase && timelineRef.current) {
      const el = timelineRef.current.querySelector(`[data-phase="${currentPhase}"]`);
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [currentPhase]);

  // Scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Scroll step log to bottom
  useEffect(() => {
    stepLogEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [stepLog]);

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => sseRef.current?.close();
  }, []);

  // Handle incoming SSE events
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case "node_status":
        // Update phase status based on agent activity
        if (event.agent_id.startsWith("D") || event.agent_id === "S4") {
          setPhaseStatus((prev) => ({
            ...prev,
            detection: event.status === "complete" ? "complete" : event.status === "active" ? "active" : prev.detection,
          }));
        }
        if (event.agent_id === "K1") {
          setPhaseStatus((prev) => ({ ...prev, define: event.status === "complete" ? "complete" : "active" }));
        }
        if (event.agent_id === "K2") {
          setPhaseStatus((prev) => ({ ...prev, measure: event.status === "complete" ? "complete" : "active" }));
        }
        if (event.agent_id === "K3" || event.agent_id === "K4" || event.agent_id === "K5") {
          setPhaseStatus((prev) => ({ ...prev, analyse: event.status === "complete" ? "complete" : "active" }));
        }
        if (event.agent_id === "K6") {
          setPhaseStatus((prev) => ({ ...prev, improve: event.status === "complete" ? "complete" : "active" }));
        }
        if (event.agent_id === "K7") {
          setPhaseStatus((prev) => ({ ...prev, control: event.status === "complete" ? "complete" : "active" }));
        }

        if (event.status === "active") {
          setMessages((prev) => [...prev, { role: "system", content: `⚡ ${event.label || event.agent_id} running...` }]);
        }
        if (event.status === "complete") {
          setMessages((prev) => [...prev, { role: "system", content: `✅ ${event.label || event.agent_id} complete.` }]);
        }
        break;

      case "phase_transition":
        setCurrentPhase(event.phase as Phase);
        if (event.status === "start") {
          setPhaseStatus((prev) => ({ ...prev, [event.phase]: "active" }));
          setMessages((prev) => [...prev, { role: "system", content: `📋 Phase: **${event.phase}** started.` }]);
        }
        if (event.status === "complete") {
          setPhaseStatus((prev) => ({ ...prev, [event.phase]: "complete" }));
        }
        break;

      case "output_delta":
        setPhaseOutputs((prev) => {
          const phase = event.phase as Phase;
          if (!prev[phase]) return prev;
          return {
            ...prev,
            [phase]: [...prev[phase], { agent_id: event.agent_id || "system", content: event.content }],
          };
        });
        break;

      case "step_progress":
        setStepLog((prev) => {
          const next = [...prev, { agent_id: event.agent_id, step: event.step, progress: event.progress, total: event.total, timestamp: Date.now() }];
          return next.slice(-100);
        });
        break;

      case "cost":
        setCost(event.total_usd);
        break;

      case "connected":
        setMessages((prev) => [...prev, { role: "system", content: `🔗 Connected to session: ${event.session_id.substring(0, 8)}...` }]);
        break;
    }
  }, []);

  // Run Kaizen
  const runKaizen = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setCost(0);
    setPhaseStatus({ detection: "idle", define: "idle", measure: "idle", analyse: "idle", improve: "idle", control: "idle" });
    setPhaseOutputs({ detection: [], define: [], measure: [], analyse: [], improve: [], control: [] });
    setStepLog([]);
    setCurrentPhase(null);

    try {
      sseRef.current?.close();

      const resp = await fetch(`${API_BASE}/trigger/goal-review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await resp.json();
      const sid = data.session_id;
      setSessionId(sid);

      const source = connectSSE(sid, API_BASE, handleSSEEvent);
      sseRef.current = source;

      setMessages((prev) => [...prev, { role: "assistant", content: `🚀 Kaizen launched! Watch the results populate below.` }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `❌ Error: ${err.message}` }]);
    } finally {
      setIsRunning(false);
    }
  }, [isRunning, handleSSEEvent]);

  // Send chat message
  const sendMessage = useCallback(async () => {
    if (!chatInput.trim() || !sessionId) {
      if (!sessionId) {
        setMessages((prev) => [...prev, { role: "assistant", content: "Please click **Run Kaizen** first to start a session." }]);
      }
      return;
    }
    const text = chatInput.trim();
    setChatInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);

    try {
      const resp = await fetch(`${API_BASE}/chat/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });
      const data = await resp.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply || data.response || "No response." }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `❌ Error: ${err.message}` }]);
    }
  }, [chatInput, sessionId]);

  // Seed RAG Corpus (pre-fill with DMAIC docs, benchmarks, case studies)
  const seedRag = useCallback(async () => {
    if (seedStatus === "seeding") return;
    setSeedStatus("seeding");

    try {
      setMessages((prev) => [...prev, { role: "system", content: "🌱 Seeding RAG corpus with DMAIC docs, benchmarks, and case studies..." }]);
      const resp = await fetch(`${API_BASE}/knowledge/seed`, { method: "POST" });
      const data = await resp.json();
      setMessages((prev) => [...prev, { role: "system", content: `🌱 ${data.message}` }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "system", content: `❌ RAG seed error: ${err.message}` }]);
    } finally {
      setSeedStatus("done");
    }
  }, [seedStatus]);

  // Update External Knowledge (standalone — no Kaizen)
  const updateKnowledge = useCallback(async () => {
    if (knowledgeStatus === "fetching") return;
    setKnowledgeStatus("fetching");
    setKnowledgeSummary(null);

    try {
      setMessages((prev) => [...prev, { role: "system", content: "📚 Fetching external knowledge (Java + Python)... " }]);
      setStepLog((prev) => [...prev, { agent_id: "S4", step: "📚 Starting external knowledge update...", progress: 0, total: 1, timestamp: Date.now() }]);

      const resp = await fetch(`${API_BASE}/knowledge/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ roles: ["Java Developer", "Python Developer"], session_id: sessionId }),
      });
      const data = await resp.json();

      setKnowledgeSummary(data.message);
      setMessages((prev) => [...prev, { role: "system", content: `📚 ${data.message}` }]);
      setStepLog((prev) => [...prev, { agent_id: "S4", step: "✅ Knowledge update complete", progress: 1, total: 1, timestamp: Date.now() }]);

      // Connect SSE if we got a session_id (standalone mode — no prior Kaizen session)
      if (data.session_id && (!sessionId || sessionId !== data.session_id)) {
        sseRef.current?.close();
        setSessionId(data.session_id);
        const source = connectSSE(data.session_id, API_BASE, handleSSEEvent);
        sseRef.current = source;
      }
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "system", content: `❌ Knowledge update error: ${err.message}` }]);
    } finally {
      setKnowledgeStatus("done");
    }
  }, [knowledgeStatus, sessionId, handleSSEEvent]);

  /* ─── Render a single content line with bold parsing ─── */
  const renderContent = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) =>
      part.startsWith("**") && part.endsWith("**")
        ? <strong key={i}>{part.slice(2, -2)}</strong>
        : <span key={i}>{part}</span>
    );
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 64px)", fontFamily: "var(--font-geist-sans, system-ui, sans-serif)", background: "#f1f5f9" }}>
      {/* ─── Left: Chat Panel ─── */}
      <div style={{ width: 300, borderRight: "1px solid #e2e8f0", display: "flex", flexDirection: "column", background: "#fff", flexShrink: 0 }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid #e2e8f0", fontWeight: 600, fontSize: 13, color: "#1e293b", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>💬 Chat</span>
          <span style={{ fontSize: 11, color: "#64748b", fontFamily: "monospace" }}>${cost.toFixed(6)}</span>
        </div>

        {/* Activity Log */}
        <div style={{ maxHeight: 100, overflowY: "auto", borderBottom: "1px solid #e2e8f0", background: "#0f172a", padding: "4px 8px", fontFamily: "monospace", fontSize: 10, lineHeight: 1.5 }}>
          <div style={{ color: "#475569", fontSize: 9, fontWeight: 700, textTransform: "uppercase", marginBottom: 2 }}>📡 Activity</div>
          {stepLog.length === 0 && <div style={{ color: "#334155", fontStyle: "italic" }}>Waiting...</div>}
          {stepLog.slice(-12).map((s, i) => (
            <div key={i} style={{ color: s.progress === 0 ? "#facc15" : s.progress === s.total ? "#4ade80" : "#93c5fd" }}>
              {s.agent_id} › {s.step}
              <span style={{ color: "#475569", marginLeft: 4 }}>[{s.progress === 0 ? "..." : s.progress}/{s.total}]</span>
            </div>
          ))}
          <div ref={stepLogEndRef} />
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: 10, display: "flex", flexDirection: "column", gap: 6 }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              padding: "6px 10px",
              borderRadius: 6,
              fontSize: 12,
              lineHeight: 1.4,
              maxWidth: "92%",
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background: msg.role === "user" ? "#2563eb" : msg.role === "system" ? "#f1f5f9" : "#fff",
              color: msg.role === "user" ? "#fff" : "#0f172a",
              border: msg.role === "assistant" ? "1px solid #e2e8f0" : "none",
            }}
            dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") }}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Chat input */}
        <div style={{ padding: 8, borderTop: "1px solid #e2e8f0", display: "flex", gap: 6 }}>
          <input
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask about the pipeline..."
            style={{ flex: 1, padding: "6px 10px", borderRadius: 4, border: "1px solid #cbd5e1", fontSize: 12, outline: "none" }}
          />
          <button onClick={sendMessage} style={{ padding: "6px 12px", borderRadius: 4, border: "none", background: "#2563eb", color: "#fff", fontSize: 12, cursor: "pointer" }}>Send</button>
        </div>

        {/* Seed RAG Corpus button */}
        <div style={{ padding: "4px 8px" }}>
          <button
            onClick={seedRag}
            disabled={seedStatus === "seeding"}
            style={{
              width: "100%",
              padding: "5px 14px",
              borderRadius: 4,
              border: "1px solid #cbd5e1",
              background: seedStatus === "seeding" ? "#f1f5f9" : "#fff",
              color: seedStatus === "seeding" ? "#94a3b8" : "#475569",
              fontSize: 11,
              fontWeight: 500,
              cursor: seedStatus === "seeding" ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {seedStatus === "seeding"
              ? "🌱 Seeding..."
              : seedStatus === "done"
              ? "✅ RAG Seeded"
              : "🌱 Seed RAG Corpus"}
          </button>
        </div>

        {/* Knowledge Update button */}
        <div style={{ padding: "4px 8px" }}>
          <button
            onClick={updateKnowledge}
            disabled={knowledgeStatus === "fetching"}
            style={{
              width: "100%",
              padding: "5px 14px",
              borderRadius: 4,
              border: "1px solid #cbd5e1",
              background: knowledgeStatus === "fetching" ? "#f1f5f9" : "#fff",
              color: knowledgeStatus === "fetching" ? "#94a3b8" : "#475569",
              fontSize: 11,
              fontWeight: 500,
              cursor: knowledgeStatus === "fetching" ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {knowledgeStatus === "fetching"
              ? "🔄 Fetching..."
              : knowledgeStatus === "done"
              ? "✅ Knowledge Updated"
              : "📚 Update External Knowledge"}
          </button>
          {knowledgeSummary && (
            <div style={{ marginTop: 3, fontSize: 10, color: "#059669", textAlign: "center" }}>
              {knowledgeSummary.length > 60 ? knowledgeSummary.substring(0, 60) + "..." : knowledgeSummary}
            </div>
          )}
        </div>

        {/* Run button */}
        <div style={{ padding: "6px 8px" }}>
          <button
            onClick={runKaizen}
            disabled={isRunning}
            style={{
              width: "100%",
              padding: "8px 14px",
              borderRadius: 4,
              border: "none",
              background: isRunning ? "#94a3b8" : "#7c3aed",
              color: "#fff",
              fontSize: 12,
              fontWeight: 600,
              cursor: isRunning ? "not-allowed" : "pointer",
            }}
          >
            {isRunning ? "🔄 Running..." : "🎯 Run Kaizen"}
          </button>
        </div>
      </div>

      {/* ─── Centre: Results Timeline ─── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Top bar */}
        <div style={{
          padding: "8px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#fff",
          borderBottom: "1px solid #e2e8f0",
          fontSize: 12,
          color: "#475569",
          flexShrink: 0,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <strong style={{ color: "#0f172a", fontSize: 14 }}>📊 Kaizen Results</strong>
            {currentPhase && phaseStatus[currentPhase] === "active" && (
              <span style={{ color: "#f59e0b", display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f59e0b", animation: "pulse 1.5s infinite" }} />
                {PHASE_LABELS[currentPhase]?.icon} {PHASE_LABELS[currentPhase]?.label || currentPhase}
              </span>
            )}
          </div>
          <span style={{ fontFamily: "monospace", fontSize: 11 }}>${cost.toFixed(6)}</span>
        </div>

        {/* Scrollable timeline */}
        <div ref={timelineRef} style={{ flex: 1, overflowY: "auto", padding: "12px 16px" }}>
          {PHASE_ORDER.map((phase) => {
            const status = phaseStatus[phase];
            const outputs = phaseOutputs[phase];
            const config = PHASE_LABELS[phase];
            const isActive = status === "active";
            const isComplete = status === "complete";
            const isIdle = status === "idle";

            // Group outputs by agent
            const agentGroups: Record<string, { content: string }[]> = {};
            for (const out of outputs) {
              if (!agentGroups[out.agent_id]) agentGroups[out.agent_id] = [];
              agentGroups[out.agent_id].push({ content: out.content });
            }

            return (
              <div
                key={phase}
                data-phase={phase}
                style={{
                  marginBottom: 12,
                  borderRadius: 8,
                  border: `1px solid ${isActive ? "#f59e0b" : isComplete ? "#d1fae5" : "#e2e8f0"}`,
                  background: isActive ? "#fffbeb" : isComplete ? "#f0fdf4" : "#fff",
                  overflow: "hidden",
                  transition: "all 0.3s ease",
                  boxShadow: isActive ? "0 0 0 2px rgba(245,158,11,0.15)" : "0 1px 2px rgba(0,0,0,0.04)",
                  opacity: isIdle ? 0.5 : 1,
                }}
              >
                {/* Phase header */}
                <div style={{
                  padding: "10px 14px",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  borderBottom: outputs.length > 0 ? "1px solid #e2e8f0" : "none",
                  fontSize: 13,
                  fontWeight: 600,
                  color: isActive ? "#92400e" : isComplete ? "#065f46" : "#475569",
                }}>
                  <span>{config.icon}</span>
                  <span style={{ flex: 1 }}>{config.label}</span>
                  {isActive && <span style={{ fontSize: 11, color: "#92400e", background: "#fde68a", padding: "2px 6px", borderRadius: 4 }}>Running</span>}
                  {isComplete && <span style={{ fontSize: 11, color: "#065f46", background: "#a7f3d0", padding: "2px 6px", borderRadius: 4 }}>✓ Complete</span>}
                  {isIdle && <span style={{ fontSize: 11, color: "#94a3b8" }}>Waiting</span>}
                </div>

                {/* Output entries grouped by agent */}
                {Object.entries(agentGroups).map(([agentId, entries]) => (
                  <div key={agentId} style={{ padding: "2px 14px 6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, marginTop: 6 }}>
                      <span style={{
                        display: "inline-block",
                        padding: "1px 6px",
                        borderRadius: 3,
                        fontSize: 10,
                        fontWeight: 700,
                        color: "#fff",
                        background: AGENT_COLORS[agentId] || "#6b7280",
                      }}>
                        {agentId}
                      </span>
                    </div>
                    {entries.map((e, i) => (
                      <div key={i} style={{
                        padding: "3px 0 3px 12px",
                        borderLeft: `2px solid ${AGENT_COLORS[agentId] || "#e2e8f0"}`,
                        marginLeft: 4,
                        marginBottom: 2,
                        fontSize: 12,
                        lineHeight: 1.5,
                        color: "#1e293b",
                      }}>
                        {renderContent(e.content)}
                      </div>
                    ))}
                  </div>
                ))}

                {/* Waiting state */}
                {outputs.length === 0 && isActive && (
                  <div style={{ padding: "14px", textAlign: "center", color: "#92400e", fontSize: 12 }}>
                    <span style={{ display: "inline-block", animation: "pulse 1.5s infinite" }}>⏳ Processing...</span>
                  </div>
                )}
                {outputs.length === 0 && isIdle && (
                  <div style={{ padding: "10px 14px", color: "#94a3b8", fontSize: 12, fontStyle: "italic" }}>
                    Awaiting previous phase...
                  </div>
                )}
              </div>
            );
          })}

          {/* No runs yet */}
          {Object.values(phaseOutputs).every((v) => v.length === 0) && (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "#94a3b8" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🎯</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#64748b", marginBottom: 6 }}>Ready to Investigate</div>
              <div style={{ fontSize: 12 }}>Click <strong>Run Kaizen</strong> to start a DMAIC investigation of your recruitment pipeline.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
