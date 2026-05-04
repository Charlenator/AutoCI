"use client";

import { useState } from "react";
import type { CandidateCard } from "../lib/chat-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CandidateTableProps {
  rows: CandidateCard[];
  onSchedule: (card: CandidateCard) => void;
}

export default function CandidateTable({ rows, onSchedule }: CandidateTableProps) {
  if (rows.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <th className="py-3 pr-4">Candidate</th>
            <th className="py-3 pr-4">Skills</th>
            <th className="py-3 pr-4">Match</th>
            <th className="py-3 pr-4">Flags</th>
            <th className="py-3 pr-4">CV</th>
            <th className="py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((row) => (
            <CandidateRow key={row.id} row={row} onSchedule={onSchedule} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CandidateRow({
  row,
  onSchedule,
}: {
  row: CandidateCard;
  onSchedule: (card: CandidateCard) => void;
}) {
  const [cvError, setCvError] = useState<string | null>(null);
  const [cvLoading, setCvLoading] = useState(false);

  const handleDownloadCv = async () => {
    if (!row.cv_storage_path) return;
    setCvLoading(true);
    setCvError(null);
    try {
      const res = await fetch(`${API_BASE}/candidates/${row.id}/cv`);
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`CV fetch failed (${res.status}): ${errText}`);
      }
      const data = await res.json();
      window.open(data.url, "_blank");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setCvError(msg);
    } finally {
      setCvLoading(false);
    }
  };

  const skillChips = row.skills.slice(0, 5);
  const extraCount = row.skills.length - 5;

  return (
    <tr className="hover:bg-gray-50">
      {/* Candidate */}
      <td className="py-3 pr-4">
        <div className="font-medium text-gray-900">{row.name || "—"}</div>
        <div className="text-xs text-gray-400 mt-0.5">{row.email}</div>
        {row.phone && <div className="text-xs text-gray-400">{row.phone}</div>}
      </td>

      {/* Skills */}
      <td className="py-3 pr-4">
        <div className="flex flex-wrap gap-1">
          {skillChips.map((skill) => (
            <span
              key={skill}
              className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded"
            >
              {skill}
            </span>
          ))}
          {extraCount > 0 && (
            <span className="inline-block text-xs text-gray-400 px-1">
              +{extraCount} more
            </span>
          )}
        </div>
      </td>

      {/* Match */}
      <td className="py-3 pr-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 w-10">
            {Number(row.match_score).toFixed(2)}
          </span>
          <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${Math.min(Number(row.match_score) * 100, 100)}%` }}
            />
          </div>
        </div>
      </td>

      {/* Flags */}
      <td className="py-3 pr-4">
        <div className="flex flex-wrap gap-1">
          {row.is_duplicate && (
            <span className="inline-block bg-yellow-50 text-yellow-700 text-xs px-2 py-0.5 rounded border border-yellow-200">
              Duplicate
            </span>
          )}
          {row.missing_fields.length > 0 && (
            <span className="inline-block bg-orange-50 text-orange-700 text-xs px-2 py-0.5 rounded border border-orange-200">
              {row.missing_fields.length} missing
            </span>
          )}
          {row.confidential && (
            <span className="inline-block bg-purple-50 text-purple-700 text-xs px-2 py-0.5 rounded border border-purple-200">
              Confidential
            </span>
          )}
        </div>
      </td>

      {/* CV */}
      <td className="py-3 pr-4">
        <button
          type="button"
          onClick={() => void handleDownloadCv()}
          disabled={!row.cv_storage_path || cvLoading}
          className="text-blue-600 text-xs font-medium hover:underline disabled:text-gray-300 disabled:no-underline disabled:cursor-not-allowed"
        >
          {cvLoading ? "Loading…" : "Download"}
        </button>
        {cvError && (
          <span className="block text-red-600 text-xs mt-0.5">{cvError}</span>
        )}
      </td>

      {/* Actions */}
      <td className="py-3">
        <button
          type="button"
          onClick={() => onSchedule(row)}
          className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700"
        >
          Schedule Meeting
        </button>
      </td>
    </tr>
  );
}
