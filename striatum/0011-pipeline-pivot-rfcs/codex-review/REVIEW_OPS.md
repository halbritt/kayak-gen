# Implementation/ops review - RFCs 0009-0013

author: operator
Verdict recommendation: accept_with_findings

Accept the RFC set as a sequenced roadmap, but keep implementation CLI-first,
schema-first, and dependency-neutral. Do not implement RFC 0013 web comparison
work until RFC 0009 artifacts, RFC 0011 stability placeholders, and RFC 0012
resistance metadata have landed.

Tests observed by the review agent: `.venv/bin/python -m pytest -q` returned
69 passed, 2 xfailed.

## Findings

### F-OPS-001 - High - Sweep failure records need a pre-validation candidate key

Invalid candidates cannot be reliably keyed by `Hull.hash()`. Add
`candidate_key = sha256(spec_hash + ordered variable JSON)` to every
`CandidateRecord`; set `hull_hash` only for valid hulls.

### F-OPS-002 - High - Comparison RFC depends on missing artifacts

RFC 0013 should defer implementation except pure Pareto unit tests until sweep
records, resistance metadata/warnings, and stability placeholders exist.

### F-OPS-003 - High - Resistance output is too precise-looking for sweep ranking

Add default metadata to `ResistanceCurve`: model family, accepted use, constants,
quadrature settings, calibration status, and warnings. Keep calibration data
selection out of scope.

### F-OPS-004 - Medium - Stability has placeholder shape and hidden KG

Add `LoadCase` and `StabilityResult` with initial GM only. Preserve
`Hydrostatics.GM0_m` for compatibility, but record load-case source and make
full GZ explicitly not implemented.

### F-OPS-005 - Medium - Mesh diagnostics should not promote readiness

Implement pure NumPy diagnostics and `mesh-check` first. Default readiness must
not exceed `stl_surface` or `cfd_surface_candidate`, never `cfd_ready`.

### F-OPS-006 - Medium - CLI command semantics need tests

Each new command should have help, bad-input, and output-contract tests. For
RFC 0009, add `--resume` and JSON-only specs unless a dependency decision adds
YAML.

### F-OPS-007 - Low - Avoid new dependencies

Use JSON/Pydantic, stdlib `csv`, NumPy mesh diagnostics, and stdlib comparison
helpers. Do not add YAML, pandas, scipy, or web-test dependencies in this safe
slice.

## Safe implementation slice

1. Revise RFC wording for candidate keys, dependency sequencing, load-case
   diagnostics, resistance metadata, and exploratory Pareto warnings.
2. Add mesh diagnostics and `mesh-check`.
3. Add resistance metadata/warnings.
4. Add `LoadCase`/`StabilityResult` initial-stability placeholder.
5. Add deterministic JSON sweep expansion, candidate records, resume, and CSV.
6. Add pure Pareto utilities and synthetic tests only; defer UI.
