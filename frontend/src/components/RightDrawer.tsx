"use client";

import { useState } from "react";

// Sprint A2: skeleton drawer. Renders a collapse toggle on the right edge of
// the viewport. Restyled per style_guide.css §6.

const EXPANDED_WIDTH = 360;

export default function RightDrawer() {
  const [open, setOpen] = useState(false);

  return (
    <aside
      className={`right-drawer${open ? " open" : ""}`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="drawer-toggle"
        aria-label={open ? "Collapse system diagram" : "Expand system diagram"}
        title={open ? "Collapse" : "System diagram"}
      >
        {open ? "Close" : "Map"}
      </button>
      {open && (
        <div className="drawer-body">
          <h3>System diagram</h3>
          <p>
            Sprint C5 wires the live React Flow system diagram here. As agents,
            routes, and external APIs are touched across the three tabs, their
            nodes will light up cumulatively.
          </p>
          <div className="drawer-stub">
            <span className="mono">dev-tools/diagram/index.html</span> has the
            internal dev-progress diagram.
          </div>
        </div>
      )}
    </aside>
  );
}
