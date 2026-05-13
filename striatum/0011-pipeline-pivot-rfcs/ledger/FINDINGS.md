# Findings ledger - 0011

author: operator
Date: 2026-05-13
Review inputs: roadmap, domain/math/mesh, implementation/ops

## Stats

- Source findings: 24
- Deduplicated findings: 12
- By severity: blocker 4 / high 6 / medium 2 / low 0
- Actionable now: 8
- Needs human decision at final review: 4
- Human decisions answered post-run: 6

## Findings

### F-001 - Sweep records need pre-validation candidate identity

- Sources: F-ROAD-002, F-OPS-001
- Severity: high
- Classification: actionable-now
- RFC(s): 0009
- File(s): `docs/rfcs/0009-sweep-run-records.md`, future
  `kayakgen/search/sweep.py`
- Statement: RFC 0009 requires invalid candidates to be recorded, but its draft
  centers records on `hull_hash`, which only exists after successful `Hull`
  validation.
- Required remediation: Add `candidate_index` and deterministic
  `candidate_key` based on spec hash plus ordered variable assignments. Make
  `hull_hash` optional and require failed records to persist attempted
  parameters plus validation errors.

### F-002 - RFC 0009/0010 sequencing and mesh artifact dependency are unclear

- Sources: F-ROAD-001, F-OPS-005
- Severity: high
- Classification: actionable-now
- RFC(s): 0009, 0010
- File(s): `docs/rfcs/0009-sweep-run-records.md`,
  `docs/rfcs/0010-cfd-ready-mesh-contract.md`, `docs/rfcs/README.md`
- Statement: RFC 0009 includes mesh diagnostics artifacts while RFC 0010
  defines those diagnostics later.
- Required remediation: Make mesh diagnostics optional in RFC 0009 and
  explicitly dependent on RFC 0010 diagnostics being present. In the roadmap,
  sequence the safe implementation as mesh diagnostics plus sweep records.

### F-003 - Mesh readiness lacks profile and tolerance contract

- Sources: F-DOM-001, F-DOM-002, F-OPS-005
- Severity: blocker
- Classification: actionable-now
- RFC(s): 0010
- File(s): `docs/rfcs/0010-cfd-ready-mesh-contract.md`, future
  `kayakgen/eval/mesh_diagnostics.py`
- Statement: `cfd_ready` is not testable without a solver profile, and raw
  index-topology checks are insufficient for current meshes with independent
  station-ring vertices.
- Required remediation: Add `MeshSolverProfile` to the RFC/code contract, make
  `cfd_ready` impossible without a named profile, keep current default readiness
  below `cfd_ready`, and implement diagnostics that report raw and
  tolerance-welded boundary/nonmanifold counts.

### F-004 - CFD coordinate convention needs explicit human decision

- Sources: F-DOM-003
- Severity: high
- Classification: needs-human-decision
- RFC(s): 0010
- File(s): `docs/rfcs/0010-cfd-ready-mesh-contract.md`
- Statement: The mesh manifest says x spans `-L/2` to `+L/2`, but not which end
  is bow. This matters for future asymmetric hulls and CFD flow direction.
- Required remediation: Record as a human decision. Do not silently choose in
  implementation. RFC/code may include nullable or provisional metadata fields
  and warnings that bow-positive convention is undecided.
- Post-run decision: `+x` points toward the stern, `-x` points toward the bow;
  bow appears on the left in standard side views.

### F-005 - Load-case displacement semantics are undefined

- Sources: F-ROAD-003, F-DOM-004
- Severity: blocker
- Classification: needs-human-decision
- RFC(s): 0011
- File(s): `docs/rfcs/0011-hydrostatic-stability-load-cases.md`
- Statement: RFC 0011 defines paddler/hull/cargo mass but does not decide
  whether v1 solves equilibrium waterline or reports design-waterline
  diagnostics only.
- Required remediation: Keep implementation to design-waterline diagnostics.
  Add explicit `load_mass_kg`, `displaced_mass_kg`, and
  `displacement_error_kg`; warn that the result is not an equilibrium load-case
  stability pass/fail until a human chooses sinkage/trim semantics.
- Post-run decision: RFC 0011 should support both diagnostic and equilibrium
  modes, with equilibrium solving sinkage and trim together.

### F-006 - KG reference frame conflicts with current GM formula

- Sources: F-DOM-005, F-OPS-004
- Severity: blocker
- Classification: needs-human-decision
- RFC(s): 0011
- File(s): `docs/rfcs/0011-hydrostatic-stability-load-cases.md`,
  `kayakgen/eval/hydrostatics.py`
- Statement: The draft names `kg_above_waterline_m`, but current `GM0_m`
  subtracts `0.25` as if KG is baseline/keel-referenced.
- Required remediation: Do not guess a new reference frame. Rename the safe v1
  field to `kg_above_keel_m`/baseline-referenced, preserve numeric compatibility,
  and record waterline/seat reference as a human decision.
- Post-run decision: support keel, waterline, and seat-relative KG references
  and normalize internally to keel/baseline height for computation.

### F-007 - Stability result contract must replace top-level `GZCurve`

- Sources: F-ROAD-004, F-DOM-006, F-OPS-004
- Severity: high
- Classification: actionable-now
- RFC(s): 0011
- File(s): `docs/rfcs/0011-hydrostatic-stability-load-cases.md`,
  `kayakgen/eval/contract.py`, future `kayakgen/eval/stability.py`
- Statement: `EvaluationResult.stability: GZCurve | None` cannot carry load
  case, method, status, warnings, or explicit not-implemented provenance.
- Required remediation: Add `LoadCase` and `StabilityResult`, nest
  `GZCurve | None`, and change `EvaluationResult.stability` to
  `StabilityResult | None`.

### F-008 - Resistance metadata and raw validity warnings are missing

- Sources: F-ROAD-005, F-DOM-007, F-DOM-008, F-OPS-003
- Severity: high
- Classification: actionable-now
- RFC(s): 0012
- File(s): `docs/rfcs/0012-resistance-model-calibration.md`,
  `kayakgen/eval/contract.py`, `kayakgen/eval/resistance.py`
- Statement: Current resistance curves only contain numeric arrays and code
  wording mixes Wigley verification/calibration with kayak calibration.
- Required remediation: Add `ResistanceMetadata` to `ResistanceCurve`, mark
  current output `raw_ittc_michell`, `uncalibrated`, and
  `comparative_filter`, include quadrature/constants/warnings, and rename
  Wigley language to verification unless a human-selected calibration dataset
  exists.
- Post-run decision: prefer published kayak/canoe resistance data if a usable
  source can be found and licensed; Sea Kayaker-derived tables and published
  passive-drag studies are first candidates to vet.

### F-009 - Pareto comparison must not default to exploratory resistance

- Sources: F-DOM-009, F-OPS-002
- Severity: blocker
- Classification: actionable-now
- RFC(s): 0013
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`, future
  `kayakgen/search/pareto.py`
- Statement: RFC 0013 can create a misleading primary frontier if it minimizes
  raw uncalibrated resistance by default.
- Required remediation: Add objective provenance requirements and label any
  raw-resistance frontier as exploratory. In this workflow, implement only pure
  Pareto utilities/tests and avoid default CLI/UI ranking on raw resistance.
- Post-run decision: uncalibrated analytical resistance is not allowed as a
  default Pareto objective; wait for calibrated RFC 0012 output.

### F-010 - Sweep records lack evaluator provenance

- Sources: F-DOM-010
- Severity: medium
- Classification: actionable-now
- RFC(s): 0009, 0011, 0012
- File(s): `docs/rfcs/0009-sweep-run-records.md`, future
  `kayakgen/search/sweep.py`
- Statement: Candidate records need evaluator settings and versions for
  auditability.
- Required remediation: Add `evaluator_settings`, `evaluator_versions`, and
  warnings to candidate records. Include load-case, mesh diagnostics profile,
  and resistance metadata when available.

### F-011 - RFC 0013 dependency/title should match staged implementation

- Sources: F-ROAD-006, F-ROAD-007
- Severity: medium
- Classification: docs-only
- RFC(s): 0013
- File(s): `docs/rfcs/0013-pareto-frontier-comparison-ui.md`
- Statement: RFC 0013 uses mesh diagnostics without listing RFC 0010 and its
  title promises UI while acceptance is report/CLI-first.
- Required remediation: Add RFC 0010 to context and either retitle toward
  comparison reports or explicitly gate web UI acceptance behind later RFC 0008
  completion.

### F-012 - Avoid new dependencies and tighten CLI contracts

- Sources: F-OPS-006, F-OPS-007
- Severity: medium
- Classification: actionable-now
- RFC(s): 0009-0013
- File(s): `kayakgen/cli/main.py`, tests
- Statement: New commands can become uneven and dependency-heavy if YAML,
  pandas, scipy, or web-test dependencies are added prematurely.
- Required remediation: Keep the safe slice JSON/Pydantic/stdlib/NumPy only.
  Add help, bad-input, and output-contract tests for each command touched.

## Implementation guidance

Safe now:

- Revise RFCs 0009-0013 for the findings above.
- Implement conservative mesh diagnostics and `mesh-check`.
- Implement `ResistanceMetadata` and warnings without choosing calibration data.
- Implement `LoadCase`/`StabilityResult` for initial design-waterline stability
  only, preserving existing GM output compatibility.
- Implement deterministic JSON sweep records with candidate keys, failed
  records, resume, evaluator provenance, optional mesh diagnostics, and CSV.
- Implement pure Pareto/dominance utilities with synthetic tests only.

Do not implement without human decision:

- Exact CFD readiness semantics for watertight vs open-surface solver profiles:
  decided for first profile as open wetted surface; watertight remains future.
- Bow-positive coordinate convention and flow direction: decided as stern
  positive (`+x` stern, `-x` bow).
- Equilibrium waterline/sinkage/trim solving: decided as a required mode that
  solves sinkage and trim together.
- Waterline- or seat-referenced KG semantics: decided as multi-reference input
  normalized internally to keel/baseline height.
- Canonical resistance calibration dataset or raw validity envelope: direction
  chosen as published kayak/canoe data, but the concrete dataset still requires
  source/provenance review.
- Default Pareto ranking that includes exploratory resistance as a primary
  objective: decided no; wait for calibrated resistance.
