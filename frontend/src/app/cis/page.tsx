"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { connectSSE, type SSEEvent } from "@/lib/sse";
import InterventionsTable from "@/components/InterventionsTable";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────

interface ScopingTurn {
  role: "user" | "agent";
  message: string;
}

interface ScopingState {
  problem: string | null;
  scope: string | null;
  requested_outcomes: string[] | null;
  role_title: string | null;
  target_kpi: string | null;
  confidence: number;
  ready: boolean;
  turns: ScopingTurn[];
}

interface InterventionRow {
  intervention_id: string;
  title: string;
  description: string | null;
  linked_root_cause: string | null;
  impact: "high" | "medium" | "low" | null;
  effort: string | null;
  priority: number | null;
  owner: string | null;
  due_date: string | null;
  status: "proposed" | "accepted" | "in_progress" | "done" | "rejected";
}

// ── Default empty state ───────────────────────────────────────────────────

const EMPTY_STATE: ScopingState = {
  problem: null,
  scope: null,
  requested_outcomes: null,
  role_title: null,
  target_kpi: null,
  confidence: 0,
  ready: false,
  turns: [],
};

// ── Component ─────────────────────────────────────────────────────────────

export default function CISPage() {
  // Scoping
  const [scopingState, setScopingState] = useState<ScopingState>(EMPTY_STATE);
  const [userInput, setUserInput] = useState("");
  const [scopingLoading, setScopingLoading] = useState(false);

  // Tool selection
  const [toolPlan, setToolPlan] = useState<string[] | null>(null);
  const [toolReasoning, setToolReasoning] = useState<string | null>(null);
  const [selectingTools, setSelectingTools] = useState(false);

  // Run
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  // SSE timeline events
  const [phaseWriteups, setPhaseWriteups] = useState<
    { phase: string; headline: string; tl_dr: string }[]
  >([]);
  const [interventions, setInterventions] = useState<InterventionRow[]>([]);
  const [outputDeltas, setOutputDeltas] = useState<string[]>([]);
  const sseRef = useRef<EventSource | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Auto-scroll timeline
  useEffect(() => {
    if (timelineRef.current) {
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
    }
  }, [phaseWriteups, outputDeltas]);

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      sseRef.current?.close();
    };
  }, []);

  // ── Scoping ───────────────────────────────────────────────────────────

  const handleStartScoping = useCallback(async () => {
    if (!userInput.trim()) return;
    setScopingLoading(true);

    try {
      const res = await fetch(`${API_BASE}/cis/scope`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scoping_state: EMPTY_STATE,
          user_message: userInput.trim(),
        }),
      });
      if (!res.ok) throw new Error(`Scope failed (${res.status})`);
      const data = await res.json();
      setScopingState(data.scoping_state);
    } catch (err) {
      console.error("Scoping error:", err);
    } finally {
      setScopingLoading(false);
    }
  }, [userInput]);

  const handleScopingReply = useCallback(async () => {
    if (!userInput.trim()) return;
    setScopingLoading(true);

    try {
      const res = await fetch(`${API_BASE}/cis/scope`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scoping_state: scopingState,
          user_message: userInput.trim(),
        }),
      });
      if (!res.ok) throw new Error(`Scope reply failed (${res.status})`);
      const data = await res.json();
      setScopingState(data.scoping_state);
      setUserInput("");
    } catch (err) {
      console.error("Scoping reply error:", err);
    } finally {
      setScopingLoading(false);
    }
  }, [userInput, scopingState]);

  // ── Tool selection ────────────────────────────────────────────────────

  const handleSelectTools = useCallback(async () => {
    setSelectingTools(true);
    try {
      const res = await fetch(`${API_BASE}/cis/select-tools`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scoping_state: scopingState }),
      });
      if (!res.ok) throw new Error(`Select tools failed (${res.status})`);
      const data = await res.json();
      setToolPlan(data.ordered);
      setToolReasoning(data.reasoning);
    } catch (err) {
      console.error("Tool selection error:", err);
    } finally {
      setSelectingTools(false);
    }
  }, [scopingState]);

  // ── Run ───────────────────────────────────────────────────────────────

  const handleRun = useCallback(async () => {
    if (!toolPlan || toolPlan.length === 0) return;
    setRunning(true);
    setOutputDeltas([]);
    setPhaseWriteups([]);
    setInterventions([]);

    try {
      const res = await fetch(`${API_BASE}/cis/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scoping_state: scopingState,
          tool_plan: toolPlan,
        }),
      });
      if (!res.ok) throw new Error(`Run failed (${res.status})`);
      const data = await res.json();
      const sid: string = data.session_id;
      setSessionId(sid);

      // Connect SSE
      sseRef.current?.close();
      const source = connectSSE(sid, API_BASE, (event: SSEEvent) => {
        switch (event.type) {
          case "phase_writeup":
            setPhaseWriteups((prev) => [
              ...prev,
              {
                phase: event.phase,
                headline: event.writeup?.headline ?? event.phase,
                tl_dr: event.writeup?.tl_dr ?? "",
              },
            ]);
            break;
          case "output_delta":
            setOutputDeltas((prev) => [...prev, event.content]);
            break;
          case "interventions":
            // Interventions arrived — fetch full list
            fetch(`${API_BASE}/cis/interventions/${sid}`)
              .then((r) => r.json())
              .then((d) => setInterventions(d.interventions ?? []))
              .catch(console.error);
            break;
          case "fmea":
            // Could show FMEA results; for now just log
            break;
          case "node_status":
            break;
          case "phase_transition":
            break;
          case "connected":
            break;
        }
      });
      sseRef.current = source;
    } catch (err) {
      console.error("Run error:", err);
      setRunning(false);
    }
  }, [toolPlan, scopingState]);

  // After session completes, fetch interventions
  useEffect(() => {
    if (!sessionId || running) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/cis/interventions/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.interventions && data.interventions.length > 0) {
            setInterventions(data.interventions);
            clearInterval(timer);
          }
        }
      } catch {
        // ignore
      }
    }, 3000);
    return () => clearInterval(timer);
  }, [sessionId, running]);

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="flex h-full" style={{ height: "calc(100vh - 56px)" }}>
      {/* Left rail — tool list or prior runs placeholder */}
      <aside className="w-64 border-r border-gray-200 bg-gray-50 p-4 overflow-y-auto flex-shrink-0">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          {toolPlan ? "Selected tools" : "Available tools"}
        </h3>
        {toolPlan ? (
          <ul className="space-y-1">
            {toolPlan.map((tool) => (
              <li
                key={tool}
                className="text-sm text-gray-700 px-2 py-1 rounded bg-white border border-gray-200"
              >
                {tool}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-gray-400 leading-relaxed">
            Complete scoping to see the recommended tool list.
          </p>
        )}

        {toolReasoning && (
          <div className="mt-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Reasoning
            </h4>
            <p className="text-xs text-gray-600 leading-relaxed">
              {toolReasoning}
            </p>
          </div>
        )}
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Charter bar */}
        {scopingState.ready && scopingState.problem && (
          <div className="border-b border-gray-200 px-6 py-3 bg-white">
            <div className="flex items-start gap-4 text-sm">
              <div className="flex-1 min-w-0">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Charter
                </span>
                <p className="text-gray-800 font-medium mt-0.5 truncate">
                  {scopingState.problem}
                </p>
                {scopingState.scope && (
                  <p className="text-xs text-gray-500 mt-0.5">
                    Scope: {scopingState.scope}
                  </p>
                )}
              </div>
              {scopingState.role_title && (
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-gray-400">Role</span>
                  <p className="text-sm font-medium text-gray-700">
                    {scopingState.role_title}
                  </p>
                </div>
              )}
              {scopingState.confidence > 0 && (
                <div className="text-right flex-shrink-0">
                  <span className="text-xs text-gray-400">Confidence</span>
                  <p className="text-sm font-medium text-gray-700">
                    {Math.round(scopingState.confidence * 100)}%
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Scoping chat / Timeline area */}
        <div className="flex-1 overflow-y-auto px-6 py-4" ref={timelineRef}>
          {/* If not ready: show scoping chat */}
          {!scopingState.ready && scopingState.turns.length === 0 && (
            <div className="max-w-lg mx-auto mt-16 text-center">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">
                Continuous Improvement Suite
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                Describe a problem you want to investigate. The scoping agent
                will ask clarifying questions, then recommend the right tools.
              </p>
            </div>
          )}

          {/* Scoping turns */}
          {!scopingState.ready &&
            scopingState.turns.map((turn, i) => (
              <div
                key={i}
                className={`mb-3 flex ${
                  turn.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[70%] rounded-lg px-4 py-2 text-sm ${
                    turn.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {turn.message}
                </div>
              </div>
            ))}

          {scopingLoading && (
            <div className="text-sm text-gray-400 text-center py-4">
              Thinking…
            </div>
          )}

          {/* Phase timeline (SSE driven) */}
          {phaseWriteups.length > 0 && (
            <div className="mt-6 space-y-4">
              <h3 className="text-sm font-semibold text-gray-700">
                Phase Timeline
              </h3>
              {phaseWriteups.map((wu, i) => (
                <div
                  key={i}
                  className="border border-gray-200 rounded-lg p-4 bg-white"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-gray-400 uppercase">
                      {wu.phase}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-gray-800">
                    {wu.headline}
                  </h4>
                  {wu.tl_dr && (
                    <p className="text-xs text-gray-500 mt-1">{wu.tl_dr}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Output deltas (live streaming) */}
          {outputDeltas.length > 0 && (
            <div className="mt-4 space-y-1">
              {outputDeltas.map((line, i) => (
                <p key={i} className="text-xs text-gray-500 font-mono">
                  {line}
                </p>
              ))}
            </div>
          )}

          {/* Interventions table */}
          {interventions.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Proposed Interventions
              </h3>
              <InterventionsTable rows={interventions} />
            </div>
          )}
        </div>

        {/* Bottom input area */}
        <div className="border-t border-gray-200 px-6 py-3 bg-white">
          {!scopingState.ready && scopingState.turns.length === 0 && (
            <div className="flex gap-2">
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="e.g. Why is offer acceptance dropping for UX Designer roles?"
                rows={2}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleStartScoping();
                  }
                }}
              />
              <button
                type="button"
                onClick={handleStartScoping}
                disabled={!userInput.trim() || scopingLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed self-end"
              >
                Start scoping
              </button>
            </div>
          )}

          {!scopingState.ready && scopingState.turns.length > 0 && (
            <div className="flex gap-2">
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Type your answer…"
                rows={1}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleScopingReply();
                  }
                }}
              />
              <button
                type="button"
                onClick={handleScopingReply}
                disabled={!userInput.trim() || scopingLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          )}

          {scopingState.ready && !toolPlan && (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleSelectTools}
                disabled={selectingTools}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {selectingTools ? "Selecting tools…" : "Pick tools"}
              </button>
            </div>
          )}

          {scopingState.ready && toolPlan && !sessionId && (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleRun}
                disabled={running}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {running ? "Running…" : "Run"}
              </button>
            </div>
          )}

          {sessionId && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">
                Session: {sessionId.slice(0, 8)}…
              </span>
              {running && (
                <span className="text-xs text-green-600 font-medium">
                  Running
                </span>
              )}
              {!running && interventions.length > 0 && (
                <span className="text-xs text-green-600 font-medium">
                  Complete
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
