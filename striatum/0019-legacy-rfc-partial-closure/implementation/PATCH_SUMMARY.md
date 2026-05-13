author: operator [self-declared: operator-implementer]

# Patch summary - workflow 0019

Run: `run_777e1515eafe41c6adc27b3df1ab8ae6`
Job: `implement_findings`

## Files changed

- `docs/rfcs/0004-plumb-bow.md`
- `docs/rfcs/0006-design-constraints.md`
- `docs/rfcs/README.md`
- `docs/workflows/0019-legacy-rfc-partial-closure/OPERATOR_REPORT.md`
- `generator.py`
- `kayakgen/model/__init__.py`
- `kayakgen/model/advisory.py`
- `kayakgen/model/classes.py`
- `kayakgen/model/geometry.py`
- `kayakgen/ui/desktop.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `tests/test_classes.py`
- `tests/test_cli.py`
- `tests/test_golden.py`
- `tests/test_plumb_bow.py`
- `tests/test_web.py`

## Findings addressed

- F-001/F-002: renamed the misleading watertight plumb-bow test, kept open
  surface semantics explicit, and updated RFC 0004/README wording so exact
  end caps and watertight solids remain deferred.
- F-003: applied bow-rake blending to deck centerline height while preserving
  default golden geometry.
- F-004: added focused non-default rake tests for `Cp` and `center_box_ratio`
  interactions.
- F-005: updated RFC 0006/README status wording and annotated class range
  source intent in code.
- F-006: added shared `design_advisory()`, surfaced warnings in desktop/web
  metrics, clamped web `beam_wl_m <= beam_oa_m`, and added validation payload
  tests.
- F-007: extended the legacy `KayakGenerator` shim with `beam_wl` and
  `bow_rake` compatibility arguments while preserving default goldens.
- F-008: added CLI `generate` and `evaluate --skip-resistance` coverage for
  non-default `bow_rake` and explicit `beam_wl_m`.

## Still deferred

- Exact plumb-stem/end-cap geometry at `x = +/-L/2`.
- Closed/watertight hull-plus-deck solid readiness.
- Asymmetric bow/stern rake controls.
- Desktop yellow dismissible validation banner and manual visual closure.
- Future shape parameters such as rocker, deadrise, chine radius, and fully
  honoured `LCB_frac`.

## Verification

- `.venv/bin/python -m pytest tests/test_plumb_bow.py tests/test_golden.py tests/test_cli.py tests/test_classes.py tests/test_web.py -q`
  -> 56 passed.
- `.venv/bin/python -m pytest -q` -> 133 passed.
- `git diff --check` -> clean.
- `ruff` was not run because it is not installed in the current virtualenv.
