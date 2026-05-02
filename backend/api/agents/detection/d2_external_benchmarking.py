"""D2: External Benchmarking Agent — Pulls industry benchmarks from Supabase.
Compares 3 KPIs (TTF, applied→hire conversion, offer acceptance) against industry medians.

Also pulls a *live* salary signal from `adzuna_postings` (live competitor postings
fetched by S4 at the start of the Kaizen) and compares against the median accepted
hire salary in `hires`. This sits alongside the static `industry_benchmarks` row —
the static row is the slow-moving anchor, the Adzuna signal is the right-now
ground truth."""

from dataclasses import dataclass
from statistics import median


@dataclass
class ExternalBenchmarkResult:
    role_family: str
    region: str
    our_ttf: float
    benchmark_median: float
    benchmark_p25: float
    benchmark_p75: float
    delta_pct: float


# How a higher value reads against the benchmark — e.g. higher TTF is BAD, higher OAR is GOOD.
# Used by D3 to decide gap severity direction.
KPI_DIRECTION = {
    "time_to_fill":     "lower_better",
    "conversion_rate":  "higher_better",
    "offer_acceptance": "higher_better",
}


class D2ExternalBenchmarkingAgent:
    """Compares internal metrics against industry_benchmarks table for all 3 KPIs."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def run(self, role_title: str, internal_ttf: float, region: str = "South Africa") -> list[dict]:
        """TTF-only legacy path (kept for backward compatibility with the orchestrator)."""
        try:
            resp = self.supabase.table("industry_benchmarks").select("*").eq(
                "role_family", role_title
            ).eq("region", region).execute()
            benchmarks = resp.data or []
        except Exception:
            benchmarks = []

        results = []
        for b in benchmarks:
            delta = ((internal_ttf - b["median_ttf_days"]) / b["median_ttf_days"] * 100) if b["median_ttf_days"] else 0
            results.append({
                "role_family": b["role_family"],
                "region": b["region"],
                "our_ttf": round(internal_ttf, 1),
                "benchmark_median": b["median_ttf_days"],
                "benchmark_p25": b["p25_ttf_days"],
                "benchmark_p75": b["p75_ttf_days"],
                "delta_pct": round(delta, 1),
            })
        return results

    def run_multi_kpi(self, role_title: str, kpis: dict, region: str = "South Africa") -> dict:
        """Compare each of the 3 KPIs against benchmarks. Returns:
            {role_family, region, comparisons: [{kpi, our_value, benchmark, delta_pct, direction, severity}]}
        Severity: green if within ±10%, amber if 10–25% off, red if >25% off in the unfavourable direction.
        """
        try:
            resp = self.supabase.table("industry_benchmarks").select("*").eq(
                "role_family", role_title
            ).eq("region", region).execute()
            rows = resp.data or []
        except Exception:
            rows = []

        if not rows:
            return {"role_family": role_title, "region": region, "comparisons": []}

        b = rows[0]
        # Map KPI key → benchmark column name
        bench_cols = {
            "time_to_fill":     "median_ttf_days",
            "conversion_rate":  "conversion_rate_median",
            "offer_acceptance": "offer_acceptance_median",
        }

        comparisons = []
        for kpi_key, bench_col in bench_cols.items():
            entry = kpis.get(kpi_key)
            if entry is None:
                continue
            our_value = entry["value"]
            bench_value = b.get(bench_col)
            if bench_value is None or bench_value == 0:
                continue
            delta_pct = (our_value - bench_value) / bench_value * 100

            direction = KPI_DIRECTION[kpi_key]
            unfavourable_pct = delta_pct if direction == "lower_better" else -delta_pct
            if unfavourable_pct > 25:
                severity = "red"
            elif unfavourable_pct > 10:
                severity = "amber"
            else:
                severity = "green"

            comparisons.append({
                "kpi": kpi_key,
                "label": entry.get("label", kpi_key),
                "our_value": our_value,
                "benchmark": bench_value,
                "delta_pct": round(delta_pct, 1),
                "direction": direction,
                "severity": severity,
            })

        return {
            "role_family": role_title,
            "region": region,
            "comparisons": comparisons,
            "live_salary_signal": self._live_salary_signal(role_title),
        }

    def _live_salary_signal(self, role_title: str) -> dict | None:
        """Compare median accepted-hire salary against median Adzuna posting salary.

        Always returns a structured signal (or `None` only on a hard query failure).
        Status field is honest about sample-size limitations — many real Adzuna
        postings hide salary, so saying "insufficient data" is more useful than
        silently dropping the comparison.

            status="ok"                  : ≥5 Adzuna salaries + ≥3 internal hires
            status="low_confidence"      : 2-4 Adzuna salaries + ≥3 internal hires
            status="insufficient_data"   : <2 Adzuna salaries OR <3 internal hires
        """
        try:
            role_rows = self.supabase.table("roles").select("role_id").eq(
                "title", role_title
            ).limit(1).execute().data or []
            if not role_rows:
                return None
            role_id = role_rows[0]["role_id"]

            internal_rows = self.supabase.table("hires").select("salary").eq(
                "role_id", role_id
            ).eq("accepted", True).execute().data or []

            adzuna_rows = self.supabase.table("adzuna_postings").select(
                "salary_min, salary_max"
            ).ilike("title", f"%{role_title}%").execute().data or []
        except Exception:
            return None

        internal_salaries = [r["salary"] for r in internal_rows if r.get("salary")]
        adzuna_salaries: list[float] = []
        for r in adzuna_rows:
            mn, mx = r.get("salary_min"), r.get("salary_max")
            if mn and mx:
                adzuna_salaries.append((mn + mx) / 2)
            elif mn:
                adzuna_salaries.append(mn)
            elif mx:
                adzuna_salaries.append(mx)

        adzuna_n = len(adzuna_salaries)
        internal_n = len(internal_salaries)
        adzuna_postings_total = len(adzuna_rows)

        # Insufficient data — surface the gap rather than hiding it.
        if adzuna_n < 2 or internal_n < 3:
            return {
                "status": "insufficient_data",
                "internal_n": internal_n,
                "adzuna_n": adzuna_n,
                "adzuna_postings_total": adzuna_postings_total,
                "reason": (
                    f"only {adzuna_n} of {adzuna_postings_total} Adzuna postings disclose salary; "
                    f"{internal_n} accepted internal hire(s) on file"
                ),
            }

        internal_median = median(internal_salaries)
        adzuna_median = median(adzuna_salaries)
        if adzuna_median == 0:
            return {
                "status": "insufficient_data",
                "internal_n": internal_n,
                "adzuna_n": adzuna_n,
                "adzuna_postings_total": adzuna_postings_total,
                "reason": "Adzuna median computed as 0 — bad data",
            }

        delta_pct = (internal_median - adzuna_median) / adzuna_median * 100
        if delta_pct < -15:
            severity = "red"
        elif delta_pct < -5:
            severity = "amber"
        else:
            severity = "green"

        status = "ok" if adzuna_n >= 5 else "low_confidence"

        return {
            "status": status,
            "internal_median": round(internal_median, 0),
            "adzuna_median": round(adzuna_median, 0),
            "delta_pct": round(delta_pct, 1),
            "severity": severity,
            "internal_n": internal_n,
            "adzuna_n": adzuna_n,
            "adzuna_postings_total": adzuna_postings_total,
        }
