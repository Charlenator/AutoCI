"use client";

interface InterventionRow {
  intervention_id: string;
  title: string;
  description: string | null;
  linked_root_cause: string | null;
  impact: "high" | "medium" | "low" | null;
  effort: string | null;
  priority: number | null;
  owner: string | null;
  due_date: string | null;
  status: "proposed" | "accepted" | "in_progress" | "done" | "rejected";
}

interface InterventionsTableProps {
  rows: InterventionRow[];
}

const IMPACT_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-600",
};

const STATUS_COLORS: Record<string, string> = {
  proposed: "bg-blue-50 text-blue-700 border-blue-200",
  accepted: "bg-green-50 text-green-700 border-green-200",
  in_progress: "bg-purple-50 text-purple-700 border-purple-200",
  done: "bg-gray-50 text-gray-500 border-gray-200",
  rejected: "bg-red-50 text-red-500 border-red-200",
};

export default function InterventionsTable({ rows }: InterventionsTableProps) {
  if (rows.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-gray-400">
        No interventions proposed yet.
      </div>
    );
  }

  // Sort by priority ascending (100 = best, so sort descending for display)
  const sorted = [...rows].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <th className="py-3 pr-3 w-12">#</th>
            <th className="py-3 pr-3">Title</th>
            <th className="py-3 pr-3">Description</th>
            <th className="py-3 pr-3">Root Cause</th>
            <th className="py-3 pr-3">Impact</th>
            <th className="py-3 pr-3">Effort</th>
            <th className="py-3 pr-3">Owner</th>
            <th className="py-3 pr-3">Due</th>
            <th className="py-3">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sorted.map((row, i) => (
            <tr key={row.intervention_id} className="hover:bg-gray-50">
              <td className="py-3 pr-3 text-gray-400 font-mono text-xs">
                {i + 1}
              </td>
              <td className="py-3 pr-3 font-medium text-gray-900 max-w-[200px] truncate" title={row.title}>
                {row.title}
              </td>
              <td className="py-3 pr-3 text-gray-600 max-w-[250px] truncate" title={row.description ?? ""}>
                {row.description ?? "—"}
              </td>
              <td className="py-3 pr-3 text-gray-600 max-w-[200px] truncate text-xs" title={row.linked_root_cause ?? ""}>
                {row.linked_root_cause ?? "—"}
              </td>
              <td className="py-3 pr-3">
                {row.impact ? (
                  <span
                    className={`inline-block text-xs px-2 py-0.5 rounded font-medium ${
                      IMPACT_COLORS[row.impact] || "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {row.impact.charAt(0).toUpperCase() + row.impact.slice(1)}
                  </span>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </td>
              <td className="py-3 pr-3 font-mono text-xs text-gray-500">
                {row.effort ?? "—"}
              </td>
              <td className="py-3 pr-3 text-gray-600 text-xs">
                {row.owner ?? "—"}
              </td>
              <td className="py-3 pr-3 text-gray-600 text-xs">
                {row.due_date ? new Date(row.due_date).toLocaleDateString() : "—"}
              </td>
              <td className="py-3">
                {row.status ? (
                  <span
                    className={`inline-block text-xs px-2 py-0.5 rounded border ${
                      STATUS_COLORS[row.status] || "bg-gray-100 text-gray-600 border-gray-200"
                    }`}
                  >
                    {row.status.replace("_", " ")}
                  </span>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
