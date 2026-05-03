"use client";

import Citation from "./Citation";
import type { Citation as CitationType } from "../../lib/chat-types";

interface CitationDrawerProps {
  citations: CitationType[];
  activeIndex: number | null;
  onClose: () => void;
}

// Side panel for citations. Either renders the focused citation (when
// activeIndex is set) or a small list of all citations the user can browse.
export default function CitationDrawer({ citations, activeIndex, onClose }: CitationDrawerProps) {
  if (citations.length === 0) return null;
  const active = activeIndex == null ? null : citations.find((c) => c.index === activeIndex);

  return (
    <aside className="w-96 flex-shrink-0 border-l border-gray-200 bg-gray-50 flex flex-col h-full">
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <h2 className="text-sm font-semibold text-gray-800">Sources</h2>
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-gray-500 hover:text-gray-800"
          aria-label="Close source drawer"
        >
          Close
        </button>
      </header>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {active ? (
          <Citation citation={active} />
        ) : (
          citations.map((c) => <Citation key={c.index} citation={c} />)
        )}
      </div>
    </aside>
  );
}
