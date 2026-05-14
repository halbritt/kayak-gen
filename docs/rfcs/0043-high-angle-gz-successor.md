# RFC 0043: High-Angle GZ Successor

Status: proposed
Date: 2026-05-14
Context: successor to RFC 0020 and RFC 0024, using the generated closed-body
handoff work from RFC 0022 and preserving the unavailable-result boundary for
real kayak secondary-stability claims.
Disposition of predecessors: RFC 0043 supersedes the remaining proposed
implementation scope of RFC 0020 where that scope could imply premature real
kayak `GZ` output. It preserves RFC 0024 as the landed structured-unavailable
handoff boundary and narrows the next step to an explicit heeled-integration
design gate.

## Problem

The project now has a clearer evidence spine than RFC 0020 had when it was
written: explicit synthetic closed-volume diagnostics, generated closed-body
construction, self-intersection diagnostics, and a structured high-angle GZ
handoff that keeps unsupported results unavailable. That still does not mean
real kayak high-angle `GZ` has landed.

The remaining gap is not a UI or serialization gap. It is the hydrostatic model
for heeled volume integration over the accepted generated body: heel transform,
sinkage and trim policy, displacement residuals, waterplane clipping, CG
conventions, deck/flooding assumptions, and warning behavior. Without an RFC
successor that narrows those choices, an implementation could accidentally turn
fixture math, open display surfaces, or partially diagnosed generated bodies
into numeric secondary-stability claims.

## Goals

- Scope the next high-angle `GZ` work without claiming that a real generated
  kayak curve is currently available.
- Preserve RFC 0024's hard gate: only a generated kayak closed body with
  passing diagnostics can ever emit real kayak `GZ` values.
- Define the modeling decisions that must be made before heeled volume
  integration is implemented.
- Keep synthetic bodies available for internal math tests only, with
  `fixture_only` labeling and no user-facing stability claims.
- Require unavailable results, warnings, and `None` summary metrics whenever
  evidence or model support is missing.
- Make future CLI, sweep, comparison, desktop, and web surfaces consume the same
  result contract once the model lands.

## Non-Goals

- No runtime implementation in this RFC.
- No accepted heeled-volume integration algorithm or numerical tolerance is
  declared here.
- No delivered `GZ`, `GZ_max`, angle-of-maximum-GZ, range-of-positive-stability,
  capsize range, or secondary-stability value is claimed.
- No dynamic capsize, bracing, rolling, waves, surf, flooding progression,
  re-entry, or active paddler response model.
- No final prediction, seaworthiness, safety, or design-fitness claim.
- No validation against measured kayak stability tests.
- No promotion of open display meshes, open CFD packages, or synthetic fixtures
  to real kayak stability evidence.

## Dependencies

- RFC 0011 for load-case mass and KG conventions.
- RFC 0014 for upright trim fields and the reserved `GZCurve` boundary.
- RFC 0016, RFC 0021, and RFC 0022 for closed-volume and generated-body
  diagnostics.
- RFC 0024 for generated-body high-angle GZ handoff gates and fixture-only
  labeling.
- RFC 0023 only as a related evidence model: CFD volume-mesh readiness does not
  by itself authorize stability output.

## Proposal

This successor keeps RFC 0024's unavailable boundary in place and narrows the
next implementation to an evidence-first `GZ` evaluator design. A future
workflow may implement real generated-body high-angle `GZ` only after it records
and tests all of the following model choices:

- the generated-body profile accepted for stability use, including body type,
  closure policy, body diagnostic refs, self-intersection status, source hull
  hash, coordinate system, units, and tolerances;
- the heel-angle grid policy, with default and caller-supplied grids echoed in
  results;
- the heel transform convention and sign convention for reported righting arm;
- whether upright trim is held fixed, trim is solved independently at each
  heel, or both modes are supported under explicit names;
- the sinkage/displacement equilibrium solve at each heel point, including
  residual definitions, convergence status, iteration limits, and failure
  warnings;
- the CG convention for hull, paddler, and cargo, including whether each CG is
  fixed to hull coordinates or world coordinates;
- waterline clipping and displaced-volume integration semantics for the heeled
  generated body;
- deck immersion, cockpit opening, and flooding assumptions, represented as
  assumptions and warnings rather than hidden design facts.

Until those choices are accepted and implemented, generated kayak results remain
unavailable. The evaluator boundary may continue to return structured
unavailable records, but it must not fill `gz_m`, `righting_moment_nm`,
`max_gz_m`, `heel_at_max_gz_deg`, `range_positive_stability_deg`, or
`area_under_positive_gz_m_deg` with placeholder, fixture-derived, or heuristic
values.

## Result Contract

The successor keeps the RFC 0024 shape as the target read model:

```python
GZCurve(
    body_ref: str | None,
    body_type: str | None,
    body_diagnostic_ref: str | None,
    heel_grid_deg: list[float],
    heel_deg: list[float],
    gz_m: list[float],
    righting_moment_nm: list[float],
    max_gz_m: float | None,
    heel_at_max_gz_deg: float | None,
    range_positive_stability_deg: float | None,
    area_under_positive_gz_m_deg: float | None,
    assumptions: list[str],
    warnings: list[str],
)
```

Unavailable real-kayak results keep computed arrays empty and summary metrics
`None`. If a later implementation adds per-heel status, it must be additive and
must distinguish successful heel points from missing, failed, or skipped points.

Synthetic explicit bodies may produce internal fixture records only when the
record is marked `fixture_only`. Fixture records can test sign conventions,
summary-metric derivation, and convergence plumbing, but they are not valid
inputs for sweep ranking, comparison summaries, user-facing UI stability
claims, or real kayak documentation.

## Claim Gates

A real generated kayak `GZCurve` may be emitted only when all gates pass for
the same hull and body evidence:

- body type is a generated kayak stability body, not an explicit synthetic
  fixture;
- body diagnostics report a closed generated body with positive signed volume,
  zero blocking boundary and nonmanifold conditions, and no blocking
  self-intersections under recorded tolerances;
- `source_hull_hash`, coordinate system, units, closure policy, and diagnostic
  refs match the evaluated hull;
- the accepted heeled integration model is available for that body profile;
- every computed heel point records convergence metadata or a warning;
- summary metrics are derived only from computed `gz_m` values.

If any gate fails, the result is unavailable. Acceptable warnings include
`generated_closed_body_not_available`, `fixture_only_body_not_user_facing`,
`heeled_integration_model_not_available`, `heel_point_non_converged`,
`deck_immersion_assumption`, `flooding_not_modeled`, and more specific
diagnostic-derived reasons.

## Acceptance Criteria

- This RFC lands as documentation only, with no runtime behavior change.
- This RFC is indexed as a successor design gate only; it does not authorize
  emitting `GZ`, `GZ_max`, range-of-positive-stability, capsize-range, or other
  secondary-stability metrics before the heeled integration model is accepted.
- Existing unavailable high-angle GZ behavior remains truthful: no real kayak
  secondary-stability arrays or summary metrics are emitted without passing
  generated-body evidence and an accepted heeled integration model.
- The future implementation workflow has an explicit checklist for body
  evidence, heel grid, trim policy, CG convention, displacement solve,
  waterline clipping, deck/flooding assumptions, and warning behavior.
- Open display meshes, open mesh packages, CFD package directories, and
  synthetic closed-volume fixtures remain insufficient for real kayak GZ
  output.
- Fixture-only math tests, if added later, cannot satisfy user-facing stability
  claims or comparison ranking.
- CLI, sweep, comparison, desktop, and web surfaces continue to hide or warn on
  unavailable secondary-stability metrics until the accepted model is
  implemented and tested.

## Open Questions

- Should the first supported stability body include the full deck, a capped
  hull-only body, or a stability-specific body distinct from CFD profiles?
- Should the first implementation hold upright trim fixed at heel, solve trim
  per heel point, or expose both as explicitly named modes?
- Should paddler and cargo CG be fixed to the hull, fixed in world coordinates,
  or selectable per load case?
- What heel grid should be canonical for comparison records: `0..90` degrees,
  a wider range, or user-specified grids with recommended defaults?
- Should range of positive stability be grid-bounded only, or interpolated
  between computed points after sign crossing?
- What minimal analytic or synthetic fixtures are acceptable for numerical
  regression without leaking into real kayak claims?
- What measured stability sources, if any, are licensed and relevant enough for
  a later validation RFC?

## Implementation Path

1. Accept or amend this successor RFC as the scope boundary for high-angle GZ
   work.
2. Draft the heeled integration design decision for body profile, trim policy,
   CG convention, waterline clipping, residuals, tolerances, and warnings.
3. Add only fixture-only math tests until the generated-body evidence and
   integration model are both accepted.
4. Implement the generated-body evaluator behind the RFC 0024 gates, returning
   unavailable records whenever evidence or convergence is missing.
5. Wire CLI, sweep, comparison, desktop, and web display only after result JSON
   proves assumptions, warnings, body refs, and summary derivation are stable.
6. Reserve measured validation, user-facing confidence wording, and any final
   prediction language for a separate validation RFC.

## Domain Modeling

`GZCurve` remains an evaluator read model derived from a `Hull`, `LoadCase`,
and generated `ClosedVolumeBody`. The heeled integration model is a domain
service boundary that must be explicit before values are emitted. Secondary
stability summaries are derived read-model fields, not authored hull state and
not safety or capsize guarantees.
