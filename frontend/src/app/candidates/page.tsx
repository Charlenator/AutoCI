"use client";

import { useCallback, useState } from "react";
import type { CandidateCard, CandidatesSearchResponse } from "../../lib/chat-types";
import CandidateTable from "../../components/CandidateTable";
import ScheduleMeetingModal from "../../components/ScheduleMeetingModal";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CandidatesPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CandidateCard[] | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schedulingFor, setSchedulingFor] = useState<CandidateCard | null>(null);

  const doSearch = useCallback(async () => {
    const q = query.trim();
    if (!q || pending) return;
    setPending(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/candidates/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q, limit: 20 }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Search failed (${res.status}): ${errText}`);
      }
      const data: CandidatesSearchResponse = await res.json();
      setResults(data.results ?? []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setResults([]);
    } finally {
      setPending(false);
    }
  }, [query, pending]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      void doSearch();
    }
  };

  const handleSent = () => {
    setSchedulingFor(null);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Candidate Search</h1>
        <p className="text-sm text-gray-500 mt-1">
          Semantic search over CVs ingested via the inbound email pipeline.
        </p>
      </header>

      {/* Search bar */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Search by skill, role, or keyword..."
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={pending}
        />
        <button
          type="button"
          onClick={() => void doSearch()}
          disabled={pending || !query.trim()}
          className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {pending ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Error state */}
      {error && (
        <p className="text-red-600 text-sm mb-4">{error}</p>
      )}

      {/* Pending */}
      {pending && !results && (
        <div className="text-gray-400 text-sm py-8 text-center">Searching…</div>
      )}

      {/* Empty state — never searched */}
      {!pending && results === null && (
        <div className="text-gray-400 text-sm py-8 text-center">
          Type a query above and press Enter to search.
        </div>
      )}

      {/* Results */}
      {results !== null && !pending && results.length === 0 && !error && (
        <div className="text-gray-400 text-sm py-8 text-center">
          No candidates found. Try a different query.
        </div>
      )}

      {results !== null && results.length > 0 && (
        <CandidateTable rows={results} onSchedule={(card) => setSchedulingFor(card)} />
      )}

      {/* Schedule Meeting Modal */}
      {schedulingFor && (
        <ScheduleMeetingModal
          candidate={schedulingFor}
          onClose={() => setSchedulingFor(null)}
          onSent={handleSent}
        />
      )}
    </div>
  );
}
