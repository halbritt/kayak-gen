# Findings ledger - watertight solid mesh profile

author: operator [self-declared: operator-ledger]
run: run_877488bcf83244479df1d95d7b420a65
job: findings_ledger
date: 2026-05-13

## Gate result

Implement a named watertight-required solver profile and package-readiness
boundary. Do not implement watertight geometry generation in this workflow.

Current hull/deck packages must remain below `cfd_ready`.

## Stats

- Review artifacts: 3.
- Verdicts: 3 `accept_with_findings`.
- Safe-now findings: 4.
- Deferred findings: 2.

## Deduplicated findings

### F-001 - Add a named watertight-required profile

Source lanes: T-001, T-002, D-003, O-001.

Type: actionable-now.

Add a stable profile constructor for a future watertight solid solver profile.
The profile should require watertightness, accept hull/deck source parts, reject
open waterline boundaries, and provide a stable profile name that RFC 0015
dispatch can later reference.

### F-002 - Keep current packages blocked below `cfd_ready`

Source lanes: T-003, D-001, O-002.

Type: actionable-now.

When the watertight profile is selected for the current generated hull/deck
surfaces, readiness must remain below `cfd_ready` with explicit blockers for
boundary/open-volume state and the absence of a closed combined solid writer.

### F-003 - Expose profile selection without changing defaults

Source lanes: O-001, O-003.

Type: actionable-now.

Preserve the default open wetted-surface package behavior. Add a small CLI
selector for the watertight profile and tests that assert the manifest records
the selected profile.

### F-004 - Update docs/status without overclaiming

Source lanes: T-003.

Type: actionable-now.

Update RFC 0010 and the RFC index to say a watertight-required profile boundary
exists, but current generated packages remain blocked and not `cfd_ready`.

### F-005 - Do not implement end caps or combined solid closure

Source lanes: D-001, D-002.

Type: deferred.

RFC 0004 still defers exact end-cap and watertight hull-plus-deck semantics.
Do not synthesize closure polygons or change geometry goldens in this workflow.

### F-006 - Do not integrate solver dispatch yet

Source lanes: T-002, O-001.

Type: deferred.

This workflow may create a profile boundary that dispatch can reference, but
CFD job specs and adapters remain workflow 0025.

## Implementation guidance

Safe-now:

- add `watertight_solid_profile()` or equivalent;
- ensure `write_mesh_package(..., solver_profile=watertight_solid_profile())`
  writes a manifest with blocked readiness;
- add a CLI profile selector if low-risk;
- add focused mesh-package/CLI tests;
- update RFC/status docs and operator report.

Do not implement:

- new hull/deck mesh geometry;
- end caps;
- combined watertight solids;
- `cfd_ready` success for current generated packages;
- solver dispatch or solver adapters.
