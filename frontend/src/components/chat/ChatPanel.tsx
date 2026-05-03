"use client";

import { useCallback, useRef, useState } from "react";

import {
  buildCitations,
  type ChatResponse,
  type Citation as CitationType,
  type QueryPlan,
} from "../../lib/chat-types";
import CitationChip from "./CitationChip";
import CitationDrawer from "./CitationDrawer";
import KnowledgeSourcesPanel from "./KnowledgeSourcesPanel";
import QueryTransformationCard from "./QueryTransformationCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ChatTurn =
  | { role: "user"; id: string; content: string }
  | {
      role: "assistant";
      id: string;
      content: string;
      plan: QueryPlan | null;
      citations: CitationType[];
      error?: string;
    };

export default function ChatPanel() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [pending, setPending] = useState(false);
  const [draft, setDraft] = useState("");
  const [activeCitation, setActiveCitation] = useState<{ turnId: string; citationIndex: number } | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
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
        citations,
      };
      setTurns((t) => [...t, assistantTurn]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          id: newId(),
          content: "",
          plan: null,
          citations: [],
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

  const drawerAssistantTurn = activeCitation
    ? turns.find(
        (t): t is Extract<ChatTurn, { role: "assistant" }> =>
          t.role === "assistant" && t.id === activeCitation.turnId
      )
    : undefined;
  const drawerCitations = drawerAssistantTurn?.citations ?? [];
  const drawerActiveIndex = activeCitation?.citationIndex ?? null;

  return (
    <div className="flex h-full">
      <section className="flex-1 min-w-0 flex flex-col">
        <div className="flex items-center justify-between px-6 py-2 border-b border-gray-200 bg-white">
          <span className="text-xs uppercase tracking-wide text-gray-500">RAG Chat</span>
          <button
            type="button"
            onClick={() => setSourcesOpen(true)}
            className="text-xs text-blue-700 hover:text-blue-900 hover:underline"
          >
            Browse knowledge sources
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {turns.length === 0 && (
            <EmptyState />
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
                activeCitation={
                  activeCitation && activeCitation.turnId === turn.id
                    ? activeCitation.citationIndex
                    : null
                }
              />
            )
          )}
          {pending && (
            <div className="text-sm text-gray-500 italic">Thinking...</div>
          )}
        </div>
        <div className="border-t border-gray-200 px-6 py-3 bg-white">
          <div className="flex gap-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask about the recruitment pipeline. e.g. 'What's our average time to fill for Java Developers?'"
              rows={2}
              disabled={pending}
              className="flex-1 resize-none rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
            <button
              type="button"
              onClick={() => void send()}
              disabled={pending || !draft.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </section>
      {activeCitation && (
        <CitationDrawer
          citations={drawerCitations}
          activeIndex={drawerActiveIndex}
          onClose={() => setActiveCitation(null)}
        />
      )}
      <KnowledgeSourcesPanel
        open={sourcesOpen}
        onClose={() => setSourcesOpen(false)}
      />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="text-sm text-gray-500 max-w-xl">
      <p className="mb-2">
        The Query Planner picks a validated SQL template, freeform SELECT, vector
        retrieval, or a combination of those, then shows you the routing decision
        before the answer arrives.
      </p>
      <p className="mb-2">Try one of these to see it work:</p>
      <ul className="list-disc list-inside space-y-1">
        <li>What is our average time to fill for Java Developers?</li>
        <li>Show me the offer acceptance rate for UX Designer.</li>
        <li>What is DMAIC and how does AutoCI use it?</li>
      </ul>
    </div>
  );
}

function UserMessage({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-2xl bg-blue-600 text-white rounded-md px-4 py-2 text-sm whitespace-pre-wrap">
        {content}
      </div>
    </div>
  );
}

function AssistantMessage({
  turn,
  onChipClick,
  activeCitation,
}: {
  turn: Extract<ChatTurn, { role: "assistant" }>;
  onChipClick: (citationIndex: number) => void;
  activeCitation: number | null;
}) {
  if (turn.error) {
    return (
      <div className="max-w-2xl bg-red-50 border border-red-200 rounded-md px-4 py-3 text-sm text-red-800">
        {turn.error}
      </div>
    );
  }
  return (
    <div className="max-w-2xl space-y-2">
      {turn.plan && <QueryTransformationCard plan={turn.plan} />}
      <div className="bg-white border border-gray-200 rounded-md px-4 py-3 text-sm text-gray-800 whitespace-pre-wrap">
        {turn.content || "(no reply text)"}
      </div>
      {turn.citations.length > 0 && (
        <div className="flex items-center gap-1 flex-wrap text-xs text-gray-500">
          <span className="uppercase tracking-wide">Sources:</span>
          {turn.citations.map((c) => (
            <CitationChip
              key={c.index}
              index={c.index}
              onClick={() => onChipClick(c.index)}
              active={activeCitation === c.index}
            />
          ))}
        </div>
      )}
    </div>
  );
}
