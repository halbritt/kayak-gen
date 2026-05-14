---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-002
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_64d51c5f592445878ffdf80171d62b2f
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_sweep_optimization_codex
lease: lease_947beafde68a47b0b9d1118d4ffcbfd1

# Vote - Sweep And Optimization Admissibility

Vote: Option A - Conservative Default Whitelist, with an objective-registry gate before optimizer work.

## Decision Sentence

Adopt a conservative sweep and comparison admissibility policy: treat RFC 0009 as a landed/partial sweep-run-record slice, keep default Pareto ranking limited to currently delivered and availability-gated `GM0_m`, `displacement_error_kg`, and `mesh_problem_count`, allow raw resistance only as an explicitly requested exploratory objective with accepted-use warnings, and block optimizer/scalar-fitness work until objective metadata and claim-gated promotion rules are accepted.

## Evidence

The research packet's central reconciliation is sound. RFC 0009 remains indexed `proposed`, but current `kayakgen sweep` behavior covers the run-record backbone while retaining deltas for `pending`, the unused `stl` option, and objective metadata (`striatum/0050-decision-panel-research/research/sweep_optimization/RESEARCH.md:21-23`, `:50-59`). RFC 0009 itself keeps v1 focused on bounded sweeps, explicitly excludes optimization and automatic best-kayak selection, and preserves analytical resistance as comparative rather than final physics (`docs/rfcs/0009-sweep-run-records.md:20-37`).

RFC 0013 already states the comparison posture this vote should preserve: default reports exclude raw uncalibrated resistance, manually requested raw resistance is exploratory, and the initial objective set is initial `GM0_m`, load-case displacement error, and mesh diagnostic problem count when available (`docs/rfcs/0013-pareto-frontier-comparison-ui.md:8-16`, `:53-63`, `:87-90`). The current implementation matches that posture: `DEFAULT_OBJECTIVE_CANDIDATES` contains only `GM0_m:max`, `displacement_error_kg:min`, and `mesh_problem_count:min`; defaults are selected only from metrics present on complete candidates; resistance and design-fitness objectives are marked claim-gated/exploratory and require accepted-use provenance (`kayakgen/search/compare.py:24-28`, `:119-128`, `:175-178`, `:313-348`).

The no-claims boundary is not optional. The roadmap says resistance is `uncalibrated_comparative`, not a calibrated model, final prediction, design-fitness score, or default optimization objective; raw CFD remains local/unvalidated or unavailable; high-angle stability remains unavailable; advisory design validity is not final design fitness (`docs/ROADMAP.md:33-59`). Batch H makes the decision rule explicit: comparison may use only metrics whose claim state and availability are explicit, and optimization must not silently treat raw resistance, raw CFD, advisory validity, or unavailable stability as final design fitness (`docs/ROADMAP.md:209-222`).

The local claim gates enforce the same line. Resistance can be treated as calibrated prediction only with `calibrated_model`, `final_prediction`, calibration fixture IDs, model version, accepted fit, fit metrics, a validity envelope, and no uncalibrated warnings; final design fitness has a separate `validated_design_fitness` gate that no current output satisfies (`kayakgen/eval/claims.py:195-227`). Today's resistance metadata is `uncalibrated_comparative`, accepted only for `comparative_filter`, with no calibration fixtures, no fit, no validity envelope, and explicit uncalibrated warnings (`kayakgen/eval/resistance.py:19-29`, `:165-198`). Pareto dominance also behaves correctly for uncertainty: missing metrics or required accepted-use provenance failures make candidates non-dominating rather than silently comparable (`kayakgen/search/pareto.py:64-80`, `:116-154`).

My independent external check supports this conservative stance. NASA's CFD V&V tutorial organizes credibility around uncertainty/error, verification, validation, convergence, grid, and temporal studies, and its uncertainty/error page identifies physical modeling, geometry modeling, round-off, iterative convergence, discretization, programming, and usage errors as distinct ways simulations can diverge from truth: https://www.grc.nasa.gov/www/wind/valid/tutorial/tutorial.html and https://www.grc.nasa.gov/WWW/wind/valid/tutorial/errors.html. That supports keeping raw CFD and unvalidated numerical outputs out of ranking-sensitive defaults. pymoo and OpenMDAO also put objective and constraint definitions in the application/problem layer rather than inferring metric trustworthiness from the optimizer: https://pymoo.org/interface/problem.html, https://openmdao.org/newdocs/versions/latest/features/core_features/adding_desvars_cons_objs/adding_objective.html, and https://openmdao.org/newdocs/versions/latest/features/core_features/adding_desvars_cons_objs/adding_constraint.html.

## Rejected Alternatives

- Treating RFC 0009 as wholly unimplemented loses because the sweep runner and run-record surface are already user-facing; the right action is partial/landed reconciliation with named deltas, not pretending the feature is absent.
- Promoting raw resistance to a default objective loses because both the roadmap and runtime metadata mark it `uncalibrated_comparative`; it lacks accepted fit, model version, calibration fixture IDs, uncertainty/validity envelope, and in-envelope proof.
- Starting optimizer work before objective metadata loses because optimizers will exploit any numeric metric. Without units, direction, source evaluator, claim state, availability, accepted-use requirement, and role, implementation would re-derive policy informally and risk overclaiming.
- Adding scalar `design_fitness` or "best kayak" now loses because no current claim gate supports final design fitness, and calibrated resistance alone would still not prove overall design fitness.
- Using design-warning counts, advisory validity, raw CFD, or unavailable high-angle stability as objectives loses because those records are either warnings, raw/unvalidated dispatch state, or explicitly unavailable metrics.

## Implementation Gates

Before any optimizer RFC or implementation:

1. Reconcile RFC 0009 status in the RFC index and roadmap as landed/partial, including the `pending` status mismatch, the reserved or unimplemented `stl` evaluator option, and mesh-diagnostics reality.
2. Add an objective metadata/registry layer for comparison and future search. Each metric must declare label, unit, direction, source evaluator, availability rule, claim-state requirement, accepted-use requirement, and role: default objective, explicit exploratory objective, constraint/filter, display-only, unavailable, or forbidden until claim gate.
3. Preserve current behavior where failed/skipped candidates remain visible but are not frontier-eligible, and missing/provenance-failed metrics warn instead of silently dominating.
4. Keep raw resistance explicit and exploratory only; add speed-specific resistance metric names such as target-speed or Froude-indexed metrics before any resistance objective is promoted.
5. Require tests proving optimizer/search defaults cannot include raw resistance, raw CFD, advisory validity or warning counts, unavailable high-angle stability, or `design_fitness`.

No-claims language must remain in force: `GM0_m` is initial/primary stability only, `mesh_problem_count` is an inspection/open-surface diagnostic not `cfd_ready` proof, `displacement_error_kg` is load-fit residual not global hull quality, and no current metric is final seaworthiness, calibrated performance, solver readiness, secondary stability, or final design fitness.

Confidence: high.
