import Link from "next/link";

// Sprint A2: Chat tab skeleton. Real Query Planner + Citation Drawer + Knowledge
// Sources panel land in Sprint B.

export default function ChatPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Chat</h1>
        <p className="text-gray-600 max-w-2xl">
          Ask AutoCI a question. The Query Planner decides whether to hit
          structured SQL templates, freeform <code>SELECT</code>, or vector
          retrieval, and shows you the decision before the answer arrives.
          Every claim links back to its source.
        </p>
      </header>

      <section className="bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        <div className="text-center text-gray-500 max-w-md mx-auto">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            Sprint B in progress
          </h2>
          <p className="text-sm leading-relaxed mb-6">
            The Query Planner (rebuilt S1), Citation Drawer, and Knowledge
            Sources Panel ship here next. Until then, the working chat lives on
            the legacy dashboard.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Open legacy dashboard
          </Link>
        </div>
      </section>

      <section className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <FeatureStub
          title="Query Transformation Card"
          description="Above every answer: how the prompt was interpreted, which template was matched, what params were extracted."
        />
        <FeatureStub
          title="Citation Drawer"
          description="Click any [1] or [2] chip to see the full source — chunk text, posting, article, or SQL plus rows."
        />
        <FeatureStub
          title="Knowledge Sources Panel"
          description="Inventory of every corpus and queryable table with row counts and samples."
        />
      </section>
    </div>
  );
}

function FeatureStub({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="font-semibold text-gray-800 text-sm mb-1">{title}</h3>
      <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
    </div>
  );
}
