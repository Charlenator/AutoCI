"use client";

import Citation from "./Citation";
import type { Citation as CitationType } from "../../lib/chat-types";

interface CitationDrawerProps {
  citations: CitationType[];
  activeIndex: number | null;
  onClose: () => void;
}

// Side panel for citations. Renders the focused citation when activeIndex is
// set, or a small list of all citations. Restyled per style_guide.css §11.
export default function CitationDrawer({ citations, activeIndex, onClose }: CitationDrawerProps) {
  if (citations.length === 0) return null;
  const active = activeIndex == null ? null : citations.find((c) => c.index === activeIndex);

  return (
    <aside className="cite-drawer">
      <header className="cite-drawer-head">
        <div>
          <h2>
            Sources
            <span className="badge">{citations.length}</span>
          </h2>
          <p>The individual records that produced this answer.</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="btn btn-ghost"
          aria-label="Close source drawer"
        >
          Close
        </button>
      </header>
      <div className="cite-drawer-body">
        {active ? (
          <Citation citation={active} focused />
        ) : (
          citations.map((c) => <Citation key={c.index} citation={c} />)
        )}
      </div>
    </aside>
  );
}
