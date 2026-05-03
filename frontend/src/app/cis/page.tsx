// Sprint A2: Continuous Improvement Suite tab skeleton. Real K_SCOPING +
// K_TOOL_SELECTOR + dynamic orchestrator + interventions table + FMEA land
// in Sprint C. Styled per style_guide.css §15.

export default function CISPage() {
  return (
    <div className="cis-page">
      <aside className="cis-side">
        <h3>Available tools</h3>
        <p style={{ fontSize: "13px", color: "var(--text-soft)" }}>
          Sprint C wires the tool selector here. For now, the legacy dashboard
          has the working Kaizen flow.
        </p>
      </aside>

      <div className="cis-main">
        <header className="cis-header">
          <h1 className="chat-title">Continuous Improvement Suite</h1>
          <p className="chat-subtitle">
            Conversational scoping, then tool selection, then execution with
            HITL gates between each DMAIC phase.
          </p>
        </header>

        <div className="timeline" style={{ padding: "40px 32px" }}>
          <div
            style={{
              maxWidth: "520px",
              color: "var(--text-soft)",
              fontSize: "14px",
              lineHeight: "1.6",
            }}
          >
            <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 8px", fontWeight: 600 }}>
              Sprint C in progress
            </h3>
            <p>
              The scoping chat plus tool selector plus dynamic orchestrator
              replace the current fixed DMAIC pipeline. Until then, the legacy
              dashboard has the working Kaizen flow.
            </p>
            <div style={{ marginTop: "14px", display: "flex", gap: "8px" }}>
              <a
                href="/dashboard"
                className="btn btn-primary"
              >
                Open legacy dashboard
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
