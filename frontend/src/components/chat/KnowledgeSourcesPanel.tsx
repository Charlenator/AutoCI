"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CorpusEntry {
  name: string;
  description: string;
  chunk_count: number;
  confidential_count: number;
  embedded_count: number;
  samples: { chunk_id: string; chunk_text: string; metadata: Record<string, unknown> | null }[];
}

interface TableEntry {
  name: string;
  description: string;
  row_count: number;
  columns: { column_name: string; data_type: string }[];
  samples: Record<string, unknown>[];
}

interface SourcesPayload {
  corpora: CorpusEntry[];
  tables: TableEntry[];
  summary: {
    corpora_count: number;
    tables_count: number;
    total_chunks: number;
    total_table_rows: number;
  };
  as_of: number;
}

interface KnowledgeSourcesPanelProps {
  open: boolean;
  onClose: () => void;
}

// Modal-style overlay listing every RAG corpus + queryable SQL table that
// AutoCI can answer from. Closes the brief's "≥3 structured documents
// visibility" requirement.
export default function KnowledgeSourcesPanel({ open, onClose }: KnowledgeSourcesPanelProps) {
  const [data, setData] = useState<SourcesPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || data) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/sources/`);
        if (!res.ok) throw new Error(`Sources fetch failed: ${res.status}`);
        const json = (await res.json()) as SourcesPayload;
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, data]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex items-stretch justify-end bg-black/30"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <section
        className="w-full max-w-2xl bg-white border-l border-gray-200 flex flex-col h-full"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Knowledge sources</h2>
            <p className="text-xs text-gray-500">
              Every corpus and queryable table the chat can draw from.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-800 px-2 py-1"
          >
            Close
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-6">
          {loading && (
            <p className="text-sm text-gray-500 italic">Loading inventory...</p>
          )}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md px-4 py-3 text-sm text-red-800">
              {error}
            </div>
          )}
          {data && <SummaryRow summary={data.summary} />}
          {data && (
            <Section title="Vector corpora" subtitle="Indexed in corpus_chunks (BAAI/bge-small-en-v1.5, 384-d)">
              {data.corpora.map((c) => (
                <CorpusCard key={c.name} corpus={c} />
              ))}
              {data.corpora.length === 0 && (
                <p className="text-sm text-gray-500">No corpora yet.</p>
              )}
            </Section>
          )}
          {data && (
            <Section title="Queryable SQL tables" subtitle="Available to the Query Planner via validated templates and freeform SELECT">
              {data.tables.map((t) => (
                <TableCard key={t.name} table={t} />
              ))}
            </Section>
          )}
        </div>
      </section>
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <header className="mb-3">
        <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">
          {title}
        </h3>
        <p className="text-xs text-gray-500">{subtitle}</p>
      </header>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function SummaryRow({ summary }: { summary: SourcesPayload["summary"] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <SummaryStat label="Corpora" value={summary.corpora_count} />
      <SummaryStat label="Total chunks" value={summary.total_chunks} />
      <SummaryStat label="SQL tables" value={summary.tables_count} />
      <SummaryStat label="Total rows" value={summary.total_table_rows} />
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-md px-3 py-2">
      <div className="text-xs uppercase tracking-wide text-blue-700">{label}</div>
      <div className="text-lg font-semibold text-blue-900 tabular-nums">
        {value.toLocaleString()}
      </div>
    </div>
  );
}

function CorpusCard({ corpus }: { corpus: CorpusEntry }) {
  return (
    <article className="border border-gray-200 rounded-md p-3 bg-white">
      <header className="flex items-baseline justify-between gap-3 mb-2">
        <h4 className="font-semibold text-sm text-gray-900">{corpus.name}</h4>
        <span className="text-xs text-gray-500 tabular-nums">
          {corpus.chunk_count} chunks
          {corpus.confidential_count > 0 ? ` · ${corpus.confidential_count} confidential` : ""}
          {corpus.embedded_count !== corpus.chunk_count
            ? ` · ${corpus.embedded_count} embedded`
            : ""}
        </span>
      </header>
      {corpus.description && (
        <p className="text-xs text-gray-600 mb-2">{corpus.description}</p>
      )}
      {corpus.samples.length > 0 && (
        <details className="text-xs text-gray-700">
          <summary className="cursor-pointer hover:text-gray-900">
            Sample chunks ({corpus.samples.length})
          </summary>
          <ul className="mt-2 space-y-2">
            {corpus.samples.map((s) => (
              <li
                key={s.chunk_id}
                className="border-l-2 border-blue-200 pl-3 text-xs whitespace-pre-wrap"
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
    <article className="border border-gray-200 rounded-md p-3 bg-white">
      <header className="flex items-baseline justify-between gap-3 mb-2">
        <h4 className="font-semibold text-sm text-gray-900">{table.name}</h4>
        <span className="text-xs text-gray-500 tabular-nums">
          {table.row_count.toLocaleString()} rows
        </span>
      </header>
      {table.description && (
        <p className="text-xs text-gray-600 mb-2">{table.description}</p>
      )}
      {table.columns.length > 0 && (
        <details className="text-xs text-gray-700">
          <summary className="cursor-pointer hover:text-gray-900">
            Columns ({table.columns.length})
          </summary>
          <ul className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            {table.columns.map((c) => (
              <li key={c.column_name} className="font-mono text-gray-700">
                {c.column_name}
                <span className="text-gray-400"> {c.data_type}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
      {table.samples.length > 0 && (
        <details className="text-xs text-gray-700 mt-1">
          <summary className="cursor-pointer hover:text-gray-900">
            Sample rows ({table.samples.length})
          </summary>
          <pre className="mt-2 p-2 bg-gray-50 border border-gray-200 rounded text-xs overflow-x-auto">
            {JSON.stringify(table.samples, null, 2)}
          </pre>
        </details>
      )}
    </article>
  );
}
