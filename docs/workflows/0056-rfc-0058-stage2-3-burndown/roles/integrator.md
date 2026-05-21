# Role: Integrator

Wire the stage 2 contract functions into their RFC-named call
sites:

- `resolve_analytical_claim_label(hull, fit_registry=())` at the
  `GeneratedBodyGZCurve` construction site in
  `kayakgen/eval/stability/evaluator.py`.
- `cfd_in_loop_evaluator_status(registry=(), hull_scope=...)` at
  the evaluators-block render in
  `kayakgen/ui/web/generate_spec_form.py`.

Register the stability CLI sub-app from `kayakgen/cli/main.py`.

Do not re-implement any track's logic. Limit edits to the wiring
layer and the integration tests. If a track's module is missing
or its public surface is wrong, escalate as a `needs_revision` for
that track rather than patching around it.

Run the full repo suite (minus the env-gated OpenFOAM smoke) plus
ruff and the forbidden-claim / ui-theme-orphan / import-boundary /
services-boundary scans before publishing your patch summary.

Publish the required patch summary with the exact packet byline.
