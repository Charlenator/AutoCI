"""O3: Phase Gate Enforcer — Validates phase outputs before allowing progression."""

from dataclasses import dataclass
from api.tools.t2_validation_interceptor import ValidationResult

@dataclass
class GateDecision:
    phase: str
    passed: bool
    fatal: list[str]
    warnings: list[str]

class PhaseGateEnforcer:
    """Checks phase outputs meet quality gates. Blocks progression on fatal errors."""

    PHASE_ORDER = ["detection", "define", "measure", "analyse", "improve", "control"]

    def check(self, phase: str, output: dict) -> GateDecision:
        """Validate phase output against gates."""
        fatal = []
        warnings = []

        if phase == "detection":
            if not output.get("internal"):
                fatal.append("Internal benchmarking: no data computed")
            if not output.get("gap", {}).get("flagged_metrics"):
                warnings.append("No flagged metrics — Kaizen may not be needed")

        elif phase == "define":
            if not output.get("problem_statement"):
                fatal.append("Define: missing problem statement")
            if not output.get("sipoc"):
                warnings.append("Define: SIPOC incomplete")

        elif phase == "measure":
            metrics = output.get("current_state_metrics", {})
            if not metrics.get("time_to_fill_days"):
                warnings.append("Measure: time_to_fill missing")
            if metrics.get("total_candidates", 0) < 5:
                warnings.append(f"Measure: sample size {metrics.get('total_candidates')} < 5")

        elif phase == "analyse":
            if not output.get("root_causes"):
                fatal.append("Analyse: no root causes identified")
            if not output.get("synthesised_findings"):
                warnings.append("Analyse: no synthesis produced")

        elif phase == "improve":
            interventions = output.get("interventions", [])
            if len(interventions) < 3:
                warnings.append(f"Improve: only {len(interventions)} interventions (min 3)")

        elif phase == "control":
            if not output.get("kanban_board"):
                warnings.append("Control: kanban board missing")

        passed = len(fatal) == 0
        return GateDecision(phase=phase, passed=passed, fatal=fatal, warnings=warnings)

    def can_proceed(self, current_phase: str, result: dict) -> tuple[bool, list[str]]:
        """Check gate and return (can_proceed, messages)."""
        decision = self.check(current_phase, result)
        return decision.passed, decision.fatal + decision.warnings
