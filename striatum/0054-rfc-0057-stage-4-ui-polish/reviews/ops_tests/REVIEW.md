author: reviewer-ops-tests-codex-gpt-5.5-001

# Review: ops/tests for RFC 0057 Stage 4 UI polish

## Findings

### Medium: cancellation tests pass even if cancellation is ignored

The cancellation/resume tests do not currently prove the operational
contract they name. In `tests/test_generative_jobs_manager.py`,
`test_manager_cancel_transitions_to_resumable` accepts either
`resumable` or `succeeded` after calling `cancel()`, and
`test_manager_resume_after_cancel` returns early when the job does not
become resumable. The same pattern appears in
`tests/test_generative_jobs_subprocess.py::test_subprocess_manager_cancel_via_flag`
and the web lifecycle test in `tests/test_generative_jobs_web.py`.

Because `succeeded` is treated as an acceptable outcome after a cancel
request, a regression where the runner stops checking
`progress_sink.should_cancel()` would still satisfy these tests for the
fast sweep payloads. That leaves the Stage 4 subprocess-default and
operational cancellation path under-tested even though the manager and
route APIs report that cancellation was requested.

Suggested fix: add at least one deterministic cancellation test that
uses a controllable fake runner/progress sink, a deliberately blocking
candidate emission seam, or a monkeypatched runner that waits until
`cancel()` has been observed. That test should require terminal
`state == "resumable"`, `error.kind == "cancelled_by_operator"`, and
subprocess `cancel.flag` cleanup.

## Coverage Notes

The Stage 4 surfaces are otherwise covered at the unit/route level:

- form builder defaults, CLI-shape serialization, admissible objective
  filtering, display-only refusal, claim-gated refusal, and CFD-in-loop
  acknowledgement: `tests/test_generate_spec_form.py`
- Pareto scatter/table view-model, deterministic row ordering, third
  objective color axis, forbidden metric scrubbing, candidate handoff,
  and undo: `tests/test_generate_frontier_view.py`
- auto-poll cadence, terminal detail refresh, listener teardown, reinstall,
  coalescing, and manager exception tolerance:
  `tests/test_generate_state_listener.py`
- fork-with-new-seed primitive and route errors:
  `tests/test_generative_jobs_fork.py`
- log redaction and byte-stability: `tests/test_log_redaction.py`
- subprocess manager default behavior and crash-survival:
  `tests/test_generative_jobs_subprocess.py`,
  `tests/test_generative_jobs_web.py`, and `tests/test_cli_serve.py`

Residual risk: the auto-poll listener tests use short wall-clock sleeps.
They passed locally, but they remain scheduler-sensitive compared with a
fake clock or directly stepped poll loop.

## Verification

- `pytest` was not on PATH in the shell; reran through repo venv.
- `.venv/bin/python -m pytest tests/test_generate_spec_form.py tests/test_generate_frontier_view.py tests/test_generate_state_listener.py tests/test_generative_jobs_fork.py tests/test_log_redaction.py tests/test_generative_jobs_web.py tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py`:
  `89 passed in 34.82s`
- `.venv/bin/python -m pytest tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces tests/test_ui_theme.py::test_no_orphan_color_literals_under_kayakgen_ui`:
  `2 passed in 0.87s`
- `.venv/bin/python -m pytest`:
  `1045 passed, 4 skipped in 402.97s`

The four skips are the expected opt-in OpenFOAM smoke/stage tests gated
on `KAYAKGEN_OPENFOAM_SMOKE=1` and related local solver availability.
