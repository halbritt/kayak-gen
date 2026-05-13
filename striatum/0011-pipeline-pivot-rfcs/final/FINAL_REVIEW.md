# Final review - 0011

author: operator
Date: 2026-05-13
Verdict: accepted

## Coverage check

| Finding | Required action | Status | Evidence |
|---|---|---|---|
| F-001 | Fix | pass | `docs/rfcs/0009-sweep-run-records.md` and `kayakgen/search/sweep.py` use `candidate_key` before validation; `tests/test_sweep.py` covers invalid failed records. |
| F-002 | Fix | pass | RFC 0009 marks mesh diagnostics optional and dependent on RFC 0010; `run_sweep` only writes mesh diagnostics when enabled. |
| F-003 | Fix | pass | `kayakgen/eval/mesh_diagnostics.py` adds profile/readiness schema and raw/welded counts; tests cover default, deck, welded, nonfinite, and degenerate cases. |
| F-004 | Human decision | pass | Patch summary keeps bow-positive coordinate convention deferred; implementation does not choose a flow direction. |
| F-005 | Escalate and safe diagnostic | pass | `StabilityResult` reports design-waterline-only load/displacement/error fields and warnings; no equilibrium solver was added. |
| F-006 | Escalate and preserve compatibility | pass | Safe v1 field is `kg_above_keel_m`; default GM remains compatible; waterline/seat reference remains a human decision. |
| F-007 | Fix | pass | `EvaluationResult.stability` is now `StabilityResult | None` with optional nested `GZCurve`; `tests/test_stability.py` covers round-trip. |
| F-008 | Fix | pass | `ResistanceMetadata` is populated by `resistance_curve`; tests assert model family, calibration status, use, warnings, and quadrature. |
| F-009 | Fix safe slice | pass | `kayakgen/search/pareto.py` requires accepted-use provenance for protected objectives; no CLI/UI default raw-resistance ranking was added. |
| F-010 | Fix | pass | `CandidateRecord` includes evaluator settings, versions, warnings, and optional mesh diagnostics; `tests/test_sweep.py` covers mesh artifacts. |
| F-011 | Docs fix | pass | RFC 0013 now lists RFC 0010 and gates exploratory resistance/UI behavior. |
| F-012 | Fix | pass | Implementation stayed within existing dependencies; CLI tests cover `sweep`, `mesh-check`, and `stability`. |

## Test review

Final verification reran `.venv/bin/python -m pytest -q`, which returned 95
passed and 2 expected xfails for the known RFC 0005 low-Froude and 200 ms
acceptance gaps. `git diff --check` passed. `.venv/bin/kayakgen --help` showed
the new `mesh-check`, `stability`, and working `sweep` commands. Ruff could not
be run because `.venv/bin/ruff` is not installed.

## Verdict notes

Accepted. The safe structural implementation matches the ledger: the project
now has draft pivot RFCs, reproducible sweep records, conservative mesh
diagnostics, explicit resistance provenance, initial stability/load-case
results, and provenance-aware Pareto utilities. The remaining domain decisions
are recorded rather than guessed.
