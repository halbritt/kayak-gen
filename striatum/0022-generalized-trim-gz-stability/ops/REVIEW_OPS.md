author: operator [self-declared: operator-ops-review]

# Ops review - generalized trim and GZ stability

Verdict intent: accept_with_findings

## Findings

### O-001 - Strict pydantic models make the trim migration snapshot-sensitive

`LoadCase`, `StabilityResult`, `GZCurve`, `EvaluationResult`, sweep records, and
comparison reports all use `extra="forbid"`. That is useful for catching typos,
but it means every new trim or GZ field is a compatibility decision. RFC 0014's
proposed `LongitudinalLoadComponent`, trim residual fields, and expanded
`GZCurve` shape cannot be emitted casually without breaking strict readers or
renaming today's CLI JSON fields.

Required action: add trim fields additively with defaults or nullable values,
preserve existing compact `LoadCase` fields and existing `StabilityResult`
field names, and add round-trip tests for legacy compact load cases plus new
componentized load cases. If `GZCurve` is reshaped, either keep the current
field names compatible or gate new fields behind a deliberate schema/version
decision before any `gz_curve` value is emitted.

### O-002 - Forward/aft trim and solver failure need deterministic tests

Current tests prove centered sinkage convergence, waterline KG normalization,
and one too-heavy out-of-bracket failure. They do not yet prove the RFC 0014
trim sign contract: `+x` stern, `-x` bow, forward LCG producing bow-down trim,
and aft LCG producing stern-down trim. They also do not cover an in-bracket
iteration-limit failure path.

Required action: add small deterministic tests for forward LCG, aft LCG,
residual fields, convergence status, iteration count, and warnings. Include a
non-convergence test that exercises the max-iteration path, not only an
out-of-bracket mass. Keep assertions on sign, residual tolerances, status, and
bounded iteration counts rather than fragile exact iteration traces.

### O-003 - CLI stability JSON must stay field-stable

`kayakgen stability` currently writes raw `StabilityResult` JSON, and the tests
assert only a few substrings or selected keys. New trim output can easily break
downstream scripts if `equilibrium_draft_m`, `sinkage_m`, `trim_angle_deg`,
`displacement_error_kg`, `method`, `status`, or warning names are renamed or
moved without aliases.

Required action: add CLI tests that parse the JSON and assert the stable field
surface for both the default design-waterline mode and `--equilibrium` trim
mode. New fields such as `load_lcg_m`, `buoyancy_lcb_m`, `moment_error_kg_m`,
and draft-at-midship semantics should be additive and snapshot-stable once
introduced.

### O-004 - Sweep records do not yet carry stability or trim summaries

`run_sweep` writes `EvaluationResult` artifacts with hydrostatics and optional
resistance only. Candidate summaries include hydrostatic `GM0_m`, displaced
mass, wetted area, `Cp_actual`, and optional resistance fields, but not
`StabilityResult` fields. `compare.py` already lists `displacement_error_kg` as
a possible default objective, yet current sweep summaries never provide it.

Required action: introduce stability evaluation in sweeps as an explicit,
default-compatible evaluator option, then write stable scalar summary fields
for trim/equilibrium comparison: displacement error, trim angle, moment error,
convergence status, iteration count, and relevant warnings. Preserve old sweep
specs by giving new evaluator options defaults, and keep CSV/run-record column
names deterministic.

### O-005 - Generalized trim should stay bounded and opt-in where expensive

The existing sinkage solver is a bounded bisection over copied hull drafts. A
generalized trim implementation should not pull high-angle volume integration,
mesh closure, CFD, or an unconstrained nonlinear solver into default CLI,
evaluation, or sweep paths. Hidden solver costs would make tests and sweeps
brittle.

Required action: use a deterministic bounded solver with explicit tolerance,
max iterations, residual reporting, and non-converged result status. Keep
high-angle `GZCurve` unavailable unless a named closed-volume model is present,
and keep expensive stability modes out of default `evaluate` and sweep behavior
unless the user opts in.

## Verification

Targeted current-state tests pass with the repo virtualenv:

`.venv/bin/python -m pytest tests/test_stability.py tests/test_cli.py tests/test_sweep.py tests/test_compare.py`

Result: 36 passed.
