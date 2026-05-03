"""Validated SQL template registry — Sprint B1.

The S1 Query Planner prefers a template over freeform SQL whenever a query maps
to a known shape. Each template here has been hand-checked against the schema,
which is why we trust them to return verified, accurate results.

Safety model:
  Layer 1 (this file): only parameterized templates with strict param validation
                       are exposed. String params are escaped via _quote_str.
  Layer 2: the s3_sql_executor applies a regex allowlist on freeform SQL.
  Layer 3: the LLM is told in the prompt to emit only SELECT statements.
  Layer 4: run_select_query RPC (migration 005) enforces SELECT-only at the DB.

The planner sees TEMPLATE_REGISTRY's metadata (id + label + description +
params_schema), picks one, and emits {template_id, params}. The executor then
calls TEMPLATE_REGISTRY[id]["build"](params) and runs the resulting SQL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TemplateParam:
    """Parameter definition for a SQL template."""
    name: str
    type: str                       # "string" | "int" | "float" | "stage_name"
    optional: bool = False
    description: str = ""
    default: Any = None
    enum: list[str] | None = None   # if set, value must be one of these


@dataclass
class SQLTemplate:
    """A single validated, parameterizable SELECT query."""
    id: str
    humanized_label: str            # shown in UI per the natural-language-first rule
    description: str                # 1-line, used in the Planner's prompt
    params: list[TemplateParam] = field(default_factory=list)
    build: Callable[[dict], str] = None


# ---------------------------------------------------------------------------
# Param validation + safe substitution
# ---------------------------------------------------------------------------

class TemplateParamError(ValueError):
    pass


def _quote_str(s: Any) -> str:
    """Escape a string value for inline SQL substitution (Postgres single-quote escape)."""
    if s is None:
        return "NULL"
    s_str = str(s)
    return "'" + s_str.replace("'", "''") + "'"


def validate_params(template: SQLTemplate, raw_params: dict | None) -> dict:
    """Validate params against the template's schema; return a normalized dict."""
    raw_params = raw_params or {}
    out: dict[str, Any] = {}

    for spec in template.params:
        if spec.name not in raw_params:
            if spec.optional:
                out[spec.name] = spec.default
                continue
            raise TemplateParamError(
                f"Template '{template.id}' missing required param '{spec.name}'"
            )

        value = raw_params[spec.name]

        if value is None:
            if spec.optional:
                out[spec.name] = None
                continue
            raise TemplateParamError(
                f"Template '{template.id}' param '{spec.name}' cannot be None"
            )

        if spec.type == "string" or spec.type == "stage_name":
            if not isinstance(value, str):
                raise TemplateParamError(
                    f"Template '{template.id}' param '{spec.name}' must be string, got {type(value).__name__}"
                )
            if spec.enum and value not in spec.enum:
                raise TemplateParamError(
                    f"Template '{template.id}' param '{spec.name}'='{value}' not in allowed values {spec.enum}"
                )
            out[spec.name] = value

        elif spec.type == "int":
            try:
                out[spec.name] = int(value)
            except (TypeError, ValueError) as exc:
                raise TemplateParamError(
                    f"Template '{template.id}' param '{spec.name}' must be int: {exc}"
                ) from exc

        elif spec.type == "float":
            try:
                out[spec.name] = float(value)
            except (TypeError, ValueError) as exc:
                raise TemplateParamError(
                    f"Template '{template.id}' param '{spec.name}' must be float: {exc}"
                ) from exc

        else:
            raise TemplateParamError(
                f"Template '{template.id}' has unknown param type '{spec.type}' on '{spec.name}'"
            )

    return out


# ---------------------------------------------------------------------------
# Stage names — single source of truth for the conversion templates
# ---------------------------------------------------------------------------

PIPELINE_STAGES = ["Applied", "Screening", "Interview 1", "Interview 2", "Offer", "Hired"]


# ---------------------------------------------------------------------------
# Template builders
# ---------------------------------------------------------------------------

def _b_time_to_fill(p: dict) -> str:
    role_filter = ""
    if p.get("role_title"):
        role_filter = f"AND r.title ILIKE {_quote_str('%' + p['role_title'] + '%')}"
    return f"""
        SELECT
            ROUND(AVG(EXTRACT(EPOCH FROM (h.start_date::timestamp - c.applied_date::timestamp)) / 86400)::numeric, 1) AS avg_days,
            COUNT(*) AS sample_size,
            r.title AS role_title
        FROM hires h
        JOIN candidates c ON c.candidate_id = h.candidate_id
        JOIN roles r ON r.role_id = h.role_id
        WHERE h.accepted = true
          AND h.start_date IS NOT NULL
          {role_filter}
        GROUP BY r.title
        ORDER BY avg_days
    """


def _b_offer_acceptance_rate(p: dict) -> str:
    role_filter = ""
    if p.get("role_title"):
        role_filter = f"AND r.title ILIKE {_quote_str('%' + p['role_title'] + '%')}"
    return f"""
        SELECT
            r.title AS role_title,
            ROUND(100.0 * SUM(CASE WHEN h.accepted = true THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS acceptance_rate_pct,
            COUNT(*) AS offers_made
        FROM hires h
        JOIN roles r ON r.role_id = h.role_id
        WHERE 1 = 1
          {role_filter}
        GROUP BY r.title
        ORDER BY acceptance_rate_pct
    """


def _b_conversion_rate(p: dict) -> str:
    role_filter = ""
    if p.get("role_title"):
        role_filter = f"AND r.title ILIKE {_quote_str('%' + p['role_title'] + '%')}"

    from_stage = p.get("from_stage", "Applied")
    to_stage = p.get("to_stage", "Hired")

    return f"""
        WITH staged AS (
            SELECT
                c.candidate_id,
                r.title AS role_title,
                MAX(CASE WHEN pe.stage = {_quote_str(from_stage)} THEN 1 ELSE 0 END) AS reached_from,
                MAX(CASE WHEN pe.stage = {_quote_str(to_stage)} THEN 1 ELSE 0 END) AS reached_to
            FROM candidates c
            JOIN roles r ON r.role_id = c.role_id
            LEFT JOIN pipeline_events pe ON pe.candidate_id = c.candidate_id
            WHERE 1 = 1 {role_filter}
            GROUP BY c.candidate_id, r.title
        )
        SELECT
            role_title,
            COUNT(*) FILTER (WHERE reached_from = 1) AS reached_from_count,
            COUNT(*) FILTER (WHERE reached_to = 1) AS reached_to_count,
            ROUND(100.0 * COUNT(*) FILTER (WHERE reached_to = 1) / NULLIF(COUNT(*) FILTER (WHERE reached_from = 1), 0), 1) AS conversion_pct
        FROM staged
        GROUP BY role_title
        ORDER BY conversion_pct
    """


def _b_kpis_for_role(p: dict) -> str:
    role_filter = f"AND r.title ILIKE {_quote_str('%' + p['role_title'] + '%')}"
    return f"""
        WITH role_pool AS (
            SELECT r.role_id, r.title
            FROM roles r
            WHERE 1 = 1 {role_filter}
        ),
        role_candidates AS (
            SELECT c.* FROM candidates c JOIN role_pool r ON c.role_id = r.role_id
        ),
        role_hires AS (
            SELECT h.*, c.applied_date AS applied_date
            FROM hires h
            JOIN candidates c ON c.candidate_id = h.candidate_id
            WHERE h.role_id IN (SELECT role_id FROM role_pool)
        ),
        ttf AS (
            SELECT
                ROUND(AVG(EXTRACT(EPOCH FROM (start_date::timestamp - applied_date::timestamp)) / 86400)::numeric, 1) AS avg_ttf_days,
                COUNT(*) AS hires_count
            FROM role_hires
            WHERE accepted = true AND start_date IS NOT NULL
        ),
        oar AS (
            SELECT
                ROUND(100.0 * SUM(CASE WHEN accepted THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS oar_pct,
                COUNT(*) AS offers_count
            FROM role_hires
        ),
        conv AS (
            SELECT
                ROUND(100.0 * (SELECT COUNT(*) FROM role_hires WHERE accepted) / NULLIF(COUNT(*), 0), 1) AS applied_to_hire_pct,
                COUNT(*) AS applicants
            FROM role_candidates
        )
        SELECT
            (SELECT title FROM role_pool LIMIT 1) AS role_title,
            ttf.avg_ttf_days,
            ttf.hires_count,
            oar.oar_pct,
            oar.offers_count,
            conv.applied_to_hire_pct,
            conv.applicants
        FROM ttf, oar, conv
    """


def _b_pipeline_volume_by_stage(p: dict) -> str:
    role_filter = ""
    if p.get("role_title"):
        role_filter = f"AND r.title ILIKE {_quote_str('%' + p['role_title'] + '%')}"
    return f"""
        SELECT
            r.title AS role_title,
            pe.stage,
            COUNT(DISTINCT pe.candidate_id) AS candidates_at_stage
        FROM pipeline_events pe
        JOIN candidates c ON c.candidate_id = pe.candidate_id
        JOIN roles r ON r.role_id = c.role_id
        WHERE 1 = 1 {role_filter}
        GROUP BY r.title, pe.stage
        ORDER BY r.title, pe.stage
    """


def _b_candidate_search_by_skill(p: dict) -> str:
    skill = p["skill_keyword"]
    skill_safe = _quote_str("%" + skill + "%")
    return f"""
        SELECT
            c.candidate_id,
            c.name,
            c.email,
            c.experience_summary,
            c.skills_json,
            c.cv_storage_path,
            c.is_duplicate,
            c.missing_fields_json
        FROM candidates c
        WHERE c.confidential = false
          AND c.name IS NOT NULL
          AND (
              c.skills_json::text ILIKE {skill_safe}
              OR c.experience_summary ILIKE {skill_safe}
          )
        ORDER BY c.created_at DESC
        LIMIT 50
    """


def _b_candidate_by_email(p: dict) -> str:
    email_safe = _quote_str(p["email"])
    return f"""
        SELECT
            c.candidate_id,
            c.name,
            c.email,
            c.phone,
            c.experience_summary,
            c.skills_json,
            c.cv_storage_path,
            c.is_duplicate,
            c.missing_fields_json,
            c.created_at
        FROM candidates c
        WHERE c.confidential = false
          AND lower(c.email) = lower({email_safe})
        LIMIT 5
    """


def _b_industry_benchmark_for_role(p: dict) -> str:
    role_safe = _quote_str("%" + p["role_title"] + "%")
    region_filter = ""
    if p.get("region"):
        region_filter = f"AND ib.region = {_quote_str(p['region'])}"
    return f"""
        SELECT
            ib.role_family,
            ib.region,
            ib.median_ttf_days,
            ib.p25_ttf_days,
            ib.p75_ttf_days,
            ib.conversion_rate_median,
            ib.offer_acceptance_median,
            ib.source_yield_median,
            ib.sample_size,
            ib.data_source
        FROM industry_benchmarks ib
        WHERE ib.role_family ILIKE {role_safe}
          {region_filter}
        ORDER BY ib.region, ib.role_family
    """


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, SQLTemplate] = {
    "time_to_fill": SQLTemplate(
        id="time_to_fill",
        humanized_label="Average time to fill",
        description="Average days from candidate application to hire start date, broken down by role.",
        params=[
            TemplateParam("role_title", "string", optional=True,
                          description="Filter to roles whose title contains this substring (case-insensitive)."),
        ],
        build=_b_time_to_fill,
    ),
    "offer_acceptance_rate": SQLTemplate(
        id="offer_acceptance_rate",
        humanized_label="Offer acceptance rate",
        description="Percentage of offers accepted, broken down by role.",
        params=[
            TemplateParam("role_title", "string", optional=True),
        ],
        build=_b_offer_acceptance_rate,
    ),
    "conversion_rate": SQLTemplate(
        id="conversion_rate",
        humanized_label="Stage conversion rate",
        description="Percentage of candidates who reach a target stage from a starting stage. Defaults to Applied -> Hired.",
        params=[
            TemplateParam("role_title", "string", optional=True),
            TemplateParam("from_stage", "stage_name", optional=True, default="Applied", enum=PIPELINE_STAGES),
            TemplateParam("to_stage", "stage_name", optional=True, default="Hired", enum=PIPELINE_STAGES),
        ],
        build=_b_conversion_rate,
    ),
    "kpis_for_role": SQLTemplate(
        id="kpis_for_role",
        humanized_label="Three KPIs for a role",
        description="Returns time-to-fill, offer acceptance rate, and applied-to-hire conversion for a single role in one row.",
        params=[
            TemplateParam("role_title", "string",
                          description="The role to look up; matched as a substring (e.g. 'Java Dev' matches 'Senior Java Developer')."),
        ],
        build=_b_kpis_for_role,
    ),
    "pipeline_volume_by_stage": SQLTemplate(
        id="pipeline_volume_by_stage",
        humanized_label="Pipeline volume by stage",
        description="Count of distinct candidates currently/ever at each pipeline stage, grouped by role.",
        params=[
            TemplateParam("role_title", "string", optional=True),
        ],
        build=_b_pipeline_volume_by_stage,
    ),
    "candidate_search_by_skill": SQLTemplate(
        id="candidate_search_by_skill",
        humanized_label="Find candidates by skill",
        description="Returns up to 50 non-confidential candidates whose skills or experience contain the given keyword.",
        params=[
            TemplateParam("skill_keyword", "string",
                          description="Skill or technology to search for (case-insensitive substring match)."),
        ],
        build=_b_candidate_search_by_skill,
    ),
    "candidate_by_email": SQLTemplate(
        id="candidate_by_email",
        humanized_label="Find candidate by email",
        description="Look up a candidate by exact email match.",
        params=[
            TemplateParam("email", "string"),
        ],
        build=_b_candidate_by_email,
    ),
    "industry_benchmark_for_role": SQLTemplate(
        id="industry_benchmark_for_role",
        humanized_label="External market benchmark for a role",
        description="Returns industry-benchmark medians (TTF, conversion, OAR) for a role, optionally filtered by region.",
        params=[
            TemplateParam("role_title", "string"),
            TemplateParam("region", "string", optional=True),
        ],
        build=_b_industry_benchmark_for_role,
    ),
}


def planner_template_summary() -> str:
    """Compact, prompt-friendly listing of every template, for the Query Planner's system prompt."""
    lines: list[str] = []
    for tpl in TEMPLATE_REGISTRY.values():
        param_bits: list[str] = []
        for p in tpl.params:
            tag = "?" if p.optional else "!"
            extra = f" enum={p.enum}" if p.enum else ""
            param_bits.append(f"{p.name}{tag}:{p.type}{extra}")
        params_str = ", ".join(param_bits) if param_bits else "(none)"
        lines.append(f'- "{tpl.id}" — {tpl.humanized_label}. {tpl.description} Params: {params_str}')
    return "\n".join(lines)


def build_template_sql(template_id: str, raw_params: dict | None) -> str:
    """Validate params and build the SQL string for the named template."""
    if template_id not in TEMPLATE_REGISTRY:
        raise TemplateParamError(f"Unknown template '{template_id}'")
    tpl = TEMPLATE_REGISTRY[template_id]
    validated = validate_params(tpl, raw_params)
    return tpl.build(validated)
