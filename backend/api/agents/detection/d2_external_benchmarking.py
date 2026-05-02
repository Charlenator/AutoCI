"""D2: External Benchmarking Agent — Pulls industry benchmarks from Supabase."""

from dataclasses import dataclass

@dataclass
class ExternalBenchmarkResult:
    role_family: str
    region: str
    our_ttf: float
    benchmark_median: float
    benchmark_p25: float
    benchmark_p75: float
    delta_pct: float

class D2ExternalBenchmarkingAgent:
    """Compares internal metrics against industry_benchmarks table."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def run(self, role_title: str, internal_ttf: float, region: str = "South Africa") -> list[dict]:
        """Fetch benchmarks and compute deltas."""
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
