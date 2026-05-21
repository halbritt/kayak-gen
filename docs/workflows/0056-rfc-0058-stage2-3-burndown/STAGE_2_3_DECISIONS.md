# Workflow 0056 — RFC 0058 stage 2 + 3 + NB-1 decisions

This workflow lands RFC 0058 stages 2 and 3 on top of the schemas
that workflow 0055 merged. Stage 2 = the two contract functions
(`resolve_analytical_claim_label`, `cfd_in_loop_evaluator_status`).
Stage 3 = the `kayakgen stability` CLI sub-app + Generate panel
read-model wiring. The workflow also closes workflow 0054's only
non-blocking successor item, **NB-1** (stepped-clock seam for the
auto-poll listener tests).

Defaults are byte-stable: with no accepted `StabilityFitRecord` and
no graduated CFD-in-loop fit, every contract returns the value the
codebase already produces. No fixture is promoted. No claim-state
literal beyond the two already named in RFC 0058 is introduced.

| Row  | Decision                                                                                                                                            |
|------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| D-1  | `resolve_analytical_claim_label(hull, fit_registry) -> Literal["unvalidated_hydrostatic_comparison", "validated_hydrostatic_comparison"]` lives in `kayakgen/eval/stability/high_angle_contracts.py` and is exported from `kayakgen/eval/stability/__init__.py`. |
| D-2  | `GeneratedBodyGZCurve.result_semantics` widens its `Literal` to `{"unvalidated_hydrostatic_comparison", "validated_hydrostatic_comparison"}`. Default value stays `unvalidated_hydrostatic_comparison`. |
| D-3  | `fit_registry` is an iterable of accepted `StabilityFitRecord` instances. The resolver returns `validated_hydrostatic_comparison` only when at least one record has `acceptance_verdict="accepted"` AND its `hull_family_scope` matches the hull's `hull_class` AND `design_hash` is in `hull_family_scope.design_hash_envelope`. |
| D-4  | The resolver does **not** load fits from disk. Callers (e.g. the evaluator) pass an in-memory iterable. Stage 4 (a future workflow) is when real fits land; until then the wired call site passes `()`. |
| D-5  | `cfd_in_loop_evaluator_status(*, registry, hull_scope, persistent_opt_in: bool \| None = None) -> Literal["opt_in_only", "first_class"]` lives in `kayakgen/services/generative_jobs.py`. `registry` is a `StabilityFitRegistry`-shaped iterable (see D-7); `hull_scope` is a `HullFamilyScope`. |
| D-6  | Default behavior: `cfd_in_loop_evaluator_status` returns `"opt_in_only"` whenever (a) `registry` does not contain an accepted analytical `StabilityFitRecord` covering `hull_scope`, OR (b) `registry` does not contain an accepted **CFD-in-loop** fit covering the same scope, OR (c) the operator's persistent setting (when supplied) explicitly opts out. Otherwise `"first_class"`. |
| D-7  | A CFD-in-loop fit is identified by a `fit_kind` discriminator on `StabilityFitRecord` (extension) — but RFC 0058 stage 2 does **not** ship that discriminator. For this workflow, the helper accepts a structural protocol with a `.kind` attribute (`"analytical"` or `"cfd_in_loop"`); the registry is empty by default, so the helper still returns `"opt_in_only"`. A successor RFC adds the discriminator field on the record. |
| D-8  | Persistent opt-out wins over graduation (RFC 0058 open-question recommendation). When `persistent_opt_in is False`, the helper returns `"opt_in_only"` even if both fits are present. When `persistent_opt_in is None` (caller-unaware), graduation can take effect. |
| D-9  | `kayakgen stability` CLI sub-app lives in `kayakgen/cli/stability_cli.py` and is registered as `app.add_typer(stability_app, name="stability")` in `kayakgen/cli/main.py`. Four subcommands: `ingest-rig-run`, `promote-fixture`, `accept-fit`, `residual-plot`. |
| D-10 | All four CLI subcommands are **schema-only** — they validate inputs against the workflow-0055 Pydantic records, write the canonical manifest JSON to disk (`data/stability/fixtures/<fixture_id>/manifest.json` or `data/stability/fits/<fit_id>.json`), refuse overwrites, and exit with non-zero on validation failure. None of them ingest physical sensor data, run a fit, or render a real residual plot beyond a vendored stub. |
| D-11 | `kayakgen stability residual-plot` writes an SVG placeholder that reuses the resistance-side renderer pattern from RFC 0054 (vendored). The SVG content for stage 3 contains the fit_id, hull_class, and the four metric values — no real curve data. The fit-vs-measured plot lands in a successor workflow once a real fit exists. |
| D-12 | `data/stability/fixtures/` and `data/stability/fits/` are created on demand by the CLI. Neither directory is committed; both are gitignored. The CLI's tests use `tmp_path` for all writes. |
| D-13 | Generate panel frontier-view colour wiring: `_render_generate_frontier_scatter()` (or its successor) calls `resolve_analytical_claim_label(hull, fit_registry=())` to compute the scatter-point colour for each row. Validated points use the existing `theme.kg-state-validated` token; unvalidated points use `theme.kg-state-raw`. No new token, no scatter-API change. |
| D-14 | Generate panel form-builder evaluator block: `_render_evaluators_block()` (or its successor) calls `cfd_in_loop_evaluator_status(registry=(), hull_scope=current_scope)` and hides the explicit acknowledgement checkbox when the return is `"first_class"`. The toggle still renders. In `"opt_in_only"` mode (the default until a real fit lands), the existing acknowledgement copy is unchanged. |
| D-15 | RFC 0046's three-mechanism opt-in API is **not modified** by this workflow. The graduation helper takes an optional `persistent_opt_in: bool \| None`; the form-builder passes `None` for now (lets graduation take effect). A future workflow wires the real persistent setting through. |
| D-16 | NB-1 stepped-clock seam: `install_generate_state_listener` gains an optional `time_provider: Callable[[], float] \| None = None` parameter that defaults to `time.monotonic`. A new `clock_step: float \| None = None` parameter on the listener lets tests step deterministically (when set, the listener treats every iteration as advancing by `clock_step`). |
| D-17 | NB-1 test polish: `tests/test_generate_state_listener.py` gains stepped-clock variants of each cadence/coalesce/reinstall test. The existing `time.sleep`-based tests stay (deleting them is out of scope for this workflow) so the seam can be validated against current behavior. |
| D-18 | RFC 0058 status flips from `landed (schemas only)` to `landed` once stages 2 + 3 ship. The "Open Questions" section on RFC 0058 is updated to mark the four open questions either `resolved` (with this workflow's pin) or `deferred to successor RFC`. The first-promotion gate (stage 4 — physical rig run) remains explicit in the status line. |
| D-19 | A new `DECISION_LOG` row `D039` records this workflow's pin on the persistent-opt-out-wins rule and the `fit_kind` discriminator deferral. `ROADMAP.md`'s "Stability calibration acceptance" track flips to `landed`. |
| D-20 | The forbidden-claim scrub list and the `ui-theme-orphan-scan`, `import-boundary-scan`, and `services-boundary-scan` gates remain enforced. No new safety/seaworthiness/final-prediction/design-fitness wording is introduced. |
| D-21 | Out-of-scope, deferred to a successor: structured `EvaluatorVersion(record_hash, evaluator_id)` (RFC 0058 open Q2), `StabilityFitRecord.expires_at` (open Q4), real fit ingestion, real residual plotting, the `fit_kind` discriminator field, frontier-view per-point hover with metric values, and any change to RFC 0046's persistent-setting API. |
