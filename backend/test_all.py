#!/usr/bin/env python3
"""AutoCI — Multi-level test suite. Run: python3 test_all.py [--level 1|2|3|4|5]"""

import sys
import json
import os
from datetime import date

# ── Level 1: Unit Tests (0 dependencies) ──────────────────────────────────

ANSI = {"GREEN": "\033[92m", "RED": "\033[91m", "YELLOW": "\033[93m", "RESET": "\033[0m"}
pass_count = 0
fail_count = 0

def test(name, fn):
    global pass_count, fail_count
    try:
        fn()
        print(f"  {ANSI['GREEN']}✓{ANSI['RESET']} {name}")
        pass_count += 1
    except Exception as e:
        print(f"  {ANSI['RED']}✗{ANSI['RESET']} {name}: {e}")
        fail_count += 1

def level1_unit():
    print(f"\n{'='*60}\n📦 LEVEL 1: Unit Tests\n{'='*60}")

    # T1 — AnalyticsLibrary
    from api.tools.t1_mcp_analytics import AnalyticsLibrary
    a = AnalyticsLibrary()

    test("TTF with empty data", lambda: a.time_to_fill([], []) == 0.0)

    events = [
        {"candidate_id": "A", "stage": "Applied", "event_date": date(2025,1,1), "outcome": "Advanced"},
        {"candidate_id": "A", "stage": "Offer", "event_date": date(2025,2,1), "outcome": "Offer Extended"},
    ]
    hires = [{"candidate_id": "A", "accepted": True}]
    ttf = a.time_to_fill(events, hires)
    test(f"TTF single hire (expected 31): got {ttf}", lambda: abs(ttf - 31.0) < 1)

    test("Conversion 100%", lambda: abs(a.stage_conversion_rate(events, "Applied") - 1.0) < 0.01)
    test("Dropoff 0%", lambda: abs(a.stage_dropoff_rate(events, "Applied") - 0.0) < 0.01)

    oar = a.offer_acceptance_rate(hires, [{"outcome": "Accepted"}])
    test("OAR 100%", lambda: abs(oar - 1.0) < 0.01)

    bench = a.benchmark_comparison(45.0, 35.0)
    test("Benchmark ~28.6% delta", lambda: abs(bench["delta_pct"] - 28.6) < 1)

    outliers = a.outlier_detection([10, 20, 15, 100, 12, 18])
    test(f"Outlier detection: index 3 (value 100) = {outliers}", lambda: 3 in outliers)

    # T2 — ValidationInterceptor
    from api.tools.t2_validation_interceptor import validate_agent_output
    from pydantic import BaseModel

    class TestSchema(BaseModel):
        value: float

    @validate_agent_output(schema=TestSchema, min_sample_size=3)
    def good_output():
        return {"value": 42.0}

    @validate_agent_output(schema=TestSchema, min_sample_size=3)
    def bad_output_shape():
        return {"wrong_key": 1}

    r1, v1 = good_output()
    test("T2: valid output passes", lambda: v1.passed)

    r2, v2 = bad_output_shape()
    test("T2: bad schema fails", lambda: not v2.passed)

    # S1 — TranslationAgent
    from api.agents.specialists.s1_translation import TranslationAgent
    t = TranslationAgent()
    test("S1: SQL routing for 'time to fill'", lambda: t.classify("What is our time to fill?").agent_routed_to == "s3_sql")
    test("S1: RAG routing for 'culture'", lambda: t.classify("Tell me about company culture").agent_routed_to == "s2_rag")

    # O3 — PhaseGateEnforcer
    from api.workflows.o3_phase_gate import PhaseGateEnforcer
    g = PhaseGateEnforcer()
    d_fail = g.check("define", {"problem_statement": "", "sipoc": None})
    test("O3: empty define fails", lambda: not d_fail.passed)
    d_good = g.check("define", {"problem_statement": "High TTF", "sipoc": {"S": "x"}})
    test("O3: good define passes", lambda: d_good.passed)

# ── Level 2: Supabase Integration ──────────────────────────────────────────

def level2_supabase():
    print(f"\n{'='*60}\n📦 LEVEL 2: Supabase Integration\n{'='*60}")
    try:
        from supabase import create_client
        supa = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
        resp = supa.table("industry_benchmarks").select("*").eq("region", "South Africa").execute()
        test(f"D2: benchmarks count = {len(resp.data)}", lambda: len(resp.data) >= 3)
        resp2 = supa.table("roles").select("*").execute()
        test(f"Roles count = {len(resp2.data)}", lambda: len(resp2.data) >= 3)
    except Exception as e:
        test(f"Supabase connection: {e}", lambda: False)

# ── Level 3: LiteLLM Router (needs API key) ────────────────────────────────

def level3_litellm():
    print(f"\n{'='*60}\n📦 LEVEL 3: LiteLLM Router\n{'='*60}")
    if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-"):
        print(f"  {ANSI['YELLOW']}⚠ SKIP: ANTHROPIC_API_KEY not set{ANSI['RESET']}")
        return
    from api.tools.t3_litellm_router import LiteLLMRouter
    r = LiteLLMRouter()
    content, log = r.route("tagging", [
        {"role": "system", "content": "Answer in one word: is this metric or semantic?"},
        {"role": "user", "content": "What is our time to fill for senior Java devs?"},
    ])
    test(f"LiteLLM response received (${log.cost_usd:.6f}, {log.duration_ms}ms)", lambda: len(content) > 0)
    test(f"Model used: {log.model_used}", lambda: log.model_used == "deepseek-chat")

# ── Level 4: FastAPI Server ────────────────────────────────────────────────

def level4_fastapi():
    print(f"\n{'='*60}\n📦 LEVEL 4: FastAPI HTTP\n{'='*60}")
    import httpx
    try:
        r = httpx.get("http://localhost:8000/health", timeout=5)
        test("GET /health", lambda: r.status_code == 200 and r.json()["status"] == "ok")
        r2 = httpx.post("http://localhost:8000/trigger/manual", json={}, timeout=5)
        test("POST /trigger/manual", lambda: r2.status_code == 200 and r2.json().get("session_id"))
        r3 = httpx.post("http://localhost:8000/trigger/goal-review", timeout=5)
        test("POST /trigger/goal-review", lambda: r3.status_code == 200)
    except Exception as e:
        test(f"Server not running: {e}", lambda: False)

# ── Level 5: Full E2E Kaizen (needs Supabase + LLM keys) ──────────────────

def level5_e2e_kaizen():
    print(f"\n{'='*60}\n📦 LEVEL 5: Full E2E Kaizen Lifecycle\n{'='*60}")
    if not os.environ.get("SUPABASE_SERVICE_KEY", "") or not (os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-") or os.environ.get("DEEPSEEK_API_KEY", "")):
        print(f"  {ANSI['YELLOW']}⚠ SKIP: Needs SUPABASE_SERVICE_KEY + at least one LLM key{ANSI['RESET']}")
        return
    from supabase import create_client
    from api.tools.t3_litellm_router import LiteLLMRouter
    from api.workflows.o2_meta_orchestrator import MetaOrchestrator
    supa = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    llm = LiteLLMRouter(supabase_client=supa)
    orch = MetaOrchestrator(supa, llm)
    result = orch.run_full_kaizen(session_id="e2e-test-001", role_title="Senior Java Developer")
    test("E2E completed", lambda: result.phase is not None and result.phase != "error")
    test("D1: internal metrics computed", lambda: result.detection is not None and "time_to_fill_days" in str(result.detection))
    if result.define:
        test("K1: Define output", lambda: len(result.define.get("problem_statement", "")) > 0)
    if result.analyse:
        test("K3: Root causes found", lambda: len(result.analyse.get("root_causes", [])) > 0)
    print(f"  Phase: {result.phase}")
    if result.detection:
        gap = result.detection.get("gap", {})
        print(f"  Kaizen required: {gap.get('kaizen_required')}")

# ── MCP Server Test ─────────────────────────────────────────────────────────

def test_mcp_server():
    print(f"\n{'='*60}\n📦 MCP Server Test\n{'='*60}")
    from mcp_server import AnalyticsMCPServer
    mcp = AnalyticsMCPServer()
    tools = mcp.list_tools()
    test(f"MCP: {len(tools)} tools registered", lambda: len(tools) >= 4)
    r = mcp.handle_mcp_request({
        "method": "tools/call",
        "params": {"name": "benchmark_comparison", "arguments": {"internal_value": 45.0, "benchmark_median": 35.0}}
    })
    test("MCP: benchmark tool returns delta_pct", lambda: "delta_pct" in str(r))

# ── Runner ──────────────────────────────────────────────────────────────────

def load_env():
    """Load .env file if present."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v)

if __name__ == "__main__":
    load_env()
    level = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--level" else 0

    if level in (0, 1): level1_unit()
    if level in (0, 2): level2_supabase()
    if level in (0, 3): level3_litellm()
    if level in (0, 4): level4_fastapi()
    if level in (0, 5): level5_e2e_kaizen()
    if level in (0, 6): test_mcp_server()

    print(f"\n{'='*60}")
    print(f"RESULTS: {ANSI['GREEN']}{pass_count} passed{ANSI['RESET']}, {ANSI['RED']}{fail_count} failed{ANSI['RESET']}")
    print(f"{'='*60}")
    sys.exit(0 if fail_count == 0 else 1)
