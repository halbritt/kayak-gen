author: implementer-codex-gpt-5.5-001

# Form Builder Patch Summary

## Scope

- Updated `kayakgen/ui/web/generate_spec_form.py`.
- Updated `tests/test_generate_spec_form.py`.
- Did not edit `kayakgen/ui/web/app.py`.

## Changes

- Tightened the Generate objective picklist to use the central
  `is_objective_metric_admissible(..., explicit_exploratory=False)` gate.
- Kept display-only high-angle GZ and turning metrics out of the picklist.
- Kept RFC 0044 claim-gated metrics (`Rt_N_last`, `design_fitness`) out of
  the picklist and refused stale/hand-edited selections with structured inline
  refusal metadata.
- Changed the objective UI control to a multi-select bound to selected metrics,
  with per-metric direction controls.
- Added serializer support for the multi-select state shape while retaining the
  previous `generative_objectives` list shape for compatibility.

## Verification

- PASS: `.venv/bin/pytest -q tests/test_generate_spec_form.py`
- PASS: `.venv/bin/python -m py_compile kayakgen/ui/web/generate_spec_form.py tests/test_generate_spec_form.py`
- PARTIAL: `.venv/bin/pytest -q tests/test_generate_spec_form.py tests/test_generative_jobs_web.py tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py`
  - Result: 46 passed, 1 failed.
  - Failure: `tests/test_generative_jobs_web.py::test_generate_panel_submit_and_refresh`
    raises a `RecursionError` through `kayakgen/ui/web/generate_state_listener.py`
    when calling `web.ctrl.refresh_generative_jobs()`. That file is outside this
    job's write scope.
