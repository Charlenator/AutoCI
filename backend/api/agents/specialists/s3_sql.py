"""S3: SQL Agent — Converts NL queries to SQL, runs against pipeline schema, returns metrics.
Wraps T1 AnalyticsLibrary for computed metrics; uses T3 for net-new SQL generation."""

from api.tools.t1_mcp_analytics import AnalyticsLibrary
from api.tools.t3_litellm_router import LiteLLMRouter
from dataclasses import dataclass

@dataclass
class SQLQueryResult:
    sql: str | None
    data: list[dict] | dict
    computed_metrics: dict | None = None

class SQLAgent:
    """Routes known metric queries to T1; unknown ones get SQL-gen via T3."""

    KNOWN_METRIC_MAP = {
        "time to fill": "time_to_fill",
        "conversion rate": "stage_conversion_rate",
        "dropoff": "stage_dropoff_rate",
        "offer acceptance": "offer_acceptance_rate",
        "source yield": "source_yield",
    }

    def __init__(self, supabase_client, llm_router: LiteLLMRouter):
        self.supabase = supabase_client
        self.llm = llm_router
        self.analytics = AnalyticsLibrary()

    def execute(self, query: str, session_id: str = None,
                pipeline_events: list[dict] = None,
                hires: list[dict] = None,
                candidates: list[dict] = None,
                offer_outcomes: list[dict] = None) -> SQLQueryResult:
        """Execute query against known metrics or generate SQL."""
        q = query.lower()

        for keyword, method_name in self.KNOWN_METRIC_MAP.items():
            if keyword in q:
                method = getattr(self.analytics, method_name)
                if method_name == "time_to_fill":
                    val = method(pipeline_events or [], hires or [])
                    return SQLQueryResult(sql=None, data=[], computed_metrics={method_name: val})
                elif method_name == "stage_conversion_rate":
                    # Extract stage from query
                    stages = ["Applied", "Screening", "Interview 1", "Interview 2", "Offer"]
                    stage = next((s for s in stages if s.lower() in q), "Applied")
                    val = method(pipeline_events or [], stage)
                    return SQLQueryResult(sql=None, data=[], computed_metrics={f"{stage}_conversion": val})
                elif method_name == "offer_acceptance_rate":
                    val = method(hires or [], offer_outcomes or [])
                    return SQLQueryResult(sql=None, data=[], computed_metrics={"offer_acceptance_rate": val})

        # Fallback: T3 generates SQL
        messages = [
            {"role": "system", "content": "You generate PostgreSQL queries for the AutoCI recruitment schema. Return ONLY valid SQL, no explanation."},
            {"role": "user", "content": f"Write a PostgreSQL query to answer: {query}\n\nSchema: roles(id, role_id, title, department, hiring_manager, salary_band, open_date, close_date, status), candidates(candidate_id, role_id, source_channel, applied_date), pipeline_events(candidate_id, stage, event_date, outcome, interviewer_id), hires(candidate_id, role_id, offer_date, start_date, salary, accepted), offer_outcomes(candidate_id, role_id, outcome, decline_reason), keywords(keyword_id, label, category, avg_ttf_days, avg_acceptance_rate), industry_benchmarks(role_family, region, median_ttf_days, p25_ttf_days, p75_ttf_days, sample_size), job_descriptions(jd_id, role_id, description_text, posted_date), posting_keywords(posting_id, posting_type, keyword_id), interviewers(interviewer_id, name, department, average_scheduling_lag_days)."}]
        sql, log = self.llm.route("sql_generation", messages, session_id=session_id,
                                   from_agent="s3_sql", to_agent="t3_llm")

        data = []
        if sql:
            try:
                resp = self.supabase.rpc("execute_sql", {"query": sql}).execute()
                data = resp.data or []
            except Exception as e:
                pass

        return SQLQueryResult(sql=sql, data=data)
