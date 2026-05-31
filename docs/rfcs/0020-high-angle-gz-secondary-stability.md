# RFC 0020: High-Angle GZ and Secondary Stability

Status: superseded by RFC 0024 + RFC 0043 (closed by RFC 0064)
Date: 2026-05-13
Context: builds on RFC 0014 generalized trim and reserved `GZCurve` contract,
and depends on RFC 0016 closed-volume geometry.

## Problem

Current stability work can report upright equilibrium and trim fields, but it
does not compute high-angle righting arms. Kayak design comparisons need
secondary stability signals such as maximum GZ, angle of maximum GZ, and range
of positive stability, but those values are easy to fake without a named
closed-volume body, load-case assumptions, and warning rules.

## Goals

- Define when a real `GZCurve` may be emitted.
- Compute righting arm over a documented heel-angle grid using a named
  closed-volume body.
- Report secondary-stability metrics with residuals and warnings.
- Preserve fixed-CG and load-case assumptions in every result.
- Keep unsupported cases unavailable instead of returning placeholder curves.

## Non-Goals

- Dynamic capsize modeling, bracing, waves, surf, or re-entry behavior.
- Human biomechanics or active paddler response.
- Validating stability output against measured kayak tests in this RFC.
- Optimizing cockpit or cargo layout automatically.
- Replacing upright trim equilibrium from RFC 0014.

## Dependencies

- RFC 0014 for load cases, trim fields, and the reserved `GZCurve` shape.
- RFC 0016 for the accepted closed-volume body used in heel integration.
- RFC 0011 for load-case mass and KG conventions.

## Proposal

Implement `evaluate_gz_curve(hull, load_case, heel_grid_deg, body_ref)` only
when `body_ref` points to a closed-volume body that passes the accepted
diagnostics. The evaluator heels the body through the requested grid and solves
for displacement equilibrium at each heel angle under the chosen trim policy.

The output follows the reserved RFC 0014 model:

```python
GZCurve(
    heel_deg: list[float],
    gz_m: list[float],
    righting_moment_nm: list[float],
    max_gz_m: float | None,
    heel_at_max_gz_deg: float | None,
    range_positive_stability_deg: float | None,
    assumptions: list[str],
    warnings: list[str],
)
```

Secondary-stability summary fields are derived from the curve:

- `initial_slope_m_per_deg` over a small-angle range;
- `max_gz_m`;
- `heel_at_max_gz_deg`;
- `range_positive_stability_deg`;
- `area_under_positive_gz_m_deg`;
- warnings for flooded/deck-immersion assumptions, non-convergence, or CG model
  limitations.

The first implementation should keep paddler and cargo CG fixed to the hull
unless a human decision selects another convention. Results must state this
assumption directly.

## Acceptance Criteria

- Unsupported hulls return an explicit `closed_volume_body_not_available`
  warning and no synthetic GZ values.
- A supported closed-volume body produces deterministic GZ arrays for a
  declared heel grid.
- Each heel point reports convergence or a warning.
- Secondary-stability metrics are derived from the computed curve, not from
  independent heuristics.
- CLI and JSON outputs include assumptions, warnings, body reference, and heel
  grid metadata.
- Tests cover unavailable body behavior, synthetic symmetric-body behavior,
  non-convergence warnings, and summary-metric derivation.

## Open Questions

- Should the canonical heel grid be `0..90` degrees, `0..180` degrees, or a
  user-specified grid with recommended defaults?
- Should trim be held fixed from upright equilibrium, solved independently at
  each heel, or selectable?
- Should paddler CG stay fixed to the hull, fixed in world coordinates, or be a
  load-case option?
- How should deck immersion, cockpit flooding, and open-cockpit assumptions be
  represented before detailed deck/cockpit modeling exists?

## Implementation Path

- Step 1 - Land RFC 0016 closed-volume geometry and diagnostics.
- Step 2 - Add a `GZCurve` evaluator that refuses unsupported bodies.
- Step 3 - Implement heel-grid equilibrium on synthetic closed-body fixtures.
- Step 4 - Add summary metrics and warning propagation.
- Step 5 - Expose the output through CLI/JSON surfaces only after fixture tests
  prove deterministic behavior.

## Domain Modeling

`GZCurve` is an evaluator read model derived from a `Hull`, `LoadCase`, and
`ClosedVolumeBody`. Secondary-stability metrics are summaries of that read
model, not new hull aggregate state.
