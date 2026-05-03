import Link from "next/link";

// Sprint A2: Continuous Improvement Suite tab skeleton. Real K_SCOPING +
// K_TOOL_SELECTOR + dynamic orchestrator + interventions table + FMEA land
// in Sprint C.

export default function CISPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <span>🛠️</span>
          <span>Continuous Improvement Suite</span>
        </h1>
        <p className="text-gray-600 max-w-2xl">
          Conversational scoping → tool selection → execution. The agent picks
          the right Six Sigma tools for the job — Five Whys, Ishikawa, FMEA,
          Impact/Effort — instead of running every DMAIC phase by default.
        </p>
      </header>

      <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        <div className="text-center text-gray-500 max-w-md mx-auto">
          <div className="text-5xl mb-4">🚧</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            Sprint C in progress
          </h2>
          <p className="text-sm leading-relaxed mb-6">
            The K_SCOPING chat loop + K_TOOL_SELECTOR + dynamic orchestrator
            replace the current fixed DMAIC pipeline. Until then, the working
            Kaizen flow lives on the legacy dashboard.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <span>📊</span>
            <span>Open legacy dashboard</span>
          </Link>
        </div>
      </section>

      <section className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <FeatureStub
          icon="💬"
          title="Scoping conversation"
          description="K_SCOPING agent asks clarifying questions until the problem, target, and success criteria are clear."
        />
        <FeatureStub
          icon="🧰"
          title="Right-tool-for-the-job"
          description="K_TOOL_SELECTOR picks from D1-D3 / K1-K7 / FMEA / Impact-Effort based on the charter."
        />
        <FeatureStub
          icon="📋"
          title="Interventions table"
          description="Replaces Kanban. Each row links back to the K4/K5 root cause that justifies it."
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
