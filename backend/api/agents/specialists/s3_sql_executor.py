"""S3 SQL Executor — Sprint B1.

Thin executor that takes a QueryPlan from S1 Query Planner and runs it against
Supabase via the `run_select_query` RPC (migration 005). All heavy lifting
(intent classification, template choice, SQL generation) happens upstream in
the planner; this file just safely runs what the planner decided.

Safety stack (defense in depth):
  Layer 1 (planner): templates first, freeform SELECT only when no template fits
  Layer 2 (this file): regex allowlist on freeform SQL before sending to the DB
  Layer 3 (planner system prompt): "only emit SELECT"
  Layer 4 (DB-side): run_select_query RPC rejects non-SELECT at the DB boundary
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from api.agents.specialists.s1_query_planner import QueryPlan
from api.agents.specialists.sql_templates import (
    TemplateParamError,
    build_template_evidence_sql,
    build_template_sql,
)


# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class ExecutorResult:
    template_id: str | None        # which template ran (None for freeform)
    sql: str                        # the actual SQL we sent
    rows: list[dict] = field(default_factory=list)
    error: str | None = None        # human-readable error, if any
    row_count: int = 0
    # B-evidence: companion non-aggregated query showing the source rows that
    # produced the aggregate result. None when the template has no evidence
    # builder (or for freeform SELECTs). evidence_error captures evidence-only
    # failures so the main result still renders if the evidence query trips.
    evidence_sql: str | None = None
    evidence_rows: list[dict] = field(default_factory=list)
    evidence_row_count: int = 0
    evidence_error: str | None = None


# ---------------------------------------------------------------------------
# Regex allowlist (Layer 2)
# ---------------------------------------------------------------------------

_SELECT_PREFIX = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(DROP|INSERT|UPDATE|DELETE|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|REPLACE"
    r"|MERGE|VACUUM|REINDEX|COPY|EXECUTE|CALL|DO|LOCK|COMMIT|ROLLBACK"
    r"|SAVEPOINT|SET)\b",
    re.IGNORECASE,
)


class FreeformSQLValidationError(ValueError):
    """Freeform SQL failed the Python-side allowlist before being sent to the DB."""


def _validate_freeform_sql(sql: str) -> None:
    stripped = sql.strip()
    if not stripped:
        raise FreeformSQLValidationError("empty SQL")
    if not _SELECT_PREFIX.match(stripped):
        raise FreeformSQLValidationError("only SELECT or WITH-CTE statements are allowed")
    if _FORBIDDEN_KEYWORDS.search(stripped):
        raise FreeformSQLValidationError("forbidden keyword detected (write/DDL operation)")
    # Stacked statement guard — matches the DB-side rule
    body = re.sub(r";\s*$", "", stripped)
    if ";" in body:
        raise FreeformSQLValidationError("multiple statements not allowed")


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class SQLExecutor:
    """Runs the SQL portion of a QueryPlan against Supabase."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def execute(self, plan: QueryPlan) -> ExecutorResult:
        """Build SQL from the plan, validate it, run it, return rows."""
        if not plan.needs_sql:
            return ExecutorResult(template_id=None, sql="", rows=[], error="plan does not need SQL")

        # Path A — validated template
        if plan.sql_template_id:
            try:
                sql = build_template_sql(plan.sql_template_id, plan.sql_template_params)
            except TemplateParamError as exc:
                return ExecutorResult(
                    template_id=plan.sql_template_id,
                    sql="",
                    rows=[],
                    error=f"template param error: {exc}",
                )
            result = self._run(sql, plan.sql_template_id)
            if result.error is None:
                self._attach_evidence(result, plan)
            return result

        # Path B — freeform SELECT (already vetted by the planner; we re-validate here)
        if plan.sql_freeform:
            try:
                _validate_freeform_sql(plan.sql_freeform)
            except FreeformSQLValidationError as exc:
                return ExecutorResult(
                    template_id=None,
                    sql=plan.sql_freeform,
                    rows=[],
                    error=f"freeform SQL rejected: {exc}",
                )
            return self._run(plan.sql_freeform, None)

        return ExecutorResult(
            template_id=None,
            sql="",
            rows=[],
            error="plan flagged needs_sql but supplied neither template nor freeform SQL",
        )

    def _run(self, sql: str, template_id: str | None) -> ExecutorResult:
        """Send SQL to the run_select_query RPC and unpack the result."""
        try:
            resp = self.supabase.rpc("run_select_query", {"sql_text": sql}).execute()
        except Exception as exc:  # noqa: BLE001 -- DB driver may raise broadly
            return ExecutorResult(
                template_id=template_id,
                sql=sql,
                rows=[],
                error=f"DB error: {exc}",
            )

        rows = resp.data
        # The RPC returns a JSONB array; supabase-py decodes it to a Python list of dicts.
        # Some clients wrap it in `{"rows": [...]}`; normalize both shapes.
        if isinstance(rows, dict) and "rows" in rows:
            rows = rows["rows"]
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            rows = [rows]  # single-object response shouldn't happen but be defensive

        return ExecutorResult(
            template_id=template_id,
            sql=sql,
            rows=rows,
            error=None,
            row_count=len(rows),
        )

    def _attach_evidence(self, result: ExecutorResult, plan: QueryPlan) -> None:
        """Run the optional evidence query for the template and attach its rows in-place.

        Evidence failures are isolated — the main aggregate result stands even if
        the evidence query trips. The validation pass treats the generated SQL
        as freeform so it goes through the same allowlist as user-derived SQL,
        belt-and-braces.
        """
        if not plan.sql_template_id:
            return
        try:
            evidence_sql = build_template_evidence_sql(
                plan.sql_template_id, plan.sql_template_params
            )
        except TemplateParamError as exc:
            result.evidence_error = f"evidence param error: {exc}"
            return
        if not evidence_sql:
            return  # template has no evidence path; not an error

        try:
            _validate_freeform_sql(evidence_sql)
        except FreeformSQLValidationError as exc:
            result.evidence_sql = evidence_sql
            result.evidence_error = f"evidence SQL rejected: {exc}"
            return

        try:
            resp = self.supabase.rpc("run_select_query", {"sql_text": evidence_sql}).execute()
        except Exception as exc:  # noqa: BLE001 -- DB driver may raise broadly
            result.evidence_sql = evidence_sql
            result.evidence_error = f"evidence DB error: {exc}"
            return

        rows = resp.data
        if isinstance(rows, dict) and "rows" in rows:
            rows = rows["rows"]
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            rows = [rows]

        result.evidence_sql = evidence_sql
        result.evidence_rows = rows
        result.evidence_row_count = len(rows)
