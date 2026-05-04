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
from api.agents.kaizen.k_writeup import WriteupAgent
from api.agents.specialists.s1_query_planner import QueryPlannerAgent
from api.agents.specialists.s2_rag import RAGAgent
from api.agents.specialists.s3_sql_executor import SQLExecutor
from api.agents.specialists.s4_research import ResearchAgent
from api.agents.cis.fmea import FMEAAgent
from api.sse import (
    push_event, make_node_event, make_phase_event, make_output_event,
    make_step_event, make_cost_event, make_phase_writeup_event,
    wait_for_hitl_response, clear_hitl_queue,
)


# 2026-05-02: temporarily disabled the 30s auto-advance — Donna's call to make
# every gate manual while the writeup UX is still being iterated on. The "ask"
# path was racing the timer (user submits a question, timer expires before the
# answer streams back, auto-advances). Keeping the queue.Queue.get timeout in
# place but cranking it high; effectively manual-only until we re-enable.
HITL_TIMEOUT_SECONDS = 86400.0  # 24h — long enough that no realistic session hits it

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
        self.research = ResearchAgent(supabase_client)
        self.writeup = WriteupAgent(llm_router)
        self.s1 = QueryPlannerAgent(llm_router)
        self.s2 = RAGAgent(supabase_client)
        self.s3 = SQLExecutor(supabase_client)
        # K3 owns K4/K5 — give them the same RAG client so K4 can pull case
        # studies once per run and K5 can pull per-branch (Phase 4.5 T2.1).
        self.k3 = K3AnalyseHostAgent(llm_router, rag_agent=self.s2)
        self.k6 = K6ImproveAgent(llm_router, rag_agent=self.s2)
        self.k7 = K7ControlAgent(llm_router)

    def _sse(self, session_id: str, event: dict):
        try:
            push_event(session_id, event)
        except Exception:
            pass

    def _out(self, session_id: str, phase: str, agent_id: str, content: str):
        """Shorthand for pushing an output_delta event."""
        self._sse(session_id, make_output_event(phase, content, agent_id))

    def _emit_cost_snapshot(self, session_id: str) -> None:
        """Push a `cost` SSE event with running totals so the dashboard ticker
        updates incrementally (was previously only emitted at end of Kaizen)."""
        try:
            resp = self.supabase.table("agent_invocations").select(
                "cost_usd, input_tokens, output_tokens, cached_tokens"
            ).eq("session_id", session_id).execute()
            rows = resp.data or []
            self._sse(session_id, make_cost_event(
                total_usd=sum(r.get("cost_usd", 0) or 0 for r in rows),
                session_id=session_id,
                input_tokens=sum(r.get("input_tokens", 0) or 0 for r in rows),
                output_tokens=sum(r.get("output_tokens", 0) or 0 for r in rows),
                cached_tokens=sum(r.get("cached_tokens", 0) or 0 for r in rows),
            ))
        except Exception:
            pass  # cost-ticker miss isn't worth aborting a Kaizen for

    def _emit_writeup(
        self,
        session_id: str,
        phase: str,
        phase_output,
        prior_writeups: list,
        role_title: str,
        problem_brief: str | None,
        data: dict,
        market_data: dict | None = None,
    ) -> dict | None:
        """Run the writeup agent for a completed phase, emit the phase_writeup SSE event,
        and append to prior_writeups. Returns the writeup dict, or None if it failed.

        `market_data` is the S4 fetch snapshot taken in detection (Adzuna / Tavily / News).
        It's the same payload across all phases of a Kaizen so the writeup agent can cite
        live external data alongside kaizen_node outputs.

        A failed writeup must NOT abort the Kaizen — we surface the error and let
        the HITL gate auto-advance.
        """
        try:
            writeup = self.writeup.run(
                phase=phase,
                phase_output=phase_output,
                prior_writeups=prior_writeups,
                role_title=role_title,
                problem_brief=problem_brief,
                session_id=session_id,
                market_data=market_data,
            )
            wu_dict = writeup.to_dict()
            prior_writeups.append(wu_dict)
            self._sse(session_id, make_phase_writeup_event(phase, wu_dict))
            # Push a running cost snapshot so the dashboard ticker reflects
            # the price of the work just completed, not a $0 placeholder until
            # the very end of the Kaizen.
            self._emit_cost_snapshot(session_id)
            return wu_dict
        except Exception as e:
            self._out(session_id, phase, "K_WRITEUP",
                      f"⚠️ Writeup generation failed: {e}. Auto-advancing.")
            return None

    def _await_hitl(
        self,
        session_id: str,
        phase: str,
        role_title: str,
        problem_brief: str | None,
        data: dict,
    ) -> bool:
        """Block at a HITL gate. Returns True if the Kaizen should continue,
        False if the user aborted. A 30s timeout auto-advances.

        Loops to handle 'ask' decisions: each `ask` runs the chat agent inline
        and re-blocks for the next decision.
        """
        while True:
            response = wait_for_hitl_response(session_id, timeout_seconds=HITL_TIMEOUT_SECONDS)
            if response is None:
                self._out(session_id, phase, "O2", "⏱ Auto-advancing (no input within 30s).")
                return True
            decision = response.get("decision")
            if decision == "advance":
                return True
            if decision == "abort":
                self._out(session_id, phase, "O2", "🛑 User aborted the Kaizen.")
                return False
            if decision == "ask":
                message = response.get("message", "").strip()
                if message:
                    self._handle_ask(session_id, phase, message, role_title, data)
                continue
            self._out(session_id, phase, "O2",
                      f"⚠️ Unknown HITL decision '{decision}', auto-advancing.")
            return True

    def _handle_ask(
        self,
        session_id: str,
        phase: str,
        message: str,
        role_title: str,
        data: dict,
    ) -> None:
        """Route a user follow-up through the Sprint B1 Query Planner pipeline
        and stream the answer back as output_delta events tagged with the
        current phase. Plan envelope + SQL rows + RAG chunks are also reported
        so the timeline shows the routing decision."""
        try:
            plan = self.s1.plan(message, session_id=session_id)
            self._out(session_id, phase, "S1",
                      f"You asked: {message}")
            if plan.explanation:
                self._out(session_id, phase, "S1",
                          f"Routing: {plan.explanation} (confidence {plan.confidence:.2f})")

            answered = False

            if plan.needs_sql:
                result = self.s3.execute(plan)
                if result.error:
                    self._out(session_id, phase, "S3",
                              f"SQL error: {result.error}")
                elif result.row_count == 0:
                    self._out(session_id, phase, "S3",
                              "Structured query returned no rows.")
                elif result.row_count == 1:
                    only = result.rows[0]
                    metrics_str = ", ".join(
                        f"{k}={v}" for k, v in only.items() if v is not None
                    )
                    self._out(session_id, phase, "S3",
                              f"Answer: {metrics_str}")
                    answered = True
                else:
                    label = result.template_id or "freeform SELECT"
                    self._out(session_id, phase, "S3",
                              f"Answer ({label}): {result.row_count} rows returned.")
                    answered = True

            if plan.needs_rag:
                rag_query = plan.rag_query or message
                rag = self.s2.retrieve(rag_query, top_k=5)
                chunks = getattr(rag, "chunks", None) or []
                if chunks:
                    self._out(session_id, phase, "S2",
                              f"Knowledge base: {rag.context_window[:1500]}")
                    answered = True
                else:
                    self._out(session_id, phase, "S2",
                              "Nothing matched in the knowledge base.")

            if not answered:
                self._out(session_id, phase, "O2",
                          "No retrieval path produced a result. Try rephrasing.")
        except Exception as e:
            self._out(session_id, phase, "O2", f"Ask handler error: {e}")

    def fetch_pipeline_data(self, role_title: str | None = None) -> dict:
        """Pull pipeline data, optionally scoped to a single role.

        When `role_title` matches a row in `roles`, candidates / pipeline_events /
        hires / offer_outcomes are filtered to that role's records only. The full
        `roles` and `industry_benchmarks` tables are always returned (they're small
        and used cross-role for comparison).
        """
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

        if role_title:
            target = next((r for r in roles if r.get("title") == role_title), None)
            if target:
                role_id = target["role_id"]
                candidates = [c for c in candidates if c.get("role_id") == role_id]
                cand_ids = {c["candidate_id"] for c in candidates}
                pipeline_events = [e for e in pipeline_events if e.get("candidate_id") in cand_ids]
                hires = [h for h in hires if h.get("role_id") == role_id]
                offer_outcomes = [o for o in offer_outcomes if o.get("role_id") == role_id]

        return {
            "roles": roles, "candidates": candidates,
            "pipeline_events": pipeline_events, "hires": hires,
            "offer_outcomes": offer_outcomes, "benchmarks": benchmarks,
        }

    def run_full_kaizen(
        self,
        session_id: str,
        role_title: str = "Senior Java Developer",
        problem_brief: str | None = None,
        target_kpi: str | None = None,
        tool_plan: list[str] | None = None,
    ) -> KaizenSessionResult:
        """Run a full DMAIC Kaizen.

        Args:
            session_id: UUID linking SSE events to this run.
            role_title: Role family to benchmark (drives D2 lookup + S4 search query).
            problem_brief: Optional user-supplied investigation prompt. When provided,
                K1 frames SIPOC + problem statement around this brief — not the auto-detected gap.
            target_kpi: Optional KPI key (`time_to_fill`, `conversion_rate`, `offer_acceptance`).
                When provided, the Kaizen treats this KPI as the trigger regardless of D3's
                normal threshold logic. Used by per-KPI "Investigate" buttons.
            tool_plan: Optional list of tool keys (e.g., ["D1", "K1", "K6"]).
                If provided, iterate over tools in order instead of hardcoded pipeline.
                If None, fall back to legacy hardcoded sequence.
        """
        data = self.fetch_pipeline_data(role_title=role_title)
        if not data:
            return KaizenSessionResult(session_id=session_id, phase="error")

        # If a tool plan is provided, execute it and return
        if tool_plan is not None:
            return self._run_with_tool_plan(
                session_id, role_title, problem_brief, target_kpi, tool_plan, data
            )

        # Accumulated phase writeups — fed to the writeup agent on each new phase
        # so it can reference prior findings without re-deriving them.
        prior_writeups: list[dict] = []

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

        # ── D2: EXTERNAL BENCHMARKING (multi-KPI) ────────────────────
        self._sse(session_id, make_node_event("D2", "active", "External Benchmarking"))
        self._out(session_id, "detection", "D2", "🔍 Comparing 3 KPIs against industry benchmarks...")
        external = self.d2.run_multi_kpi(role_title, internal.kpis)
        self._sse(session_id, make_node_event("D2", "complete"))
        for c in external.get("comparisons", []):
            sev_icon = {"green": "✅", "amber": "🟡", "red": "🔴"}.get(c["severity"], "•")
            unit = "d" if c["kpi"] == "time_to_fill" else ""
            our = f"{c['our_value']:.1%}" if unit == "" else f"{c['our_value']:.1f}{unit}"
            bench = f"{c['benchmark']:.1%}" if unit == "" else f"{c['benchmark']:.1f}{unit}"
            self._out(session_id, "detection", "D2",
                      f"{sev_icon} **{c['label']}**: {our} vs benchmark {bench} ({c['delta_pct']:+.1f}%)")

        # NEW (Phase 4.5 T1.2): live salary signal computed from adzuna_postings vs hires.salary.
        salary_signal = external.get("live_salary_signal")
        if salary_signal:
            status = salary_signal.get("status")
            if status == "insufficient_data":
                self._out(session_id, "detection", "D2",
                          f"⚠️ **Salary vs live market**: insufficient data — {salary_signal.get('reason', '')}")
            else:
                sev_icon = {"green": "✅", "amber": "🟡", "red": "🔴"}.get(salary_signal["severity"], "•")
                conf = " (low confidence)" if status == "low_confidence" else ""
                self._out(session_id, "detection", "D2",
                          f"{sev_icon} **Salary vs live market**{conf}: R{salary_signal['internal_median']:,.0f} our hires (n={salary_signal['internal_n']}) "
                          f"vs R{salary_signal['adzuna_median']:,.0f} Adzuna median (n={salary_signal['adzuna_n']}) — {salary_signal['delta_pct']:+.1f}%")
            # Fold the signal into market_data so writeups can cite it directly
            # without re-deriving it. The writeup agent already gets market_data per phase.
            market_data["salary_signal"] = salary_signal

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

        # User-supplied brief or target_kpi forces the Kaizen to proceed regardless of D3
        forced_proceed = bool(problem_brief) or bool(target_kpi)
        proceed = gap.kaizen_required or forced_proceed

        if proceed and forced_proceed:
            reason = "user-supplied brief" if problem_brief else f"targeted KPI: {target_kpi}"
            self._out(session_id, "detection", "D3", f"**Kaizen Required**: Yes — {reason}")
        elif gap.kaizen_required:
            self._out(session_id, "detection", "D3", "**Kaizen Required**: Yes — proceeding to DMAIC")
        else:
            self._out(session_id, "detection", "D3", "**Kaizen Required**: No — all metrics within acceptable range")

        detection_result = {
            "internal": internal.__dict__,
            "external": external,
            "gap": gap.__dict__,
            "market": market_data,
            "problem_brief": problem_brief,
            "target_kpi": target_kpi,
        }

        if not proceed:
            self._sse(session_id, make_phase_event("detection", "complete", detection_result))
            return KaizenSessionResult(session_id=session_id, phase="detection", detection=detection_result)

        self._sse(session_id, make_phase_event("detection", "complete", detection_result))

        self._emit_writeup(session_id, "detection", detection_result, prior_writeups,
                           role_title, problem_brief, data, market_data=market_data)
        if not self._await_hitl(session_id, "detection", role_title, problem_brief, data):
            clear_hitl_queue(session_id)
            return KaizenSessionResult(session_id=session_id, phase="aborted",
                                       detection=detection_result)

        # ── DEFINE ───────────────────────────────────────────────────
        self._sse(session_id, make_phase_event("define", "start"))
        self._sse(session_id, make_node_event("K1", "active", "Define (SIPOC)"))
        self._out(session_id, "define", "K1", "📋 Scoping problem statement and SIPOC...")
        define = self.k1.run(
            gap.__dict__,
            session_id=session_id,
            problem_brief=problem_brief,
            target_kpi=target_kpi,
            role_title=role_title,
        )
        self._sse(session_id, make_node_event("K1", "complete"))

        self._out(session_id, "define", "K1", f"**Problem Statement**: {define.problem_statement}")
        for role, desc in getattr(define, "sipoc", {}).items():
            self._out(session_id, "define", "K1", f"**SIPOC — {role}**: {desc}")
        self._out(session_id, "define", "K1", f"**Financial Impact**: {define.financial_impact}")
        self._out(session_id, "define", "K1", f"**KPI Target**: {define.kpi_target}")
        self._sse(session_id, make_phase_event("define", "complete"))

        self._emit_writeup(session_id, "define", define.__dict__, prior_writeups,
                           role_title, problem_brief, data, market_data=market_data)
        if not self._await_hitl(session_id, "define", role_title, problem_brief, data):
            clear_hitl_queue(session_id)
            return KaizenSessionResult(session_id=session_id, phase="aborted",
                                       detection=detection_result, define=define.__dict__)

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

        self._emit_writeup(session_id, "measure", measure.__dict__, prior_writeups,
                           role_title, problem_brief, data, market_data=market_data)
        if not self._await_hitl(session_id, "measure", role_title, problem_brief, data):
            clear_hitl_queue(session_id)
            return KaizenSessionResult(session_id=session_id, phase="aborted",
                                       detection=detection_result, define=define.__dict__,
                                       measure=measure.__dict__)

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

        # Phase 4.5 T2.1: surface RAG case studies that fed K4/K5 so the user
        # sees the precedent base for the analysis.
        rag_citations = getattr(analyse, "rag_citations", []) or []
        if rag_citations:
            self._out(session_id, "analyse", "K3",
                      f"📚 **{len(rag_citations)} case study chunks** retrieved from `kaizen_case_studies` to anchor analysis:")
            for c in rag_citations[:8]:  # cap display
                branch = f" [{c['branch']}]" if c.get("branch") else ""
                self._out(session_id, "analyse", "K3",
                          f"   {c['id']}{branch}: {c['snippet'][:160]}")

        self._out(session_id, "analyse", "K3",
                  f"**Synthesis**: {analyse.synthesised_findings[:300]}...")
        self._sse(session_id, make_phase_event("analyse", "complete"))

        self._emit_writeup(session_id, "analyse", analyse.__dict__, prior_writeups,
                           role_title, problem_brief, data, market_data=market_data)
        if not self._await_hitl(session_id, "analyse", role_title, problem_brief, data):
            clear_hitl_queue(session_id)
            return KaizenSessionResult(session_id=session_id, phase="aborted",
                                       detection=detection_result, define=define.__dict__,
                                       measure=measure.__dict__, analyse=analyse.__dict__)

        root_causes_str = str([
            {"perspective": f"Chain {i}", "causes": rc["causal_factors"]}
            for i, rc in enumerate(analyse.root_causes)
        ])

        # ── IMPROVE ──────────────────────────────────────────────────
        self._sse(session_id, make_phase_event("improve", "start"))
        self._sse(session_id, make_node_event("K6", "active", "Improve (Interventions)"))
        self._out(session_id, "improve", "K6", "💡 Generating improvement interventions...")
        # Offset K6's R-IDs by the analyse phase's citation count so a single
        # numbering scheme spans the whole Kaizen.
        analyse_citation_count = len(getattr(analyse, "rag_citations", []) or [])
        improve = self.k6.run(
            root_causes_str, analyse.synthesised_findings,
            session_id=session_id, citation_id_offset=analyse_citation_count,
        )
        self._sse(session_id, make_node_event("K6", "complete"))

        for inv in getattr(improve, "interventions", []):
            ev = f" [{inv.evidence_id}]" if getattr(inv, "evidence_id", None) else ""
            self._out(session_id, "improve", "K6",
                      f"📌 **{inv.title}**{ev} — Impact={inv.impact}, Effort={inv.effort}, Priority={inv.priority_score}")
            self._out(session_id, "improve", "K6", f"   {inv.description[:200]}")
        self._out(session_id, "improve", "K6", f"**Recommendation**: {improve.recommendation[:400]}")

        # Surface K6's RAG case studies inline so the user sees the precedent
        # base for the interventions (mirrors the K3 surfacing in analyse).
        improve_citations = getattr(improve, "rag_citations", []) or []
        if improve_citations:
            self._out(session_id, "improve", "K6",
                      f"📚 **{len(improve_citations)} case study chunks** retrieved to anchor interventions:")
            for c in improve_citations[:6]:
                self._out(session_id, "improve", "K6",
                          f"   {c['id']}: {c['snippet'][:160]}")

        self._sse(session_id, make_phase_event("improve", "complete"))

        self._emit_writeup(session_id, "improve", improve.__dict__, prior_writeups,
                           role_title, problem_brief, data, market_data=market_data)
        if not self._await_hitl(session_id, "improve", role_title, problem_brief, data):
            clear_hitl_queue(session_id)
            return KaizenSessionResult(session_id=session_id, phase="aborted",
                                       detection=detection_result, define=define.__dict__,
                                       measure=measure.__dict__, analyse=analyse.__dict__,
                                       improve=improve.__dict__)

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

        self._emit_writeup(session_id, "control", control.__dict__, prior_writeups,
                           role_title, problem_brief, data, market_data=market_data)

        # Cost event (USD + token breakdown)
        try:
            cost_resp = self.supabase.table("agent_invocations").select(
                "cost_usd, input_tokens, output_tokens, cached_tokens"
            ).eq("session_id", session_id).execute()
            rows = cost_resp.data or []
            total_cost = sum(r.get("cost_usd", 0) or 0 for r in rows)
            input_tokens = sum(r.get("input_tokens", 0) or 0 for r in rows)
            output_tokens = sum(r.get("output_tokens", 0) or 0 for r in rows)
            cached_tokens = sum(r.get("cached_tokens", 0) or 0 for r in rows)
            self._sse(session_id, make_cost_event(
                total_usd=total_cost,
                session_id=session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
            ))
        except Exception:
            pass

        clear_hitl_queue(session_id)

        return KaizenSessionResult(
            session_id=session_id, phase="complete",
            detection=detection_result, define=define.__dict__,
            measure=measure.__dict__, analyse=analyse.__dict__,
            improve=improve.__dict__, control=control.__dict__,
        )

    def _run_with_tool_plan(
        self,
        session_id: str,
        role_title: str,
        problem_brief: str | None,
        target_kpi: str | None,
        tool_plan: list[str],
        data: dict,
    ) -> KaizenSessionResult:
        """Execute a custom tool plan from K_TOOL_SELECTOR."""
        import logging
        prior_writeups = []
        detection_result = {}
        root_causes: list[str] = []

        # We'll treat the session as already having a kaizen_sessions row inserted by the caller.
        # The caller (routes/cis.py) will insert the session row.

        for tool in tool_plan:
            tool = tool.strip().upper()
            if tool == "D1":
                self._sse(session_id, make_node_event("D1", "active", "Internal Benchmarking"))
                self._out(session_id, "detection", "D1", "📊 Computing pipeline metrics...")
                internal = self.d1.run(
                    data["pipeline_events"], data["hires"],
                    data["candidates"], data["offer_outcomes"],
                )
                internal = internal[0] if isinstance(internal, tuple) else internal
                self._sse(session_id, make_node_event("D1", "complete"))
                detection_result["internal"] = internal.__dict__
                # emit some output
                self._out(session_id, "detection", "D1", f"**Time to Fill**: {internal.time_to_fill_days} days")
            elif tool == "D2":
                self._sse(session_id, make_node_event("D2", "active", "External Benchmarking"))
                external = self.d2.run_multi_kpi(role_title, getattr(internal, "kpis", {}))
                self._sse(session_id, make_node_event("D2", "complete"))
                detection_result["external"] = external
            elif tool == "D3":
                self._sse(session_id, make_node_event("D3", "active", "Gap Analysis"))
                gap = self.d3.analyze(getattr(internal, "__dict__", {}), detection_result.get("external", {}), session_id=session_id)
                self._sse(session_id, make_node_event("D3", "complete"))
                detection_result["gap"] = gap.__dict__
            elif tool == "K1":
                self._sse(session_id, make_phase_event("define", "start"))
                define = self.k1.run(
                    detection_result.get("gap", {}),
                    session_id=session_id,
                    problem_brief=problem_brief,
                    target_kpi=target_kpi,
                    role_title=role_title,
                )
                self._sse(session_id, make_phase_event("define", "complete"))
                self._emit_writeup(session_id, "define", define.__dict__, prior_writeups,
                                   role_title, problem_brief, data)
                # HITL gate
                if not self._await_hitl(session_id, "define", role_title, problem_brief, data):
                    return KaizenSessionResult(session_id=session_id, phase="aborted", detection=detection_result)
            elif tool == "K2":
                self._sse(session_id, make_phase_event("measure", "start"))
                measure = self.k2.run(
                    data["pipeline_events"], data["hires"],
                    data["candidates"], data["offer_outcomes"],
                    session_id=session_id,
                )
                self._sse(session_id, make_phase_event("measure", "complete"))
                self._emit_writeup(session_id, "measure", measure.__dict__, prior_writeups,
                                   role_title, problem_brief, data)
                if not self._await_hitl(session_id, "measure", role_title, problem_brief, data):
                    return KaizenSessionResult(session_id=session_id, phase="aborted", detection=detection_result)
            elif tool in ("K3", "K4", "K5"):
                # Run analyse phase (K3 host which includes K4/K5)
                self._sse(session_id, make_phase_event("analyse", "start"))
                analyse = self.k3.run(
                    problem_brief or "Problem",
                    session_id=session_id,
                    on_step=lambda aid, lbl, prog, tot: self._sse(session_id, make_step_event(aid, lbl, prog, tot)),
                )
                self._sse(session_id, make_phase_event("analyse", "complete"))
                # Collect root causes
                for rc in getattr(analyse, "root_causes", []):
                    factors = rc.get("causal_factors", [])
                    root_causes.extend(factors)
                self._emit_writeup(session_id, "analyse", analyse.__dict__, prior_writeups,
                                   role_title, problem_brief, data)
                if not self._await_hitl(session_id, "analyse", role_title, problem_brief, data):
                    return KaizenSessionResult(session_id=session_id, phase="aborted", detection=detection_result)
            elif tool == "K6":
                self._sse(session_id, make_phase_event("improve", "start"))
                improve = self.k6.run(
                    str(root_causes),
                    "synthesised findings",
                    session_id=session_id,
                    linked_root_causes=root_causes,
                )
                self._sse(session_id, make_phase_event("improve", "complete"))
                # Insert interventions into DB
                interventions_list = getattr(improve, "interventions", [])
                for inv in interventions_list:
                    try:
                        self.supabase.table("interventions").insert({
                            "session_id": session_id,
                            "title": getattr(inv, "title", ""),
                            "description": getattr(inv, "description", ""),
                            "linked_root_cause": getattr(inv, "linked_root_cause", ""),
                            "impact": getattr(inv, "impact", ""),
                            "effort": getattr(inv, "effort", ""),
                            "priority": getattr(inv, "priority_score", None),
                            "owner": None,
                            "due_date": None,
                            "status": "proposed",
                        }).execute()
                    except Exception as e:
                        logging.warning(f"Failed to insert intervention: {e}")
                # Emit interventions event
                self._sse(session_id, {"type": "interventions", "data": [inv.__dict__ for inv in interventions_list]})
                self._emit_writeup(session_id, "improve", improve.__dict__, prior_writeups,
                                   role_title, problem_brief, data)
                if not self._await_hitl(session_id, "improve", role_title, problem_brief, data):
                    return KaizenSessionResult(session_id=session_id, phase="aborted", detection=detection_result)
            elif tool == "FMEA":
                self._sse(session_id, make_phase_event("fmea", "start"))
                fmea_agent = self.fmea
                fmea_result = fmea_agent.run(
                    problem=problem_brief or "General",
                    role_title=role_title,
                    session_id=session_id,
                )
                self._sse(session_id, make_phase_event("fmea", "complete"))
                # Emit fmea event
                self._sse(session_id, {"type": "fmea", "data": fmea_result.__dict__})
            else:
                logging.warning(f"Unknown tool in tool_plan: {tool}")

        # After executing plan, return result (simplified)
        return KaizenSessionResult(
            session_id=session_id, phase="complete",
            detection=detection_result if detection_result else None,
        )
