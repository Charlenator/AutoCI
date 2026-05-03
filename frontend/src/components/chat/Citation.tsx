"use client";

import type { Citation as CitationType } from "../../lib/chat-types";

interface CitationProps {
  citation: CitationType;
}

// Renders the full body of a single citation inside the drawer. Branches by
// kind — RAG chunk, validated SQL template, freeform SELECT — and uses simple
// labelled blocks. Keep it dumb; design sprint will repaint.
export default function Citation({ citation }: CitationProps) {
  return (
    <article className="bg-white border border-gray-200 rounded-md p-4">
      <header className="flex items-baseline justify-between mb-3 pb-2 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-800">
          [{citation.index}] {citation.shortLabel}
        </h3>
      </header>
      {citation.kind === "rag" && citation.ragChunk && (
        <RagChunkBody chunk={citation.ragChunk} />
      )}
      {(citation.kind === "sql_template" || citation.kind === "sql_freeform") && citation.sqlResult && (
        <SqlResultBody sqlResult={citation.sqlResult} />
      )}
    </article>
  );
}

function RagChunkBody({ chunk }: { chunk: NonNullable<CitationType["ragChunk"]> }) {
  return (
    <div className="space-y-2 text-sm">
      <Field label="Corpus" value={chunk.corpus_name} />
      {chunk.similarity != null && (
        <Field label="Similarity" value={chunk.similarity.toFixed(3)} />
      )}
      <div>
        <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
          Chunk text
        </div>
        <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
          {chunk.chunk_text}
        </p>
      </div>
      {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
        <details className="text-xs text-gray-500">
          <summary className="cursor-pointer hover:text-gray-700">Metadata</summary>
          <pre className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 overflow-x-auto">
            {JSON.stringify(chunk.metadata, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function SqlResultBody({ sqlResult }: { sqlResult: NonNullable<CitationType["sqlResult"]> }) {
  const rows = sqlResult.rows ?? [];
  const columnKeys = rows.length > 0 ? Object.keys(rows[0]) : [];
  return (
    <div className="space-y-3 text-sm">
      {sqlResult.template_id && (
        <Field label="Template" value={sqlResult.template_id} />
      )}
      <Field label="Rows returned" value={String(sqlResult.row_count)} />
      <details>
        <summary className="cursor-pointer text-xs uppercase tracking-wide text-gray-500 hover:text-gray-700">
          SQL
        </summary>
        <pre className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 overflow-x-auto text-xs text-gray-800 whitespace-pre-wrap">
          {sqlResult.sql.trim()}
        </pre>
      </details>
      {rows.length > 0 && (
        <div>
          <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
            Result rows
          </div>
          <div className="overflow-x-auto">
            <table className="text-xs w-full border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {columnKeys.map((k) => (
                    <th
                      key={k}
                      className="text-left font-semibold text-gray-600 px-2 py-1.5"
                    >
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 20).map((row, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    {columnKeys.map((k) => (
                      <td key={k} className="px-2 py-1.5 text-gray-800 align-top">
                        {formatCell(row[k])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length > 20 && (
              <p className="text-xs text-gray-500 mt-1">
                Showing first 20 of {rows.length} rows.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-xs uppercase tracking-wide text-gray-500 min-w-[70px]">
        {label}
      </span>
      <span className="text-sm text-gray-800">{value}</span>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
