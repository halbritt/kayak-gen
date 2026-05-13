author: operator [self-declared: operator-ledger]

# Findings ledger - workflow 0025

Run id: `run_ac6771c05d58422da72797fa47edf967`
Job: `findings_ledger`

Gate result: proceed with implementation.

## Stats

- Traceability review: 5 findings, verdict `accept_with_findings`.
- Domain review: 5 findings, verdict `accept_with_findings`.
- Ops review: 5 findings, verdict `accept_with_findings`.
- Deduplicated implementation findings: 7.

## Deduplicated findings

### F-001 - Land only the local CFD dispatch contract

Implement serializable job specs, run records, solver profiles, local job
directories, and CLI state commands. Do not add OpenFOAM, SU2, hosted workers,
container execution, cancellation, or cost controls in this workflow.

### F-002 - Enforce mesh package profile and readiness gates during prepare

`cfd prepare` must load the mesh package manifest and reject missing,
malformed, mismatched, or insufficient mesh packages. The open wetted-surface
path may exercise queue states from `cfd_surface_candidate`; the watertight
solid path must require `cfd_ready` and reject current packages.

### F-003 - Preserve raw/unvalidated semantics in records and status text

Job/run records and CLI status output must say results are raw and unvalidated.
Unavailable and mock-failure adapters must not emit calibrated resistance,
validated drag, or comparison-score claims.

### F-004 - Persist reproducible job inputs

Persist mesh manifest reference, solver profile, speed, seawater density,
kinematic viscosity, schema version, and warnings in `job.json`/`run.json`.
Validate positive speed and fluid values.

### F-005 - Use deterministic local job directories

Derive stable job IDs from the mesh package hash/profile/fluid inputs and write
small JSON records that can round-trip in tests. Keep paths relative where the
manifest requires relative artifacts and avoid copying large STL files.

### F-006 - Model unavailable and failed-command states truthfully

The unavailable adapter must write `status: unavailable` without needing any
solver binary. The mock local-command adapter must deliberately fail through a
known local Python executable and write `status: failed`, `error_kind:
command_failed`, error text, and logs.

### F-007 - Update docs and tests around the landed boundary

Add focused model, filesystem, and CLI tests for prepare success, readiness
rejection, unavailable state, failed command state, and run-record parsing.
Update RFC 0015, the RFC index, and operator reports to describe partial local
dispatch only.

## Implementation guidance

Safe now:

- Add `kayakgen.eval.cfd.jobs` or an equivalent `kayakgen.eval.cfd` package for
  job/run/profile/adapter contracts.
- Add `kayakgen cfd prepare/status/run` to the Typer CLI.
- Add unavailable open-surface, unavailable watertight-solid, and mock failing
  command profiles.
- Reject readiness below the selected solver profile's requirement.
- Write deterministic `job.json`, `run.json`, and local log artifacts.
- Run focused CFD/CLI tests, the full suite, `git diff --check`, and
  `striatum --repo . doctor`.

Do not implement:

- Real OpenFOAM, SU2, RANS, hosted, Docker, or remote solver execution.
- Volume meshing, watertight solid geometry, end caps, or current `cfd_ready`
  success.
- Normalized force/residual comparison records before real solver output exists.
- Calibrated, validated, or final resistance claims from unavailable/mock runs.
- Web job route behavior beyond docs/status references unless a later workflow
  accepts that surface explicitly.
