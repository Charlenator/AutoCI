"use client";

import { useState } from "react";

// Sprint A2: skeleton drawer. Renders a collapse toggle on the right edge of
// the viewport. Empty content for now — the React Flow system diagram lights-up
// view is wired in Sprint C5.
//
// Future: cumulative node-status updates as agents are touched across all 3 tabs.

const COLLAPSED_WIDTH = 32;
const EXPANDED_WIDTH = 360;

export default function RightDrawer() {
  const [open, setOpen] = useState(false);

  return (
    <aside
      style={{ width: open ? EXPANDED_WIDTH : COLLAPSED_WIDTH }}
      className="border-l border-gray-200 bg-white flex flex-col flex-shrink-0 transition-[width] duration-200 ease-out"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="px-2 py-3 hover:bg-gray-50 border-b border-gray-200 flex items-center justify-center text-gray-500 hover:text-gray-800"
        aria-label={open ? "Collapse system diagram" : "Expand system diagram"}
        title={open ? "Collapse" : "System diagram"}
      >
        <span className="text-xl">{open ? "→" : "🗺️"}</span>
      </button>
      {open && (
        <div className="flex-1 overflow-y-auto p-4 text-sm text-gray-600">
          <h2 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
            <span>🗺️</span>
            <span>System diagram</span>
          </h2>
          <p className="text-xs text-gray-500 leading-relaxed">
            Sprint C5 wires the live React Flow system diagram here. As agents,
            routes, and external APIs are touched across the three tabs, their
            nodes will light up cumulatively.
          </p>
          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-500">
            Placeholder — the static dev-progress diagram lives at{" "}
            <code className="text-gray-700">dev-tools/diagram/index.html</code>.
          </div>
        </div>
      )}
    </aside>
  );
}
