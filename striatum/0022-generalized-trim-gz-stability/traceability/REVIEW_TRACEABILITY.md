author: operator [self-declared: operator-traceability-review]

# Traceability review - generalized trim and GZ stability

Verdict intent: accept_with_findings

## Findings

### T-001 - RFC 0014 is still proposed and should not be fully landed as written

RFC 0014 is the right target for workflow 0022, but it is still `proposed` and
contains open questions for closed-volume body choice, default paddler LCG, heel
angle spacing, and fixed-paddler-CG semantics. The workflow queue also lists RFC
0014 acceptance or amendment as a prerequisite before implementation.

Required action: accept or amend RFC 0014 before coding beyond the review
ledger. The safe implementation slice is generalized upright trim equilibrium
and serialization; full high-angle GZ must remain deferred unless the
closed-volume and CG-assumption questions are resolved in the RFC and tests.

### T-002 - LoadCase has no longitudinal component model yet

RFC 0011 intentionally deferred generalized trim because current `LoadCase`
contains only compact mass/KG fields and no longitudinal CG or load-position
inputs. RFC 0014 requires explicit `LongitudinalLoadComponent` values and says
legacy compact fields must normalize into the component model without changing
current default equilibrium-sinkage behavior.

Required action: add the component model and normalization path while preserving
existing compact `LoadCase` JSON. Current fields such as `paddler_mass_kg`,
`hull_mass_kg`, `cargo_mass_kg`, KG references, and seawater density should keep
round-tripping, and tests must cover both compact-only inputs and explicit
component inputs.

### T-003 - StabilityResult cannot yet encode moment-balance trim

The current equilibrium evaluator solves displaced mass only, reports
`trim_angle_deg = 0.0` under a centered-load assumption, and warns
`generalized_trim_not_implemented`. RFC 0014 requires sinkage plus trim by
matching displacement and longitudinal moment, including load LCG, buoyancy LCB,
moment residual, displacement residual, convergence status, iteration count, and
warnings.

Required action: extend the result contract with optional trim-equilibrium
fields without removing the current equilibrium-sinkage fields. Tests must prove
that forward LCG (`-x`, bow) produces bow-down trim, aft LCG (`+x`, stern)
produces stern-down trim, residuals are reported, and non-convergence remains
visible.

### T-004 - CLI, evaluate, and sweep records do not yet carry trim stability

`kayakgen stability --equilibrium` can write the current sinkage result, but
`kayakgen evaluate` does not populate `EvaluationResult.stability`, sweep
evaluator options have no stability mode, candidate summaries expose only
hydrostatic `GM0_m`, and sweep artifacts do not record load-case or trim
settings. RFC 0014 requires CLI output and sweep/evaluation records to carry trim
equilibrium output without breaking existing JSON consumers.

Required action: add an opt-in stability surface for evaluation/sweep records
and keep old records valid. Existing JSON fields such as `method`, `status`,
`equilibrium_draft_m`, `sinkage_m`, `trim_angle_deg`,
`equilibrium_tolerance_kg`, `equilibrium_iterations`, warnings, and `gz_curve`
should not be renamed or removed; new trim fields should be optional/defaulted
and covered by CLI and sweep tests.

### T-005 - High-angle GZ output must remain unavailable in this slice

RFC 0011 reserved high-angle GZ until heeled-volume semantics are decided, and
RFC 0014 allows real `GZCurve` values only when a named closed-volume model is
used. The current implementation correctly raises `GZNotImplementedError` and
never emits placeholder righting arms. The PRD and design constraints describe
full 0-90 degree GZ, max GZ, heel-at-max, and range-positive-stability as product
goals, but those are not acceptance-safe until the volume model and paddler-CG
assumptions are explicit.

Required action: keep `evaluate_gz_curve` unavailable unless a named
closed-volume body lands in the RFC and code. Defer real `gz_m`,
`righting_moment_nm`, `max_gz_m`, `heel_at_max_gz_deg`,
`range_positive_stability_deg`, canonical heel spacing, and fixed/moving
paddler-CG semantics. Tests should continue proving unsupported high-angle
stability does not produce synthetic curves.

### T-006 - Status docs need exact partial-status updates after implementation

RFC 0011 is currently `landed-equilibrium-sinkage`, RFC 0014 is `proposed`, and
the RFC index says generalized trim/high-angle stability is queued. A successful
workflow 0022 trim slice would change the RFC 0011 deferral state and RFC 0014
roadmap status, but it still would not complete high-angle GZ.

Required action: after implementation, update RFC 0011, RFC 0014, and
`docs/rfcs/README.md` to name the exact landed slice, such as generalized
upright trim equilibrium, and preserve explicit deferrals for high-angle GZ,
closed-volume selection, heel range/spacing, and paddler-CG behavior.

## Required gate

Proceed to ledger with a partial-landing scope: longitudinal load components,
upright sinkage-plus-trim equilibrium, compatible JSON/CLI/sweep surfaces, and
truthful status updates. Do not implement or claim high-angle GZ unless the
closed-volume decision is accepted and covered by tests.
