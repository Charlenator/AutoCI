"use client";

import { useCallback, useMemo, useState } from "react";
import type { CandidateCard } from "../lib/chat-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type SortKey = "name" | "match_score" | "skills" | "flags";
type SortDir = "asc" | "desc";

interface CandidateTableProps {
  rows: CandidateCard[];
  onSchedule: (card: CandidateCard) => void;
}

function initials(name: string | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return parts[0][0].toUpperCase();
}

export default function CandidateTable({ rows, onSchedule }: CandidateTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("match_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleSort = useCallback(
    (key: SortKey) => {
      if (key === sortKey) {
        setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
    },
    [sortKey],
  );

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "name":
          cmp = (a.name ?? "").localeCompare(b.name ?? "");
          break;
        case "match_score":
          cmp = a.match_score - b.match_score;
          break;
        case "skills":
          cmp = a.skills.length - b.skills.length;
          break;
        case "flags": {
          const aFlags = (a.is_duplicate ? 1 : 0) + a.missing_fields.length + (a.confidential ? 1 : 0);
          const bFlags = (b.is_duplicate ? 1 : 0) + b.missing_fields.length + (b.confidential ? 1 : 0);
          cmp = aFlags - bFlags;
          break;
        }
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const sortIndicator = (key: SortKey) => {
    if (key !== sortKey) return "";
    return sortDir === "asc" ? " ▲" : " ▼";
  };

  if (rows.length === 0) return null;

  return (
    <table className="cand-table">
      <thead>
        <tr>
          <th onClick={() => toggleSort("name")} style={{ cursor: "pointer", userSelect: "none" }}>
            Candidate{sortIndicator("name")}
          </th>
          <th onClick={() => toggleSort("skills")} style={{ cursor: "pointer", userSelect: "none" }}>
            Skills{sortIndicator("skills")}
          </th>
          <th onClick={() => toggleSort("match_score")} style={{ cursor: "pointer", userSelect: "none", width: 130 }}>
            Match{sortIndicator("match_score")}
          </th>
          <th onClick={() => toggleSort("flags")} style={{ cursor: "pointer", userSelect: "none", width: 140 }}>
            Flags{sortIndicator("flags")}
          </th>
          <th style={{ width: 100 }}>CV</th>
          <th style={{ width: 160 }}>Actions</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((row) => (
          <CandidateRow key={row.id} row={row} onSchedule={onSchedule} />
        ))}
      </tbody>
    </table>
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

  const handleDownloadCv = useCallback(async () => {
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
  }, [row]);

  // Skills: show up to 3 rows (max ~15 skills with compact tags)
  const maxDisplayed = 15;
  const displayed = row.skills.slice(0, maxDisplayed);
  const extraCount = row.skills.length - maxDisplayed;

  return (
    <tr>
      {/* Candidate */}
      <td>
        <div className="cand-name">
          <div className="cand-avatar">{initials(row.name)}</div>
          <div>
            <div>{row.name || "—"}</div>
            <div className="cand-sub">
              {row.email}
              {row.phone && <> · {row.phone}</>}
            </div>
          </div>
        </div>
      </td>

      {/* Skills — tightly grouped, up to 3 rows */}
      <td>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "3px",
            maxHeight: "68px", // ~3 rows of compact tags
            overflow: "hidden",
          }}
        >
          {displayed.map((skill) => (
            <span key={skill} className="tag">
              {skill}
            </span>
          ))}
          {extraCount > 0 && (
            <span
              style={{
                fontSize: "10.5px",
                color: "var(--muted)",
                fontFamily: "var(--font-mono)",
                padding: "1px 5px",
              }}
            >
              +{extraCount}
            </span>
          )}
        </div>
      </td>

      {/* Match — rendered as percentage */}
      <td>
        <div className="score">
          <span>{(row.match_score * 100).toFixed(0)}%</span>
          <div className="score-bar">
            <i style={{ width: `${Math.min(row.match_score * 100, 100)}%` }} />
          </div>
        </div>
      </td>

      {/* Flags */}
      <td>
        <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
          {row.is_duplicate && <span className="flag">Duplicate</span>}
          {row.missing_fields.length > 0 && (
            <span className="flag">
              {row.missing_fields.length} missing
            </span>
          )}
          {row.confidential && <span className="flag ok">Confidential</span>}
          {!row.is_duplicate && row.missing_fields.length === 0 && !row.confidential && (
            <span className="flag ok" style={{ color: "var(--muted)" }}>
              OK
            </span>
          )}
        </div>
      </td>

      {/* CV */}
      <td>
        <button
          type="button"
          onClick={() => void handleDownloadCv()}
          disabled={!row.cv_storage_path || cvLoading}
          className="row-btn"
          style={{ fontSize: "11.5px" }}
        >
          {cvLoading ? "Loading…" : "Download"}
        </button>
        {cvError && (
          <span
            style={{
              display: "block",
              color: "var(--accent)",
              fontSize: "10.5px",
              marginTop: "2px",
              fontFamily: "var(--font-mono)",
            }}
          >
            {cvError}
          </span>
        )}
      </td>

      {/* Actions */}
      <td>
        <div className="row-actions">
          <button
            type="button"
            onClick={() => onSchedule(row)}
            className="row-btn primary"
          >
            Schedule Meeting
          </button>
        </div>
      </td>
    </tr>
  );
}
