author: reviewer-ops-tests-codex-gpt-5.5-002
schema_version: striatum.review.v1
kind: finding
logical_name: review
workflow_id: 0056-rfc-0058-stage2-3-burndown
role: reviewer_ops_tests
verdict: needs_revision

# Ops / Tests Review

## Findings

### Medium: first-class CFD-in-loop hides the acknowledgement but form submission still requires it

`kayakgen/ui/web/generate_spec_form.py:1094` hides the CFD-in-loop
acknowledgement checkbox whenever
`generative_cfd_in_loop_status === 'opt_in_only'` is false, which is the
intended RFC 0058 D-14 branch for a future `"first_class"` graduation.
However, `build_spec_from_form_state()` still refuses any request with
`generative_evaluators.cfd_in_loop=True` and
`generative_cfd_in_loop_acknowledged=False`, regardless of
`generative_cfd_in_loop_status` (`kayakgen/ui/web/generate_spec_form.py:622`).

That leaves the first-class branch internally inconsistent: once the helper is
patched or wired to return `"first_class"`, the UI can hide the only control
that would satisfy the serializer, and a user who toggles the first-class
CFD-in-loop evaluator will hit `cfd_in_loop_ack_required`. The existing tests
cover the hidden-state mirror (`tests/test_generate_spec_form.py:342`) and the
opt-in refusal (`tests/test_generate_spec_form.py:280`) separately, but no test
asserts that a first-class status admits a CFD-in-loop request without the
acknowledgement.

Required remediation: make the serializer's acknowledgement gate conditional
on the same first-class status used by the render branch, and add a regression
test with `generative_cfd_in_loop_status="first_class"`,
`generative_evaluators.cfd_in_loop=True`, and
`generative_cfd_in_loop_acknowledged=False`.

## Coverage Notes

- The two contract functions have branch coverage for empty registries,
  one-sided fits, accepted/rejected records, non-covering scopes, covering
  scopes, persistent opt-out, and persistent opt-in.
- The schema tests cover threshold refusal, strict-skip warning, accepted-fit
  metadata requirements, promotion-packet review failures, SHA-256 shape, and
  non-empty hull-family envelopes.
- The stability CLI tests cover happy and refusal paths for
  `ingest-rig-run`, `promote-fixture`, and `accept-fit`, plus the
  `residual-plot` happy path. A direct `residual-plot` refusal test would be a
  useful hardening addition, but the command is covered indirectly by model
  validation and the full suite remained green.
- Frontier-view colour wiring is covered for hull rows with an empty registry
  (`kg-state-raw`) and a covering accepted fit (`kg-state-validated`), and the
  existing forbidden high-angle metric scrub still holds.
- NB-1 stepped-clock variants cover install/no-thread, running ticks, idle
  ticks, terminal-detail refresh, coalescing, reinstall, and wall-clock no-op
  behavior with `time.sleep` banned in stepped mode.

## Verification

- Focused RFC 0058 / Generate tests:
  `.venv/bin/pytest tests/test_stability_accepted_fit.py tests/test_resolve_analytical_claim_label.py tests/test_cfd_in_loop_evaluator_status.py tests/test_cli_stability.py tests/test_generate_frontier_view.py tests/test_generate_spec_form.py tests/test_generate_state_listener.py tests/test_high_angle_stability_evaluator.py`
  -> 83 passed.
- Full suite: `.venv/bin/pytest` -> 1091 passed, 4 skipped. The skips were the
  opt-in OpenFOAM-v2512 smoke/stage tests that require
  `KAYAKGEN_OPENFOAM_SMOKE=1` / `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`.
- Ruff: `.venv/bin/ruff check .` -> passed.
- Explicit scans:
  `.venv/bin/pytest tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces tests/test_ui_theme.py::test_no_orphan_color_literals_under_kayakgen_ui tests/test_import_boundaries.py tests/test_services_boundaries.py`
  -> 100 passed.
