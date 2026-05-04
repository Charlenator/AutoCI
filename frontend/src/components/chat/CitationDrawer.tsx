"use client";

import { useCallback, useState } from "react";
import Citation from "./Citation";
import type {
  Citation as CitationType,
  LiveSearchPayload,
  QueryPlan,
  SqlResult,
} from "../../lib/chat-types";

interface CitationDrawerProps {
  citations: CitationType[];
  activeIndex: number | null;
  plan?: QueryPlan | null;
  sqlResult?: SqlResult | null;
  ragChunkCount?: number;
  liveSearch?: LiveSearchPayload | null;
}

// ═══════════════════════════════════════════════════════════════════════════
//  Provenance sidebar — always-visible Chain-of-Thought log
//  "Answer Provenance" with card + arrow layout showing how this answer was
//  produced. Polymorphic per retrieval method.
// ═══════════════════════════════════════════════════════════════════════════

export default function CitationDrawer({
  citations,
  activeIndex,
  plan,
  sqlResult,
  ragChunkCount,
  liveSearch,
}: CitationDrawerProps) {
  const active = activeIndex == null ? null : citations.find((c) => c.index === activeIndex);

  return (
    <aside className="cite-drawer open">
      <header className="cite-drawer-head">
        <div>
          <h2>
            Answer Provenance
            <span className="badge">{citations.length}</span>
          </h2>
          <p>Chain-of-thought log showing how this answer was produced.</p>
        </div>
      </header>
      <div className="cite-drawer-body">
        {plan && <ProvenanceTimeline
          plan={plan}
          sqlResult={sqlResult ?? null}
          ragChunkCount={ragChunkCount ?? 0}
          liveSearch={liveSearch ?? null}
          citations={citations}
        />}

        {/* ── Focused citation card, or all citations ── */}
        {active ? (
          <Citation citation={active} focused />
        ) : (
          citations.map((c) => <Citation key={c.index} citation={c} />)
        )}
      </div>
    </aside>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
//  ProvenanceTimeline
//  Vertical stepper showing: User Query → System Reasoning → Action →
//  Result (polymorphic). Professional / developer-centric / Vercel aesthetic.
// ═══════════════════════════════════════════════════════════════════════════

function ProvenanceTimeline({
  plan,
  sqlResult,
  ragChunkCount,
  liveSearch,
  citations,
}: {
  plan: QueryPlan;
  sqlResult: SqlResult | null;
  ragChunkCount: number;
  liveSearch: LiveSearchPayload | null;
  citations: CitationType[];
}) {
  // Determine retrieval method(s) for polymorphic rendering
  const method = plan.needs_live_search
    ? "live"
    : plan.needs_sql && plan.needs_rag
    ? "combined"
    : plan.needs_sql
    ? "sql"
    : plan.needs_rag
    ? "vector"
    : "none";

  // ── Step 1: User Intent — always shown ────────────────
  // ── Step 2: System Reasoning — always shown ───────────
  // ── Step 3: The Action (polymorphic) ───────────────────
  // ── Step 4: The Result (polymorphic) ──────────────────

  return (
    <div className="prov">
      {/* Step 1 — User Query */}
      <div className="prov-card">
        <div className="prov-card-head">
          <span className="prov-card-num">1</span>
          <span className="prov-card-label">Step 1 · User Intent</span>
          <span className="prov-card-title">Your Query</span>
        </div>
        <div className="prov-card-body">
          
            <div className="prov-text">{plan.original_query}</div>
          
        </div>
      </div>

      <div className="prov-arrow">▾</div>

      {/* Step 2 — System Reasoning */}
      <div className="prov-card">
        <div className="prov-card-head">
          <span className="prov-card-num">2</span>
          <span className="prov-card-label">Step 2 · System Reasoning</span>
          <span className="prov-card-title">
            {plan.explanation || "The system decided how to answer."}
          </span>
        </div>
        <div className="prov-card-body">
          {plan.fallback_reason && (
            <div >
              <div className="prov-block-label">Fallback</div>
              <div className="prov-text" style={{ color: "var(--accent)" }}>
                {plan.fallback_reason}
              </div>
            </div>
          )}
          <div >
            <dl className="prov-kv">
              <dt>Confidence</dt>
              <dd>
                <b>{(plan.confidence * 100).toFixed(0)}%</b>
              </dd>
              {plan.sql_template_id && (
                <>
                  <dt>Template</dt>
                  <dd>{plan.sql_template_id}</dd>
                </>
              )}
              {plan.sql_template_params && Object.keys(plan.sql_template_params).length > 0 && (
                <>
                  <dt>Params</dt>
                  <dd>{JSON.stringify(plan.sql_template_params)}</dd>
                </>
              )}
              {plan.rag_corpus_filter && (
                <>
                  <dt>Corpus</dt>
                  <dd>{plan.rag_corpus_filter}</dd>
                </>
              )}
              {plan.needs_live_search && (
                <>
                  <dt>Sources</dt>
                  <dd>{plan.live_search_sources.join(", ") || "all"}</dd>
                </>
              )}
            </dl>
          </div>
        </div>
      </div>

      <div className="prov-arrow">▾</div>

      {/* Step 3 — The Action (polymorphic) */}
      <div className="prov-card">
        <div className="prov-card-head">
          <span className="prov-card-num">3</span>
          <span className="prov-card-label">Step 3 · Action</span>
          <span className="prov-card-title">{actionTitle(method)}</span>
        </div>
        <div className="prov-card-body">
          {method === "sql" && sqlResult && (
            <SqlActionBlock plan={plan} sqlResult={sqlResult} />
          )}
          {method === "vector" && <VectorActionBlock plan={plan} />}
          {(method === "live") && <LiveActionBlock plan={plan} liveSearch={liveSearch} />}
          {method === "combined" && (
            <>
              {plan.needs_sql && sqlResult && <SqlActionBlock plan={plan} sqlResult={sqlResult} />}
              {plan.needs_rag && <VectorActionBlock plan={plan} />}
            </>
          )}
          {method === "none" && (
            <div >
              <div className="prov-text">No retrieval method was selected.</div>
            </div>
          )}
        </div>
      </div>

      <div className="prov-arrow">▾</div>

      {/* Step 4 — The Result (polymorphic) */}
      <div className="prov-card">
        <div className="prov-card-head">
          <span className="prov-card-num">4</span>
          <span className="prov-card-label">Step 4 · Result</span>
          <span className="prov-card-title">{resultTitle(method)}</span>
        </div>
        <div className="prov-card-body">
          {method === "sql" && sqlResult && <SqlResultBlock sqlResult={sqlResult} citations={citations} />}
          {method === "vector" && <VectorResultBlock plan={plan} citations={citations} />}
          {method === "live" && <LiveResultBlock liveSearch={liveSearch} />}
          {method === "combined" && (
            <>
              {plan.needs_sql && sqlResult && <SqlResultBlock sqlResult={sqlResult} citations={citations} />}
              {plan.needs_rag && <VectorResultBlock plan={plan} citations={citations} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Action block helpers ────────────────────────────────────────────────

function actionTitle(method: string): string {
  switch (method) {
    case "sql": return "SQL Query Execution";
    case "vector": return "Vector Similarity Search";
    case "live": return "Live API Request";
    case "combined": return "Combined SQL + Vector Retrieval";
    default: return "No Action";
  }
}

function resultTitle(method: string): string {
  switch (method) {
    case "sql": return "Query Results";
    case "vector": return "Retrieved Knowledge Chunks";
    case "live": return "API Response";
    case "combined": return "Combined Results";
    default: return "—";
  }
}

function SqlActionBlock({ plan, sqlResult }: { plan: QueryPlan; sqlResult: SqlResult }) {
  const sqlText = sqlResult.sql || plan.sql_freeform || "";
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(sqlText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }, [sqlText]);

  return (
    <div >
      <div className="prov-block-label">Exact Query</div>
      <dl className="prov-kv" style={{ marginBottom: "8px" }}>
        {sqlResult.template_id && (
          <>
            <dt>Template</dt>
            <dd><b>{sqlResult.template_id}</b></dd>
          </>
        )}
        <dt>Rows</dt>
        <dd><b>{sqlResult.row_count}</b></dd>
      </dl>
      <div className="prov-code-wrap">
        <button
          type="button"
          className={`prov-copy${copied ? " copied" : ""}`}
          onClick={handleCopy}
        >
          {copied ? "Copied" : "Copy"}
        </button>
        <pre className="prov-code">{sqlText}</pre>
      </div>
    </div>
  );
}

function VectorActionBlock({ plan }: { plan: QueryPlan }) {
  return (
    <div >
      <div className="prov-block-label">Similarity Search</div>
      <dl className="prov-kv">
        <dt>Knowledge Store</dt>
        <dd>{plan.rag_corpus_filter || "default corpus"}</dd>
        <dt>Corpus</dt>
        <dd>{plan.rag_corpus_filter || "—"}</dd>
        <dt>Query</dt>
        <dd>{plan.rag_query || plan.original_query}</dd>
      </dl>
    </div>
  );
}

function LiveActionBlock({ plan, liveSearch }: { plan: QueryPlan; liveSearch: LiveSearchPayload | null }) {
  const sources = plan.live_search_sources.length > 0
    ? plan.live_search_sources.join(", ")
    : "all sources";
  const [copied, setCopied] = useState(false);

  const responseJson = liveSearch ? JSON.stringify(liveSearch, null, 2) : "";
  const method = plan.needs_sql ? "POST" : "GET";

  const handleCopy = useCallback(() => {
    if (!responseJson) return;
    navigator.clipboard.writeText(responseJson).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }, [responseJson]);

  return (
    <>
      <div >
        <div className="prov-block-label">Endpoint</div>
        <dl className="prov-kv">
          <dt>Sources</dt>
          <dd>{sources}</dd>
          <dt>Method</dt>
          <dd><b>{method}</b></dd>
          <dt>Topic</dt>
          <dd>{plan.live_search_topic || plan.original_query}</dd>
        </dl>
      </div>
      {responseJson && (
        <div >
          <div className="prov-block-label">API Response</div>
          <div className="prov-code-wrap">
            <button
              type="button"
              className={`prov-copy${copied ? " copied" : ""}`}
              onClick={handleCopy}
            >
              {copied ? "Copied" : "Copy"}
            </button>
            <pre className="prov-json">{responseJson}</pre>
          </div>
        </div>
      )}
    </>
  );
}

// ── Result block helpers ────────────────────────────────────────────────

function SqlResultBlock({ sqlResult, citations }: { sqlResult: SqlResult; citations: CitationType[] }) {
  const [sourceOpen, setSourceOpen] = useState(false);
  const rows = sqlResult.rows ?? [];
  const evidenceRows = sqlResult.evidence_rows ?? [];
  const evidenceCount = sqlResult.evidence_row_count ?? evidenceRows.length;

  // Find the SQL citation to extract the full SQL
  const sqlCitation = citations.find((c) => c.kind === "sql_template" || c.kind === "sql_freeform");
  const fullSql = sqlCitation?.sqlResult?.sql || sqlResult.sql;

  return (
    <>
      <div >
        <div className="prov-block-label">Result Table</div>
        <table className="prov-table">
          <thead>
            <tr>
              {rows.length > 0 && Object.keys(rows[0]).map((k) => (
                <th key={k}>{k}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 10).map((row, i) => (
              <tr key={i}>
                {Object.keys(rows[0]).map((k) => (
                  <td key={k}>{formatCell(row[k])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length > 10 && (
          <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "6px", fontFamily: "var(--font-mono)" }}>
            Showing first 10 of {rows.length} rows.
          </div>
        )}
        {rows.length === 0 && (
          <div style={{ fontSize: "12px", color: "var(--muted)" }}>No rows returned.</div>
        )}
      </div>

      {/* Source records — collapsed by default */}
      {(evidenceRows.length > 0 || sqlResult.evidence_sql) && (
        <div className="prov-collapse">
          <div
            className="prov-collapse-trigger"
            onClick={() => setSourceOpen((v) => !v)}
          >
            <span>Source Records</span>
            <span style={{ marginLeft: "auto" }}>
              {evidenceCount} row{evidenceCount === 1 ? "" : "s"}
            </span>
            <span>{sourceOpen ? "−" : "+"}</span>
          </div>
          {sourceOpen && (
            <div className="prov-collapse-body">
              <table className="prov-table">
                <thead>
                  <tr>
                    {evidenceRows.length > 0 && Object.keys(evidenceRows[0]).map((k) => (
                      <th key={k}>{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {evidenceRows.slice(0, 20).map((row, i) => (
                    <tr key={i}>
                      {Object.keys(evidenceRows[0]).map((k) => (
                        <td key={k}>{formatCell(row[k])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {evidenceRows.length > 20 && (
                <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "4px", fontFamily: "var(--font-mono)" }}>
                  Showing first 20 of {evidenceRows.length} rows.
                </div>
              )}

              {/* Source SQL — collapsed by default inside source records */}
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
                      fontWeight: 600,
                    }}
                  >
                    Source SQL
                  </summary>
                  <pre className="prov-code" style={{ marginTop: "6px" }}>
                    {sqlResult.evidence_sql.trim()}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      )}

      {/* Full SQL — collapsed by default */}
      {fullSql && (
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
            Full SQL
          </summary>
          <pre className="prov-code" style={{ marginTop: "6px" }}>
            {fullSql.trim()}
          </pre>
        </details>
      )}
    </>
  );
}

function VectorResultBlock({ plan, citations }: { plan: QueryPlan; citations: CitationType[] }) {
  const ragCitations = citations.filter((c) => c.kind === "rag");

  if (ragCitations.length === 0) {
    return (
      <div >
        <div className="prov-text" style={{ color: "var(--muted)" }}>
          No chunks retrieved for "{plan.rag_query || plan.original_query}".
        </div>
      </div>
    );
  }

  return (
    <>
      {ragCitations.map((cit) => (
        <div key={cit.index} >
          <div className="prov-block-label">
            Chunk [{cit.index}]
            {cit.ragChunk?.similarity != null && (
              <span style={{ marginLeft: "8px", color: "var(--ink)", fontWeight: 700 }}>
                similarity <b>{(cit.ragChunk.similarity * 100).toFixed(1)}%</b>
              </span>
            )}
          </div>
          <div className="prov-quote">
            {cit.ragChunk?.chunk_text || "—"}
          </div>
          {cit.ragChunk?.metadata && Object.keys(cit.ragChunk.metadata).length > 0 && (
            <details style={{ marginTop: "6px" }}>
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
                {JSON.stringify(cit.ragChunk.metadata, null, 2)}
              </pre>
            </details>
          )}
        </div>
      ))}
    </>
  );
}

function LiveResultBlock({ liveSearch }: { liveSearch: LiveSearchPayload | null }) {
  if (!liveSearch || Object.keys(liveSearch).length === 0) {
    return (
      <div >
        <div className="prov-text" style={{ color: "var(--muted)" }}>
          No live data was returned.
        </div>
      </div>
    );
  }

  return (
    <div >
      <div className="prov-block-label">Source Summary</div>
      {Object.entries(liveSearch).map(([name, info]) => (
        <div key={name} style={{ display: "flex", justifyContent: "space-between", fontSize: "12.5px", padding: "2px 0" }}>
          <span style={{ color: "var(--text-soft)", fontFamily: "var(--font-mono)" }}>{name}</span>
          <span>
            {info?.error ? (
              <span style={{ color: "var(--accent)", fontSize: "12px" }}>{info.error}</span>
            ) : (
              <b style={{ color: "var(--ink)" }}>{info?.count ?? 0} items</b>
            )}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Cell formatter ──────────────────────────────────────────────────────

function formatCell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
