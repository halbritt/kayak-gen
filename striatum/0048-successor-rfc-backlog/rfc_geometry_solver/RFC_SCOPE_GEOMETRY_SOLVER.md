---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: rfc-scoper-codex-gpt-5.5-009
kind: synthesis
run: run_c1de081e76f14cd1a81194e306338ac2
session: sess_52c24de0141e476d94fb067aae3d9357
job: job_run_c1de081e76f14cd1a81194e306338ac2_rfc_scope_geometry_solver
lease: lease_b1c2182cd28b426da4c011aef3ccbe1d
date: 2026-05-14

# RFC Scope - Geometry Solver Successors

## Summary

Drafted proposed RFC 0040 and RFC 0041 as documentation-only successor scope
for the closed-volume/solver-readiness and real CFD adapter backlog.

RFC 0040 consolidates the evidence ladder from open inspection surfaces through
synthetic diagnostics, generated closed bodies, volume-mesh handoff evidence,
and solver dispatch prerequisites. It keeps generated closed bodies below
watertight solver readiness until matching volume-mesh evidence exists.

RFC 0041 scopes the first external-solver adapter after the
`fixture-local-command` adapter. It requires a named solver decision,
dependency checks, deterministic case templates, raw-result parsing, mesh
profile gates, and CI-friendly fixture coverage while keeping every real-solver
output `raw_unvalidated`.

No runtime behavior was implemented.

## Files Changed

- `docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md` - new proposed
  successor RFC for closed-volume and solver-readiness evidence ordering.
- `docs/rfcs/0041-real-cfd-adapter-successor.md` - new proposed successor RFC
  for the first real external CFD adapter slice.
- `striatum/0048-successor-rfc-backlog/rfc_geometry_solver/RFC_SCOPE_GEOMETRY_SOLVER.md`
  - this synthesis artifact.

## Open Questions

- Which volume mesher, if any, should become the first production
  implementation target after fixture diagnostics prove the contract?
- Should the first external adapter wait for watertight-solid evidence, or may
  a documented open-surface solver mode be accepted as a raw incremental path?
- Which solver target has the lowest maintenance cost while still consuming a
  mesh profile the project can honestly produce?
- What minimum volume-mesh quality metrics and thresholds are meaningful before
  calibration or validation data exists?
- Should optional installed-solver smoke tests live in the normal suite with
  skips or in a separate integration-test profile?

## No-Claims Boundary

- Open hull/deck STLs and default mesh packages remain inspection/open-surface
  artifacts, not closed-volume or solver-ready evidence.
- Synthetic closed-volume fixtures remain diagnostic fixtures, not generated
  kayak CFD or stability evidence.
- Generated closed bodies may support closed-volume evaluation, but they do not
  imply `cfd_ready` without matching volume-mesh handoff evidence.
- The adapter RFC does not claim OpenFOAM, SU2, Docker/container execution,
  hosted workers, production volume meshing, calibrated CFD, final prediction,
  final design fitness, or watertight readiness.
- Solver outputs remain raw and unvalidated unless a separate accepted
  validation or calibration RFC changes the claim gate.

## Verification

- No whitespace warnings:
  `git diff --check --no-index /dev/null docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md`
  (exit 1 expected for a new-file diff; no output).
- No whitespace warnings:
  `git diff --check --no-index /dev/null docs/rfcs/0041-real-cfd-adapter-successor.md`
  (exit 1 expected for a new-file diff; no output).
- No whitespace warnings:
  `git diff --check --no-index /dev/null striatum/0048-successor-rfc-backlog/rfc_geometry_solver/RFC_SCOPE_GEOMETRY_SOLVER.md`
  (exit 1 expected for a new-file diff; no output).
