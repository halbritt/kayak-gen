# Ops review - watertight solid mesh profile

author: operator [self-declared: operator-ops-review]
run: run_877488bcf83244479df1d95d7b420a65
job: review_ops
date: 2026-05-13
verdict: accept_with_findings

## Findings

### O-001 - Add a selectable profile without breaking existing packages

`write_mesh_package()` already accepts an optional `MeshSolverProfile`, but the
CLI always uses the default open profile. A minimal safe change is to add a
named `watertight_solid_profile()` and expose a small CLI option for selecting
`open-wetted-surface` or `watertight-solid`.

Required action: preserve default behavior and manifest shape.

### O-002 - Package readiness should explain watertight rejection

Current `_package_readiness()` returns a generic "watertight solid profile is
not implemented" reason for watertight profiles. The new profile should also
surface boundary/nonmanifold blockers already found in per-part diagnostics and
make it clear that the package writer has not produced a closed combined solid.

Required action: add deterministic warning text and tests.

### O-003 - Focused tests are enough for this slice

Useful focused coverage:

- profile fields for the watertight profile;
- default open package behavior remains `cfd_surface_candidate`;
- watertight-selected package remains below `cfd_ready`;
- CLI writes a manifest with the selected watertight profile;
- diagnostics still catch synthetic open/invalid mesh cases.

Required action: run focused mesh/CLI tests and the full suite.

## Recommendation

Implement the profile selector, readiness warnings, tests, and docs only. Do
not touch mesh generation or STL writing.
