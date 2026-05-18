# RFC 0057: Generative-Search Jobs and Web Workspace

Status: proposed
Date: 2026-05-18
Context: RFC 0009 introduced the sweep/candidate lifecycle; RFC 0044
landed v1 NSGA-II active search; RFC 0047 landed the v2 EHVI successor;
RFC 0049 introduced the `ArtifactStore` + `SqliteIndex` cross-run
inspection surface (`kayakgen runs list/query/reindex`). All four are
CLI-only. The Trame web workspace edits a single hull and reads
existing per-candidate JSON records via `kayakgen.ui.web.read_models`,
but has no surface for *launching* a sweep or active search, no way to
watch a long-running run, and no Pareto-frontier picker that hands a
selected candidate back into the existing comparison/3D view. This RFC
adds (a) a durable long-lived job surface so search/sweep runs survive
across web-process lifetimes, and (b) a "Generate" panel in the web
workspace that drives that surface.

## Problem

`kayakgen search` and `kayakgen sweep` are batch CLI tools that can
take minutes to hours depending on budget. They already persist
`state.json` checkpoints under their output directory and support
`--resume`, but no other surface knows the job exists while it is
running. There is no enumerable list of in-flight runs, no progress
tail, no cancel signal, no shared status anyone can subscribe to. The
existing `/api/cfd/*` route family runs synchronously in the Trame
process — adequate for a single mock CFD call but unworkable for a
search that may evaluate hundreds of candidates.

For an operator to launch a search today, they must hand-author a
search-spec JSON, run the CLI, watch the terminal, and then post-hoc
load the run directory in a separate `kayakgen compare` invocation.
The web workspace already renders single hulls, comparison reports,
high-angle GZ display blocks, and CFD job status — but it cannot start
a search, watch one, or browse the resulting Pareto frontier. That gap
is what makes the generative path effectively expert-only.

## Goals

- Define a `GenerativeJob` aggregate that owns a long-lived
  search-or-sweep run: spec, output directory, status, progress
  metrics, log tail, cancellation flag, resume pointer.
- Persist every job as a JSON record on disk so jobs survive web
  restarts and can be enumerated/resumed by any client.
- Expose a `/api/jobs/*` route family on the Trame web app that lets
  the browser start, watch, cancel, and resume jobs against the same
  on-disk store the CLI uses.
- Land a Trame "Generate" panel that builds a search spec, kicks off a
  job, tails progress, lists running and completed jobs, and surfaces
  the resulting Pareto frontier with a candidate picker that hands a
  selected candidate into the existing single-hull and comparison views.
- Preserve every existing claim and admissibility gate (RFC 0043
  display-only refusal, RFC 0044 explicit-exploratory requirement,
  RFC 0046 opt-in mechanism precedence, the forbidden-claim scan on
  `app.py`/`controllers.py`).
- Route every output through `ArtifactStore` + `SqliteIndex` (RFC 0049)
  so `kayakgen runs query` and the new web surface read from the same
  source of truth.
- Keep all execution local. No hosted, queued, or remote-worker
  capability is introduced (D023 remains deferred).

## Non-Goals

- This RFC does not introduce a real solver, calibrated resistance, a
  hosted demo, or any change to the claim-state vocabulary. The
  Pareto frontiers it surfaces remain whatever `claim_state` their
  candidate records already carry (`raw_unvalidated`,
  `uncalibrated_comparative`).
- It does not parallelize the search algorithm itself across
  processes or hosts. Population-level concurrency stays inside the
  existing single-process runner; this RFC only makes the run *itself*
  observable across processes.
- It does not introduce authentication, multi-user isolation, or
  cross-machine job submission. The web app remains a single-operator
  local tool.
- It does not change the CLI surface. `kayakgen search` and
  `kayakgen sweep` keep their existing flags and exit codes. The new
  job surface is additive.
- It does not introduce a new algorithm. NSGA-II (RFC 0044) and EHVI
  (RFC 0047) are the only algorithms the Generate panel exposes.
- It does not add a real-time WebSocket protocol. Progress polling
  over the existing Trame state-update channel is sufficient at the
  observed candidate-emission cadence.

## Dependencies

- RFC 0009 for the sweep candidate lifecycle (`pending`, `completed`,
  `failed`, `constraint_failed`) the Pareto picker filters on.
- RFC 0043 for the high-angle GZ display-only refusal that the
  spec-builder must enforce when offering metrics as objectives.
- RFC 0044 for NSGA-II spec shape, `objectives_explicit_exploratory`,
  and the claim-admissibility gate.
- RFC 0046 for the per-job profile-flag / persistent-setting / env-knob
  opt-in precedence when CFD evaluation is part of the search loop.
- RFC 0047 for the EHVI algorithm spec shape and dimensionality
  refusal.
- RFC 0049 for `ArtifactStore` + `SqliteIndex`. The job store sits in
  the same artifact-root layout and uses `run_hash` as the join key.
- RFC 0052 for `ConvergenceFlag` + within-evaluator-noise advisory
  that the Pareto picker surfaces.
- RFC 0055 for the design-report export the Pareto picker links to.

## Proposal

### New aggregate: `GenerativeJob`

```python
GenerativeJob(
    job_id: str,                       # uuid4 hex
    schema_version: Literal["1"],
    job_kind: Literal["sweep", "search"],
    spec_ref: str,                     # path under artifact root
    spec_hash: str,                    # sha256 of canonical spec JSON
    output_dir: str,                   # path under artifact root
    state: Literal[
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled",
        "resumable",
    ],
    progress: GenerativeJobProgress,   # see below
    started_at: datetime | None,
    completed_at: datetime | None,
    cancellation_requested_at: datetime | None,
    error: GenerativeJobError | None,
    log_tail_ref: str,                 # path to bounded log file
    resumable_from_checkpoint: bool,
)

GenerativeJobProgress(
    schema_version: Literal["1"],
    realized_evaluations: int,
    budget_max_evaluations: int | None,
    generation: int | None,            # NSGA-II only
    iteration: int | None,             # EHVI only
    pending_count: int,
    completed_count: int,
    failed_count: int,
    constraint_failed_count: int,
    wall_clock_seconds: float,
    last_candidate_key: str | None,
    last_update_at: datetime,
)

GenerativeJobError(
    kind: Literal[
        "spec_validation_failed",
        "evaluator_error",
        "ehvi_dimension_unsupported",
        "objective_claim_state_inadmissible",
        "high_angle_gz_display_only",
        "cancelled_by_operator",
        "internal_error",
    ],
    message: str,
    candidate_key: str | None,
)
```

All states are reachable from `queued`; `resumable` is the post-cancel
or post-process-crash state where a `state.json` checkpoint exists and
the next `POST /api/jobs/<id>/resume` will pick up from it.

### On-disk layout

Jobs persist under a new artifact-root subdirectory:

```
<artifact_root>/jobs/
  <job_id>/
    job.json                  # serialized GenerativeJob
    spec.json                 # frozen copy of the submitted spec
    log.txt                   # bounded ring buffer, sha256-stamped
    output/                   # the run_dir; sweep or search writes here
      candidates/...
      state.json              # existing checkpoint (RFC 0044)
      run.json
```

`<artifact_root>` is the same root `ArtifactStore` uses. The
`SqliteIndex` gains a `generative_jobs` table joining `job_id` →
`spec_hash`, `state`, `started_at`, `output_dir`, `run_hash`. A new
`kayakgen runs query --jobs` flag surfaces the same table on the CLI.

### Job manager

A new module `kayakgen/services/generative_jobs.py` owns the
`GenerativeJobManager` interface: `start(spec, kind)`, `get(job_id)`,
`list(filter)`, `cancel(job_id)`, `resume(job_id)`, `tail_log(job_id,
since)`. Implementations:

- `InProcessGenerativeJobManager` runs each job in a background
  `threading.Thread` inside the same process. Progress events arrive
  on a `queue.Queue`; the manager flushes the latest progress to
  `job.json` after each event and writes log lines through a
  bounded-file logger. This is the default for `kayakgen serve`.
- `SubprocessGenerativeJobManager` (opt-in) spawns each job as a
  detached `python -m kayakgen.services.generative_jobs.run` process
  so a web-process crash does not lose the job. Progress is written
  by the child directly to `job.json`; the manager only reads.

Both implementations enforce the same cancellation protocol: a
`cancellation_requested_at` write to `job.json` is checked by the
runner between candidate emissions; on detection the runner shuts down
cleanly, leaves `state.json` intact, and exits to state `resumable`.

### Runner seams

`kayakgen.search.active.runner.run_search` and
`kayakgen.sweep.run_sweep` gain a new optional
`progress_sink: GenerativeJobProgressSink | None = None` argument.
When present, the runner calls
`progress_sink.candidate_completed(record, summary)` after each
candidate write and
`progress_sink.checkpoint(state)` at each `state.json` write. Default
behavior with `progress_sink=None` is byte-equal to today.

### Web surface

The Trame app gains a new "Generate" panel (collapsible, sibling to
the existing Parameters / Geometry / Review regions) with three modes:

1. **Build spec.** Form for `name`, `base_hull` (defaults from the
   currently loaded hull), `search_space` (per-variable
   distribution: `uniform`/`log_uniform`/`discrete` with min/max/step),
   `algorithm` (radio: NSGA-II vs EHVI; per-algorithm sub-form),
   `objectives` (multi-select filtered to admissible metrics —
   display-only metrics never appear in the picklist; metrics whose
   role requires `objectives_explicit_exploratory` show an explicit
   checkbox the user must tick), `budget` (max evaluations + wall
   clock), `evaluators` (toggles for hydrostatics, stability, mesh
   diagnostics, sensitivity, turning, STL emission). The form
   round-trips a search-spec JSON identical in shape to what the CLI
   accepts. Submit triggers `POST /api/jobs/search` (or `/sweep`).
2. **Watch.** Table of jobs with `job_id`, `kind`, `state`, progress
   bar, started_at, last_update_at, wall_clock_seconds. Selecting a
   row opens a detail card with a log tail (last N bounded lines),
   cancel button, resume button (when state is `resumable`), and a
   live count of `completed_count` / `failed_count` /
   `constraint_failed_count` / `pending_count`. Polling cadence is
   1 s while a job is running, 10 s while idle.
3. **Pareto pick.** Once a job reaches `succeeded`, the panel renders
   a 2D scatter of the resolved Pareto frontier (`run.json` →
   `pareto_frontier`) coloured by `claim_state` and shaped by
   `convergence_flag`. Clicking a point loads that candidate into the
   existing single-hull view and (optionally) pushes it into the
   comparison panel. A "design report" button calls the existing
   `kayakgen design-report` codepath against the candidate.

### New routes

```
GET    /api/jobs                  → list of GenerativeJobSummary
POST   /api/jobs/search           → start a search job from a spec body
POST   /api/jobs/sweep            → start a sweep job from a spec body
GET    /api/jobs/<id>             → full GenerativeJob
GET    /api/jobs/<id>/log         → bounded log tail (since cursor)
GET    /api/jobs/<id>/frontier    → resolved Pareto frontier
POST   /api/jobs/<id>/cancel      → set cancellation_requested_at
POST   /api/jobs/<id>/resume      → resume a `resumable` job
POST   /api/jobs/<id>/load-candidate
                                  → hand a candidate to single-hull view
```

Every spec body passes through the same validators the CLI uses
(`load_search_spec`, `load_sweep_spec`) before the job is created;
rejection returns the same structured error tokens.

### Forbidden-copy enforcement

The new panel's static template, generated job-status labels, and
Pareto-picker captions are added to the
`tests/test_web_forbidden_copy.py` regression scan. The fixed caption
under any high-angle GZ column is the same string already enforced by
RFC 0043 stage 3 ("Unvalidated hydrostatic comparison; not safety,
seaworthiness, calibrated, validated, or final-prediction claim").

### Claim admissibility at spec submission

`POST /api/jobs/search` calls
`ensure_objectives_claim_admissible_for_search` (RFC 0044) and
`ensure_objectives_not_high_angle_gz` (RFC 0043) before persisting the
spec. Rejection returns the structured token to the panel, which
surfaces it inline next to the offending objective row. The same
applies to EHVI's `EhviDimensionError` for 4+ objectives.

### Resume

Resuming reuses the existing `--resume` codepath: the job manager
re-invokes `run_search(spec_path, output_dir, resume=True)` against
the persisted `state.json`. The job transitions
`resumable` → `running` and progress counters are recovered from the
existing per-candidate records.

## Acceptance Criteria

- New `GenerativeJob`, `GenerativeJobProgress`, `GenerativeJobError`,
  and `GenerativeJobSummary` Pydantic records exist with byte-stable
  canonical JSON serialization and `schema_version="1"`.
- `InProcessGenerativeJobManager` lands first; the
  `SubprocessGenerativeJobManager` may follow in a separate stage.
- `kayakgen.search.active.runner.run_search` and `kayakgen.sweep`
  accept an optional `progress_sink`; default behavior with
  `progress_sink=None` is byte-equal to before across the full test
  suite.
- The job store integrates with `ArtifactStore` + `SqliteIndex`:
  `kayakgen runs query --jobs` lists the same jobs the web panel
  lists.
- Submitting a spec via the web panel and via the CLI on the same
  base hull and seed produces byte-identical `candidates/<key>/record.json`
  files (within determinism guarantees of the chosen algorithm).
- The Generate panel never offers a display-only metric as an
  objective; attempting to inject one via the JSON-spec textarea is
  refused with the structured token from RFC 0043.
- A cancellation issued while a candidate evaluation is in flight
  shuts the job down cleanly, leaves the `state.json` checkpoint
  intact, and reports `state="resumable"`.
- Resuming a cancelled job byte-equals running the same spec from
  scratch to the same realized-evaluations count, given the seeded
  determinism contract of RFC 0044.
- `tests/test_web_forbidden_copy.py` covers the new panel and
  job-status surface; no forbidden-claim copy appears in any rendered
  state.
- The new routes are covered by web integration tests against the
  Trame test client.
- No new claim-state, readiness-level, or `accepted_uses` literal is
  introduced. No hosted operation is enabled.
- `docs/USER_GUIDE.md`, `docs/ARCHITECTURE_MAP.md`, `docs/DDD.md`,
  `docs/SPEC.md`, `docs/PRD.md`, and `docs/ROADMAP.md` are updated
  in the same landing.

## Open Questions

- Should `InProcessGenerativeJobManager` or
  `SubprocessGenerativeJobManager` be the default for `kayakgen
  serve`? In-process is simpler and survives the common case; the
  subprocess variant is more robust but adds a child-process surface
  to test. Recommended default: in-process for stage 1, with the
  subprocess implementation behind an opt-in `serve --jobs-subprocess`
  flag landed in stage 2.
- Should the `/api/jobs/*` route family also accept a CLI-shaped
  search-spec JSON body, or only a panel-builder shape that the panel
  serializes? Reusing the CLI shape is cheaper and keeps the spec
  byte-identical between surfaces; recommended yes.
- Should the Pareto picker support 3D objective scatter, or stay 2D
  with a "pick two objectives" selector? 2D with selector is simpler
  and matches EHVI's 1/2/3-objective range; 3D requires a Trame VTK
  scatter renderer. Recommended 2D with selector for stage 1.
- Should the panel offer a "rerun with new seed" affordance that
  forks an existing successful job? Useful for variance-of-seed
  diagnostics; defer to a follow-up if not implemented in stage 1.
- Should log lines be redacted for absolute filesystem paths before
  surfacing in the browser? Recommended: redact home-dir prefix and
  show paths relative to the artifact root.
- Where do active CFD jobs (RFC 0046 `succeeded` path) attach? An
  in-loop search that triggers real-solver CFD per candidate could
  multiply runtime by orders of magnitude. Recommended: stage 1
  exposes only hydrostatics/stability/mesh-diagnostics evaluators in
  the panel's evaluator picker; CFD-in-loop is a separate stage with
  its own evaluator opt-in row and an explicit per-job opt-in
  acknowledgment.

## Implementation Path

Stage 1 — core job surface:

1. Land `GenerativeJob`/`GenerativeJobProgress`/`GenerativeJobError`/
   `GenerativeJobSummary` Pydantic records with serialization round-trip
   tests.
2. Land `GenerativeJobManager` interface and
   `InProcessGenerativeJobManager` implementation with cancellation +
   resume tests.
3. Wire `progress_sink` into `run_search` and `run_sweep`; default
   behavior byte-stable.
4. Extend `SqliteIndex` with the `generative_jobs` table and
   `kayakgen runs query --jobs` CLI surface.

Stage 2 — web panel:

5. Add `/api/jobs/*` routes against `InProcessGenerativeJobManager`.
6. Add the "Generate" Trame panel with build/watch/pick modes.
7. Extend `tests/test_web_forbidden_copy.py` and
   `tests/test_web.py` to cover the new surface.

Stage 3 — robustness:

8. Land `SubprocessGenerativeJobManager` behind
   `serve --jobs-subprocess` opt-in.
9. Add a resume-after-process-crash integration test that simulates
   `SIGKILL` on the runner subprocess and verifies clean recovery.

Each stage lands as its own commit per the project's one-phase-per-RFC
rule.

## Domain Modeling

`GenerativeJob` is an *application-services* aggregate, not a hull-
domain entity. It owns the lifecycle of a long-lived computation; the
hull-domain output of that computation is whatever the underlying
search or sweep already produces. Cancellation, resume, and log tail
are application concerns; they do not change the per-candidate record
or the Pareto frontier semantics.

`GenerativeJobProgress` is a read-model view computed from the
candidate-record stream; persisting it on `job.json` is a denormalization
for fast list/watch queries, not a new source of truth.

Job execution is *not* a domain entity; the runner is a stateless
function whose only durable artifacts are the candidate records,
`state.json`, `run.json`, the bounded log file, and the job record
itself.

The web panel is a thin Trame view-model over the same read models the
existing comparison panel and single-hull view already use. No
hull-domain logic moves into the UI layer; the import-boundary tests
(`tests/test_import_boundaries.py`) extend to confirm
`kayakgen/ui/web/` does not import from `kayakgen/search/` or
`kayakgen/sweep/` directly — every cross-boundary call goes through
`kayakgen/services/generative_jobs.py`.
