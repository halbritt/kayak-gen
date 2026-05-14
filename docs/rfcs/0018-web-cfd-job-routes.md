# RFC 0018: Web CFD Job Routes

Status: partial local-web-dispatch
Date: 2026-05-13
Context: builds on RFC 0008 web frontend direction, RFC 0010 mesh packages,
and RFC 0015 local CFD job records.

Implementation note: workflow 0029 landed the first local web route slice on
2026-05-13. The implementation exposes `/api/cfd/*` over server-local
filesystem job records and a compact browser panel. Hosted workers, auth,
cancellation guarantees, real solver adapters, web-side mesh-package creation,
and validated or calibrated CFD claims remain deferred.

## Problem

The web frontend direction reserves CFD job workflows, but current accepted
work is local CLI dispatch only. Users need browser-visible job preparation,
status, and raw-result inspection that reflects the same truth as the CLI:
mesh readiness gates exist, real solver execution may be unavailable, and
outputs are raw unless a later RFC validates them.

Without explicit routes, web work can drift into a separate job model or imply
hosted execution before that infrastructure exists.

## Goals

- Define REST-style routes for CFD profiles, job creation, job status, and raw
  result retrieval.
- Reuse `CfdJobSpec`, `CfdRunRecord`, mesh package manifests, and solver
  profile readiness gates.
- Make unavailable, queued, running, failed, and succeeded states visible in
  the browser.
- Keep raw/unvalidated warnings present in API payloads and UI copy.
- Allow the first implementation to use local filesystem jobs only.

## Non-Goals

- Hosted multi-user queues, authentication, billing, or quotas.
- Browser-based solver execution.
- Real-time cancellation guarantees.
- Claiming that a real CFD adapter exists.
- Replacing CLI job commands.

## Dependencies

- RFC 0008 for the web frontend boundary.
- RFC 0015 for job and run-record schemas.
- RFC 0010 for mesh-package readiness reporting.
- RFC 0017 only when web routes expose a real solver adapter.

## Proposal

Add a web API layer over the existing local job store. The initial route shape:

```text
GET  /api/cfd/profiles
POST /api/cfd/jobs
GET  /api/cfd/jobs/{job_id}
POST /api/cfd/jobs/{job_id}/run
GET  /api/cfd/jobs/{job_id}/logs
GET  /api/cfd/jobs/{job_id}/raw-result
```

`POST /api/cfd/jobs` accepts a hull reference, mesh package reference, solver
profile, speed, density, and viscosity. It returns the same job ID and status
record the CLI would write. Readiness rejection returns a structured error with
the selected profile, required readiness, observed readiness, and relevant
diagnostics.

The UI should show solver profiles, mesh readiness, job state, timestamps,
error kind/message, and links to logs or raw outputs. It must not present raw
CFD output as validated resistance, calibrated drag, or final design fitness.

The first route implementation may call local dispatch synchronously for
`prepare` and `run`. Any later asynchronous worker must preserve the same
payloads.

## Acceptance Criteria

- Routes serialize the same job and run records used by the CLI.
- Mesh readiness rejection is visible as a structured API error.
- Unavailable solver profiles are visible and cannot be mistaken for completed
  runs.
- Browser UI shows raw/unvalidated status for all CFD outputs.
- Tests cover profile listing, job creation, readiness rejection, unavailable
  state, failed state, and successful fixture-state rendering.
- The implementation can run against local filesystem jobs without hosted
  infrastructure.

## Landed Local Slice

The first slice keeps the route layer as an adapter over RFC 0015 records. It
lists built-in local solver profiles, prepares jobs from an explicit
server-local `mesh_package_ref`, reads persisted `CfdJobSpec` and
`CfdRunRecord` files, runs the local adapter synchronously, and returns bounded
log/raw-result artifact wrappers.

Every job, run, log, raw-result, and structured error payload includes
`result_semantics: raw_unvalidated` and the plain warning that CFD results are
raw and unvalidated. The browser panel renders queued, unavailable, failed, and
future succeeded records as local dispatch state, with unavailable and failed
states shown as terminal problem states.

The web server derives one local CFD job root per process, defaulting to
`.kayakgen-web-cfd-jobs` or `KAYAKGEN_WEB_CFD_JOBS_ROOT` when set. Job IDs are
validated as names, and log/raw-result references are resolved inside the
selected job directory before reading.

## Open Questions

- When should `run` move from synchronous local adapter execution to durable
  background scheduling?
- What route should own web-side mesh-package creation: existing mesh APIs or a
  new CFD preparation route?
- How should logs be paged or streamed once real solver adapters can produce
  larger output?
- Should browser state poll job records, use server-sent events, or defer live
  progress until hosted workers exist?

## Implementation Path

- Step 1 - Add API schemas that wrap existing `CfdJobSpec` and `CfdRunRecord`.
- Step 2 - Add profile and job creation routes against local job storage.
- Step 3 - Add status, logs, and raw-result routes with structured errors.
- Step 4 - Add a browser job panel that renders states and warnings.
- Step 5 - Add tests for API payloads and browser-visible status wording.

## Domain Modeling

Web CFD routes are an application boundary over existing CFD job read models.
They do not introduce a new domain aggregate; they expose solver infrastructure
state to browser clients.
