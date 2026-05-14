---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: rfc-scoper-codex-gpt-5.5-008
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: rfc_scope_calibration_stability
run: run_c1de081e76f14cd1a81194e306338ac2
session: sess_f6ce075cb1db4db5b6f137e75b248219
job: job_run_c1de081e76f14cd1a81194e306338ac2_rfc_scope_calibration_stability
lease: lease_e5f17310e6784ecbbf32e4f7b341adc9
date: 2026-05-14

# RFC Scope - Calibration And Stability Successors

## Summary

Drafted proposed RFC 0042 and RFC 0043 as documentation-only successor
scopes. RFC 0042 narrows resistance calibration work to source review,
provenance, fixture promotion, and RFC 0025/0027 claim gates before any
calibrated resistance wording can appear. RFC 0043 keeps high-angle `GZ`
unavailable until generated-body evidence and an accepted heeled integration
model exist.

No runtime behavior, tests, package code, README index, changelog, or
`.striatum/` files were changed.

## Files Changed

- `docs/rfcs/0042-resistance-calibration-fixture-successor.md` - new proposed
  successor RFC for source-review and fixture-promotion scope.
- `docs/rfcs/0043-high-angle-gz-successor.md` - new proposed successor RFC for
  high-angle `GZ` model scoping and unavailable-result gates.
- `striatum/0048-successor-rfc-backlog/rfc_calibration_stability/RFC_SCOPE_CALIBRATION_STABILITY.md`
  - this synthesis artifact.

## Source Findings

- Current user-facing docs still describe resistance as an uncalibrated
  comparative ITTC/Michell screening filter.
- RFC 0027 already defines the calibrated-prediction gate; successor work
  should not create a parallel claim helper or promote validation fixtures into
  calibration evidence.
- Current user-facing docs keep high-angle `GZ` unavailable and require real
  heeled integration over generated closed-body evidence before secondary
  stability metrics can appear.
- RFC 0024 already bars open surfaces, CFD package directories, and synthetic
  fixtures from user-facing kayak secondary-stability claims.

## Open Questions

- Which measured resistance source should receive the first full source-review
  packet, and can any licensable kayak-envelope dataset support calibration
  fixture promotion?
- What geometry, load, speed/Froude, uncertainty, and metric evidence is
  sufficient before a resistance fixture can become calibration evidence?
- What stability body, trim policy, CG convention, heel grid, waterline
  clipping, residual tolerance, and deck/flooding warning model should the
  first high-angle `GZ` implementation use?
- What synthetic or analytic fixtures are acceptable for numerical regression
  while remaining excluded from user-facing kayak stability claims?

## Verification

- Passed: `rg -n "[[:blank:]]$" docs/rfcs/0042-resistance-calibration-fixture-successor.md docs/rfcs/0043-high-angle-gz-successor.md striatum/0048-successor-rfc-backlog/rfc_calibration_stability/RFC_SCOPE_CALIBRATION_STABILITY.md`
  returned no trailing-whitespace matches.
- Passed: `git diff --check -- docs/rfcs/0042-resistance-calibration-fixture-successor.md docs/rfcs/0043-high-angle-gz-successor.md`.
- Passed: `git diff --check -- striatum/0048-successor-rfc-backlog/rfc_calibration_stability/RFC_SCOPE_CALIBRATION_STABILITY.md`.
