# RFC0077 numerical experiment

This is retained numerical evidence for D063 / KAYGEN-15. It changes numerical
integration of the existing ITTC/Michell model. It supplies no measured hull
resistance, calibration, design-fitness, or seaworthiness evidence.

## Inputs and observations

The exact owner-study hull inputs are committed as
`tests/fixtures/numerical/fast-tourer-{06,08,18}.json`. They were originally saved
in the 2026-11-03 fast-tourer study; hashes accompany baseline observations.
All candidate/family observations use 4, 4.5, 5, 5.5, 6 kn. The six family
controls change only candidate06's `distribution_v2.cross_section_family` to
round, shallow_arch, shallow_v, deep_v, hard_chine, or multi_chine.

- `first-results.json`: 576 baseline/alternative observations, including Wigley.
  The unchanged baseline is commit `de8783ed24042c130ee204f37f2c1b0b618f55e6`.
  Each spatial/angle axis was first varied independently; joint refinement is
  retained separately. Alternatives were exact linear depth, exact linear depth
  plus piecewise-linear longitudinal Fourier transform, and angular Gauss rules.
- `wigley-first.json`: independent polynomial-transform reference comparisons.
- `family-results.json`: 540 observations across all six cross-section families.
- `angular-results.json`: 180 observations at 800/50, 1600/100, 3200/200,
  each at 80/160/320/640 angles; no axis is inferred from joint agreement alone.
- `policy-results.json`: eight independent resolution observations for each of
  three owner candidates and five additional families; includes actual elapsed
  time, achieved absolute/relative uncertainty, and intervals.
- `policy-controls.json`: seven independent Wigley controls over Fn .25–.5,
  with closed-transform value, tail bound, outer-grid change, and discrepancy.
- `experiment-manifest.json` hashes original observations and original scripts.
  The exact original scripts are archived as `*.py.txt`; these contain the
  original machine paths for provenance. Portable versions live under
  `scripts/numerical/` and embed the original baseline kernel explicitly.

## Discriminating result

At candidate06 / 4.5 kn, the original wave resistance is approximately
228226, 34564, 4280 N at 400/25/40, 800/50/80, 1600/100/160. The exact linear
sampling-depth integral gives 5.244, 5.170, 5.080 N on those grids. The former
waterline trapezoid supplies an effective fixed half-cell width even as the
exponential layer becomes arbitrarily thin near theta=pi/2. Its error is then
amplified by sec(theta)^3. Exact exponential integration distinguishes this
failure from longitudinal aliasing: changing only the longitudinal transform
adds little once depth is corrected. At the fine family grids that additional
Fourier change is about .014–.019% of total resistance, so it is not adopted.
Angular sensitivity remains and is measured, rather than declared solved.

For a segment h, q=beta*h, define A=(1-exp(-q))/beta and
B=(1-(1+q)*exp(-q))/(beta^2*h). Its exact integral is
exp(-beta*z0) * [f0*(A-B)+f1*B]. A uses expm1; B uses a small-q series to avoid
cancellation. Decimal independent polynomial tests cover beta from 1e-6 to 1e8.
This is exact for the sampled linear depth representation, not for the unknown
continuous true hull or for the other quadrature axes.

## Independent control and tail

For Wigley f=(B/2)(1-4x^2/L^2)(1-z^2/T^2), the longitudinal transform of f_x is
imaginary with magnitude factor
X=8B/L^2 * [a*cos(alpha*a)/alpha-sin(alpha*a)/alpha^2], a=L/2.
Its depth factor is
Z=1/beta-2/(beta^3*T^2)+exp(-beta*T)*(2/(beta^2*T)+2/(beta^3*T^2)).
Integrate (X*Z)^2*sec(theta)^3 with the unchanged model prefactor. This closed
transform does not use production sampled derivatives or depth integration.

The independent outer reference uses 200001 angles up to sec(theta)=Lambda=64;
100001 angles check its observed grid change. Since Z<=1/beta and
|X|<=4B/L^2*(L/alpha+2/alpha^2), the remaining tail is bounded by
prefactor*C^2 / (4*sqrt(1-Lambda^-2)*Lambda^4), where
C=4B/L^2*(L/k0^2+2/(k0^3*Lambda)). This follows by replacing the remaining
integrand after lambda=sec(theta) substitution by
C^2/[sqrt(1-Lambda^-2)*lambda^5] and integrating to infinity.

The maximum relative (fine-kernel discrepancy + tail bound + independent
outer-grid change) across seven controls at 1600/100/640 is
7.088306821851369e-5. This recorded reference allowance is empirical implementation
control evidence over Fn .25–.5, not a universal bound on arbitrary hulls or a
physical validity envelope. Outside that numerical study scope assessment stays
unknown and retains every raw requested speed point.

## Declared screening budget and achieved uncertainty

There is no universal default tolerance. The caller must declare a relative
screening budget. The study evaluates an explicit 1% budget because the recorded
06/08 separation at 5 kn is about 3%, while the 06/18 separation at 4 kn is
about .542%; a policy must resolve the former when intervals permit and preserve
the latter as unresolved. Two 1% errors cannot justify every 3% separation, so
reported dominance uses actual achieved per-point intervals, never the budget as
if it were achieved error. This budget is a study screening choice, not a
physical accuracy claim or permission to rank all candidates.

For requested (n,m,t), eight actual observations are:
(n,m,t), (n,4m,T), (2n,4m,T), (4n,4m,T), (4n,m,T), (4n,2m,T),
(4n,4m,t), (4n,4m,M), where M=max(2t,160), T=max(4t,640).
For each speed, achieved absolute uncertainty is the requested-to-finest change
plus the three last independent-axis differences plus |finest| times the
reference allowance. Admission requires every achieved relative uncertainty to
meet the caller budget. Requested-grid values remain unchanged. The exact sampled
geometry (including pose), fluid constants, viscous contribution, resolution,
method and speeds are SHA256-bound to the assessment; actual observations and
cost are retained in the curve metadata.

Before adding the viscous surface allowance, at 400/25/40 maximum achieved relative uncertainty is 1.119% for candidate06,
.885% for08 and .950% for18. The six-family maximum is 1.282% (deep_v).
Thus06 and several families honestly fail the declared 1% budget; no tolerance is
loosened to force admission. A finer requested800/50/80 grid meets the same budget
in the candidate06 regression. Actual intervals preserve06/18 at 4 kn and resolve
06/08 at 5 kn. Nonfinite observations, mismatched inputs/methods and speeds outside
the studied Fn scope remain diagnostic unknown, with reasons and raw values.

The eight-observation five-speed prototype took 4.04–4.91 seconds per hull with
OPENBLAS_NUM_THREADS=1 on this host. Timings are observations, not deadlines.
The initial prototype recalculated a longitudinal gradient inside the angle loop;
its first-run timings are retained but are not used as fair kernel cost estimates.
The portable scripts use the later hoisted-gradient prototype. Production uses
small explicit einsum depth contractions to avoid unnecessary BLAS thread cost.

## Reproduce

From the repository root, select a new external output directory:

```bash
export KAYAKGEN_NUMERICAL_STUDY_OUT="$HOME/.local/share/kayakgen/reproduce-rfc0077"
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/numerical/quadrature_experiment.py
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/numerical/family_experiment.py
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/numerical/policy_experiment.py
```

The portable scripts retain the same inputs and formulas; elapsed times and
roundoff may differ. `tests/test_michell_linear_depth.py`,
`test_resistance_assessment.py`, and `test_resistance_intervals.py` exercise the
production correction, admission, exact-input binding, and unresolved comparisons.

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

The original eight-wave-grid observations are retained unchanged. A follow-up
`total-policy-results.json` and `viscous-surface-followup.json` record the complete
surface-inclusive budget, including the additional observed cost. The latter
checks 60/120/240/480 across the three inputs and all section families: the largest
60→480 surface change is .03226% for hard_chine, so zero viscous numerical error
was not assumed. The first interrupted release run is not acceptance evidence;
it was stopped to include this measured contribution before landing.

With the surface contribution included, maximum achieved relative uncertainty is
1.122% for candidate06, .889% for08, .954% for18 and 1.283% for the deep_v family.
The original admission outcomes and unresolved/separated pair conclusions remain
unchanged. The full surface-inclusive prototype takes 4.09–4.87 seconds per hull
on this host; `surface-followup-manifest.json` binds that follow-up and its recipe.

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

## Independent binding and comparison closure

`closure/` retains seven actual assessed curve controls, the independent script
and its before/after source-hash receipt. The review reproduced and closed:
reported 10 kn Fn relabeling, stale serialized resistance/fluid/method records,
coherently zeroed uncertainty contradicting retained observations, unsupported
policy relabeling, and comparison across different speeds or fluids. No raw
physical claim was promoted. A wider 06/08 pair at 5 kn resolves; the closer 06/18
pair at 4 kn stays unresolved. Actual altered pose/fluid fingerprints differ, and
assessing a posed curve with the wrong pose stays unknown. These are explicit
boundary/consistency checks, not authentication of independently forged complete
evidence or a universal proof of numerical or physical accuracy. Content/run
integrity remains the artifact store's responsibility.
