author: integrator-claude-opus-4.7-001
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
workflow_id: 0056-rfc-0058-stage2-3-burndown
job_id: integrate

# Patch Summary

## Changes

- `kayakgen/eval/stability/evaluator.py`: imported
  `resolve_analytical_claim_label` from `high_angle_contracts` and wired
  it into the `_generated_body_gz_curve` construction site. Pass
  `fit_registry=()` (decision D-4); the resolved literal is fed to
  `GeneratedBodyGZCurve.result_semantics` instead of relying on the
  field default.
- `kayakgen/ui/web/generate_spec_form.py`:
  - imported `HullFamilyScope`, `CFDInLoopEvaluatorStatus`, and
    `cfd_in_loop_evaluator_status` at the form-builder boundary;
  - added `_current_hull_family_scope(state)` that returns a one-element
    scope from `base_hull` when both `hull_class` and `design_hash`
    are present, else `None`;
  - added `refresh_cfd_in_loop_status(app)` that calls
    `cfd_in_loop_evaluator_status(registry=(), hull_scope=...)` and
    mirrors the result onto
    `state.generative_cfd_in_loop_status` (default `"opt_in_only"`);
  - `initialize_form_state` seeds the new state key to
    `"opt_in_only"`;
  - `render_spec_form_section` calls `refresh_cfd_in_loop_status` once
    after `initialize_form_state`;
  - the CFD-in-loop acknowledgement checkbox now carries
    `v_show=("generative_cfd_in_loop_status === 'opt_in_only'",)`, so
    the toggle still renders when the helper graduates the evaluator to
    `"first_class"` while the acknowledgement copy hides reactively
    (D-14);
  - added `refresh_cfd_in_loop_status` to `__all__`.
- `tests/test_high_angle_stability_evaluator.py` (new): one wired-default
  test that drives `evaluate_gz_curve` on a generated closed body and
  asserts `result_semantics == "unvalidated_hydrostatic_comparison"` —
  byte-stable against the pre-wiring default.
- `tests/test_generate_spec_form.py`: extended with two
  `refresh_cfd_in_loop_status` tests — a default test that asserts the
  `"opt_in_only"` mirror onto state, and a stub-registry test that
  monkeypatches `cfd_in_loop_evaluator_status` to return
  `"first_class"` and asserts the literal lands on state so the
  reactive `v_show` hides the acknowledgement checkbox.

## Byte-stability

- `resolve_analytical_claim_label(hull, fit_registry=())` returns
  `"unvalidated_hydrostatic_comparison"` for every hull. The
  `GeneratedBodyGZCurve.result_semantics` default is unchanged in the
  wired path, so the existing
  `tests/test_stability.py::test_generated_body_v1_*` assertions hold
  unchanged.
- `cfd_in_loop_evaluator_status(registry=(), hull_scope=...)` always
  returns `"opt_in_only"` with an empty registry, so the
  acknowledgement copy stays visible until a real fit lands.

## Author-track surface

- No track-owned modules were modified
  (`high_angle_contracts.py`, `generative_jobs.py`,
  `stability_cli.py`, `generate_frontier_view.py`,
  `generate_state_listener.py` are untouched here).

## Verification

- `.venv/bin/python -m pytest --ignore=tests/test_openfoam_v2512_smoke.py`
  — 1089 passed, 2 skipped (env-gated OpenFOAM succeeded stages).
- `.venv/bin/python -m ruff check .` — clean.
- `.venv/bin/python -m pytest tests/test_ui_theme.py tests/test_web_layout.py tests/test_import_boundaries.py tests/test_services_boundaries.py`
  — 126 passed (forbidden-claim, ui-theme-orphan, import-boundary, and
  services-boundary scans all green).
