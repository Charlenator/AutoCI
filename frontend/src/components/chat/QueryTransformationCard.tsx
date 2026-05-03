"use client";

import { planRouteSummary, type QueryPlan } from "../../lib/chat-types";

interface QueryTransformationCardProps {
  plan: QueryPlan;
}

// Renders the planner's decision above the assistant's reply so the user can
// see how their question was interpreted before reading the answer.
// Closes the brief's "query transformation visibility" requirement.
export default function QueryTransformationCard({ plan }: QueryTransformationCardProps) {
  const routes = planRouteSummary(plan);
  return (
    <section className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
      <header className="flex items-baseline justify-between mb-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-blue-700">
          How I read your question
        </h3>
        <span className="text-xs text-blue-700 tabular-nums">
          confidence {plan.confidence.toFixed(2)}
        </span>
      </header>
      {plan.explanation && (
        <p className="text-sm text-gray-800 mb-2">{plan.explanation}</p>
      )}
      <dl className="grid grid-cols-[120px_1fr] gap-x-3 gap-y-1 text-xs">
        <dt className="text-gray-500 uppercase tracking-wide">Original query</dt>
        <dd className="text-gray-800">{plan.original_query}</dd>
        <dt className="text-gray-500 uppercase tracking-wide">Routes</dt>
        <dd className="text-gray-800">
          <ul className="space-y-0.5">
            {routes.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </dd>
        {plan.fallback_reason && (
          <>
            <dt className="text-gray-500 uppercase tracking-wide">Fallback</dt>
            <dd className="text-amber-700">{plan.fallback_reason}</dd>
          </>
        )}
      </dl>
    </section>
  );
}
