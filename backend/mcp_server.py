"""MCP Server — Exposes T1 AnalyticsLibrary as MCP tools for AI clients."""

import json
from typing import Any

class MCPTool:
    """Represents an MCP tool with name, params, and handler."""
    def __init__(self, name: str, description: str, parameters: dict, handler):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

class AnalyticsMCPServer:
    """MCP server wrapping T1 AnalyticsLibrary for structured AI consumption."""

    def __init__(self):
        self.tools: dict[str, MCPTool] = {}
        self._register_tools()

    def _register_tools(self):
        self.tools["time_to_fill"] = MCPTool(
            name="time_to_fill",
            description="Calculate average time-to-fill for hired candidates",
            parameters={"type": "object", "properties": {
                "pipeline_events": {"type": "array", "items": {"type": "object"}},
                "hires": {"type": "array", "items": {"type": "object"}},
            }, "required": ["pipeline_events", "hires"]},
            handler=lambda **kw: self._calc_ttf(kw["pipeline_events"], kw["hires"]),
        )

        self.tools["stage_conversion_rate"] = MCPTool(
            name="stage_conversion_rate",
            description="Calculate conversion rate for a pipeline stage",
            parameters={"type": "object", "properties": {
                "pipeline_events": {"type": "array"}, "stage": {"type": "string"},
            }, "required": ["pipeline_events", "stage"]},
            handler=lambda **kw: self._calc_conversion(kw["pipeline_events"], kw["stage"]),
        )

        self.tools["offer_acceptance_rate"] = MCPTool(
            name="offer_acceptance_rate",
            description="Calculate offer acceptance rate",
            parameters={"type": "object", "properties": {
                "hires": {"type": "array"}, "offer_outcomes": {"type": "array"},
            }, "required": ["hires", "offer_outcomes"]},
            handler=lambda **kw: self._calc_oar(kw["hires"], kw["offer_outcomes"]),
        )

        self.tools["benchmark_comparison"] = MCPTool(
            name="benchmark_comparison",
            description="Compare internal metric against industry benchmark",
            parameters={"type": "object", "properties": {
                "internal_value": {"type": "number"}, "benchmark_median": {"type": "number"},
            }, "required": ["internal_value", "benchmark_median"]},
            handler=lambda **kw: self._calc_benchmark(kw["internal_value"], kw["benchmark_median"]),
        )

    def _calc_ttf(self, pipeline_events: list[dict], hires: list[dict]) -> dict:
        accepted = {h["candidate_id"] for h in hires if h.get("accepted")}
        applied, hired = {}, {}
        for ev in pipeline_events:
            if ev["stage"] == "Applied" and ev.get("outcome") == "Advanced":
                applied[ev["candidate_id"]] = ev["event_date"]
            if ev["stage"] == "Offer" and ev["candidate_id"] in accepted:
                hired[ev["candidate_id"]] = ev["event_date"]

        ttfs = [(hired[cid] - applied[cid]).days for cid in accepted if cid in applied and cid in hired]
        mean = float(sum(ttfs) / len(ttfs)) if ttfs else 0.0
        return {"value": round(mean, 1), "unit": "days", "sample_size": len(ttfs)}

    def _calc_conversion(self, pipeline_events: list[dict], stage: str) -> dict:
        at = [e for e in pipeline_events if e["stage"] == stage]
        if not at:
            return {"value": 0, "sample_size": 0}
        advanced = sum(1 for e in at if e.get("outcome") == "Advanced")
        return {"value": round(advanced / len(at), 3), "sample_size": len(at)}

    def _calc_oar(self, hires: list[dict], offer_outcomes: list[dict]) -> dict:
        accepted = sum(1 for o in offer_outcomes if o.get("outcome") == "Accepted")
        total = len(offer_outcomes)
        return {"value": round(accepted / total, 3) if total else 0, "sample_size": total}

    def _calc_benchmark(self, internal: float, benchmark: float) -> dict:
        if not benchmark:
            return {"delta_pct": 0, "severity": "unknown"}
        delta = ((internal - benchmark) / benchmark) * 100
        severity = "green"
        if abs(delta) > 50:
            severity = "red"
        elif abs(delta) > 20:
            severity = "amber"
        return {"delta_pct": round(delta, 1), "severity": severity}

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "parameters": t.parameters}
                for t in self.tools.values()]

    def call_tool(self, name: str, args: dict) -> Any:
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool.handler(**args)

    def handle_mcp_request(self, request: dict) -> dict:
        """Handle standard MCP JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {"tools": self.list_tools()}
        elif method == "tools/call":
            result = self.call_tool(params.get("name", ""), params.get("arguments", {}))
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}
