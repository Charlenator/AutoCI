"use client";

import { useState } from "react";
import type { LiveSearchPayload, QueryPlan, SqlResult } from "../../lib/chat-types";

interface QueryTransformationCardProps {
  plan: QueryPlan;
  sqlResult: SqlResult | null;
  ragChunkCount: number;
  liveSearch?: LiveSearchPayload | null;
}

// Collapsed by default — most users want the answer, not the methodology.
// When expanded, three blocks: Your query / What we ran / Exact query.
// Restyled per style_guide.css §10 — the ONE dark surface in light mode.
export default function QueryTransformationCard({
  plan,
  sqlResult,
  ragChunkCount,
  liveSearch,
}: QueryTransformationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const route = describeRoute(plan, sqlResult, ragChunkCount);
  const exactQuery = describeExactQuery(plan, sqlResult);
  const liveSearchSummary = describeLiveSearch(plan, liveSearch);

  return (
    <section className={`qtc${expanded ? " open" : ""}`}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="qtc-head"
        aria-expanded={expanded}
      >
        <span className="qtc-head-l">
          <span className="qtc-tag">How this was answered</span>
          <span className="qtc-route">{route.shortLabel}</span>
        </span>
        <span className="qtc-head-r">
          <span className="qtc-conf">
            confidence <b>{plan.confidence.toFixed(2)}</b>
          </span>
          <span className="qtc-toggle" aria-hidden>
            {expanded ? "−" : "+"}
          </span>
        </span>
      </button>

      {expanded && (
        <div className="qtc-body">
          <div className="qtc-block">
            <div className="qtc-label">Your query</div>
            <div className="qtc-prose">{plan.original_query}</div>
          </div>

          <div className="qtc-block">
            <div className="qtc-label">What we ran</div>
            <div className="qtc-detail">
              <span className="qtc-pill">{route.kindLabel}</span>
              {route.detailLabel}
            </div>
            {liveSearchSummary && (
              <div className="qtc-detail" style={{ marginTop: "8px" }}>
                <span className="qtc-pill" style={{ background: "var(--debug-accent)", color: "var(--debug-bg)" }}>
                  Live web search
                </span>
                {liveSearchSummary}
              </div>
            )}
            {plan.explanation && (
              <div className="qtc-explain">{plan.explanation}</div>
            )}
            {plan.fallback_reason && (
              <div className="qtc-explain" style={{ color: "var(--debug-accent)" }}>
                Fallback: {plan.fallback_reason}
              </div>
            )}
          </div>

          {exactQuery && (
            <div className="qtc-block">
              <div className="qtc-label">Exact query</div>
              {exactQuery.kind === "sql" && (
                <pre className="qtc-pre">{exactQuery.text}</pre>
              )}
              {exactQuery.kind === "vector" && (
                <div className="qtc-pre">
                  <dl className="qtc-kv">
                    <dt>Embedded query</dt>
                    <dd>{exactQuery.query}</dd>
                    {exactQuery.corpusFilter && (
                      <>
                        <dt>Corpus filter</dt>
                        <dd>{exactQuery.corpusFilter}</dd>
                      </>
                    )}
                  </dl>
                </div>
              )}
              {exactQuery.kind === "combined" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {exactQuery.sqlText && (
                    <div>
                      <div className="qtc-label" style={{ marginBottom: "4px" }}>
                        SQL
                      </div>
                      <pre className="qtc-pre">{exactQuery.sqlText}</pre>
                    </div>
                  )}
                  <div>
                    <div className="qtc-label" style={{ marginBottom: "4px" }}>
                      Vector retrieval
                    </div>
                    <div className="qtc-pre">
                      <dl className="qtc-kv">
                        <dt>Embedded query</dt>
                        <dd>{exactQuery.vectorQuery}</dd>
                        {exactQuery.corpusFilter && (
                          <>
                            <dt>Corpus filter</dt>
                            <dd>{exactQuery.corpusFilter}</dd>
                          </>
                        )}
                      </dl>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Routing label helpers
// ---------------------------------------------------------------------------

interface RouteDescription {
  kindLabel: string;
  shortLabel: string;
  detailLabel: string;
}

function describeRoute(
  plan: QueryPlan,
  sqlResult: SqlResult | null,
  ragChunkCount: number,
): RouteDescription {
  const usedSql = plan.needs_sql;
  const usedRag = plan.needs_rag;

  if (usedSql && usedRag) {
    return {
      kindLabel: "Combined SQL + Vector",
      shortLabel: "SQL + vector retrieval",
      detailLabel: combineDetails(plan, sqlResult, ragChunkCount),
    };
  }
  if (usedSql) {
    if (plan.sql_template_id) {
      return {
        kindLabel: "Validated SQL template",
        shortLabel: `template ${plan.sql_template_id}`,
        detailLabel: `Template "${plan.sql_template_id}"${
          plan.sql_template_params && Object.keys(plan.sql_template_params).length
            ? ` with params ${formatParams(plan.sql_template_params)}`
            : ""
        }${rowsTrailer(sqlResult)}`,
      };
    }
    return {
      kindLabel: "Freeform SELECT",
      shortLabel: "freeform SELECT",
      detailLabel: `LLM-generated SELECT statement${rowsTrailer(sqlResult)}`,
    };
  }
  if (usedRag) {
    return {
      kindLabel: "Vector retrieval",
      shortLabel: "RAG vector retrieval",
      detailLabel: `Semantic search${
        plan.rag_corpus_filter ? ` against the "${plan.rag_corpus_filter}" corpus` : ""
      }${ragChunkCount > 0 ? ` — ${ragChunkCount} chunk${ragChunkCount === 1 ? "" : "s"}` : ""}`,
    };
  }
  return {
    kindLabel: "No route",
    shortLabel: "no retrieval",
    detailLabel: "Nothing matched.",
  };
}

function combineDetails(plan: QueryPlan, sqlResult: SqlResult | null, ragChunkCount: number): string {
  const sqlBit = plan.sql_template_id
    ? `validated template "${plan.sql_template_id}"`
    : "freeform SELECT";
  const ragBit = plan.rag_corpus_filter
    ? `vector search against "${plan.rag_corpus_filter}"`
    : "vector search";
  return `${sqlBit}${rowsTrailer(sqlResult)} + ${ragBit}${
    ragChunkCount > 0 ? ` (${ragChunkCount} chunk${ragChunkCount === 1 ? "" : "s"})` : ""
  }.`;
}

function rowsTrailer(sqlResult: SqlResult | null): string {
  if (!sqlResult || sqlResult.error) return "";
  const c = sqlResult.row_count ?? 0;
  return ` — ${c} row${c === 1 ? "" : "s"}`;
}

function formatParams(params: Record<string, unknown>): string {
  return (
    "{" +
    Object.entries(params)
      .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
      .join(", ") +
    "}"
  );
}

// ---------------------------------------------------------------------------
// Exact-query block helpers
// ---------------------------------------------------------------------------

type ExactQuery =
  | { kind: "sql"; text: string }
  | { kind: "vector"; query: string; corpusFilter: string | null }
  | {
      kind: "combined";
      sqlText: string | null;
      vectorQuery: string;
      corpusFilter: string | null;
    };

function describeLiveSearch(plan: QueryPlan, liveSearch: LiveSearchPayload | null | undefined): string | null {
  if (!plan.needs_live_search) return null;
  const topic = plan.live_search_topic || plan.original_query;

  const topLevelError = (liveSearch as unknown as { error?: string } | null)?.error;
  if (typeof topLevelError === "string") {
    return `Failed: ${topLevelError}`;
  }

  if (!liveSearch || Object.keys(liveSearch).length === 0) {
    const sources = plan.live_search_sources.length
      ? plan.live_search_sources.join(", ")
      : "all sources";
    return `Searched ${sources} for "${topic}".`;
  }

  const parts: string[] = [];
  for (const [name, info] of Object.entries(liveSearch)) {
    if (info?.error) {
      parts.push(`${name}: ${info.error}`);
    } else {
      const c = info?.count ?? 0;
      parts.push(`${name}: ${c} item${c === 1 ? "" : "s"}`);
    }
  }
  return `Searched for "${topic}" — ${parts.join(", ")}.`;
}

function describeExactQuery(plan: QueryPlan, sqlResult: SqlResult | null): ExactQuery | null {
  const sqlText = sqlResult?.sql || plan.sql_freeform || null;
  const vectorQuery = plan.rag_query || plan.original_query;

  if (plan.needs_sql && plan.needs_rag) {
    return {
      kind: "combined",
      sqlText: sqlText ? sqlText.trim() : null,
      vectorQuery,
      corpusFilter: plan.rag_corpus_filter,
    };
  }
  if (plan.needs_sql && sqlText) {
    return { kind: "sql", text: sqlText.trim() };
  }
  if (plan.needs_rag) {
    return {
      kind: "vector",
      query: vectorQuery,
      corpusFilter: plan.rag_corpus_filter,
    };
  }
  return null;
}
