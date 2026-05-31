# RFC 0053: Turning and Edged-Waterline Metrics

Status: landed TurningMetrics + opt-in --turning flag + sweep evaluator
Date: 2026-05-16
Context: Phase 8 item 4 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Today's
hydrostatics evaluator computes upright displaced volume and
waterplane area. Sea-kayak and surfski designers also care about
turning behavior — and turning is dominated by the *edged*
waterline length and lateral-plane shift, neither of which is
exposed by the upright surface.

## Problem

Asking "does this hull turn well when edged?" requires:

- The effective waterline length when the hull is heeled
  (rounding/sharpening at the bow as the edged waterline lifts the
  fine entry out of the water).
- The lateral-plane shift between upright and edged: how much the
  centre of lateral resistance moves forward/aft when the paddler
  edges.
- A yaw / turning proxy, ideally derived from the edged waterline
  length and the parallel-mid-body fraction.
- A rocker-derived maneuverability signal (the rocker integral
  along the waterline, weighted by depth at each station).

None of these are surfaced today.

## Goals

- Add an evaluator that takes a `Hull` + heel angle and computes the
  edged waterline length, lateral-plane shift, a derived turning
  proxy, and a rocker-weighted maneuverability signal.
- Surface these on a new `TurningMetrics` block of
  `EvaluationResult` (additive; default `None`).
- Add a new opt-in CLI flag on `kayakgen evaluate` (and a sweep
  evaluator flag) to compute them.

## Non-Goals

- No claim that the turning proxy predicts on-water turning
  behavior; it is a geometric proxy, labelled as such.
- No dynamic analysis (no acceleration / yaw rate / radius of turn).
- No active paddler modeling.

## Proposal

### Evaluator surface

```python
class TurningMetrics(BaseModel):
    schema_version: Literal["1"] = "1"
    heel_deg: float
    edged_waterline_length_m: float
    upright_waterline_length_m: float
    lateral_plane_shift_m: float
    rocker_weighted_maneuverability_signal: float
    method: Literal["geometric_proxy_v1"] = "geometric_proxy_v1"
    notes: list[str] = Field(default_factory=list)
```

Computed by integrating the heeled cross-sections against the still
waterline and the upright cross-sections against the same waterline.

### CLI surface

`kayakgen evaluate <hull> --turning --heel-deg 8`
emits the `turning_metrics` block in the result JSON.

`evaluators.turning_metrics: bool = False` on `SweepSpec.evaluators`
mirrors the same opt-in for sweep candidates.

## Acceptance Criteria

- For a symmetric reference hull (e.g. default `Hull()`), the edged
  waterline length at heel=0 deg equals the upright waterline
  length exactly.
- For heel angles from 0-30 deg in 5 deg steps, the edged waterline
  length decreases monotonically.
- The lateral plane shift at heel=0 deg is zero (by symmetry).
- Default `kayakgen evaluate` output stays byte-stable when
  `--turning` is absent.

## Open Questions

- What heel-angle range is most useful for sea kayaks vs surfskis?
  Default `heel_deg=8` (typical edged-paddling angle).
- Should the turning proxy be normalised (dimensionless) or carry
  its raw units (m³ or similar)?
- Does the rocker-weighted maneuverability signal need to be split
  bow vs stern?

## Implementation Path

1. Define `TurningMetrics` in `kayakgen/eval/contract.py`.
2. Land `kayakgen/eval/turning.py` with the geometric integrators.
3. Add the `--turning` flag to `kayakgen evaluate`.
4. Add the sweep `evaluators.turning_metrics` flag.
5. Tests on the parametrized hull matrix.
6. Update `docs/USER_GUIDE.md`.

## Domain Modeling

`TurningMetrics` is a value object attached additively to
`EvaluationResult`. The turning evaluator is a domain service over
the Hull aggregate. No new aggregate, no new claim state, no new
readiness gate.
