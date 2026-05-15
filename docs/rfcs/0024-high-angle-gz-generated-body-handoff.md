# RFC 0024: High-Angle GZ Generated-Body Handoff

Status: landed structured-unavailable handoff; workflow 0053 added grid-bounded fixture summary semantics
Date: 2026-05-13
Context: narrows RFC 0020 using the generated closed-body boundary from RFC
0016 and the unavailable high-angle GZ contract from RFC 0014.

## Problem

RFC 0020 defines the desired high-angle `GZCurve`, but it leaves room for
synthetic fixtures or open surfaces to be mistaken for real kayak secondary
stability. The current implementation has only synthetic closed-volume
diagnostics and explicitly cannot build generated kayak closed bodies.

The project needs a stricter handoff: high-angle GZ remains unavailable until a
generated closed body passes diagnostics. Synthetic bodies can test geometry and
math, but they cannot claim real kayak stability.

## Goals

- Supersede RFC 0020 where it could allow premature real-kayak GZ output.
- Define the generated-body `body_ref` required for high-angle GZ.
- Record heel grid, load-case assumptions, body diagnostics, warnings, and
  summary metrics in every result.
- Preserve synthetic fixtures for deterministic math tests without letting them
  appear in user-facing kayak comparisons.
- Keep unsupported generated hulls explicitly unavailable.

## Non-Goals

- Validating GZ output against measured kayak tests.
- Modeling dynamic capsize, bracing, waves, surf, or re-entry behavior.
- Modeling flooding, cockpit openings, paddler body volume, or active paddler
  motion beyond recorded assumptions.
- Using solver-specific CFD package directories as the stability body.

## Dependencies

- RFC 0014 load cases, trim fields, and reserved `GZCurve` shape.
- RFC 0016 generated closed-body contract and diagnostics.
- RFC 0020 secondary-stability goals, narrowed by this RFC.
- A generated-body self-intersection diagnostic accepted for stability use.

## Proposal

`evaluate_gz_curve(hull, load_case, heel_grid_deg, body_ref)` may emit real
kayak `GZ` values only when `body_ref` resolves to a generated kayak closed
body whose diagnostics pass:

- generated-body closure readiness;
- positive signed volume under the declared normal orientation;
- zero body-level boundary and nonmanifold edges after raw and tolerance-welded
  checks;
- no blocking self-intersections;
- matching `source_hull_hash`, coordinate system, units, and tolerances;
- stability-compatible closure policy.

If any gate fails, the result is unavailable with warnings and no synthetic GZ
values. The canonical warning is `generated_closed_body_not_available` or a
more specific diagnostic-derived reason.

Synthetic explicit bodies may be used only in tests and internal math fixtures.
Their outputs must be labeled `fixture_only` and must not satisfy generated
kayak `body_ref` requirements, comparison summaries, sweep records, or UI
stability claims.

## Result Contract

The result extends the RFC 0014/0020 `GZCurve` shape with traceability fields:

```python
GZCurve(
    body_ref: str,
    body_type: str,
    body_diagnostic_ref: str,
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

`heel_grid_deg` records the requested grid. `heel_deg` records points actually
computed. Missing heel points must have warnings or per-point status if a later
model adds that field.

Recommended default grid: `0, 5, 10, ..., 90` degrees. CLI/API callers may
request a custom monotonic grid, but the result must echo the grid exactly.

## Assumptions and Warnings

Every real generated-body result must state:

- CG model for paddler, hull, and cargo;
- whether CG is fixed to hull coordinates or world coordinates;
- trim policy at heel, such as fixed upright trim or solved per heel;
- displacement residual tolerance and maximum iterations;
- waterline and deck/flooding assumptions;
- body closure policy and diagnostic refs.

Warnings must be emitted for unsupported body refs, fixture-only bodies,
non-convergence, missing heel points, deck immersion/flooding assumptions,
large residuals, extrapolated range-of-positive-stability estimates, and any
diagnostic mismatch.

## Summary Metrics

Summary metrics are derived only from computed `gz_m` values:

- `max_gz_m`;
- `heel_at_max_gz_deg`;
- `range_positive_stability_deg`;
- `area_under_positive_gz_m_deg`;
- optional `initial_slope_m_per_deg` if the low-angle grid is dense enough.

Unavailable results set summary metrics to `None`.

## Acceptance Criteria

- Open display meshes, open CFD packages, and synthetic closed-volume fixtures
  cannot produce real kayak GZ curves.
- Generated bodies with failed closure or self-intersection diagnostics return
  unavailable status and warnings.
- Passing generated-body fixtures produce deterministic curves over a declared
  heel grid.
- Result JSON includes `body_ref`, body type, diagnostic ref, heel grid,
  assumptions, warnings, and summary metrics.
- Synthetic fixture tests can verify righting-arm math but are marked
  `fixture_only` and excluded from user-facing kayak stability claims.
- CLI/sweep/UI surfaces do not display secondary-stability metrics when the
  generated-body handoff is unavailable.

## Open Questions

- Should default high-angle GZ solve trim independently at each heel or hold
  upright trim fixed for the first implementation?
- Should the first generated stability body include the deck or use a
  stability-specific capped hull body?
- What warning should represent deck immersion before cockpit/flooding modeling
  exists?
- Should `range_positive_stability_deg` interpolate between grid points or
  report grid-bounded estimates only?

## Implementation Path

- Step 1 - Add generated-body `body_ref` validation and fixture-only labeling
  to the GZ evaluator boundary.
- Step 2 - Keep high-angle GZ unavailable for current generated hulls until
  generated closed-body diagnostics pass.
- Step 3 - Implement math fixtures that prove heel-grid and summary-metric
  derivation without claiming real kayak stability.
- Step 4 - Add generated-body GZ only after closure and self-intersection
  diagnostics are accepted.
- Step 5 - Wire CLI/sweep/UI output to hide or warn on unavailable metrics.

## Domain Modeling

`GZCurve` is a read model derived from a `Hull`, `LoadCase`, and generated
`ClosedVolumeBody`. Synthetic bodies are test fixtures for evaluator math, not
domain evidence for kayak stability.
