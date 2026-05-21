author: reviewer-claims-codex-gpt-5.5-002
schema_version: striatum.review.v1
kind: finding
logical_name: review
workflow_id: 0056-rfc-0058-stage2-3-burndown
role: reviewer_claims
verdict: accept

# Claims / User-Facing Boundaries Review

## Findings

No claim-boundary findings.

I reviewed the workflow 0056 changes for overclaiming and user-facing claim
drift. The only new analytical claim labels are the two RFC 0058 labels:
`unvalidated_hydrostatic_comparison` and
`validated_hydrostatic_comparison`. The wired evaluator call still passes an
empty fit registry, so generated-body GZ output remains
`unvalidated_hydrostatic_comparison` by default.

`cfd_in_loop_evaluator_status` adds the RFC 0058 status vocabulary
`opt_in_only` / `first_class`; these are evaluator-availability states, not
candidate claim-state literals. The default empty-registry path returns
`opt_in_only`, and the Generate form keeps the existing acknowledgement copy:
`I accept evaluation may take orders of magnitude longer`.

The `kayakgen stability residual-plot` output is explicitly a placeholder in
the SVG title and is backed only by fit metadata (`fit_id`, `hull_class`, and
metric values). It does not render measured-vs-analytical curves or present
the stub as real validation.

The forbidden-claim scrub list in `tests/test_web_layout.py` is unchanged
(`git diff -- tests/test_web_layout.py` is empty). The existing focused scrub
test still passes.

## Verification

- `.venv/bin/pytest tests/test_stability_accepted_fit.py tests/test_resolve_analytical_claim_label.py tests/test_cfd_in_loop_evaluator_status.py tests/test_cli_stability.py tests/test_generate_frontier_view.py tests/test_generate_spec_form.py tests/test_generate_state_listener.py tests/test_high_angle_stability_evaluator.py`
  -> 83 passed.
- `.venv/bin/pytest tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
  -> 1 passed.
