# RFC 0077: Correct depth quadrature and measure resistance screening uncertainty

Status: landed exact linear depth + explicit interval screening policy
Date: 2026-11-07
Context: KAYGEN-15 / W10; D063; RFC0072 / D058; system review kayakgen-system-20261107.

## Problem

The original requested-grid Michell result for owner candidate06 at4.5kn changed
from228243 to34581 to4297N total under refinement. A finite result and agreement
between a pair of grids cannot establish numerical adequacy. Close comparison
also needs achieved error, independently of the caller's tolerance.

## Goals

Distinguish the failing axis experimentally, adopt the smallest supported change,
retain requested-grid values and raw diagnostics, and implement a versioned
numerical screening policy with independently checked controls and achieved
per-point uncertainty. Report unresolved hull comparisons honestly.

## Non-Goals

No physical model, calibration, accepted use, default claim gate, high-angle
objective restriction, or seaworthiness claim is promoted. No universal numerical
error guarantee, new arbitrary default tolerance, or universal integration engine.

## Proposal

The retained [experiment](../research/rfc0077/README.md) records the exact three
owner hulls, all requested4–6kn speeds, independent axes, all six section families,
alternative kernels, independent Wigley closed transforms, tail bound and costs.
It identifies the fixed-depth trapezoid's unresolved exponential boundary layer.
Adopt exact integration of sampled linear depth segments, retaining existing
longitudinal-gradient and angular rules. The extra longitudinal Fourier transform
has little measured benefit once depth is fixed and is not adopted.

`NUMERICAL_METHOD_VERSION` and curve metadata now identify
`michell_linear_depth_v2`, including unassessed diagnostics. Calibration
`model_version` remains independent and unset for this raw model. Historical
missing method metadata remains unknown; saved records are not silently upgraded.

An explicit `numerical_relative_tolerance` on `resistance_curve` and
EvaluatorOptions requests `michell_linear_depth_screening_v1`; None stays unknown.
Eight actual resolutions vary x/z/theta independently. Achieved per-speed absolute
uncertainty sums requested-to-finest change, last independent-axis residuals and
the measured independent reference allowance. Every requested speed must meet the
declared screening budget to mark the curve converged; values stay on their
requested grid. Exact speed list, sampled geometry/pose, fluid inputs and method
are fingerprint-bound. The numerical reference Fn scope .25–.5 is a study scope,
not physical validity; out-of-scope/nonfinite/mismatched inputs remain diagnostic
unknown with raw speed points retained. The1% study budget is justified by the
recorded wider06/08 and closer06/18 separations; it is never a default or achieved
error estimate. Several coarse curves honestly do not meet it.

NumericalQuality gains additive typed observations, exact speed grid, absolute
uncertainty, fingerprint and reference-control fields. Old quality remains
readable. The new policy requires its actual eight observations and binding.
`relative_changes` records achieved relative uncertainty for this policy.

Reported Pareto dominance requires no-worse separated achieved intervals for
every objective and one strict separation. Missing achieved resistance bounds
are not zero error. This applies to pure Pareto, comparison and final/history
NSGA-II/EHVI frontiers. Comparison adds explicit numerical-overlap advisories.
Internal selection, crowding and acquisition use diagnostic point estimates;
new search metadata records that distinction. Resistance history summaries label
point-estimate min/max/median instead of implying a strict winning candidate.
The existing physical admissibility and numerical-status gates remain in force.

## Evaluation context integration

`EvaluationContext.operating_comparison_inputs()` returns a fresh schema-v1 JSON
projection of physical loads, CG references, density, viscosity, exact ordered
speeds and operating intent. It excludes labels, hull identity, input origins,
supplied-field provenance and resistance quadrature/budget. Explicit component
names/order and unused compact masses do not change comparison conditions;
component physical distributions remain intact, and inherited KG retains its
global reference inputs.

Solved equilibrium excludes realized pose but retains hydrostatic sampling,
mass/moment tolerances, iteration limit and maximum trim. Resistance intervals
do not bound solved-pose error, so changing those solver inputs prevents a strict
winner. Fixed-pose evaluation retains requested sinkage/trim and ignores unused
solver/display settings.

Sweep forwards the budget through the common W3 evaluation service and records
`resistance_operating_context`; comparison and active-search frontier points
carry it as per-metric `operating_context`. Different or missing counterpart
conditions refuse strict dominance and yield public comparison warning
`incompatible_operating_inputs`. A different resistance grid/budget alone does
not imply operating incompatibility. Result binding rejects numerical budget
metadata inconsistent with its saved context. D048 exploratory physical-claim
permission still cannot bypass D058/D063 numerical admission or display-only gates.

## Acceptance Criteria

- Retained baseline, three inputs, five speeds, six families, independent axes,
  independent closed-transform controls/tail allowance and observed cost.
- Constant/linear depth transforms agree with independent Decimal controls even
  for beta1e8; full Wigley transform controls cover the studied Fn range.
- Explicit budgets retain requested values and evidence, permit assessed finer
  grids, and refuse inadequate coarse grids without tolerance inflation.
- Unknown/out-of-scope curves retain all raw points and remain unranked.
- Achieved intervals preserve unresolved close candidates and permit sufficiently
  separated comparisons in pure and both active-search output paths.
- Full pytest followed by Ruff passes; all prior claim invariants remain closed.

## Open Questions

Broader shape/Fn reference evidence, alternate oscillatory quadrature and measured
kayak calibration would be separate changes. The empirical uncertainty policy is
not a rigorous general bound and does not establish physical accuracy.

## Implementation Path

Retain baseline → compare independent axis/method alternatives → derive independent
controls → select depth-only correction → record achieved uncertainties → wire
explicit policy and interval outputs → full release gate → owner study replay.

## Domain Modeling

Numerical method version identifies implementation arithmetic. Screening budget
is a caller's admission ceiling. Achieved numerical uncertainty is the recorded
per-point allowance used for comparisons. Numerical reference scope is distinct
from physical validity, calibration and accepted use.

The study-derived requested-resolution floor is 400 stations, 25 depths and 40 angles.
Coarser requests retain raw values with unknown quality; they cannot borrow
the reference allowance measured at 1600/100/640. The floor is numerical study
applicability, not evidence of physical validity or automatic convergence.

The total-resistance allowance also includes actual wetted-surface refinements
at 60/120/240 longitudinal stations, evaluated with the same fluid and rigid pose.
`surface_observations` retains area, per-speed viscous resistance and time;
`viscous_uncertainty_N` is |Rv60−Rv240|+|Rv120−Rv240|. This contribution is added
to the eight-grid Michell allowance before budget admission and interval ranking.
The requested viscous values remain unchanged, and its fixed60-station surface rule
is recorded by the surface observations in numerical quality. The requested
x/z/theta quadrature metadata remains unchanged. Reported viscous inputs are recomputed
and compared before assessment, so fluid/pose mismatch stays diagnostic unknown.

Scope is calculated from actual speed, hull length and gravity; relabeling a
reported Fn cannot admit an out-of-study calculation. Typed `comparison_inputs`
binds the exact speeds, length, fluid and method/model identity. Saved assessed
curves refuse stale total/viscous observations, requested grid, fluid, method or
Fn metadata. Reported interval comparisons require common exact speeds, fluid
and method/model identity; length may vary between candidate hulls. Optional
per-metric `operating_context` must be present on both sides and equal when either
side supplies it. Standalone curves without operating context use their typed
numerical comparison conditions. Missing historical comparison inputs stay
readable and cannot establish a strict resistance winner.

Current numerical admission recognizes only the supported, verified policy.
Unknown/historical policy strings remain readable assertions and diagnostic values,
but cannot join even a singleton resistance frontier, train resistance selection,
or establish dominance. The known policy recomputes total and viscous allowances
from the eight plus three retained observations during parsing; jointly lowering
absolute and relative errors cannot manufacture zero-width comparison intervals.
Its method, scope, floor, refinement levels and reference allowance are bound to
the immutable v1 definition in `eval/michell_screening.py`, independently of a
future runtime method. Deserialization does not rerun geometry or resistance.

Web at-speed metrics expose `evaluated_speed_kt` and label the actual sampled
speed. When the view target is absent from a supplied evaluation grid, the view
shows a sampled point with an explicit `speed_selection_warning`; it does not
insert the target into the grid or relabel that point as requested. Legacy
at-target metrics retain their existing target evaluation behavior.
