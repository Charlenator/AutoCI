"use client";

import { SOURCES_DATA, type CorpusEntry, type TableEntry } from "../../lib/sources-data";

interface KnowledgeSourcesPanelProps {
  open: boolean;
  onClose: () => void;
}

// Modal-style overlay listing every RAG corpus + queryable SQL table that
// AutoCI can answer from. Uses a static snapshot of the /sources/ endpoint
// so the panel opens instantly without a network call.
// Restyled per style_guide.css §16.
export default function KnowledgeSourcesPanel({ open, onClose }: KnowledgeSourcesPanelProps) {
  if (!open) return null;

  const data = SOURCES_DATA;

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <section className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h2>Knowledge sources</h2>
            <p>Every corpus and queryable table the chat can draw from.</p>
          </div>
          <button type="button" onClick={onClose} className="btn btn-ghost">
            Close
          </button>
        </div>

        <div className="modal-body">
          <div className="modal-summary">
            <SummaryStat label="Corpora" value={data.summary.corpora_count} />
            <SummaryStat label="Total chunks" value={data.summary.total_chunks} />
            <SummaryStat label="SQL tables" value={data.summary.tables_count} />
            <SummaryStat label="Total rows" value={data.summary.total_table_rows} />
          </div>

          <div style={{ marginTop: "18px" }}>
            <div className="modal-section">
              <h3 className="modal-section-h">Vector corpora</h3>
              <p className="modal-section-sub">
                Indexed in corpus_chunks (BAAI/bge-small-en-v1.5, 384-d)
              </p>
              {data.corpora.length === 0 && (
                <p style={{ fontSize: "13px", color: "var(--text-soft)" }}>No corpora yet.</p>
              )}
              {data.corpora.map((c) => (
                <CorpusCard key={c.name} corpus={c} />
              ))}
            </div>

            <div className="modal-section">
              <h3 className="modal-section-h">Queryable SQL tables</h3>
              <p className="modal-section-sub">
                Available to the Query Planner via validated templates and freeform SELECT
              </p>
              {data.tables.map((t) => (
                <TableCard key={t.name} table={t} />
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="summary-stat">
      <div className="k">{label}</div>
      <div className="v">{value.toLocaleString()}</div>
    </div>
  );
}

function CorpusCard({ corpus }: { corpus: CorpusEntry }) {
  return (
    <article className="source-card">
      <div className="source-card-head">
        <span className="source-card-name">{corpus.name}</span>
        <span className="source-card-meta">
          {corpus.chunk_count} chunks
          {corpus.confidential_count > 0 ? ` · ${corpus.confidential_count} confidential` : ""}
          {corpus.embedded_count !== corpus.chunk_count
            ? ` · ${corpus.embedded_count} embedded`
            : ""}
        </span>
      </div>
      {corpus.description && <p className="source-card-desc">{corpus.description}</p>}
      {corpus.samples.length > 0 && (
        <details style={{ marginTop: "8px" }}>
          <summary
            style={{
              cursor: "pointer",
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontWeight: 600,
            }}
          >
            Sample chunks ({corpus.samples.length})
          </summary>
          <ul style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "8px" }}>
            {corpus.samples.map((s) => (
              <li
                key={s.chunk_id}
                style={{
                  borderLeft: "2px solid var(--ink-2)",
                  paddingLeft: "10px",
                  fontSize: "12px",
                  whiteSpace: "pre-wrap",
                  color: "var(--text-soft)",
                }}
              >
                {s.chunk_text}
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}

function TableCard({ table }: { table: TableEntry }) {
  return (
    <article className="source-card">
      <div className="source-card-head">
        <span className="source-card-name">{table.name}</span>
        <span className="source-card-meta">{table.row_count.toLocaleString()} rows</span>
      </div>
      {table.description && <p className="source-card-desc">{table.description}</p>}
      {table.columns.length > 0 && (
        <details style={{ marginTop: "8px" }}>
          <summary
            style={{
              cursor: "pointer",
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontWeight: 600,
            }}
          >
            Columns ({table.columns.length})
          </summary>
          <ul
            style={{
              marginTop: "8px",
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "4px 12px",
              fontSize: "12px",
            }}
          >
            {table.columns.map((c) => (
              <li key={c.column_name} style={{ fontFamily: "var(--font-mono)", color: "var(--text)" }}>
                {c.column_name}
                <span style={{ color: "var(--muted)" }}> {c.data_type}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
      {table.samples.length > 0 && (
        <details style={{ marginTop: "8px" }}>
          <summary
            style={{
              cursor: "pointer",
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontWeight: 600,
            }}
          >
            Sample rows ({table.samples.length})
          </summary>
          <pre
            style={{
              marginTop: "8px",
              padding: "10px 12px",
              background: "var(--sage-wash)",
              borderRadius: "var(--r-md)",
              fontSize: "11.5px",
              overflowX: "auto",
              color: "var(--text)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {JSON.stringify(table.samples, null, 2)}
          </pre>
        </details>
      )}
    </article>
  );
}
