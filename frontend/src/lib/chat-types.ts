// Shared types for the chat tab's request/response envelope.
// Mirrors the backend dataclasses in s1_query_planner.py and chat.py.

export interface QueryPlan {
  original_query: string;

  needs_sql: boolean;
  sql_template_id: string | null;
  sql_template_params: Record<string, unknown> | null;
  sql_freeform: string | null;

  needs_rag: boolean;
  rag_query: string | null;
  rag_corpus_filter: string | null;

  // B-aug: live-search augmentation. When needs_live_search is true the chat
  // route fetches from the listed sources, persists into corpus_chunks (with
  // ignore_duplicates so migration 007 holds), then re-retrieves via S2.
  needs_live_search: boolean;
  live_search_sources: string[];           // subset of {"tavily","news","adzuna"}
  live_search_topic: string | null;

  explanation: string;
  confidence: number;
  fallback_reason: string | null;
}

// Per-source summary of the live-search round-trip the chat route ran.
// Keyed by source name; { count: items returned, error: failure message | null }.
export type LiveSearchPayload = Record<
  string,
  { count?: number; error?: string | null }
>;

export interface SqlResult {
  template_id: string | null;
  sql: string;
  row_count: number;
  rows: Record<string, unknown>[];
  error: string | null;
  // B-evidence: companion non-aggregated source rows that produced the
  // aggregate above. Optional — only validated templates with a build_evidence
  // hook return these. Renders as the "Source records" expandable section.
  evidence_sql?: string | null;
  evidence_rows?: Record<string, unknown>[];
  evidence_row_count?: number;
  evidence_error?: string | null;
}

export interface RagChunk {
  chunk_id: string;
  corpus_name: string;
  chunk_text: string;
  similarity: number | null;
  metadata: Record<string, unknown> | null;
}

export interface ChatResponse {
  reply: string;
  plan: QueryPlan | null;
  sql_result: SqlResult | null;
  rag_chunks: RagChunk[] | null;
  live_search?: LiveSearchPayload | null;
  sources: string[];
}

// A normalized citation as the UI sees it. Combines RAG chunks and SQL rows
// into a single render-ready list keyed by index ([1], [2], ...).
export type CitationKind = "rag" | "sql_template" | "sql_freeform";

export interface Citation {
  index: number;                    // 1-based for [1] [2] in chips
  kind: CitationKind;
  shortLabel: string;               // e.g. "Knowledge: kaizen_case_studies", "Validated SQL: time_to_fill"
  // Per-kind payload — exactly one is set.
  ragChunk?: RagChunk;
  sqlResult?: SqlResult;
}

// Map a backend ChatResponse into a flat list of citations the UI can iterate.
// Friendly labels follow the "natural language first, jargon in brackets" rule.
export function buildCitations(response: ChatResponse): Citation[] {
  const out: Citation[] = [];
  let idx = 1;

  if (response.sql_result && !response.sql_result.error && response.sql_result.row_count > 0) {
    if (response.sql_result.template_id) {
      out.push({
        index: idx++,
        kind: "sql_template",
        shortLabel: `Validated SQL (${response.sql_result.template_id})`,
        sqlResult: response.sql_result,
      });
    } else {
      out.push({
        index: idx++,
        kind: "sql_freeform",
        shortLabel: "Freeform SELECT",
        sqlResult: response.sql_result,
      });
    }
  }

  for (const chunk of response.rag_chunks ?? []) {
    out.push({
      index: idx++,
      kind: "rag",
      shortLabel: `Knowledge (${chunk.corpus_name})`,
      ragChunk: chunk,
    });
  }

  return out;
}

// Friendly label for a planner route, used in the Query Transformation Card.
export function planRouteSummary(plan: QueryPlan): string[] {
  const lines: string[] = [];
  if (plan.needs_sql) {
    if (plan.sql_template_id) {
      const params = plan.sql_template_params
        ? Object.entries(plan.sql_template_params)
            .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
            .join(", ")
        : "";
      lines.push(`Validated SQL template: ${plan.sql_template_id}${params ? ` (${params})` : ""}`);
    } else if (plan.sql_freeform) {
      lines.push("Freeform SQL SELECT");
    }
  }
  if (plan.needs_rag) {
    const corpus = plan.rag_corpus_filter ? ` (${plan.rag_corpus_filter})` : "";
    lines.push(`Vector retrieval${corpus}`);
  }
  if (plan.needs_live_search) {
    const srcs = plan.live_search_sources.length
      ? plan.live_search_sources.join(", ")
      : "all sources";
    lines.push(`Live web search [${srcs}]`);
  }
  if (lines.length === 0) {
    lines.push("No retrieval path picked");
  }
  return lines;
}
