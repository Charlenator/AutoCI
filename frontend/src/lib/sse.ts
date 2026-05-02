/** SSE client — single EventSource per session with typed dispatch. */
export type SSEEvent =
  | { type: "node_status"; agent_id: string; status: string; label?: string; data?: any }
  | { type: "phase_transition"; phase: string; status: string; data?: any }
  | { type: "output_delta"; phase: string; agent_id?: string; content: string }
  | { type: "step_progress"; agent_id: string; step: string; progress: number; total: number }
  | { type: "cost"; total_usd: number; session_id?: string }
  | { type: "connected"; session_id: string }
  | { type: "validation"; data: any }
  | { type: "error"; data: any };

export type SSEHandler = (event: SSEEvent) => void;

export function connectSSE(
  sessionId: string,
  apiBase: string,
  onEvent: SSEHandler,
  onError?: (err: any) => void
): EventSource {
  const url = `${apiBase}/sessions/${sessionId}/stream`;
  const source = new EventSource(url);

  source.onmessage = (msg) => {
    try {
      const event: SSEEvent = JSON.parse(msg.data);
      onEvent(event);
    } catch (e) {
      console.warn("SSE parse error:", e);
    }
  };

  source.onerror = (err) => {
    console.warn("SSE error:", err);
    onError?.(err);
  };

  return source;
}
