"""O2: Meta-Orchestrator — Full Kaizen lifecycle manager.
Runs D1→D2→D3 detection, then K1→K2→K3(K4→K5)→K6→K7 DMAIC.
Pushes rich SSE output_delta events so the frontend can render a vertical results timeline."""

from dataclasses import dataclass
import json
from api.tools.t3_litellm_router import LiteLLMRouter
from api.tools.t1_mcp_analytics import AnalyticsLibrary
from api.agents.detection.d1_internal_benchmarking import D1InternalBenchmarkingAgent
from api.agents.detection.d2_external_benchmarking import D2ExternalBenchmarkingAgent
from api.agents.detection.d3_gap_analysis import D3GapAnalysisAgent
from api.agents.kaizen.k1_define import K1DefineAgent
from api.agents.kaizen.k2_measure import K2MeasureAgent
from api.agents.kaizen.k3_analyse_host import K3AnalyseHostAgent
from api.agents.kaizen.k6_improve import K6ImproveAgent
from api.agents.kaizen.k7_control import K7ControlAgent
from api.agents.specialists.s4_research import ResearchAgent
from api.sse import push_event, make_node_event, make_phase_event, make_output_event, make_step_event

@dataclass
class KaizenSessionResult:
    session_id: str
    phase: str
    detection: dict | None = None
    define: dict | None = None
    measure: dict | None = None
    analyse: dict | None = None
    improve: dict | None = None
    control: dict | None = None

class MetaOrchestrator:
    """Runs the full Kaizen lifecycle with rich SSE output events."""

    def __init__(self, supabase_client, llm_router: LiteLLMRouter):
        self.supabase = supabase_client
        self.llm = llm_router
        self.analytics = AnalyticsLibrary()

        self.d1 = D1InternalBenchmarkingAgent()
        self.d2 = D2ExternalBenchmarkingAgent(supabase_client)
        self.d3 = D3GapAnalysisAgent(llm_router)
        self.k1 = K1DefineAgent(llm_router)
        self.k2 = K2MeasureAgent(llm_router)
        self.k3 = K3AnalyseHostAgent(llm_router)
        self.k6 = K6ImproveAgent(llm_router)
        self.k7 = K7ControlAgent(llm_router)
        self.research = ResearchAgent(supabase_client)

    def _sse(self, session_id: str, event: dict):
        try:
            push_event(session_id, event)
        except Exception:
            pass

    def _out(self, session_id: str, phase: str, agent_id: str, content: str):
        """Shorthand for pushing an output_delta event."""
        self._sse(session_id, make_output_event(phase, content, agent_id))

    def fetch_pipeline_data(self) -> dict:
        try:
            roles = self.supabase.table("roles").select("*").execute().data or []
            candidates = self.supabase.table("candidates").select("*").execute().data or []
            pipeline_events = self.supabase.table("pipeline_events").select("*").execute().data or []
            hires = self.supabase.table("hires").select("*").execute().data or []
            offer_outcomes = self.supabase.table("offer_outcomes").select("*").execute().data or []
            benchmarks = self.supabase.table("industry_benchmarks").select("*").execute().data or []
        except Exception as e:
            print(f"Data fetch error: {e}")
            return {}
        return {
            "roles": roles, "candidates": candidates,
            "pipeline_events": pipeline_events, "hires": hires,
            "offer_outcomes": offer_outcomes, "benchmarks": benchmarks,
        }

    def run_full_kaizen(self, session_id: str, role_title: str = "Senior Java Developer") -> KaizenSessionResult:
        data = self.fetch_pipeline_data()
        if not data:
            return KaizenSessionResult(session_id=session_id, phase="error")

        # ── DETECTION PHASE ──────────────────────────────────────────
        self._sse(session_id, make_phase_event("detection", "start"))
        self._sse(session_id, make_node_event("D1", "active", "Internal Benchmarking"))
        self._out(session_id, "detection", "D1", "📊 Computing pipeline metrics...")

        internal_result = self.d1.run(
            data["pipeline_events"], data["hires"],
            data["candidates"], data["offer_outcomes"],
        )
        internal = internal_result[0] if isinstance(internal_result, tuple) else internal_result
        self._sse(session_id, make_node_event("D1", "complete"))

        # Rich D1 output
        self._out(session_id, "detection", "D1", f"**Time to Fill**: {internal.time_to_fill_days} days")
        for stage, rate in getattr(internal, "stage_conversions", {}).items():
            self._out(session_id, "detection", "D1", f"**{stage}** conversion: {rate:.1%}")
        if internal.source_yields:
            sources_str = ", ".join(f"{k}: {v:.1%}" for k, v in internal.source_yields.items())
            self._out(session_id, "detection", "D1", f"**Source Yields**: {sources_str}")
        self._out(session_id, "detection", "D1", f"**Offer Acceptance Rate**: {internal.offer_acceptance_rate:.1%}")

        # ── LIVE MARKET RESEARCH (S4) — per-API granular events ──────
        self._sse(session_id, make_node_event("S4", "active", "Market Research"))
        self._sse(session_id, make_step_event("S4", "🌐 Tavily web search...", 1, 4))
        self._out(session_id, "detection", "S4", "🌐 Searching Tavily for web intel...")
        tavily_results = []
        try:
            tavily_results = self.research.search_tavily(f"{role_title} hiring trends South Africa")
        except Exception as e:
            self._out(session_id, "detection", "S4", f"⚠️ Tavily error: {e}")
        self._sse(session_id, make_step_event("S4", "✅ Tavily complete", 1, 4))
        for r in tavily_results:
            if r.get("error"):
                self._out(session_id, "detection", "S4", f"⚠️ Tavily: {r['error']}")
            else:
                self._out(session_id, "detection", "S4", f"🌐 **{r['title']}**")
                self._out(session_id, "detection", "S4", f"   {r['content'][:120]}...")

        self._sse(session_id, make_step_event("S4", "📰 NewsAPI search...", 2, 4))
        self._out(session_id, "detection", "S4", "📰 Searching NewsAPI for articles...")
        news_results = []
        try:
            news_results = self.research.search_news(f"{role_title} hiring South Africa")
        except Exception as e:
            self._out(session_id, "detection", "S4", f"⚠️ NewsAPI error: {e}")
        self._sse(session_id, make_step_event("S4", "✅ NewsAPI complete", 2, 4))
        for r in news_results:
            if r.get("error"):
                self._out(session_id, "detection", "S4", f"⚠️ NewsAPI: {r['error']}")
            else:
                self._out(session_id, "detection", "S4",
                          f"📰 **{r['title']}** ({r.get('publishedAt', '')[:10]})")

        self._sse(session_id, make_step_event("S4", "💼 Adzuna job search...", 3, 4))
        self._out(session_id, "detection", "S4", "💼 Searching Adzuna for live job postings...")
        adzuna_results = []
        try:
            adzuna_results = self.research.search_adzuna(role_title)
        except Exception as e:
            self._out(session_id, "detection", "S4", f"⚠️ Adzuna error: {e}")
        self._sse(session_id, make_step_event("S4", "✅ Adzuna complete", 3, 4))
        adzuna_salaries = []
        for r in adzuna_results:
            if r.get("error"):
                self._out(session_id, "detection", "S4", f"⚠️ Adzuna: {r['error']}")
            else:
                salary_range = ""
                if r.get("salary_min") or r.get("salary_max"):
                    salary_range = f" ({r.get('salary_min') or '?'} - {r.get('salary_max') or '?'} ZAR)"
                self._out(session_id, "detection", "S4",
                          f"💼 **{r['title']}** @ {r.get('company', 'Unknown')}{salary_range}")
                if r.get("salary_min"):
                    adzuna_salaries.append(r["salary_min"])
                if r.get("salary_max"):
                    adzuna_salaries.append(r["salary_max"])

        if adzuna_salaries:
            numeric = [s for s in adzuna_salaries if s]
            if numeric:
                avg_salary = sum(numeric) / len(numeric)
                self._out(session_id, "detection", "S4",
                          f"📊 **Average Adzuna salary**: R{avg_salary:,.0f} across {len(adzuna_results)} postings")

        self._sse(session_id, make_step_event("S4", "💾 Persisting to RAG corpus...", 4, 4))
        self._out(session_id, "detection", "S4", f"💾 Saved to `adzuna_postings`, `corpus_chunks` (market_intel, industry_news, adzuna_postings)")
        self._sse(session_id, make_step_event("S4", "✅ Market research complete", 4, 4))
        self._sse(session_id, make_node_event("S4", "complete"))

        # Build market data dict for D3 context
        market_data = {
            "tavily_results": tavily_results,
            "news_results": news_results,
            "adzuna_results": adzuna_results,
        }

        # ── D2: EXTERNAL BENCHMARKING ────────────────────────────────
        self._sse(session_id, make_node_event("D2", "active", "External Benchmarking"))
        self._out(session_id, "detection", "D2", "🔍 Comparing against industry benchmarks...")
        external = self.d2.run(role_title, internal.time_to_fill_days)
        self._sse(session_id, make_node_event("D2", "complete"))
        for bench in (external or []):
            if isinstance(bench, dict):
                name = bench.get("role_title") or bench.get("source", "Industry")
                ttf = bench.get("time_to_fill_days", "N/A")
                delta = bench.get("delta_pct", 0)
                delta_str = f" ({delta:+.1f}% vs internal)" if delta else ""
                self._out(session_id, "detection", "D2", f"**{name}**: TTF = {ttf}d{delta_str}")

        # ── D3: GAP ANALYSIS ─────────────────────────────────────────
        self._sse(session_id, make_node_event("D3", "active", "Gap Analysis"))
        self._out(session_id, "detection", "D3", "🔬 Analysing gaps...")
        # Build market context string for richer gap analysis
        market_context = ""
        if market_data.get("tavily_results") or market_data.get("news_results"):
            intel_items = []
            for r in (market_data.get("tavily_results", []) + market_data.get("news_results", [])):
                if not r.get("error"):
                    intel_items.append(f"{r.get('title', '')}: {r.get('content', '')[:150]}")
            salary_items = []
            for r in (market_data.get("adzuna_results", []) or []):
                if not r.get("error") and r.get("salary_min"):
                    salary_items.append(f"{r['title']} - R{r['salary_min']}-R{r.get('salary_max','?')}")
            if intel_items:
                market_context = "Market intelligence:\n" + "\n".join(intel_items[:5])
            if salary_items:
                market_context += "\nAdzuna salary data:\n" + "\n".join(salary_items[:5])

        gap = self.d3.analyze(internal.__dict__, external, session_id=session_id,
                              market_context=market_context)
        self._sse(session_id, make_node_event("D3", "complete"))

        for g in getattr(gap, 'flagged_metrics', []):
            metric_name = g.get("metric", g) if isinstance(g, dict) else str(g)
            detail = g.get("detail", "") if isinstance(g, dict) else ""
            msg = f"⚠️ **{metric_name}** {detail}" if detail else f"⚠️ **{metric_name}**"
            self._out(session_id, "detection", "D3", msg)

        if gap.kaizen_required:
            self._out(session_id, "detection", "D3", "**Kaizen Required**: Yes — proceeding to DMAIC")
        else:
            self._out(session_id, "detection", "D3", "**Kaizen Required**: No — all metrics within acceptable range")

        detection_result = {
            "internal": internal.__dict__,
            "external": external,
            "gap": gap.__dict__,
            "market": market_data,
        }

        if not gap.kaizen_required:
            self._sse(session_id, make_phase_event("detection", "complete", detection_result))
            return KaizenSessionResult(session_id=session_id, phase="detection", detection=detection_result)

        self._sse(session_id, make_phase_event("detection", "complete", detection_result))

        # ── DEFINE ───────────────────────────────────────────────────
        self._sse(session_id, make_phase_event("define", "start"))
        self._sse(session_id, make_node_event("K1", "active", "Define (SIPOC)"))
        self._out(session_id, "define", "K1", "📋 Scoping problem statement and SIPOC...")
        define = self.k1.run(gap.__dict__, session_id=session_id)
        self._sse(session_id, make_node_event("K1", "complete"))

        self._out(session_id, "define", "K1", f"**Problem Statement**: {define.problem_statement}")
        for role, desc in getattr(define, "sipoc", {}).items():
            self._out(session_id, "define", "K1", f"**SIPOC — {role}**: {desc}")
        self._out(session_id, "define", "K1", f"**Financial Impact**: {define.financial_impact}")
        self._out(session_id, "define", "K1", f"**KPI Target**: {define.kpi_target}")
        self._sse(session_id, make_phase_event("define", "complete"))

        # ── MEASURE ──────────────────────────────────────────────────
        self._sse(session_id, make_phase_event("measure", "start"))
        self._sse(session_id, make_node_event("K2", "active", "Measure (Metrics)"))
        self._out(session_id, "measure", "K2", "📏 Computing baseline KPIs...")
        measure = self.k2.run(
            data["pipeline_events"], data["hires"],
            data["candidates"], data["offer_outcomes"],
            session_id=session_id,
        )
        self._sse(session_id, make_node_event("K2", "complete"))

        for k, v in getattr(measure, "current_state_metrics", {}).items():
            key_label = k.replace("_", " ").title()
            self._out(session_id, "measure", "K2", f"**{key_label}**: {v}")
        self._out(session_id, "measure", "K2", f"**Summary**: {measure.baseline_summary}")
        self._sse(session_id, make_phase_event("measure", "complete"))

        # ── ANALYSE — pass on_step for per-call granularity ──────────
        self._sse(session_id, make_phase_event("analyse", "start"))
        self._sse(session_id, make_node_event("K3", "active", "Analyse (Root Cause)"))

        def _step_handler(agent_id: str, label: str, progress: int, total: int):
            self._sse(session_id, make_step_event(agent_id, label, progress, total))

        analyse = self.k3.run(define.problem_statement, session_id=session_id, on_step=_step_handler)
        self._sse(session_id, make_node_event("K4", "complete"))
        self._sse(session_id, make_node_event("K5", "complete"))
        self._sse(session_id, make_node_event("K3", "complete"))

        # Rich Five Whys output
        for i, rc in enumerate(analyse.root_causes):
            chain = rc.get("why_chain", [])
            factors = rc.get("causal_factors", [])
            for j, q in enumerate(chain):
                self._out(session_id, "analyse", "K4",
                          f"🔹 **Why {j+1} (Perspective {i+1})**: {q}")
            if factors:
                self._out(session_id, "analyse", "K4",
                          f"   ⤷ Root causes: {', '.join(factors)}")

        # Rich Ishikawa output
        for category, causes in getattr(analyse, "ishikawa_factors", {}).items():
            self._out(session_id, "analyse", "K5",
                      f"🔸 **{category}**: {', '.join(causes)}")

        self._out(session_id, "analyse", "K3",
                  f"**Synthesis**: {analyse.synthesised_findings[:300]}...")
        self._sse(session_id, make_phase_event("analyse", "complete"))

        root_causes_str = str([
            {"perspective": f"Chain {i}", "causes": rc["causal_factors"]}
            for i, rc in enumerate(analyse.root_causes)
        ])

        # ── IMPROVE ──────────────────────────────────────────────────
        self._sse(session_id, make_phase_event("improve", "start"))
        self._sse(session_id, make_node_event("K6", "active", "Improve (Interventions)"))
        self._out(session_id, "improve", "K6", "💡 Generating improvement interventions...")
        improve = self.k6.run(root_causes_str, analyse.synthesised_findings, session_id=session_id)
        self._sse(session_id, make_node_event("K6", "complete"))

        for inv in getattr(improve, "interventions", []):
            self._out(session_id, "improve", "K6",
                      f"📌 **{inv.title}** — {inv.description[:150]}")
        self._out(session_id, "improve", "K6", f"**Recommendation**: {improve.recommendation[:400]}")
        self._sse(session_id, make_phase_event("improve", "complete"))

        # ── CONTROL ──────────────────────────────────────────────────
        self._sse(session_id, make_phase_event("control", "start"))
        self._sse(session_id, make_node_event("K7", "active", "Control (Kanban)"))
        self._out(session_id, "control", "K7", "📋 Building control plan and Kanban board...")
        control = self.k7.run(
            [i.__dict__ for i in improve.interventions],
            session_id=session_id,
        )
        self._sse(session_id, make_node_event("K7", "complete"))

        for col, items in getattr(control, "kanban_board", {}).items():
            self._out(session_id, "control", "K7", f"**{col}** ({len(items)} items)")
            for item in items:
                self._out(session_id, "control", "K7",
                          f"  • {item.action} — Owner: {item.owner}, Due: {item.due_date}")
        self._sse(session_id, make_phase_event("control", "complete"))

        # Cost event
        try:
            cost_resp = self.supabase.table("agent_invocations").select("cost_usd").eq("session_id", session_id).execute()
            total_cost = sum(r.get("cost_usd", 0) for r in (cost_resp.data or []))
            self._sse(session_id, {
                "type": "cost",
                "total_usd": round(total_cost, 6),
                "session_id": session_id,
            })
        except Exception:
            pass

        return KaizenSessionResult(
            session_id=session_id, phase="complete",
            detection=detection_result, define=define.__dict__,
            measure=measure.__dict__, analyse=analyse.__dict__,
            improve=improve.__dict__, control=control.__dict__,
        )
