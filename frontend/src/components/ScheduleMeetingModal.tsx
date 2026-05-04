"use client";

import { useCallback, useEffect, useReducer, useState } from "react";
import type { CandidateCard, CalSlot } from "../lib/chat-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ScheduleMeetingModalProps {
  candidate: CandidateCard | null;
  onClose: () => void;
  onSent?: (resendId: string, slotsSent: number) => void;
}

// ── Slots fetch state machine ───────────────────────────────────────────────

type SlotsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "loaded"; slots: CalSlot[] }
  | { status: "error"; message: string };

type SlotsAction =
  | { type: "FETCH_START" }
  | { type: "FETCH_DONE"; slots: CalSlot[] }
  | { type: "FETCH_ERROR"; message: string };

function slotsReducer(_: SlotsState, action: SlotsAction): SlotsState {
  switch (action.type) {
    case "FETCH_START":
      return { status: "loading" };
    case "FETCH_DONE":
      return { status: "loaded", slots: action.slots };
    case "FETCH_ERROR":
      return { status: "error", message: action.message };
  }
}

// Group slots by date label (e.g. "Mon, May 4")
function groupSlotsByDate(slots: CalSlot[]): { label: string; slots: CalSlot[] }[] {
  const map = new Map<string, CalSlot[]>();
  for (const s of slots) {
    const dt = new Date(s.start);
    const label = dt.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
    if (!map.has(label)) map.set(label, []);
    map.get(label)!.push(s);
  }
  return Array.from(map.entries()).map(([label, slotList]) => ({ label, slots: slotList }));
}

// ── Component ────────────────────────────────────────────────────────────────

export default function ScheduleMeetingModal({
  candidate,
  onClose,
  onSent,
}: ScheduleMeetingModalProps) {
  const [slotsState, dispatch] = useReducer(slotsReducer, { status: "idle" });
  const [sending, setSending] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [message, setMessage] = useState("");
  const [sendError, setSendError] = useState<string | null>(null);

  // Fetch slots when candidate becomes non-null
  useEffect(() => {
    if (!candidate) return;
    dispatch({ type: "FETCH_START" });
    fetch(`${API_BASE}/scheduling/slots?days=14`)
      .then(async (res) => {
        if (!res.ok) {
          const errText = await res.text();
          throw new Error(`Slot fetch failed (${res.status}): ${errText}`);
        }
        return res.json() as Promise<{ slots: CalSlot[] }>;
      })
      .then((data) => {
        dispatch({ type: "FETCH_DONE", slots: data.slots ?? [] });
      })
      .catch((err) => {
        dispatch({
          type: "FETCH_ERROR",
          message: err instanceof Error ? err.message : String(err),
        });
      });
  }, [candidate]);

  const toggleSlot = useCallback((idx: number) => {
    setSelected((prev) => {
      if (prev.has(idx)) {
        const next = new Set(prev);
        next.delete(idx);
        return next;
      }
      if (prev.size >= 3) return prev;
      const next = new Set(prev);
      next.add(idx);
      return next;
    });
  }, []);

  const handleSend = useCallback(async () => {
    if (!candidate) {
      setSendError("No candidate selected");
      return;
    }
    if (selected.size === 0) {
      setSendError("Please select at least one time slot");
      return;
    }
    setSending(true);
    setSendError(null);
    try {
      // Resolve slots from current state snapshot to avoid stale-ref issues
      const slotsSnap = slotsState.status === "loaded" ? slotsState.slots : [];
      if (slotsSnap.length === 0) {
        throw new Error("No available slots loaded — refresh and try again");
      }
      const chosenSlots = Array.from(selected)
        .sort((a, b) => a - b)
        .filter((i) => i < slotsSnap.length)
        .map((i) => ({
          start: slotsSnap[i].start,
          end: slotsSnap[i].end,
          booking_url: slotsSnap[i].booking_url,
        }));
      if (chosenSlots.length === 0) {
        throw new Error("Selected slots are out of range — refresh and try again");
      }
      const res = await fetch(`${API_BASE}/candidates/${candidate.id}/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slots: chosenSlots,
          message: message.trim() || null,
        }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Schedule failed (${res.status}): ${errText}`);
      }
      const data = await res.json();
      onSent?.(data.resend_id, data.slots_sent);
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setSendError(msg);
    } finally {
      setSending(false);
    }
  }, [candidate, selected, slotsState, message, onSent, onClose]);

  if (!candidate) return null;

  const grouped =
    slotsState.status === "loaded" ? groupSlotsByDate(slotsState.slots) : [];

  return (
    <div className="modal-backdrop" style={{ justifyContent: "center" }}>
      <div className="bg-[var(--paper)] rounded-[var(--r-lg)] shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col" style={{ borderRadius: "var(--r-lg)" }}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: "1px solid var(--line)" }}>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "var(--ink)", margin: 0 }}>
              Schedule Meeting
            </h2>
            <p style={{ fontSize: "13px", color: "var(--text-soft)", marginTop: "4px" }}>
              {candidate.name || "Candidate"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost"
            style={{ fontSize: "18px", padding: "4px 8px", lineHeight: 1 }}
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {slotsState.status === "loading" && (
            <div className="text-gray-400 text-sm text-center py-8">
              Loading available slots…
            </div>
          )}

          {slotsState.status === "error" && (
            <div className="text-red-600 text-sm py-4">{slotsState.message}</div>
          )}

          {slotsState.status === "loaded" && grouped.length === 0 && (
            <div className="text-gray-400 text-sm text-center py-8">
              No available slots in the next 14 days.
            </div>
          )}

          {slotsState.status === "loaded" &&
            grouped.map((group) => (
              <div key={group.label} className="mb-4">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  {group.label}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {group.slots.map((slot) => {
                    const globalIdx = slotsState.slots.indexOf(slot);
                    const isSelected = selected.has(globalIdx);
                    const startTime = new Date(slot.start).toLocaleTimeString(
                      "en-US",
                      { hour: "2-digit", minute: "2-digit" }
                    );
                    const endTime = new Date(slot.end).toLocaleTimeString(
                      "en-US",
                      { hour: "2-digit", minute: "2-digit" }
                    );
                    return (
                      <button
                        key={globalIdx}
                        type="button"
                        onClick={() => toggleSlot(globalIdx)}
                        disabled={!isSelected && selected.size >= 3}
                        className="row-btn"
                        style={{
                          fontSize: "11.5px",
                          ...(isSelected
                            ? { background: "var(--ink)", color: "#fff", borderColor: "var(--ink)" }
                            : {}),
                        }}
                      >
                        {startTime}&ndash;{endTime}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}

          {/* Selection count */}
          {slotsState.status === "loaded" && (
            <p className="text-xs text-gray-400 mt-2">
              {selected.size} / 3 selected
            </p>
          )}

          {/* Custom message */}
          {slotsState.status === "loaded" && (
            <div className="mt-4">
              <label
                htmlFor="sched-message"
                className="block text-xs font-medium text-gray-500 mb-1"
              >
                Optional message from the recruiter
              </label>
              <textarea
                id="sched-message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={2}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="e.g. Looking forward to meeting you!"
              />
            </div>
          )}

          {sendError && (
            <div className="text-red-600 text-sm mt-3">{sendError}</div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4" style={{ borderTop: "1px solid var(--line)", display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <button
            type="button"
            onClick={onClose}
            className="btn btn-ghost"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => void handleSend()}
            disabled={selected.size === 0 || sending || slotsState.status !== "loaded"}
            className="btn btn-primary"
          >
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
