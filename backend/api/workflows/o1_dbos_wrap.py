"""O1: DBOS Durable Workflow Wrap — Makes the Kaizen lifecycle fault-tolerant."""

from dbos import DBOS, WorkflowHandle
from api.workflows.o2_meta_orchestrator import MetaOrchestrator, KaizenSessionResult

class DBOSKaizenWorkflow:
    """Wraps MetaOrchestrator in DBOS for durability, recovery, and idempotency."""

    def __init__(self, orchestrator: MetaOrchestrator):
        self.orchestrator = orchestrator

    @DBOS.workflow()
    def run_kaizen(self, session_id: str, role_title: str = "Senior Java Developer") -> KaizenSessionResult:
        """Durable workflow — auto-retries on failure, can resume after crash."""
        DBOS.logger.info(f"Starting Kaizen session {session_id} for {role_title}")

        # Step 1: Data fetch (idempotent)
        data = self.orchestrator.fetch_pipeline_data()
        if not data:
            raise ValueError(f"No pipeline data available for session {session_id}")

        # Step 2: Detection (runs as single workflow step)
        result = self.orchestrator.run_full_kaizen(session_id, role_title)

        DBOS.logger.info(f"Kaizen session {session_id} complete — phase: {result.phase}")
        return result

    @DBOS.workflow()
    def run_detection_only(self, session_id: str, role_title: str = "Senior Java Developer") -> KaizenSessionResult:
        """D3 detection layer only — used for goal-review triggers."""
        data = self.orchestrator.fetch_pipeline_data()
        if not data:
            raise ValueError("No pipeline data available")

        internal = self.orchestrator.d1.run(
            data["pipeline_events"], data["hires"],
            data["candidates"], data["offer_outcomes"],
        )
        external = self.orchestrator.d2.run(role_title, internal.time_to_fill_days)
        gap = self.orchestrator.d3.analyze(internal.__dict__, external, session_id=session_id)

        return KaizenSessionResult(
            session_id=session_id,
            phase="detection_complete",
            detection={"internal": internal.__dict__, "external": external, "gap": gap.__dict__},
        )
