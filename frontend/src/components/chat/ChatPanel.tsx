"use client";

import { useCallback, useRef, useState } from "react";

import {
  buildCitations,
  type ChatResponse,
  type Citation as CitationType,
  type LiveSearchPayload,
  type QueryPlan,
  type SqlResult,
} from "../../lib/chat-types";
import CitationChip from "./CitationChip";
import CitationDrawer from "./CitationDrawer";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SUGGESTIONS = [
  "What is our average time to fill for Java Developers?",
  "Show me the offer acceptance rate for UX Designer.",
  "Do we have any applicants with project management skills?",
];

type ChatTurn =
  | { role: "user"; id: string; content: string }
  | {
      role: "assistant";
      id: string;
      content: string;
      plan: QueryPlan | null;
      sqlResult: SqlResult | null;
      ragChunkCount: number;
      citations: CitationType[];
      liveSearch: LiveSearchPayload | null;
      error?: string;
    };

export default function ChatPanel() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [pending, setPending] = useState(false);
  const [draft, setDraft] = useState("");
  const [activeCitation, setActiveCitation] = useState<{ turnId: string; citationIndex: number } | null>(null);
  const idCounter = useRef(0);


  const newId = useCallback(() => {
    idCounter.current += 1;
    return `t${idCounter.current}`;
  }, []);

  const send = useCallback(async () => {
    const text = draft.trim();
    if (!text || pending) return;
    const userTurn: ChatTurn = { role: "user", id: newId(), content: text };
    setTurns((t) => [...t, userTurn]);
    setDraft("");
    setPending(true);
    try {
      const res = await fetch(`${API_BASE}/chat/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Chat request failed (${res.status}): ${errText}`);
      }
      const data: ChatResponse = await res.json();
      const citations = buildCitations(data);
      const assistantTurn: ChatTurn = {
        role: "assistant",
        id: newId(),
        content: data.reply,
        plan: data.plan,
        sqlResult: data.sql_result,
        ragChunkCount: data.rag_chunks?.length ?? 0,
        citations,
        liveSearch: data.live_search ?? null,
      };
      setTurns((t) => [...t, assistantTurn]);
      // Auto-open the sources drawer on the first citation
      if (citations.length > 0) {
        setActiveCitation({ turnId: assistantTurn.id, citationIndex: citations[0].index });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          id: newId(),
          content: "",
          plan: null,
          sqlResult: null,
          ragChunkCount: 0,
          citations: [],
          liveSearch: null,
          error: message,
        },
      ]);
    } finally {
      setPending(false);
    }
  }, [draft, pending, newId]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  const handleSuggestion = (text: string) => {
    setDraft(text);
  };

  // Determine which assistant turn is currently active in the drawer
  const drawerTurnAssistant = activeCitation
    ? turns.find(
        (t): t is Extract<ChatTurn, { role: "assistant" }> =>
          t.role === "assistant" && t.id === activeCitation.turnId
      )
    : undefined;
  // Fall back to the last assistant turn with citations if no specific citation active
  const effectiveAssistant = drawerTurnAssistant ?? [...turns].reverse().find(
    (t): t is Extract<ChatTurn, { role: "assistant" }> =>
      t.role === "assistant" && t.citations.length > 0
  );
  const drawerCitations = effectiveAssistant?.citations ?? [];
  const drawerActiveIndex = activeCitation?.citationIndex ?? null;

  return (
    <div className="chat-page">
      <div className="chat-col">
        <div className="chat-header">
          <div>
            <h1 className="chat-title">RAG Chat</h1>
            <p className="chat-subtitle">
              Ask recruitment pipeline questions. The Query Planner picks the
              right tool — SQL, vector search, or live data.
            </p>
          </div>
        </div>

        <div className="chat-stream">
          {turns.length === 0 && (
            <div className="empty">
              <h3>Ask anything about your pipeline</h3>
              <p>
                The Query Planner picks a validated SQL template, freeform
                SELECT, vector retrieval, or a combination of those, then shows
                you the routing decision before the answer arrives.
              </p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="suggestion"
                    onClick={() => handleSuggestion(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {turns.map((turn) =>
            turn.role === "user" ? (
              <UserMessage key={turn.id} content={turn.content} />
            ) : (
              <AssistantMessage
                key={turn.id}
                turn={turn}
                onChipClick={(citationIndex) =>
                  setActiveCitation({ turnId: turn.id, citationIndex })
                }
              />
            )
          )}

          {pending && (
            <div className="assistant-msg">
              <div className="assistant-stamp">
                <div className="dot">AI</div>
                <span>Thinking...</span>
              </div>
            </div>
          )}
        </div>

        <div className="composer">
          <div className="composer-shell">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder='Ask about the recruitment pipeline. e.g. "What&rsquo;s our average time to fill for Java Developers?"'
              rows={2}
              disabled={pending}
            />
            <div className="composer-foot">
              <span className="composer-hint">
                <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> new line
              </span>
              <button
                type="button"
                onClick={() => void send()}
                disabled={pending || !draft.trim()}
                className="btn btn-primary"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>

        {effectiveAssistant && (
          <CitationDrawer
            citations={drawerCitations}
            activeIndex={drawerActiveIndex}
            plan={effectiveAssistant?.plan ?? null}
            sqlResult={effectiveAssistant?.sqlResult ?? null}
            ragChunkCount={effectiveAssistant?.ragChunkCount ?? 0}
            liveSearch={effectiveAssistant?.liveSearch ?? null}
          />
        )}
    </div>
  );
}

function UserMessage({ content }: { content: string }) {
  return (
    <div className="user-msg">
      <div className="user-bubble">{content}</div>
    </div>
  );
}

function AssistantMessage({
  turn,
  onChipClick,
}: {
  turn: Extract<ChatTurn, { role: "assistant" }>;
  onChipClick: (citationIndex: number) => void;
}) {
  if (turn.error) {
    return (
      <div className="assistant-msg">
        <div className="assistant-stamp">
          <div className="dot">AI</div>
          <span>Error</span>
        </div>
        <div
          style={{
            background: "#FCF6F4",
            border: "1px solid var(--accent)",
            borderRadius: "var(--r-lg)",
            padding: "16px 20px",
            color: "var(--text)",
            fontSize: "14px",
          }}
        >
          {turn.error}
        </div>
      </div>
    );
  }
  return (
    <div className="assistant-msg">
      <div className="assistant-stamp">
        <div className="dot">AI</div>
        <span>Assistant</span>
      </div>

      {turn.content && (
        <div className="assistant-bubble">{turn.content}</div>
      )}

      {turn.citations.length > 0 && (
        <div className="sources-row">
          <span>Sources</span>
          <span className="sep">·</span>
          {turn.citations.map((c) => (
            <CitationChip
              key={c.index}
              index={c.index}
              onClick={() => onChipClick(c.index)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
