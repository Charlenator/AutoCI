"use client";

import { useState } from "react";
import type { Citation as CitationType } from "../../lib/chat-types";

interface CitationProps {
  citation: CitationType;
  focused?: boolean;
}

// Renders the full body of a single citation inside the drawer. Branches by
// kind — RAG chunk, validated SQL template, freeform SELECT. Restyled per
// style_guide.css §11 + §12.
export default function Citation({ citation, focused = false }: CitationProps) {
  return (
    <article className={`cite-card${focused ? " focused" : ""}`}>
      <header className="cite-card-head">
        <div className="cite-card-num">{citation.index}</div>
        <span className="cite-card-kind">
          {citation.kind === "rag"
            ? "Knowledge"
            : citation.kind === "sql_template"
            ? "SQL Template"
            : "Freeform SQL"}
        </span>
        <span className="cite-card-label">{citation.shortLabel}</span>
      </header>
      <div className="cite-card-body">
        {citation.kind === "rag" && citation.ragChunk && (
          <RagChunkBody chunk={citation.ragChunk} />
        )}
        {(citation.kind === "sql_template" || citation.kind === "sql_freeform") && citation.sqlResult && (
          <SqlResultBody sqlResult={citation.sqlResult} />
        )}
      </div>
    </article>
  );
}

function RagChunkBody({ chunk }: { chunk: NonNullable<CitationType["ragChunk"]> }) {
  return (
    <div>
      <dl className="field-row">
        <dt>Corpus</dt>
        <dd>{chunk.corpus_name}</dd>
        {chunk.similarity != null && (
          <>
            <dt>Similarity</dt>
            <dd>{chunk.similarity.toFixed(3)}</dd>
          </>
        )}
      </dl>
      <div className="cite-section-label">Chunk text</div>
      <div className="chunk-text">{chunk.chunk_text}</div>
      {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
        <details style={{ marginTop: "10px" }}>
          <summary
            style={{
              cursor: "pointer",
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "var(--muted)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            Metadata
          </summary>
          <pre
            style={{
              marginTop: "6px",
              padding: "10px 12px",
              background: "var(--sage-wash)",
              borderRadius: "var(--r-md)",
              fontSize: "11.5px",
              overflowX: "auto",
              color: "var(--text)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {JSON.stringify(chunk.metadata, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function SqlResultBody({ sqlResult }: { sqlResult: NonNullable<CitationType["sqlResult"]> }) {
  return (
    <SqlResultContent sqlResult={sqlResult} />
  );
}

function SqlResultContent({ sqlResult }: { sqlResult: NonNullable<CitationType["sqlResult"]> }) {
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const rows = sqlResult.rows ?? [];
  const evidenceRows = sqlResult.evidence_rows ?? [];
  const evidenceCount = sqlResult.evidence_row_count ?? evidenceRows.length;

  return (
    <div>
      <dl className="field-row">
        {sqlResult.template_id && (
          <>
            <dt>Template</dt>
            <dd>{sqlResult.template_id}</dd>
          </>
        )}
        <dt>Rows</dt>
        <dd>{String(sqlResult.row_count)}</dd>
      </dl>

      <details>
        <summary className="cite-section-label" style={{ cursor: "pointer" }}>
          SQL
        </summary>
        <pre className="sql-pre" style={{ marginTop: "6px" }}>
          {sqlResult.sql.trim()}
        </pre>
      </details>

      <div style={{ marginTop: "10px" }}>
        {rows.length > 0 && (
          <>
            <div className="cite-section-label">Result</div>
            <RowTable rows={rows} />
          </>
        )}
      </div>

      {(evidenceRows.length > 0 || sqlResult.evidence_sql || sqlResult.evidence_error) && (
        <div className="evidence">
          <div
            className="evidence-head"
            onClick={() => setEvidenceOpen((v) => !v)}
          >
            <div className="marker">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v20M2 12h20" />
              </svg>
            </div>
            <span className="evidence-title">Source records</span>
            <span className="evidence-count">{evidenceCount}</span>
            <span style={{ color: "var(--muted)", fontSize: "12px", fontFamily: "var(--font-mono)" }}>
              {evidenceOpen ? "−" : "+"}
            </span>
          </div>

          {evidenceOpen && (
            <div className="evidence-body">
              {sqlResult.evidence_error ? (
                <p className="evidence-help" style={{ color: "var(--accent)" }}>
                  Couldn&rsquo;t load source records: {sqlResult.evidence_error}
                </p>
              ) : (
                <>
                  <p className="evidence-help">
                    The individual records that produced the aggregate above.
                  </p>
                  <RowTable rows={evidenceRows} />
                  {sqlResult.evidence_sql && (
                    <details style={{ marginTop: "10px" }}>
                      <summary
                        style={{
                          cursor: "pointer",
                          fontFamily: "var(--font-mono)",
                          fontSize: "10px",
                          color: "var(--muted)",
                          textTransform: "uppercase",
                          letterSpacing: "0.1em",
                        }}
                      >
                        Source SQL
                      </summary>
                      <pre className="sql-pre" style={{ marginTop: "6px" }}>
                        {sqlResult.evidence_sql.trim()}
                      </pre>
                    </details>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RowTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows || rows.length === 0) return null;
  const columnKeys = Object.keys(rows[0]);
  const cap = 20;
  return (
    <div>
      <table className="row-table">
        <thead>
          <tr>
            {columnKeys.map((k) => (
              <th key={k}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, cap).map((row, i) => (
            <tr key={i}>
              {columnKeys.map((k) => (
                <td key={k}>{formatCell(row[k])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > cap && (
        <p style={{ fontSize: "11px", color: "var(--muted)", marginTop: "6px", fontFamily: "var(--font-mono)" }}>
          Showing first {cap} of {rows.length} rows.
        </p>
      )}
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
