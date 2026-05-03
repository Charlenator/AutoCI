// Sprint A2: Candidate Search tab skeleton. Real semantic search + table +
// Schedule Meeting flow lands in Sprint B6-B8.

export default function CandidatesPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <span>🔍</span>
          <span>Candidate Search</span>
        </h1>
        <p className="text-gray-600 max-w-2xl">
          Recruiter-facing semantic search over CVs ingested via the inbound
          email pipeline. Sortable table with download links, missing-field
          flags, duplicate detection, and one-click meeting scheduling via
          cal.com.
        </p>
      </header>

      <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        <div className="text-center text-gray-500 max-w-md mx-auto">
          <div className="text-5xl mb-4">🚧</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            Sprint B6-B8 in progress
          </h2>
          <p className="text-sm leading-relaxed">
            Inbound CV pipeline (Edge Function + Modal worker) → Candidate
            table → Schedule Meeting flow (cal.com slot grid + Resend invite)
            land here. Migration 004 is already applied; the queue table is
            waiting for its first row.
          </p>
        </div>
      </section>

      <section className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <FeatureStub
          icon="📥"
          title="Inbound CV pipeline"
          description="Resend webhook → Edge Function → Modal worker → classify, extract, dedup, vectorize, store. .docx-only POC."
        />
        <FeatureStub
          icon="📅"
          title="Schedule meeting"
          description="14-day cal.com slot grid → recruiter ticks slots → Resend invite to candidate with deep-link buttons."
        />
      </section>
    </div>
  );
}

function FeatureStub({
  title,
  icon,
  description,
}: {
  title: string;
  icon: string;
  description: string;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-2xl mb-2">{icon}</div>
      <h3 className="font-semibold text-gray-800 text-sm mb-1">{title}</h3>
      <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
    </div>
  );
}
