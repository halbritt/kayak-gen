author: operator [self-declared: operator-0029-ledger]

# Workflow 0029 Findings Ledger

Run: `run_9126a2d7dd7a4fa3b9cbf6815a8e0c98`
Job: `findings_ledger`

## Gate Result

`accept_with_findings`

The review lanes agree that workflow 0029 is implementable as a narrow web
adapter over the existing RFC 0015 local filesystem dispatch contract. The
safe slice is local CFD job preparation, status, run-state inspection, logs,
and raw-artifact lookup through `/api/cfd/*` routes and a compact browser
panel. It must not claim hosted execution, real solver success, cancellation
guarantees, authentication, calibrated drag, validated CFD, or final design
fitness.

## Stats

- Review artifacts read: 3
- Raw review findings: 16
- Consolidated accepted findings: 7
- Rejected findings: 0
- Deferred boundary groups: 7

## Accepted Findings

### F-001 - The RFC 0018 `/api/cfd/*` route family is missing

The current web REST surface still has RFC 0008's reserved `/api/jobs` stubs
returning 501. Those stubs remain honest as legacy placeholders, but they do
not satisfy the web CFD route contract.

Required actions:

- Add `GET /api/cfd/profiles`.
- Add `POST /api/cfd/jobs`.
- Add `GET /api/cfd/jobs/{job_id}`.
- Add `POST /api/cfd/jobs/{job_id}/run`.
- Add `GET /api/cfd/jobs/{job_id}/logs`.
- Add `GET /api/cfd/jobs/{job_id}/raw-result`.
- Keep `/api/jobs` explicitly reserved or compatibility-only; do not treat it
  as completion of workflow 0029.

### F-002 - Web routes must wrap the existing local dispatch records

The route layer must expose the RFC 0015 job/read models rather than inventing
a separate in-memory job model. The implementation boundary is an adapter over
`CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, readiness gates, and local job
artifacts.

Required actions:

- Build profile payloads from the built-in solver profiles exposed by
  `kayakgen.eval.cfd.jobs`.
- Create jobs through `prepare_cfd_job()` or the same lower-level contract.
- Read status through `load_cfd_run_record()` or equivalent record parsing.
- Run local jobs through `run_cfd_job()` for the first synchronous local slice.
- Include `result_semantics: raw_unvalidated` and the plain warning text in
  every job, run, log, and raw-result response.

### F-003 - Browser-visible CFD states and warnings are absent

The Trame UI currently shows hull controls, metrics, analysis, comparison, and
export/share controls, but no CFD job panel. Users need browser-visible local
job state without confusing unavailable, failed, fixture, or raw output for
validated hydrodynamic prediction.

Required actions:

- Add a compact CFD job view or tab that lists solver profiles, accepts the
  first-slice job inputs, and exposes prepare/run/status actions.
- Render job status, solver profile, created/started/finished timestamps,
  `error_kind`, `error_message`, logs, and raw-result links.
- Show a plain raw/unvalidated warning outside JSON internals for every CFD
  status, artifact, and raw-result view.
- Distinguish `queued`, `running`, `unavailable`, `failed`, and `succeeded`
  states. Treat `unavailable` and `failed` as terminal problem states; a
  `succeeded` record, if rendered from a fixture or future adapter, is still
  raw and unvalidated.

### F-004 - Mesh readiness rejection and other failures need structured JSON

CLI dispatch errors are readable, but browser clients need stable JSON errors
instead of generic validation failures, tracebacks, or HTML responses.

Required actions:

- Convert invalid payloads, unknown profiles, readiness rejection, solver
  profile mismatch, missing jobs, missing run records, missing logs, missing
  raw results, malformed artifacts, and dispatch failures into deterministic
  JSON errors.
- Include a stable error kind, selected solver profile, required readiness,
  observed readiness when available, mesh profile mismatch details when
  available, and a user-facing message for job-preparation rejection.
- Use appropriate HTTP status codes for bad input, missing records, missing
  artifacts, and server-side dispatch failures.
- Present readiness rejection in the UI as job preparation rejected, not as a
  server crash.

### F-005 - Local job and artifact paths need a bounded filesystem contract

The web routes will read job directories, relative log references such as
`logs/stdout.log`, and optional raw-result artifacts. A route that accepts
arbitrary job IDs or paths can escape the intended local job store.

Required actions:

- Configure or derive one local CFD jobs root for the web server process.
- Validate job IDs as names, not paths.
- Resolve job, log, and raw-result paths before reading them.
- Reject any resolved path outside the jobs root or selected job directory.
- Define deterministic content behavior for logs and raw results: content type,
  missing-artifact response, and either a size/truncation policy or an explicit
  first-slice size limit.

### F-006 - The first mesh-package ingress contract must stay local and explicit

RFC 0018 leaves mesh-package creation ownership open. For this workflow, the
web CFD slice should not silently create, promote, or relabel mesh packages.

Required actions:

- Accept an explicit server-local `mesh_package_ref` or equivalent local
  reference for `POST /api/cfd/jobs`.
- Prepare against that package through the existing dispatch contract.
- Document that web-side mesh-package creation remains separate follow-up
  work.
- Do not upgrade open generated packages to `cfd_ready`; readiness remains
  whatever the mesh package manifest reports under its selected profile.

### F-007 - Tests and docs must move with the route slice

Existing tests cover RFC 0008 route registration and RFC 0015 local dispatch
separately. Workflow 0029 needs coverage across the web boundary while keeping
browser smoke optional for default CI.

Required actions:

- Add headless tests for route registration and handler payloads for
  `/api/cfd/*`.
- Cover profile listing, job creation, readiness rejection for the watertight
  profile, unavailable run state, mock failed-command state, status readback,
  log retrieval, raw-result absence, structured error payloads, and path
  traversal rejection.
- Cover browser-visible wording for raw/unvalidated CFD output and
  unavailable/failed states. Optional Playwright smoke may remain optional.
- Update user-facing docs, changelog, and RFC/workflow status text when the
  implementation lands. The docs must state that the web CFD slice is local
  filesystem dispatch only and remains raw/unvalidated.

## Implementation Scope

Safe now:

- Implement `/api/cfd/*` as a thin local adapter over the existing
  `kayakgen.eval.cfd.jobs` APIs and records.
- Add a server-local CFD jobs root and path-bounded artifact readers.
- Add a compact web UI panel/tab for profile selection, local mesh package
  reference, job preparation, run/status refresh, logs, raw-result links, and
  terminal error states.
- Keep local `POST /api/cfd/jobs/{job_id}/run` synchronous if simpler, but
  return the persisted `CfdRunRecord` and preserve recorded state transitions.
- Render raw/unvalidated warnings consistently in API payloads, UI copy, and
  tests.
- Leave RFC 0008 `/api/jobs` stubs truthful unless compatibility requires
  documented redirect/reservation behavior.

Do not implement in this workflow:

- Hosted workers, remote queues, multi-user persistence, accounts,
  authentication, billing, quotas, or cost controls.
- Cancellation guarantees, live progress guarantees, server-sent events, or
  background scheduling infrastructure.
- Real OpenFOAM, SU2, Docker/container, RANS, or hosted solver adapters.
- Any claim that a real solver succeeded, that outputs are calibrated or
  validated, or that CFD results are final design fitness signals.
- Automatic mesh-package creation, watertight promotion, volume meshing, closed
  hull-plus-deck construction, or `cfd_ready` relabeling.
- Blending CFD artifacts into hydrostatics, analytical resistance rows,
  comparison objectives, Pareto defaults, or calibrated drag summaries.
- Arbitrary file serving from user-provided paths.

## Deferred Items

- Hosted CFD workers and remote queue operation.
- Authentication, authorization, billing, quotas, and multi-user persistence.
- Cancellation semantics, live progress streaming, and durable scheduler
  guarantees.
- Real solver adapters and real solver success claims.
- Watertight volume meshes, closed-volume geometry, and any current generated
  package reaching `cfd_ready`.
- Normalized physical CFD outputs, calibrated resistance, validated drag, and
  final design fitness claims.
- Web-side mesh-package creation and any broader browser parity beyond the
  compact local CFD job panel.

## Reviewer Finding Map

- F-001 consolidates T-001.
- F-002 consolidates T-002 and O-006.
- F-003 consolidates T-003, B-001, B-002, B-004, and B-005.
- F-004 consolidates B-003 and O-002.
- F-005 consolidates O-001 and O-004.
- F-006 consolidates O-003.
- F-007 consolidates T-004 and O-005.
- T-005 is preserved in the implementation scope and deferred items.
