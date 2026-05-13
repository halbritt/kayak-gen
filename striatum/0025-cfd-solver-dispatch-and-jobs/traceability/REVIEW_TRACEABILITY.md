author: operator [self-declared: operator-traceability-review]

# Traceability review - workflow 0025

Verdict intent: accept_with_findings

## Findings

### T-001 - RFC 0015 can land a local dispatch contract without a real solver

RFC 0015's safe-now acceptance criteria are the serializable job spec, run
record, solver profile registry, local filesystem job directory, and CLI
prepare/status/run states. The real OpenFOAM/SU2 adapter choice is still an
open question and must remain deferred.

Required action: implement `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, local
job directory writing, and CLI commands using unavailable/mock adapters only.
Do not integrate or name a real solver as supported.

### T-002 - Dispatch must gate on the selected mesh package profile/readiness

RFC 0010 and workflow 0024 define two relevant mesh profiles:
`open_wetted_surface_resistance_v1` can currently reach
`cfd_surface_candidate`; `watertight_solid_resistance_v1` is intentionally
blocked at `stl_surface` for current packages. RFC 0015 requires refusing mesh
packages below the selected solver profile requirement.

Required action: load `manifest.json` during `cfd prepare`, verify the package
mesh solver profile matches the selected CFD solver profile's required mesh
profile, and reject readiness below the profile's required level with an
actionable error.

### T-003 - CLI/status wording must not imply validated CFD results

RFC 0008 reserves web job states and RFC 0015 requires consistent pending,
running, succeeded, failed, and unavailable states. RFC 0012 requires keeping
raw solver output separate from calibrated/validated resistance claims.

Required action: have CLI status output include the run state and a raw,
unvalidated-results warning. The docs/RFC status update must say the landed
slice exercises local state transitions only, not validated CFD.

### T-004 - Real solver adapter work remains out of scope

The first external solver, volume meshing, residual normalization, hosted
queueing, cancellation, and web job routes are not required to make RFC 0015's
local contract testable.

Required action: defer real solver adapters, remote execution, normalized force
records, and web route implementation. Preserve the adapter boundary so those
can be added later.

### T-005 - Status documents must match the implementation boundary

If the workflow lands, RFC 0015 and the RFC index should move from proposed to
a partial local-dispatch status only if tests prove the job/run contract and
CLI states. Any remaining solver or web work should be listed explicitly.

Required action: update RFC 0015, `docs/rfcs/README.md`, and the workflow
operator reports after implementation with the actual verification results and
remaining deferrals.
