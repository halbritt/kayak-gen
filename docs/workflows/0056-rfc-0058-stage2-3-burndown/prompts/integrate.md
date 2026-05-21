# Integration Prompt — workflow 0056

You run after every `implement_*` track has completed and published a
patch summary. Read each implementation's patch summary,
`STAGE_2_3_DECISIONS.md`, and the existing call sites in
`kayakgen/eval/stability/evaluator.py` and
`kayakgen/ui/web/generate_spec_form.py` before making changes.

Wire the new contract functions into their call sites:

- In `kayakgen/eval/stability/evaluator.py`, where the
  `GeneratedBodyGZCurve` is constructed, set its `result_semantics`
  by calling `resolve_analytical_claim_label(hull, fit_registry=())`
  rather than relying on the field's default. Pass `fit_registry=()`
  (decision D-4). If the evaluator has no `hull` reference at the
  construction site, plumb the existing argument forward without
  changing the public evaluator API. Update
  `tests/test_high_angle_stability_evaluator.py` (or the closest
  existing test) to cover the wired path — empty registry returns
  the default literal byte-stably.
- In `kayakgen/ui/web/generate_spec_form.py`, the evaluators block
  render calls `cfd_in_loop_evaluator_status(registry=(), hull_scope=current_scope)`
  to decide whether to render the explicit acknowledgement
  checkbox. When the return is `"first_class"`, hide the
  acknowledgement text but still render the toggle.
  `current_scope` is built from the spec's `base_hull`. If the
  spec form does not have a `HullFamilyScope` instance handy,
  construct a one-element scope (`hull_class=base_hull.hull_class,
  design_hash_envelope=(base_hull.design_hash,)`). Tests:
  `tests/test_generate_spec_form.py` gets a stepped test that asserts
  the default render path (`opt_in_only`) still shows the
  acknowledgement copy, and a stub-registry test that confirms
  the `first_class` branch hides it.

Do **not** modify any of the author tracks' modules
(`high_angle_contracts.py`, `generative_jobs.py`,
`stability_cli.py`, `generate_frontier_view.py`,
`generate_state_listener.py`). If a track's module surface is
wrong, escalate as a `needs_revision` for that track rather than
patching around it.

Requirements:

- The forbidden-claim scan, ui-theme-orphan scan, import-boundary
  scan, and services-boundary scan must remain green.
- The full repo suite minus the env-gated OpenFOAM smoke must pass
  before you publish the patch summary.
- The default behavior must remain byte-stable: with the empty
  registry passed in, `result_semantics` resolves to
  `unvalidated_hydrostatic_comparison` and the spec form's
  acknowledgement copy stays visible.

Write scope:
- `kayakgen/eval/stability/evaluator.py`
- `kayakgen/ui/web/generate_spec_form.py`
- `tests/test_high_angle_stability_evaluator.py`
- `tests/test_generate_spec_form.py`
- `striatum/0056-.../integration/PATCH_SUMMARY.md`

Publish the required patch summary artifact.
