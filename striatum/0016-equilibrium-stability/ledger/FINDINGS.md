author: operator [self-declared: operator-ledger]

# Findings ledger - 0016 equilibrium stability

Run id: `run_5fa409d33e554e5f92a9c99bce94c511`  
Job: `findings_ledger`  
Gate result: proceed to implementation

## Stats

- Source artifacts: 3
- Source findings: 14
- Deduplicated findings: 7
- By severity: blocker 1 / high 4 / medium 2 / low 0
- Safe-now findings: 6
- Deferred findings: 1

## Deduplicated Findings

### F-001 - Equilibrium mode is missing

- Sources: T-001, T-003, O-003
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/stability.py`, `kayakgen/cli/main.py`,
  `tests/test_stability.py`, `tests/test_cli.py`
- Statement: Stability only exposes design-waterline diagnostics, while RFC
  0011 calls for an equilibrium-solved mode.
- Required remediation: Add an additive equilibrium evaluator and CLI flag. Keep
  `evaluate_initial_stability()` and default `kayakgen stability` behavior as
  design-waterline diagnostics.

### F-002 - StabilityResult lacks equilibrium fields

- Sources: T-002, D-004, O-004
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/contract.py`, tests
- Statement: The result model cannot encode equilibrium draft, trim, tolerance,
  iterations, or convergence status.
- Required remediation: Extend `StabilityResult` with an equilibrium method
  value, converged/not-converged status, optional draft/sinkage/trim fields,
  tolerance and iteration fields. Preserve existing serialized
  design-waterline output.

### F-003 - Full generalized trim is under-specified

- Sources: D-001, T-004, final constraints
- Severity: blocker
- Classification: safe-now with explicit deferral
- Files: `kayakgen/eval/stability.py`, `docs/rfcs/0011-hydrostatic-stability-load-cases.md`
- Statement: `LoadCase` has no longitudinal CG or load distribution, and
  hydrostatics has no trimmed-waterplane integration. A truthful implementation
  cannot claim generalized sinkage+trim equilibrium yet.
- Required remediation: Implement sinkage equilibrium now. Report `trim_angle_deg
  = 0.0` only under the centered/symmetric-load assumption and include a warning
  that generalized trim requires future LCG/trimmed-volume work.

### F-004 - KG references must use equilibrium draft

- Sources: D-002, O-004
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/stability.py`, tests
- Statement: Waterline-relative KG normalization changes when the operating
  draft differs from `hull.draft_m`.
- Required remediation: In equilibrium mode, normalize KG using the solved draft
  before computing GM0.

### F-005 - Load-case density should drive equilibrium mass comparison

- Sources: D-003
- Severity: medium
- Classification: safe-now
- Files: `kayakgen/eval/stability.py`, possibly `kayakgen/eval/hydrostatics.py`
- Statement: `LoadCase.seawater_density_kg_m3` is ignored by hydrostatics'
  `displaced_mass_kg`.
- Required remediation: For equilibrium mode, compare
  `hydro.displaced_volume_m3 * load_case.seawater_density_kg_m3` to load mass.
  Preserve legacy hydrostatics mass defaults for other callers.

### F-006 - Convergence behavior needs bounded tests

- Sources: D-004, O-002, O-004
- Severity: high
- Classification: safe-now
- Files: `kayakgen/eval/stability.py`, `tests/test_stability.py`
- Statement: Equilibrium must not return best-effort values as if converged.
- Required remediation: Use deterministic bounded bisection with configurable
  tolerance and maximum iterations; add tests for convergence and out-of-bracket
  failure.

### F-007 - RFC/readme status must match the landed slice

- Sources: T-004, D-005
- Severity: medium
- Classification: safe-now
- Files: `docs/rfcs/0011-hydrostatic-stability-load-cases.md`,
  `docs/rfcs/README.md`, `docs/workflows/0016-equilibrium-stability/OPERATOR_REPORT.md`
- Statement: Docs should reflect that load-case/design-waterline work had
  already landed and this workflow lands only a conservative equilibrium
  sinkage slice.
- Required remediation: Update status/readme/operator report without claiming
  high-angle GZ or generalized trim.

## Implementation Guidance

Safe now:

- Add `evaluate_equilibrium_stability(hull, load_case=None, tolerance_kg=1.0,
  max_iterations=60)` or equivalent.
- Solve draft by bisection over copied `Hull` instances using hydrostatic
  volume times load-case density.
- Compute GM0 from the equilibrium draft and the load-case KG normalized at that
  draft.
- Set trim fields truthfully: current centered/symmetric assumption gives zero
  trim; generalized trim remains deferred and warned.
- Add `kayakgen stability --equilibrium` plus tolerance/max-iteration options.
- Add focused tests and keep the current high-angle GZ not-implemented test.

Do not implement:

- Full high-angle `GZCurve`.
- Dynamic stability, active paddler/bracing, or CFD-backed stability.
- Generalized trim without LCG/load-position inputs and trimmed-volume
  hydrostatics.
- Geometry loft changes or golden hydrostatics churn.
