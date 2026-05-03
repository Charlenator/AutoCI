"use client";

import { useState } from "react";
import type { QueryPlan, SqlResult } from "../../lib/chat-types";

interface QueryTransformationCardProps {
  plan: QueryPlan;
  sqlResult: SqlResult | null;
  ragChunkCount: number;
}

// Collapsed by default — most users want the answer, not the methodology.
// When expanded, three blocks: Your query / What we ran / Exact query.
// Closes the brief's "query transformation visibility" requirement; tucked away
// so the natural-language answer stays front-and-centre for end users.
export default function QueryTransformationCard({
  plan,
  sqlResult,
  ragChunkCount,
}: QueryTransformationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const route = describeRoute(plan, sqlResult, ragChunkCount);
  const exactQuery = describeExactQuery(plan, sqlResult);

  return (
    <section className="border border-blue-100 rounded-md bg-blue-50">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-left text-xs hover:bg-blue-100 rounded-md"
        aria-expanded={expanded}
      >
        <span className="flex items-center gap-2">
          <span className="uppercase tracking-wide font-semibold text-blue-700">
            How this was answered
          </span>
          <span className="text-blue-700/80 font-normal">{route.shortLabel}</span>
        </span>
        <span className="flex items-center gap-3 text-blue-700/80 tabular-nums">
          <span>confidence {plan.confidence.toFixed(2)}</span>
          <span aria-hidden>{expanded ? "−" : "+"}</span>
        </span>
      </button>

      {expanded && (
        <div className="border-t border-blue-100 px-3 py-3 space-y-3">
          <Block label="Your query">
            <p className="text-sm text-gray-800 whitespace-pre-wrap">
              {plan.original_query}
            </p>
          </Block>

          <Block label="What we ran">
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className="inline-block px-2 py-0.5 text-xs font-semibold rounded bg-blue-700 text-white">
                {route.kindLabel}
              </span>
              <span className="text-sm text-gray-800">{route.detailLabel}</span>
            </div>
            {plan.explanation && (
              <p className="mt-1 text-xs text-gray-600">{plan.explanation}</p>
            )}
            {plan.fallback_reason && (
              <p className="mt-1 text-xs text-amber-700">
                Fallback: {plan.fallback_reason}
              </p>
            )}
          </Block>

          {exactQuery && (
            <Block label="Exact query">
              {exactQuery.kind === "sql" && (
                <pre className="text-xs bg-white border border-gray-200 rounded p-2 overflow-x-auto whitespace-pre-wrap text-gray-800">
                  {exactQuery.text}
                </pre>
              )}
              {exactQuery.kind === "vector" && (
                <div className="text-xs bg-white border border-gray-200 rounded p-2 space-y-1">
                  <KV k="Embedded query" v={exactQuery.query} />
                  {exactQuery.corpusFilter && (
                    <KV k="Corpus filter" v={exactQuery.corpusFilter} />
                  )}
                </div>
              )}
              {exactQuery.kind === "combined" && (
                <div className="space-y-2">
                  {exactQuery.sqlText && (
                    <div>
                      <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">SQL</p>
                      <pre className="text-xs bg-white border border-gray-200 rounded p-2 overflow-x-auto whitespace-pre-wrap text-gray-800">
                        {exactQuery.sqlText}
                      </pre>
                    </div>
                  )}
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Vector retrieval</p>
                    <div className="text-xs bg-white border border-gray-200 rounded p-2 space-y-1">
                      <KV k="Embedded query" v={exactQuery.vectorQuery} />
                      {exactQuery.corpusFilter && (
                        <KV k="Corpus filter" v={exactQuery.corpusFilter} />
                      )}
                    </div>
                  </div>
                </div>
              )}
            </Block>
          )}
        </div>
      )}
    </section>
  );
}

function Block({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.08em] text-blue-800 font-semibold mb-1">
        {label}
      </div>
      {children}
    </div>
  );
}

function KV({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-gray-500 min-w-[110px]">{k}</span>
      <span className="text-gray-800 break-words">{v}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Routing label helpers
// ---------------------------------------------------------------------------

interface RouteDescription {
  kindLabel: string;          // big chip label
  shortLabel: string;          // collapsed-row tail
  detailLabel: string;         // longer explainer line
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
