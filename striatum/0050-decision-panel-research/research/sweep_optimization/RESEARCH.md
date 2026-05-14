---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-004
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_1a015f704a4f4594a072e9ffd5fd3636
job: job_run_dc0a506896094745b380fd3ad2535d59_research_sweep_optimization
lease: lease_bbb76c8f4af44f478b263768061cdef2

# Research - Sweep And Optimization Admissibility

## Decision Question

Which sweep, comparison, and future optimization metrics are admissible for candidate ranking after reconciling proposed RFC 0009 with current `kayakgen sweep` / `kayakgen compare` behavior?

## Local Constraints And No-Claims Boundaries

- RFC 0009 is still indexed `proposed`, but its core behavior has largely landed: deterministic JSON specs, `values` / `linspace` expansion, stable candidate keys from spec hash plus parameters, run records, resume skip behavior, failed validation records, candidate artifacts, `summary.csv`, optional resistance, optional mesh diagnostics, and evaluator provenance are implemented in `kayakgen/search/sweep.py` (notably lines 56-93, 96-137, 144-220, 237-323, 327-370).
- Current sweep status differs from RFC 0009 in three important ways: `pending` is not a serialized status (`complete`, `failed`, `skipped` only); `stl` is present in evaluator options but not implemented by the runner; mesh diagnostics have landed as an optional artifact. This supports changing RFC 0009 from `proposed` to a precise partial/landed-run-record status, not treating it as unimplemented.
- RFC 0009 explicitly excludes optimization and automatic best-kayak selection, and preserves resistance as a comparative filter rather than final prediction (`docs/rfcs/0009-sweep-run-records.md:20-37`).
- RFC 0013 has landed comparison reports and says default reports exclude raw uncalibrated resistance; explicit resistance objectives produce exploratory frontiers unless calibrated provenance satisfies future resistance claims (`docs/rfcs/0013-pareto-frontier-comparison-ui.md:8-16`, `:53-63`, `:87-90`).
- The roadmap forbids promoting resistance to a calibrated model, final prediction, design-fitness score, or default optimization objective; forbids treating raw CFD as validated; keeps high-angle `GZ` unavailable; and says design warnings are not proof of seaworthiness, calibrated performance, final design fitness, or solver readiness (`docs/ROADMAP.md:34-59`).
- Batch H states the governing rule for this decision: comparison can use only metrics whose claim state and availability are explicit, and optimization must not silently treat raw resistance, raw CFD, advisory validity, or unavailable stability as final design fitness (`docs/ROADMAP.md:209-222`).
- Current comparison code already encodes a conservative default: `GM0_m:max`, `displacement_error_kg:min`, and `mesh_problem_count:min` are the only default objective candidates, and only when present (`kayakgen/search/compare.py:24-28`, `:313-324`).
- Current comparison code promotes claim-gated metrics to `accepted_use_required`, labels any resistance or final-design-fitness objective as `exploratory_frontier`, and warns if accepted-use provenance is missing (`kayakgen/search/compare.py:119-128`, `:175-178`, `:327-349`).
- Current Pareto utilities make missing metrics or metrics without required accepted-use provenance non-dominating rather than silently comparable (`kayakgen/search/pareto.py:64-80`, `:116-154`).
- Current claim gates require `calibrated_model`, `final_prediction`, calibration fixture IDs, model version, `accepted_fit`, fit metrics, a validity envelope, and no uncalibrated warnings before resistance may be treated as calibrated prediction; no current output satisfies final design fitness (`kayakgen/eval/claims.py:195-227`).
- Current raw analytical resistance metadata is `uncalibrated_comparative`, accepted only for `comparative_filter`, with no calibration fixtures, no fit, no validity envelope, and uncalibrated warnings (`kayakgen/eval/resistance.py:19-29`, `:165-198`).
- Tests enforce the current admissibility split: defaults use `GM0_m`, exclude raw `Rt_N_last`, include load-case displacement error when present, preserve design validity without making warning counts objectives, mark raw resistance as exploratory and provenance-gated, reject forged / incomplete calibrated metadata, reject validation-only resistance, and reject calibrated resistance as final design fitness (`tests/test_compare.py:113-173`, `:193-209`, `:274-445`).
- Tests also enforce sweep determinism, resume behavior, failure preservation, design-validity propagation without summary scoring, optional mesh diagnostics, optional stability summaries, and absence of high-angle `GZ` summary fields (`tests/test_sweep.py:23-106`, `:120-155`).

## Current External Evidence

Access date for all external sources: 2026-05-14.

| Source | Claim supported |
| --- | --- |
| NASA NTRS, *Simulation Credibility: Advances in Verification, Validation, and Uncertainty Quantification*, NASA/TP-2016-219422, https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20160013550.pdf | Decision makers need quantified simulation credibility; credibility is tied to accuracy and uncertainty, and simulation creators are responsible for conveying that credibility. This supports making claim state and accepted-use provenance prerequisites for ranking-sensitive metrics. |
| NASA NPARC Alliance, *Tutorial on CFD Verification and Validation*, https://www.grc.nasa.gov/www/wind/valid/tutorial/tutorial.html | The maintained NASA tutorial follows AIAA G-077-1998 and organizes CFD V&V around overview, uncertainty/error, verification, validation, convergence, and grid studies. This supports keeping CFD-derived metrics out of ranking until verification/validation artifacts exist. |
| NASA NPARC Alliance, *Uncertainty and Error in CFD Simulations*, https://www.grc.nasa.gov/WWW/wind/valid/tutorial/errors.html | CFD differences from truth can come from physical modeling, geometry modeling, round-off, iterative convergence, discretization, programming, and usage errors. It also notes conceptual-stage use may trade accuracy for speed only when the accuracy level is understood. This supports allowing exploratory filters while blocking final-fitness ranking. |
| ITTC, *Recommended Procedures and Guidelines: Resistance Test 7.5-02-02-01*, revision 05, 2021, https://www.ittc.info/media/11780/75-02-02-01.pdf | Resistance-test practice includes documented procedure, validation, uncertainty analysis, and benchmark tests. This supports requiring source review, uncertainty, and validation/calibration metadata before resistance becomes a default ranking objective. |
| ITTC, *Resistance Uncertainty Analysis, Example for Resistance Test 7.5-02-02-02*, revision 01, 2002, https://ittc.info/media/2021/75-02-02-02.pdf | The ITTC example records test design, measurement systems, data reduction, bias limits, precision limits, and total uncertainty, including resistance, speed, geometry, density, viscosity, and friction coefficient terms. This supports the project rule that measured or fitted resistance must carry provenance and uncertainty before promotion. |
| pymoo documentation, *Problem* / constrained multi-objective example, https://pymoo.org/interface/problem.html | A multi-objective optimization problem is represented by declared variables, objectives (`F`), and constraints (`G`); the framework accepts user-supplied objective values and constraints. This supports project-owned admissibility metadata rather than relying on an optimizer to know which hull metrics are trustworthy. |
| pymoo documentation, *Find a Solution Set using Multi-objective Optimization*, https://pymoo.org/getting_started/part_2.html | Multi-objective workflows evaluate sets of candidate solutions against supplied objective and constraint functions, and algorithm choice depends on the problem. This supports treating kayak search as a future layer over explicit objective definitions, not as a reason to scalarize uncertain metrics now. |
| OpenMDAO documentation, *Adding an Objective* and *Adding Constraints*, https://openmdao.org/newdocs/versions/latest/features/core_features/adding_desvars_cons_objs/adding_objective.html and https://openmdao.org/newdocs/versions/latest/features/core_features/adding_desvars_cons_objs/adding_constraint.html | Engineering optimization frameworks separate design variables, objectives, and constraints. This supports making class validity, mesh readiness blockers, convergence status, and availability gates explicit constraints or filters, not hidden objective weights. |

## Reconciliation Of RFC 0009 Against Current Behavior

RFC 0009 should be considered "landed run-record safe slice / partial sweep behavior", not merely proposed. The implemented runner satisfies the acceptance backbone: deterministic expansion, stable keys, run/spec/candidate/evaluation records, summary CSV, failed validation records, resume skip counts, optional resistance, optional mesh diagnostics, evaluator settings, and evaluator versions.

Residual RFC 0009 cleanup before closing it fully:

- Update RFC index/status text to reflect landed behavior and the explicit deltas.
- Decide whether to add `pending`, remove it from RFC 0009, or reserve it for future distributed/long-running candidates.
- Either implement `stl` sweep artifacts or mark the `stl` evaluator option as reserved/no-op in docs and records.
- Add objective metadata to sweep/comparison reports before optimizer work: metric label, unit, direction, source evaluator, claim state, accepted-use requirement, availability rule, and whether the metric is a default objective, explicit exploratory objective, constraint/filter, or display-only warning.

## Metric Admissibility Matrix

| Metric or record | Current ranking admissibility | Rationale and gate |
| --- | --- | --- |
| `GM0_m` | Admissible as a default Pareto objective (`max`) when present. | Computed hydrostatic initial stability is current delivered behavior and already a default objective. Wording must stay "initial/primary stability", not seaworthiness or secondary stability. |
| `displacement_error_kg` | Admissible as a default Pareto objective (`min`) only when a load case and stability/equilibrium evaluator produced it. | It measures load-fit residual, not global hull quality. Gate on candidate `status == complete`, stability status/warnings, and preserved load-case provenance. |
| `mesh_problem_count` | Admissible as a default Pareto objective (`min`) only when mesh diagnostics artifact exists. | It is a diagnostic-quality objective for inspection/open-surface artifacts, not `cfd_ready` proof. Prefer also treating hard readiness blockers as constraints/filters. |
| `wetted_surface_m2` | Conditionally admissible as an explicit expert/geometry objective or proxy, not current default. | It is geometric and useful for low-Froude friction screening, but current defaults intentionally keep the objective set narrow. Needs objective metadata and user-selected direction. |
| `displaced_mass_kg` | Not directly admissible as a raw objective. | Use target/error form (`abs(displaced_mass_kg - target_mass_kg)` or load-case `displacement_error_kg`) after target provenance exists. Raw mass can otherwise prefer wrong displacement. |
| `Cp_actual` | Not directly admissible as a raw min/max objective. | Use as class/envelope constraint or target-deviation metric. Higher/lower Cp depends on speed class and Froude regime. |
| `trim_angle_deg`, `moment_error_kg_m`, `equilibrium_iterations` | Display or convergence/quality filters today; not default ranking objectives. | They are residuals or state descriptors. Future admissibility requires accepted target envelopes and status semantics. |
| Design-validity findings, advisory badges, warning counts | Display-only warnings and optional hard filters by explicit user/class policy; not objective scores. | Roadmap forbids treating advisory validity as design fitness. Current tests ensure warning counts do not become metrics. |
| Raw analytical resistance (`Rt_N_last`, future `Rt_N_at_target`, `Rv_N`, `Rw_N`) | Not admissible as a default objective or optimizer objective today. Admissible only as explicit `exploratory_frontier` / expert objective with accepted-use-required warnings unless the claim gate passes. | Current resistance is `uncalibrated_comparative` and lacks calibration fixture IDs, accepted fit, model version, and validity envelope. |
| Calibrated resistance | Future admissible as a resistance objective only when `claim_allows_calibrated_prediction` passes and the evaluated hull/speed lies inside the validity envelope. | Even then, it is a calibrated prediction objective, not final design fitness. |
| Raw CFD outputs | Not admissible. | Current CFD is unavailable/failed/local raw dispatch state or fixture-only; no accepted real solver success or validation path exists. |
| High-angle `GZ`, `GZ_max`, range of positive stability, capsize range | Not admissible. | Real generated-kayak high-angle stability is unavailable until generated-body evidence and accepted heeled integration land. Current sweep tests enforce absence from summary fields. |
| `design_fitness` / scalar best-kayak score | Not admissible. | No current output satisfies `validated_design_fitness`; calibrated resistance alone must not promote final design fitness. |
| Failed or skipped candidates | Not frontier/ranking eligible, but must remain visible. | Current comparison keeps failed/skipped records visible with warnings and excludes them from Pareto membership. |

## Viable Options

### Option A - Conservative Default Whitelist

Record RFC 0009 as landed/partial for sweep run records, keep optimizer work blocked, and preserve the current default objective whitelist:

- `GM0_m:max` when present;
- `displacement_error_kg:min` when present;
- `mesh_problem_count:min` when present;
- raw resistance only as explicit exploratory objective with warnings;
- high-angle stability, raw CFD, advisory validity scores, and design fitness excluded.

This option matches current code, tests, RFC 0013, and the roadmap. It is the lowest-risk decision.

### Option B - Explicit Objective Registry Before Search

Before implementing any optimizer, add a small metric registry that classifies every metric as one of:

- `default_objective`;
- `explicit_exploratory_objective`;
- `constraint_or_filter`;
- `display_only`;
- `unavailable`;
- `forbidden_until_claim_gate`.

The registry would carry unit, direction, source evaluator, claim-state requirement, availability rule, and warning text. This does not change admissibility by itself; it prevents future optimizer code from re-deriving the policy informally.

### Option C - Evidence-Gated Promotion

Keep current defaults, but define future promotion rules:

- calibrated resistance may become a non-exploratory resistance objective only after accepted fit, calibration fixture IDs, model version, fit metrics, validity envelope, and in-envelope evaluation pass;
- CFD metrics may become objectives only after solver/readiness evidence plus validated/accepted output semantics exist;
- high-angle stability metrics may become objectives only after the generated-body and heeled-integration gates land;
- class validity may become a hard constraint only after a user-selected class/preset policy is explicit.

This option is necessary regardless of whether optimizer work starts soon.

### Option D - Scalar Fitness Postponed

Do not implement a scalar `design_fitness` or "best kayak" objective until a future RFC defines validated design-fitness semantics, weights, validity envelope, and residual risk wording. Keep comparison Pareto-first.

This option avoids overclaiming but still allows useful candidate narrowing through Pareto fronts and filters.

## Risks And Unknowns

- `Rt_N_last` is a weak resistance metric name because it depends on the final speed in the curve, not a target speed. If resistance becomes admissible later, prefer explicit speed-indexed metrics such as `Rt_N_at_target` or `Rt_N_fn_0_40` with speed/Froude provenance.
- Current `displacement_error_kg` only exists when stability/equilibrium is enabled with load-case data. Default objective selection must continue to be availability-driven.
- `mesh_problem_count` collapses several diagnostic fields into one count. It is useful as a quality heuristic, but separate blockers may be needed for readiness semantics.
- Advisory validity findings are valuable for filtering and UI review, but optimizing a warning count can hide severity and domain meaning.
- Optimizers will exploit any numeric objective, including model artifacts and numerical noise. Claim-state and uncertainty gates should be machine-enforced before active search loops.
- RFC 0009's `stl` option and `pending` status are unresolved implementation/documentation mismatches that should be cleaned up before declaring RFC 0009 fully landed.

## Implementation Gates

Before any optimizer RFC or implementation:

1. Reconcile RFC 0009 status and residual deltas in `docs/rfcs/README.md` and related roadmap text.
2. Add objective metadata/registry for comparison and future search.
3. Require every objective to declare availability, unit, direction, source evaluator, claim-state requirement, and default/exploratory/filter/display role.
4. Preserve current behavior that missing or provenance-failed metrics produce warnings and do not silently dominate other candidates.
5. Keep failed/skipped candidates visible but ineligible for frontier membership.
6. Add tests that optimizer/search defaults cannot include raw resistance, raw CFD, advisory validity, unavailable high-angle stability, or `design_fitness`.
7. Add speed-specific resistance metric names before any calibrated resistance objective is promoted.

## Recommendation

Adopt Option A now, with Option B as the immediate implementation prerequisite for any future search RFC. In concrete terms: mark RFC 0009 as a landed/partial sweep-run-record slice, keep current default ranking limited to `GM0_m`, `displacement_error_kg`, and `mesh_problem_count` when available, allow raw resistance only as explicitly requested exploratory comparison, and keep optimization blocked until an objective registry and claim-gated promotion rules exist.
