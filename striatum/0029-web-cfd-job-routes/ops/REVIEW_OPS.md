author: operator [self-declared: operator-0029-ops]

# Workflow 0029 Ops And Test Review

Verdict intent: accept_with_findings

## Scope

This review covers implementation and test risks for adding web CFD routes over
the existing local dispatch contract. The main operational risks are
filesystem boundaries, deterministic JSON payloads, route error handling, and
coverage that does not require external solver binaries.

## Findings

### O-001 - Job and artifact paths need an explicit filesystem boundary

RFC 0018's routes include job status, logs, and raw-result retrieval. Existing
local dispatch records store relative log paths such as `logs/stdout.log` and
optional raw-result references. A naive route that accepts arbitrary job IDs,
job directories, or log paths can escape the intended local job store.

Required action: configure or derive a single local CFD jobs root for web
routes, validate job IDs as names rather than paths, resolve every requested
job/log/raw-result path, and reject anything outside the jobs root or selected
job directory. Cover traversal attempts in tests.

### O-002 - Bad payloads and missing records need stable structured errors

Current web REST helpers return controlled validation payloads for hull state,
but CFD routes do not exist yet. `CfdDispatchError` messages are useful but
should not leak raw tracebacks or produce inconsistent HTML errors.

Required action: convert CFD dispatch, validation, unknown profile, missing
job, missing run record, missing log, and missing raw-result failures into
JSON errors with stable `error` kinds and appropriate HTTP statuses. Preserve
useful messages while keeping responses deterministic.

### O-003 - The first route slice must define how mesh packages enter the web boundary

RFC 0018 leaves open whether mesh-package creation is owned by existing mesh
APIs, a new preparation route, or a user-provided package path. The current CLI
expects an existing mesh package directory. Tests need one concrete first
contract.

Required action: for this workflow, keep the implementation conservative:
accept a server-local `mesh_package_ref` path or equivalent explicit local
reference, prepare against it through existing dispatch code, and document that
web-side mesh-package creation remains separate. Do not silently generate or
promote a new package unless the ledger explicitly accepts that expansion.

### O-004 - Log and raw-result serving needs bounded content behavior

Solver logs can grow large once real adapters arrive, and raw-result artifacts
may be absent, malformed, or not JSON. Even for the current mock adapter, the
route behavior should be deterministic.

Required action: implement log/raw-result routes with clear content types,
missing-artifact responses, and a size/truncation policy or explicit first
slice limit. Tests should cover present stdout/stderr logs, absent raw results
for unavailable/failed states, and malformed or unexpected raw-result content
if a future fixture writes it.

### O-005 - Tests should exercise handlers, not only route registration

`tests/test_web.py` currently checks route registration for `/api/jobs` stubs.
`tests/test_cfd_jobs.py` covers the local job layer. The web CFD slice needs
integration-style coverage joining those two surfaces.

Required action: add focused tests for profile listing, job creation,
readiness rejection for the watertight profile, unavailable run state,
mock failed-command state, status readback, logs, raw-result absence, and path
traversal rejection. Browser smoke can remain optional, but headless tests
must be sufficient for default CI.

### O-006 - Synchronous local run is acceptable only if status transitions stay honest

RFC 0018 allows the first route implementation to call local dispatch
synchronously. That avoids queue infrastructure, but it must still report the
same run states as the local job layer rather than hiding transient or terminal
states.

Required action: `POST /api/cfd/jobs/{job_id}/run` may synchronously call
`run_cfd_job()` for the local slice, but the returned payload must be the
resulting `CfdRunRecord` and must preserve `queued`, `running`, `failed`,
`unavailable`, or `succeeded` semantics as recorded on disk.

## Ops/Test Summary

Workflow 0029 is implementable without external solvers if it treats web routes
as a thin, bounded, deterministic adapter over the local CFD job store. The
implementation should prioritize path safety, structured errors, and tests over
any broader hosted-worker or real-solver behavior.
