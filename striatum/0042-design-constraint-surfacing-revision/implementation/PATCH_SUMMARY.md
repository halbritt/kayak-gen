# Patch Summary

## Files Changed

- `docs/USER_GUIDE.md`
- `kayakgen/cli/main.py`
- `kayakgen/eval/contract.py`
- `kayakgen/model/__init__.py`
- `kayakgen/model/advisory.py`
- `kayakgen/model/validity.py`
- `kayakgen/search/compare.py`
- `kayakgen/search/sweep.py`
- `kayakgen/ui/desktop.py`
- `kayakgen/ui/web/controllers.py`
- `tests/test_classes.py`
- `tests/test_cli.py`
- `tests/test_compare.py`
- `tests/test_design_validity.py`
- `tests/test_sweep.py`
- `tests/test_web.py`
- `striatum/0042-design-constraint-surfacing-revision/implementation/PATCH_SUMMARY.md`

## Behavior Changed

- Added `DesignValidityFinding`, `DesignValidityReport`, and
  `evaluate_design_validity(...)` with stable codes/messages, required source
  references, additive future-field tolerance, and advisory/unsupported counts.
- Converted `design_advisory()` into a compatibility wrapper over the structured
  design-validity evaluator. Existing `DesignAdvisory.warnings` strings remain
  compatible.
- Added defaulted `design_validity` metadata to `EvaluationResult`, completed
  `CandidateRecord`s, `CandidateSummary`, and `ComparisonReport`, with separate
  design warning and unsupported counts outside objective metrics.
- Wired `kayakgen evaluate`, web `evaluation_payload()`, web metrics/analysis,
  desktop metrics, sweeps, and comparison reports through the shared
  design-validity report.
- Kept design warnings separate from resistance/CFD warnings. Web analysis now
  exposes separate design and resistance warning lists while preserving the
  legacy combined warning list for existing helper consumers.
- Added unsupported records for non-neutral `LCB_frac`, `rocker_bow_m`, and
  `rocker_stern_m`; neutral defaults remain quiet.
- Preserved enforced validation behavior. Invalid `beam_wl_m > beam_oa_m` still
  fails model/CLI validation or is live-clamped by web/desktop helpers before
  model validation.

## Tests Run

- `.venv/bin/python -m pytest tests/test_design_validity.py tests/test_classes.py tests/test_cli.py tests/test_sweep.py tests/test_compare.py tests/test_web.py`
  - Result: 92 passed.
- `.venv/bin/python -m pytest`
  - Result: 263 passed.
- `.venv/bin/python -m pytest tests/test_design_validity.py tests/test_sweep.py`
  - Result: 13 passed after final formatting/import cleanup.
- `.venv/bin/python -m pytest tests/test_sweep.py`
  - Result: 7 passed after simplifying an unchanged hydrostatics call.

Lint note: `.venv/bin/ruff` is not installed in this virtualenv, so ruff was not
run.

## Deferred Findings

- RFC 0006 yellow dismissible desktop banner UX and manual visual confirmation
  remain deferred.
- Full rocker geometry, deadrise, chine radius, flare, section archetype
  controls, and full `LCB_frac` volume redistribution remain deferred.
- High-angle `GZ`, secondary-stability curves, calibrated resistance, final
  design-fitness claims, optimizer warning penalties, closed-volume solver
  dispatch, watertight/`cfd_ready` promotion, and real CFD adapters remain
  deferred.
- No changes were made to candidate status semantics, sweep failure behavior,
  Pareto eligibility, or objective ranking.

## Proposed CHANGELOG.md Entry

- Added RFC 0031 design-validity metadata across evaluate JSON, web payloads,
  desktop/web warning helpers, sweeps, and comparison reports while preserving
  advisory-only behavior and existing validation boundaries.
