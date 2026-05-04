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
    <div className="cand-page">
      {/* Filters rail */}


      {/* Main column */}
      <div className="cand-main">
        <header className="cand-header">
          <h1 className="chat-title">Candidate Search</h1>
          <p className="chat-subtitle">
            Search your inbound CV pipeline using semantic matching. Enter required skills, a role title, or general keywords. The system
            retrieves, ranks, and surfaces the most relevant candidates from
            ingested CVs. 
          </p>
          <p className="chat-subtitle">
          The Schedule Meeting option will surface available calendar slots from your calendar. Select up to three slots to provide the candidate with, they will receive an email with a link to book one of the selected slots. Both of your calendars will be updated once a slot has been confirmed by both parties.  

          </p>
        </header>

        {/* Toolbar with search input */}
        <div className="cand-toolbar">
          <div className="search-input">
            <span className="ico">&#128269;</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Search by skill, role, or keyword e.g. Java Developer Cape Town..."
              disabled={pending}
            />
          </div>
          <button
            type="button"
            onClick={() => void doSearch()}
            disabled={pending || !query.trim()}
            className="btn btn-primary"
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
            Type a query above and press Enter to search. Results will show
            ranked candidates with match scores, skills, and available actions.
          </div>
        )}

        {/* Results */}
        {results !== null && !pending && results.length === 0 && !error && (
          <div className="text-gray-400 text-sm py-8 text-center">
            No candidates found. Try a different query or broaden your search
            terms.
          </div>
        )}

        {results !== null && results.length > 0 && (
          <div className="cand-table-wrap">
            <CandidateTable rows={results} onSchedule={(card) => setSchedulingFor(card)} />
          </div>
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
    </div>
  );
}
