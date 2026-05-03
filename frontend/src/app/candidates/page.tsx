// Sprint A2: Candidate Search tab skeleton. Real semantic search + table +
// Schedule Meeting flow lands in Sprint B6-B8. Styled per style_guide.css §14.

export default function CandidatesPage() {
  return (
    <div className="cand-page">
      {/* Filters rail — stubbed for now */}
      <aside className="filters">
        <h3>Filters</h3>
        <p style={{ fontSize: "13px", color: "var(--text-soft)" }}>
          Role, skill, seniority, location, status, date-range facets land in
          Sprint B6.
        </p>
      </aside>

      <div className="cand-main">
        <header className="cand-header">
          <h1 className="chat-title">Candidate Search</h1>
          <p className="chat-subtitle">
            Semantic search over CVs ingested via the inbound email pipeline.
            Sortable table with download links, missing-field flags, duplicate
            detection, and one-click meeting scheduling via cal.com.
          </p>
        </header>

        <div className="cand-toolbar">
          <div className="search-input">
            <svg className="ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input type="text" placeholder="Semantic search (Sprint B6)…" disabled />
          </div>
          <span className="cand-meta">0 candidates</span>
        </div>

        <div className="cand-table-wrap" style={{ padding: "40px 32px" }}>
          <div
            style={{
              maxWidth: "480px",
              color: "var(--text-soft)",
              fontSize: "14px",
              lineHeight: "1.6",
            }}
          >
            <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 8px", fontWeight: 600 }}>
              Sprint B6-B8 in progress
            </h3>
            <p>
              Inbound CV pipeline (Edge Function plus Modal worker), then the
              Candidate table, then the Schedule Meeting flow (cal.com slot grid
              plus Resend invite) land here. Migration 004 is already applied;
              the queue table is waiting for its first row.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
