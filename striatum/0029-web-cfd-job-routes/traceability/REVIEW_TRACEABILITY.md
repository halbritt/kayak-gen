author: operator [self-declared: operator-0029-traceability]

# Workflow 0029 Traceability Review

Verdict intent: accept_with_findings

## Scope

This review maps RFC 0008's reserved heavy-CFD seam, RFC 0015's landed local
dispatch contract, and RFC 0018's proposed web CFD routes onto the current web
frontend. Current implementation still exposes only the older `/api/jobs`
reserved stubs returning 501 from `kayakgen.ui.web.controllers`, while CFD job
records and solver profiles are available through `kayakgen.eval.cfd.jobs` and
the CLI.

## Findings

### T-001 - RFC 0018 route shape is not implemented by the existing RFC 0008 stubs

RFC 0008 reserved `POST /api/jobs` and `GET /api/jobs/{id}` as future heavy-CFD
stubs. RFC 0018 narrows the accepted slice to CFD-specific routes:
`GET /api/cfd/profiles`, `POST /api/cfd/jobs`, `GET /api/cfd/jobs/{job_id}`,
`POST /api/cfd/jobs/{job_id}/run`, `GET /api/cfd/jobs/{job_id}/logs`, and
`GET /api/cfd/jobs/{job_id}/raw-result`.

Current `register_rest_routes()` only registers `/api/jobs` stubs that return
`job_stub_payload()` with status 501. That is still faithful to RFC 0008, but
it does not satisfy RFC 0018.

Required action: implement the RFC 0018 `/api/cfd/*` route family as the
accepted web CFD surface. Keep any legacy `/api/jobs` compatibility behavior
explicitly reserved or redirect-only; do not treat the old two-route stub as
completion of the CFD route contract.

### T-002 - Web routes must reuse the RFC 0015 local dispatch records

RFC 0015 landed `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, local job
directories, readiness gating, unavailable profiles, and mock failed-command
behavior. RFC 0018 says the web API is an application boundary over those read
models, not a separate job aggregate.

The current web controller module does not import or wrap the CFD job APIs. A
first implementation that invents a parallel in-memory status model would
break traceability to RFC 0015.

Required action: route payloads must be built from the existing CFD job
functions and models: profile listing from the built-in solver profiles, job
creation through `prepare_cfd_job()` or the same lower-level contract, status
through `load_cfd_run_record()`, and run transitions through `run_cfd_job()`.
Responses should include `result_semantics: raw_unvalidated` wherever the
underlying records carry it.

### T-003 - Browser job states are still absent from the Trame UI

RFC 0008 reserved a job-queued CFD tier, and RFC 0018 requires browser-visible
profiles, job creation, status, run, logs, raw results, timestamps, and error
details. The current Trame UI has hull sliders, metrics, analysis, comparison
inspection, and export/share controls, but no CFD job panel or state fields.

Required action: add a compact CFD job view that exposes solver profiles, mesh
package/job inputs, prepare/run actions, status, timestamps, error
kind/message, logs, and raw-result links. The UI may remain local-filesystem
only, but it must visibly distinguish queued, running, succeeded, failed, and
unavailable states.

### T-004 - Tests and docs must move with the route slice

Current web tests assert that `/api/jobs` stubs are registered and that
`job_stub_payload()` starts with "heavy CFD". CFD dispatch tests cover CLI/local
records, but no tests exercise web profile listing, web job creation, readiness
rejection, unavailable state, failed state, log/raw-result lookup, or browser
wording.

Required action: update tests to cover the new `/api/cfd/*` route registration
and handler payloads over temporary mesh packages and local job directories.
Update `docs/USER_GUIDE.md`, RFC 0018 status, and the changelog to state that
the landed web slice is local dispatch only and still raw/unvalidated.

### T-005 - Hosted workers, real solvers, cancellation, auth, and validation remain explicit deferrals

RFC 0015 and RFC 0018 both reject claims of real solver availability or
validated CFD output. The accepted first web route slice can prepare local job
records and run unavailable/mock adapters, but cannot imply hosted execution,
background scheduling guarantees, real OpenFOAM/SU2 success, authentication,
or calibrated design fitness.

Required action: route responses, UI labels, docs, and tests must keep these
deferrals visible. Any successful fixture state must be explicitly fixture or
mock-local-command behavior, not evidence of real CFD physics.

## Traceability Summary

Workflow 0029 is ready to implement as a narrow web adapter over the accepted
RFC 0015 local dispatch boundary. The route contract is traceable if it adds
the RFC 0018 `/api/cfd/*` routes, leaves old RFC 0008 job stubs honest, reuses
`CfdJobSpec` and `CfdRunRecord`, and keeps all real-solver and validation work
deferred.
