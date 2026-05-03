# Task 05 — Sprint C: CIS rebrand + dynamic tools + interventions table

## Goal

Rebrand the existing Kaizen tab as the Continuous Improvement Suite (CIS).
Add a conversational scoping agent + a tool-selector that picks the subset
of K-tools needed per problem (could be diagnose-only via 5 Whys + Fishbone,
or full diagnose-to-fix with FMEA + interventions table). K1–K7 become
menu items, not a fixed pipeline. Replace the retired Kanban with an
interventions table that maps each intervention back to a specific K4/K5
root cause.

This task assumes B5 / B6 / B7 / B8 are done.

## Files this task touches

- NEW: `supabase/migrations/008_interventions.sql`
- MODIFY: `supabase/supabase_schema.sql`
- NEW: `backend/api/agents/cis/k_scoping.py`
- NEW: `backend/api/agents/cis/k_tool_selector.py`
- NEW: `backend/api/agents/cis/fmea.py`
- MODIFY: `backend/api/agents/kaizen/k6_improve.py`
- MODIFY: `backend/api/workflows/o2_meta_orchestrator.py`
- NEW: `backend/api/routes/cis.py`
- MODIFY: `backend/main.py`
- REWRITE: `frontend/src/app/cis/page.tsx`
- NEW: `frontend/src/components/InterventionsTable.tsx`
- MODIFY: `frontend/src/components/TopNav.tsx` (or Sidebar after Task 06) —
  rename "Kaizen" → "Continuous Improvement"
- ADD TESTS: `backend/test_all.py`

## Acceptance criteria

- Visiting `/cis` shows a charter bar (empty), a problem-statement input,
  and a scoping chat panel. Typing a problem → K_SCOPING asks 1–2
  clarifying questions → final charter snapshot rendered in the bar.
- Approving the charter triggers K_TOOL_SELECTOR. UI shows the proposed
  tool list with a "Run" button.
- Running executes only the selected tools, with HITL gates between
  multi-phase tools.
- After the run, the page renders writeups per phase + an interventions
  table at the bottom with columns: Title, Description, Root cause linked,
  Impact, Effort, Priority, Owner, Due.
- The kaizen_sessions row + each intervention is persisted; revisiting the
  CIS page lists prior runs in a left rail.
- No design polish required here; plain Tailwind. Design pass = Task 06.

---

## Sub-tasks

### 05.1 — Migration 008: `interventions` table

**File**: `supabase/migrations/008_interventions.sql` (NEW), `supabase/supabase_schema.sql` (mirror)

**Prompt to paste:**

```
Create supabase/migrations/008_interventions.sql.

Read first:
  - supabase/migrations/004_inbound_pipeline.sql — note the idempotent
    pattern (CREATE TABLE IF NOT EXISTS, ALTER TABLE ADD COLUMN IF NOT
    EXISTS, comments at top).
  - supabase/supabase_schema.sql — find the kaizen_sessions + kaizen_nodes
    block; the new table is conceptually downstream.

Implement:

  -- Migration 008: interventions table
  -- One row per concrete intervention proposed by K6_Improve, linked back
  -- to the K4/K5 root cause that motivates it. Replaces the K7 Kanban.
  -- Idempotent — safe to re-run.

  CREATE TABLE IF NOT EXISTS interventions (
    intervention_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES kaizen_sessions(session_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    linked_root_cause TEXT,           -- the K4/K5 finding text this intervention addresses
    impact TEXT CHECK (impact IN ('high', 'medium', 'low')),
    effort TEXT CHECK (effort IN ('XS', 'S', 'M', 'L', 'XL')),
    priority INT,                      -- 1 = highest
    owner TEXT,
    due_date DATE,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'accepted', 'in_progress', 'done', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE INDEX IF NOT EXISTS interventions_session_idx ON interventions (session_id);

Mirror the same CREATE TABLE block at the end of supabase/supabase_schema.sql
so a fresh install matches.

Apply via Supabase MCP:
  apply_migration({name: "008_interventions", query: <the SQL above>})

Then verify:
  list_tables({schemas: ["public"]}) shows "interventions".

Do not modify any other migration file. Do not change kaizen_sessions or
kaizen_nodes.
```

---

### 05.2 — `K_SCOPING` agent

**File**: `backend/api/agents/cis/k_scoping.py` (NEW)

**Prompt to paste:**

```
Create backend/api/agents/cis/__init__.py (empty) and
backend/api/agents/cis/k_scoping.py.

Read first:
  - backend/api/agents/specialists/s1_query_planner.py — same shape: an LLM
    agent with a JSON output and a fallback path.
  - CONTEXT/plan-of-record.md §6 — naming registry: K_SCOPING is the
    pre-run conversational scoping agent.

Implement:

  @dataclass
  class ScopingTurn:
      role: Literal["user", "agent"]
      message: str

  @dataclass
  class ScopingState:
      turns: list[ScopingTurn]
      problem: str | None = None
      scope: str | None = None
      requested_outcomes: list[str] | None = None
      role_title: str | None = None
      target_kpi: Literal["time_to_fill","conversion_rate","offer_acceptance"] | None = None
      confidence: float = 0.0
      ready: bool = False        # True when scoping is complete

  class ScopingAgent:
      def __init__(self, llm_router): ...
      def step(self, state: ScopingState, user_message: str) -> ScopingState:
          """Append the user message, ask the LLM what to do next, return new state."""

LLM contract (system prompt):
  You are scoping a continuous-improvement initiative. Hold a back-and-forth
  with the user until you have enough to write a charter:
    - the problem in one sentence
    - the in/out-of-scope boundary
    - the requested outcomes (1-3 short bullet phrases)
    - the role being improved (e.g. "Senior Java Developer")
    - the primary target KPI (one of: time_to_fill, conversion_rate, offer_acceptance)
    - your confidence that the charter is correct (0..1)

  After each user turn, output JSON:
    {
      "agent_message": str,         # the next thing to say to the user
      "ready": bool,                 # true if you have enough
      "problem": str|null,
      "scope": str|null,
      "requested_outcomes": [str]|null,
      "role_title": str|null,
      "target_kpi": str|null,        # one of the allowed values, or null
      "confidence": 0..1
    }

  When ready=true, agent_message should be a one-line confirmation rather
  than another question.

Behavior:
  - On LLM error or non-JSON: agent_message = "Sorry, I didn't catch that.
    Could you rephrase?", ready=False, confidence=0.
  - Always append the agent message to state.turns before returning.

Add a unit test in test_all.py that constructs an empty ScopingState +
fakes an LLM response of {"agent_message": "Got it.", "ready": true,
"problem": "p", "scope": "s", "requested_outcomes": ["o"], "role_title":
"R", "target_kpi": "time_to_fill", "confidence": 0.9} and asserts the
returned state.ready is true.

Do not modify any other file. Do not add any new dependency.
```

---

### 05.3 — `K_TOOL_SELECTOR` agent

**File**: `backend/api/agents/cis/k_tool_selector.py` (NEW)

**Prompt to paste:**

```
Create backend/api/agents/cis/k_tool_selector.py.

Read first:
  - backend/api/agents/cis/k_scoping.py — input is the ScopingState produced
    by ScopingAgent.
  - backend/api/agents/kaizen/ — list available tools: k1_define, k2_measure,
    k3_analyse_host, k4_five_whys, k5_ishikawa, k6_improve, k_writeup.
    plus the new fmea (05.4).
  - The detection layer: d1_internal_benchmarking, d2_external_benchmarking,
    d3_gap_analysis. These run before the K-tools when a numeric measurement
    is needed.

Implement:

  TOOL_CATALOG = {
    "D1": "Internal benchmarking — pull the KPI from our pipeline data.",
    "D2": "External benchmarking — Adzuna market signal.",
    "D3": "Gap analysis — quantify the delta against benchmarks.",
    "K1": "Define — frame the problem statement formally.",
    "K2": "Measure — confirm the metric definition + sample size.",
    "K3": "Analyse-host — meta-step that introduces analyse phase.",
    "K4": "Five Whys — root-cause iterative drilldown (RAG-grounded).",
    "K5": "Ishikawa — fishbone categorical cause map (RAG-grounded).",
    "K6": "Improve — generate interventions.",
    "FMEA": "FMEA — Severity × Occurrence × Detection on candidate failure modes.",
    "K_WRITEUP": "Writeup agent — runs after every multi-phase step.",
  }

  @dataclass
  class ToolPlan:
      ordered: list[str]            # subset of TOOL_CATALOG keys, in order
      reasoning: str                 # one paragraph rendered in the UI

  class ToolSelectorAgent:
      def __init__(self, llm_router): ...
      def select(self, scoping_state: ScopingState) -> ToolPlan:
          """Pick the subset of tools needed to answer this charter."""

LLM contract: given the charter, return JSON:
  {
    "ordered": [<keys from TOOL_CATALOG>],
    "reasoning": "<one paragraph>"
  }

Heuristic guidance for the system prompt:
  - If target_kpi exists, ALWAYS include D1.
  - If the problem mentions market / salary / candidates / current trends,
    include D2.
  - If both D1 and D2 are present, include D3.
  - K1 and K2 are cheap and almost always belong (Define + Measure).
  - K3 only if the user explicitly asks for analysis OR the next step is K4/K5.
  - K4 OR K5 (or both) if root-cause is the goal.
  - K6 if the user wants interventions.
  - FMEA if the user mentions risk / failure modes / critical paths.
  - K_WRITEUP is appended after every multi-phase tool — handle that in
    o2_meta_orchestrator (next sub-task), not here.

Validation: after parsing, drop any unknown keys; deduplicate while
preserving order. If the resulting list is empty, fall back to
["D1","K1","K2","K4","K6"].

Add a unit test that mocks the LLM and asserts: an unknown tool gets
filtered out; an empty list gets the fallback.

Do not modify any other file.
```

---

### 05.4 — FMEA agent

**File**: `backend/api/agents/cis/fmea.py` (NEW)

**Prompt to paste:**

```
Create backend/api/agents/cis/fmea.py.

Read first:
  - backend/api/agents/kaizen/k4_five_whys.py — same shape: an agent that
    takes a charter, produces a structured output, persists to
    kaizen_nodes.

Implement:

  @dataclass
  class FMEAEntry:
      failure_mode: str
      effect: str
      cause: str
      severity: int       # 1-10
      occurrence: int     # 1-10
      detection: int      # 1-10
      rpn: int            # severity * occurrence * detection

  @dataclass
  class FMEAOutput:
      entries: list[FMEAEntry]
      headline: str       # one-sentence takeaway

  class FMEAAgent:
      def __init__(self, llm_router): ...
      def run(self, *, problem: str, role_title: str | None = None,
              session_id: str | None = None) -> FMEAOutput:
          """Generate an FMEA for the given problem."""

LLM contract: ask for JSON of:
  {
    "entries": [
      {"failure_mode": str, "effect": str, "cause": str,
       "severity": 1..10, "occurrence": 1..10, "detection": 1..10},
      ... 5-8 entries ...
    ],
    "headline": str
  }

After parsing: compute RPN per entry. Sort entries by RPN desc.

Validation: clamp severity/occurrence/detection to 1..10. If parsing fails
entirely, fall back to FMEAOutput(entries=[], headline="FMEA failed to
parse").

Add a unit test that mocks the LLM and asserts RPN computation + descending sort.

Do not modify any other file.
```

---

### 05.5 — K6 prompt update — emit `linked_root_cause`

**File**: `backend/api/agents/kaizen/k6_improve.py` (MODIFY)

**Prompt to paste:**

```
Modify backend/api/agents/kaizen/k6_improve.py.

Read first:
  - The current k6_improve.py — note its dataclass + system prompt.
  - The K4 + K5 outputs (k4_five_whys.py, k5_ishikawa.py) — these are the
    sources of root_cause text that K6 must link to.

Change:
  1. Extend the Intervention dataclass with `linked_root_cause: str`.
  2. Update the system prompt: explain that K4 and K5 outputs are passed
     in as context, and each intervention MUST cite the specific root-cause
     text from one of them. The output JSON adds:
         "linked_root_cause": "<verbatim string from K4/K5 root cause list>"
  3. Update the function signature to accept the K4 + K5 outputs as
     keyword args (or a unified `root_causes: list[str]` if cleaner).
  4. Update the parsing: validate that linked_root_cause is non-empty and
     ideally matches one of the supplied root_causes (case-insensitive
     substring match). If it doesn't match, mark the intervention's
     linked_root_cause as "(unlinked)" and log a warning.

After K6 runs, the orchestrator (next sub-task) inserts each intervention
into the new `interventions` table.

Add tests that:
  - Mock the LLM with a known JSON response containing 2 interventions, one
    with linked_root_cause that matches a supplied root_cause and one that
    doesn't. Assert the second is flagged "(unlinked)".

Do not modify any other K-tool file. Do not change the public function name.
```

---

### 05.6 — Refactor `O2.run_full_kaizen` → consume tool list

**File**: `backend/api/workflows/o2_meta_orchestrator.py` (MODIFY)

**Prompt to paste:**

```
Modify backend/api/workflows/o2_meta_orchestrator.py.

Read first the existing file in full so you understand:
  - run_full_kaizen current control flow
  - the HITL queue + SSE event emission pattern
  - how each phase emits a `phase_writeup` event

Change run_full_kaizen so it consumes a ToolPlan (from K_TOOL_SELECTOR)
instead of running the hardcoded D→M→A→I→C pipeline:

  def run_full_kaizen(
      session_id: str,
      problem_brief: str,
      role_title: str | None,
      target_kpi: str | None,
      tool_plan: list[str] | None = None,    # NEW; defaults to legacy hardcoded order
  ):

  - If tool_plan is None, fall back to the legacy hardcoded sequence
    (so existing /trigger/* routes still work).
  - Otherwise iterate tool_plan in order. For each tool:
      D1/D2/D3 → call the detection agent, emit a node_status event.
      K1/K2/K3 → existing K-phase fns.
      K4/K5 → existing K-phase fns; collect their root_cause lists.
      K6 → new signature: pass root_causes from K4 + K5; insert each
        returned Intervention into the `interventions` table for this
        session_id; emit a `interventions` SSE event with the list.
      FMEA → new agent; emit `fmea` SSE event with the entries.
  - After every multi-phase tool, run K_WRITEUP and emit `phase_writeup`
    as today.
  - HITL gates: after each tool that emits a writeup, optionally pause via
    the HITL queue. Pass-through behavior is unchanged.

Don't break /trigger/manual or /trigger/goal-review — both call into
run_full_kaizen with tool_plan=None and that legacy path must still work.

Add a unit test that calls run_full_kaizen with a tiny stub ToolPlan
(["K1","K6"]) and a fake supabase + fake llm; assert that K1 then K6 ran
and an intervention row was inserted.

Do not modify any K-tool source. Do not modify trigger.py.
```

---

### 05.7 — `routes/cis.py`

**File**: `backend/api/routes/cis.py` (NEW), `backend/main.py` (1-line edit)

**Prompt to paste:**

```
Create backend/api/routes/cis.py and register it in backend/main.py.

Read first:
  - backend/api/routes/trigger.py — note the run-in-background pattern via
    threading.Thread.
  - backend/api/agents/cis/k_scoping.py + k_tool_selector.py
  - backend/api/workflows/o2_meta_orchestrator.py — run_full_kaizen signature

Implement four routes on a new APIRouter:

  POST /cis/scope
    Body: {scoping_state: ScopingState dict, user_message: str}
    Returns: updated scoping_state dict.
    Logic: ScopingAgent.step(state_from_dict, user_message) → return as dict.

  POST /cis/select-tools
    Body: {scoping_state: dict}
    Returns: {ordered: list[str], reasoning: str}
    Logic: ToolSelectorAgent.select(state).

  POST /cis/run
    Body: {scoping_state: dict, tool_plan: list[str]}
    Returns: {session_id: str}
    Logic:
      - Insert a kaizen_sessions row capturing the charter.
      - Spawn a thread that calls run_full_kaizen(session_id, ..., tool_plan).
      - Return the session_id immediately so the frontend can subscribe to
        /sessions/{id}/stream.

  GET /cis/interventions/{session_id}
    Returns: {interventions: [...]}
    Logic: select * from interventions where session_id=? order by priority asc.

Errors: 400 for empty tool_plan, 404 for missing session_id, 500 for any
backend exception.

Register in main.py:
  from api.routes import ... cis
  app.include_router(cis.router, prefix="/cis", tags=["cis"])

Add unit tests covering the happy paths for /cis/scope and /cis/select-tools.
The /cis/run path is exercised in 05.10 e2e.

Do not modify trigger.py or stream.py.
```

---

### 05.8 — `frontend/src/app/cis/page.tsx` rewrite

**File**: `frontend/src/app/cis/page.tsx` (REWRITE)

**Prompt to paste:**

```
Rewrite frontend/src/app/cis/page.tsx as a "use client" page.

Read first:
  - frontend/src/components/chat/ChatPanel.tsx — fetch + state pattern.
  - CONTEXT/style_guide.css §15 — the CIS layout target. Don't apply
    classes yet (Task 06 does the polish); use plain Tailwind.

Layout:
  Three columns (or stacked rail + main if no Sidebar yet):
    1. Tools rail (left, 280px) — shows the proposed/active tool list
       once K_TOOL_SELECTOR runs.
    2. Main column:
       - Charter bar at top — empty until scoping completes.
       - Below charter bar: KPI strip (3 KPI tiles) — populate with
         /metrics/kpis once role_title is known.
       - Phase timeline — one card per tool that runs; SSE-driven.
       - Interventions table at the bottom (when K6 has run).
    3. Optionally a chat panel on the right for the scoping conversation;
       OR put the scoping chat at the top of main and switch to the timeline
       once charter is ready. (Pick whichever is simpler — Task 06 design
       pass refines.)

State:
  - scopingState (ScopingState | null)
  - toolPlan (string[] | null)
  - sessionId (string | null)
  - sseEvents (incoming events from /sessions/{id}/stream)
  - interventions ([] | populated)

Flow:
  1. Empty state: textarea + "Start scoping" button.
  2. User types problem → POST /cis/scope. Append agent message to a chat
     stream. Loop until scopingState.ready === true.
  3. Show the charter snapshot in the bar; show "Pick tools" button.
  4. Click → POST /cis/select-tools → render tool list in the rail with a
     "Run" button.
  5. Click Run → POST /cis/run → get session_id. Open SSE to
     /sessions/{session_id}/stream. Render incoming phase_writeup +
     interventions events.
  6. After interventions event arrives, fetch /cis/interventions/{session_id}
     and render <InterventionsTable />.

Plain Tailwind. No animation libs. Don't introduce a state-management
library.

Do not modify any other file beyond what's listed in the task.
```

---

### 05.9 — `InterventionsTable.tsx`

**File**: `frontend/src/components/InterventionsTable.tsx` (NEW)

**Prompt to paste:**

```
Create frontend/src/components/InterventionsTable.tsx.

Props:
  rows: {
    intervention_id: string;
    title: string;
    description: string | null;
    linked_root_cause: string | null;
    impact: 'high'|'medium'|'low'|null;
    effort: 'XS'|'S'|'M'|'L'|'XL'|null;
    priority: number | null;
    owner: string | null;
    due_date: string | null;
    status: 'proposed'|'accepted'|'in_progress'|'done'|'rejected';
  }[];

Render columns: # (priority), Title, Description, Root cause linked,
Impact (color pill: high=accent, medium=ink-2, low=muted), Effort (mono),
Owner, Due, Status (pill).

Sort by priority asc by default.

Plain Tailwind. No edit affordances yet — read-only table. Empty state:
"No interventions proposed yet."

Do not modify any other file.
```

---

### 05.10 — End-to-end smoke

**File**: none (manual)

**Prompt to paste:**

```
End-to-end smoke for Sprint C.

1. Open the deployed Vercel URL → /cis.
2. In the empty-state textarea, type:
   "Why is offer acceptance dropping for UX Designer roles?"
3. Watch the scoping agent ask 1-2 clarifying questions. Answer
   reasonably. Confirm the charter snapshot appears once ready.
4. Click "Pick tools". Confirm a tool list renders (likely something
   like D1, D3, K1, K2, K4, K5, FMEA, K6 given the question).
5. Click "Run". SSE events stream — phase writeups appear in the
   timeline; interventions arrive at the end.
6. Confirm InterventionsTable renders 3-6 rows with linked_root_cause
   populated for at least 2 of them.
7. Confirm the kaizen_sessions row exists in Supabase, plus 3-6
   interventions rows linked to that session_id.

If anything fails, leave the failing sub-task in "In progress" and write
a "Blocked" row with the question.

Update KANBAN.md: 05.1-05.10 → "Done".
```

## Definition of done

- All 10 sub-tasks moved to KANBAN "Done"
- `python test_all.py 1` passes
- One end-to-end CIS run succeeds with interventions populated

## Commit + push

```
git add supabase/migrations/008_interventions.sql supabase/supabase_schema.sql backend/api/agents/cis/ backend/api/agents/kaizen/k6_improve.py backend/api/workflows/o2_meta_orchestrator.py backend/api/routes/cis.py backend/main.py backend/test_all.py frontend/src/app/cis/page.tsx frontend/src/components/InterventionsTable.tsx CONTEXT/handoff_to_deepseek/KANBAN.md
git commit -m "Sprint C: CIS rebrand + K_SCOPING + K_TOOL_SELECTOR + FMEA + interventions table + dynamic O2"
git push origin main
```
