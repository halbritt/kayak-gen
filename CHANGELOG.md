# Changelog

This changelog is reconstructed from `git log`, the RFC index, workflow
operator reports, and user-facing docs. It records product-visible changes and
workflow landings; detailed review findings remain in `docs/workflows/*/`.

## Unreleased

### Changed

- Web UI second-pass redesign landed upstream as `b82b544`
  ("Land WEB_UI_REWORK_2026-05-22 second-pass redesign"). Presentation-only;
  `build_spec_from_form_state` wire output unchanged. Visible changes:
  param rail gains a chip-styled validity-badge header
  (`data-testid="validity-badge"`); the Hydro `<pre>` dump becomes a
  key/value table; high-angle GZ surfaces as a tonal `VAlert`; mesh
  diagnostics render as key/value tables; the mesh readiness chip pair
  shows `No package built` + live `status_readiness` when no package
  is loaded (resolves the "unavailable" contradiction); a new
  Comparison tab hosts the Pareto frontier with a
  `live_frontier / imported_report` `ComparisonSourceToggle`; the
  Generate panel collapses two Submit buttons into a single kind-aware
  button (`data-testid="generative-submit"`), renders variable rows as
  `VDataTable`, objective rows as `VList` + `VAlert` refusal, jobs as
  `VDataTable`; the raw-JSON escape hatch is renamed
  "Raw JSON (advanced)"; the CFD expansion title is updated. Two new
  helpers land in `kayakgen/services/evaluation.py`
  (`hydro_rows_from_state`, `mesh_diagnostics_rows_from_state`) — pure
  view-model transformers, no claim-state widening.
  `tests/test_web_layout.py` gains 11 new `§9.3` checks (#9-#18).
- `docs/USER_GUIDE.md` `### serve` section rewritten to describe the
  post-rework workspace (Param rail / Hydro / Mesh / Comparison /
  Generate tabs, two-column Generate form, kind-aware single Submit,
  Comparison-tab-hosted frontier with `ComparisonSourceToggle`,
  jobs-table columns, "Raw JSON (advanced)" intent, CFD-in-loop
  slowness rationale, responsive breakpoint, validity-badge
  accessibility).
- `docs/ARCHITECTURE_MAP.md` date bumped to 2026-05-25.
- `docs/WEB_VERIFICATION.md` gains a "data-testid Hook Contract"
  section documenting the hooks as internal test-only contracts that
  may change without notice (closes audit AUD-O-015).
- `kayakgen/ui/web/generate_frontier_view.py` `FORBIDDEN_METRIC_TOKENS`
  docstring expanded to explain that the per-line
  `# noqa: kg-orphan-color` annotations are precautionary because the
  strings are RFC 0043 metric-token names, not color literals (closes
  audit AUD-D-004).

### Added

- Third `code_doc_audit` run landed under
  `docs/audits/2026-05-25-code-doc-audit/` (`release_candidate` preset,
  scope `fcb8040..b82b544`, single-commit gap left by the upstream
  UI rework landing between the 2026-05-23 audit and HEAD). Three
  lanes returned 32 findings (0 critical / 0 high / 5 medium / 9 low
  / 18 info). Lane 1 (pipeline-integrity) returned 7 positive null
  findings — the "presentation-only rework" claim verified under
  adversarial review. Lanes 2 + 3 surfaced the central-docs catch-up
  gap (CHANGELOG / USER_GUIDE / ARCHITECTURE_MAP) and the inline-help
  gap (validity-badge / comparison-toggle / submit-disabled /
  mesh-diagnostics labels). R1 docs catch-up batch landed in this
  commit closing AUD-D-001 (medium), AUD-D-002 (medium), AUD-D-004
  (low), AUD-O-007/008/009/010/012/013/014/015 (info-to-low);
  AUD-D-003 closed as wontfix; AUD-D-005..009 and AUD-O-011/016
  recorded as positive baseline. R2 (inline-help / tooltip code batch)
  for AUD-O-001/002/003/004/006 deferred to a follow-up striatum
  workflow per `feedback_striatum_required`. R3 (`Hydrostatics row
  metadata` registry — AUD-O-005) deferred as its own RFC slice.

### Fixed

- Workflow 0035 (`docs/workflows/0035-render-tests-for-registry-labels/`)
  closes 2026-05-23 audit findings AUD-O-009 (medium) and AUD-O-010
  (medium). New `tests/test_generate_panel_label_rendering.py` (3 tests)
  monkeypatches `VTextField.__init__` / `VSelect.__init__` around
  `create_app(initial_hull=Hull())`, captures each widget's kwargs by
  `data-testid`, and asserts `hint == description(key)` +
  `label == label_with_unit(key)` for every base-hull rail key; the
  objectives and variable-selector picklist items are checked against
  the `OBJECTIVE_METADATA`-sourced titles via the seeded Trame state.
  New `tests/test_desktop_slider_labels.py` (4 tests) instantiates
  `KayakGUI` against a headless Agg backend and asserts
  `Slider.label.get_text() == label_with_unit(key)` for every
  `SLIDERS` row plus three spot-checks. Both tests trip with
  AUD-O-009/010-named error messages under simulated regression.
- Workflow 0036 (`docs/workflows/0036-cli-help-text-polish/`) closes
  2026-05-23 audit findings AUD-O-011 (low) and AUD-O-012 (low).
  `kayakgen/cli/runs_cli.py` `runs list --kind` help text now
  enumerates `sweep | search | cfd | comparison`, matching the
  `runs jobs` style for `--state` / `--kind`.
  `kayakgen/ui/gui_params.py` deprecation warning text gains a
  pointer to `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`
  so downstream consumers have an actionable breadcrumb;
  `tests/test_gui_params.py` asserts both the RFC label and the
  on-disk path appear via two `pytest.warns(match=...)` blocks.

### Changed

- Second `code_doc_audit` run landed under
  `docs/audits/2026-05-23-code-doc-audit/` (`release_candidate` preset,
  scope `f78e478..3a7f2de`). The three lanes returned 8 actionable
  findings (0 critical / 0 high / 2 medium / 5 low / 1 info) plus a
  null finding from Lane 1 (Pydantic invariants intact) and 8 verified-pass
  null findings from Lane 2 (RELEASE_DISCIPLINE checklist applied
  correctly to RFC 0059/0060/0061). R1 + R2 docs batches landed in this
  commit: new `docs/audits/README.md` indexes all runs (closes AUD-O-014);
  `docs/workflows/0029-code-doc-audit/SOURCES.md` template-ness made
  explicit with pointers to past runs as worked examples (closes
  AUD-O-015). R3 (deprecation-warning URL), R4 (render tests for
  RFC 0060/0061 label surfaces), and R5 (`runs list` help-text
  symmetry) deferred to follow-up striatum workflows
  `0035-render-tests-for-registry-labels` and
  `0036-cli-help-text-polish`.

### Added

- Landed RFC 0061
  (`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`)
  closing D043's named desktop-migration follow-up to RFC 0060. The
  desktop GUI now consumes the same `HULL_PARAMETER_METADATA` registry
  the web Generate panel does, eliminating the GUI-key / Hull-key
  drift (`length` → `length_m`, `beam` → `beam_oa_m`, ...) and the
  `GUI_TO_HULL` indirection. The view-only `target_speed_kt` lives in
  a new sibling `VIEW_PARAMETER_METADATA` dict; desktop slider ranges
  live in a new `kayakgen/ui/desktop_slider_ranges.py` (per D043
  OQ1 — ranges stay out of the value-object schema).
  `kayakgen/ui/gui_params.py:hull_from_gui_params` becomes a
  deprecation shim that emits a `DeprecationWarning` naming RFC 0061
  but still returns a valid `Hull`. Driven by workflow 0034
  (`docs/workflows/0034-desktop-sliders-on-registry/`). The 12 numeric
  slider ranges and 12 default values are byte-equal to the pre-RFC
  literals; only the keys and label strings change.
- Proposed RFC 0059 "Three-Lane Code And Documentation Audit Workflow"
  (`docs/rfcs/0059-three-lane-code-and-doc-audit-workflow.md`) plus the
  runnable workflow at `docs/workflows/0029-code-doc-audit/` (workflow.json
  + RUNBOOK + SOURCES template + per-lane prompts and roles) implementing
  the `code_doc_audit` shape.
- First dogfood run of the new workflow under
  `docs/audits/2026-05-22-code-doc-audit/`: three lane FINDINGS.md
  artifacts (pipeline-integrity / docs-decision-drift / operator-adoption),
  SYNTHESIS.md, and REMEDIATION_PLAN.md. 13 findings (5 high, 5 medium, 4
  low, 3 info / null). Lane-diversity caveat documented in SYNTHESIS.md.

### Changed

- Drove the audit's R1 + R9 + R2-docs remediation batches in place
  (closes AUD-D-001 / AUD-D-002 / AUD-D-003 / AUD-D-004 / AUD-O-001 /
  AUD-O-002 / AUD-O-007 from `docs/audits/2026-05-22-code-doc-audit/`):
  - `docs/ARCHITECTURE_MAP.md` date bumped to 2026-05-22; CLI table
    gains `kayakgen runs jobs` (RFC 0057 stage 4) and the four
    `kayakgen stability {ingest-rig-run, promote-fixture, accept-fit,
    residual-plot}` rows (RFC 0058 stages 2-3).
  - `docs/USER_GUIDE.md` `### stability` section gains a D040
    legacy-routing note and a `#### Stability fixtures (RFC 0058)`
    subsection covering the four schema-only subcommands; the
    Mesh-and-CFD-readiness section gains `### mesh-evidence (RFC 0045)`;
    the `### cfd run` env-knob section documents the full RFC 0046
    three-mechanism opt-in contract (profile flag / persistent setting /
    env knob, ranked by precedence) with examples.
  - `docs/UBIQUITOUS_LANGUAGE.md` gains glossary entries for
    `MeasuredStabilityFixture`, `StabilityFitRecord`,
    `StabilityFixturePromotionPacket`, `AnalyticalClaimLabel`,
    `cfd_in_loop_evaluator_status`, and `GenerativeJob`.
  - `docs/PRD.md` high-angle-GZ bullet names RFC 0058's analytical-label
    upgrade contract.
  - `docs/rfcs/README.md` gains the RFC 0059 row.
- Synchronized the RFC 0057 stage-4 documentation set: user-guide Generate
  / `kayakgen runs jobs` usage, roadmap date/status, RFC 0057 landed status
  and `/api/generative-jobs/*` route names, D037 decision receipt, RFC index,
  and workflow operator report. No runtime behavior or no-claims boundary
  changed.

### Added

- Landed RFC 0060
  (`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`)
  defining the `HullParameterMetadata` value object + registry shape;
  driven to completion by workflow 0033 below.

### Changed

- Discipline-checklist catch-up for the 2026-05-22 audit run: RFC 0059
  promoted from `proposed` to `landed` (every high/medium finding from
  the dogfood run is now closed by workflows 0030-0033). New
  `DECISION_LOG.md` rows D041 (audit cadence — `full_repo` quarterly +
  `release_candidate` before any public-CLI / public-schema CHANGELOG
  entry), D042 (`EMPTY_STABILITY_FIT_REGISTRY` constant as the single
  source of truth for the empty fit registry through RFC 0058 stages
  2-3), and D043 (`HullParameterMetadata` presentation-layer pattern
  for UI-facing labels and tooltips). `ROADMAP.md` gains "Code+doc
  audit cadence" and "Web Generate-panel form labels" track rows.

### Fixed

- Workflow 0033 (`docs/workflows/0033-web-generate-panel-labels/`)
  closes audit finding AUD-O-003 (medium) by landing RFC 0060
  presentation-layer labels for the Trame Generate panel. New module
  `kayakgen/ui/parameter_metadata.py` ships the `HullParameterMetadata`
  value object (frozen, `extra="forbid"`), the 11-row
  `HULL_PARAMETER_METADATA` registry, and the `label_with_unit` /
  `description` helpers. `kayakgen/ui/web/generate_spec_form.py` wires
  the registry into the variable-selector picklist, the base-hull rail,
  and the objectives picklist (which sources friendly labels + units
  from the existing `OBJECTIVE_METADATA` rather than re-defining them).
  The form's submitted JSON payload remains byte-stable — verified by
  the unchanged round-trip snapshot tests in `tests/test_generate_spec_form.py`.
  New regression test `tests/test_hull_parameter_metadata.py` pins the
  registry contract; `tests/test_vocabulary_coverage.py` gains an
  `HullParameterMetadata` parametric case;
  `docs/UBIQUITOUS_LANGUAGE.md` and `docs/USER_GUIDE.md` document the
  new affordance.
- Workflow 0032 (`docs/workflows/0032-cli-ergonomics-runs-cfd/`) closes
  audit findings AUD-O-004 (medium), AUD-O-005 (medium), and AUD-O-006
  (low): `kayakgen/cli/runs_cli.py` gains optional `--header` flag on
  `runs list` and `runs jobs` (default `--no-header` for back-compat;
  prints `#`-prefixed tab-separated column header line); enumerates the
  honored `--filter` keys (`status`, `hull_design_hash`) in the help
  text. `kayakgen/cli/main.py` `mesh-evidence` refusal message appends an
  RFC 0046 three-mechanism cross-reference; `cfd prepare` success echo
  appends a "Next: kayakgen cfd run ..." line that names the three
  opt-in mechanisms. `docs/USER_GUIDE.md` `### runs` section documents
  the new `--header` flag and enumerates the filter keys.
- Workflow 0031 (`docs/workflows/0031-vocab-coverage-rfc-0057-0058/`)
  closes audit findings AUD-P-003 (medium) and AUD-P-004 (low):
  `tests/test_vocabulary_coverage.py` gains parametric coverage for the
  six new RFC 0057/0058 aggregate-root terms (`GenerativeJob`,
  `StabilityFitRecord`, `StabilityFixturePromotionPacket`,
  `MeasuredStabilityFixture`, `cfd_in_loop_evaluator_status`,
  `AnalyticalClaimLabel`) plus a new test that pins the documented
  `kayakgen runs jobs --state` six-state vocabulary against the source
  Literal in `kayakgen.services.generative_jobs.JobState`. 37 tests pass
  (was 30 pre-edit).
- Workflow 0030 (`docs/workflows/0030-stability-claim-gate-literal/`)
  closes audit findings AUD-P-001 (high) and AUD-P-002 (low / R7):
  `kayakgen/eval/contract.py` `GZCurve.result_semantics` Literal widened
  to permit both `unvalidated_hydrostatic_comparison` and
  `validated_hydrostatic_comparison` (inline two-element Literal to avoid
  a circular import with `high_angle_contracts.py`). New regression test
  `tests/test_gzcurve_result_semantics_round_trip.py` exercises the
  validated-label construction, the full `EvaluationResult` JSON
  round-trip, and the unknown-label rejection. R7 lands the shared
  `EMPTY_STABILITY_FIT_REGISTRY` constant on
  `kayakgen/eval/stability/accepted_fit.py` with a D039-citing docstring;
  the three previously-hardcoded `()` call sites
  (`kayakgen/eval/stability/evaluator.py`,
  `kayakgen/ui/web/generate_frontier_view.py`,
  `kayakgen/ui/web/generate_spec_form.py`) consume it.
- Remediated the daemon-run workflow 0054 MF-1 finding by adding
  deterministic cancellation coverage for RFC 0057 generative jobs. The new
  tests force the manager/web route and file-backed subprocess-runner paths to
  observe the cancellation seam and require `state="resumable"`,
  `error.kind="cancelled_by_operator"`, `resumable_from_checkpoint=true`, and
  subprocess `cancel.flag` cleanup. No job API, state vocabulary, solver
  posture, or no-claims boundary changed.
- Remediated workflow 0056 MF-1: Generate-panel form serialization now treats
  the CFD-in-loop acknowledgement as implicit when
  `generative_cfd_in_loop_status == "first_class"`, matching the rendered
  hidden-acknowledgement branch. The default `opt_in_only` path still requires
  the acknowledgement before submission.
- Hardened `parse_openfoam_force_dat` against the real OpenFOAM-v2512
  `forces` function-object tabular schema: rows are 10 numeric fields
  (`time` + total/pressure/viscous triples) by default, or 13 with porous
  contributions. The previous implementation assumed a combined
  19-field force+moment layout that the real v2512 binary does not emit
  (moments live in a separate `moment.dat`). Legacy parenthesised-tuple
  layouts remain rejected with `code='unsupported_layout'`. Fixtures
  under `tests/fixtures/openfoam_v2512/` and `tests/fixtures/openfoam/`
  were regenerated from a real interFoam smoke run; the
  `CfdOpenFoamForceDatSample` now reports a `porous_recorded: bool`.
- Remediated workflow 0051 must-fix review findings: OpenFOAM local adapter
  reruns now clear stale per-run raw outputs before command execution, and the
  canonical `GZCurve`/`StabilityResult` contract now round-trips
  fixed-trim generated-body v1 heel metadata. The OpenFOAM path remains
  failed/raw-unvalidated with no real `succeeded` solver path enabled, and
  generated-body high-angle stability output remains an unvalidated
  hydrostatic comparison behind the existing evidence gates.
- Fixed the workflow 0053 web-share regression: browser Share URL reconstruction
  now seeds hull state from the query string deterministically without
  perturbing slider rails. No new browser capability, hosted operation, or
  no-claim wording changed.

### Added

- Landed RFC 0058 stages 2 and 3, plus workflow 0054's NB-1
  auto-poll listener seam. The stability fit contracts now include
  `resolve_analytical_claim_label` and
  `cfd_in_loop_evaluator_status`; the `kayakgen stability` sub-app
  provides schema-only `ingest-rig-run`, `promote-fixture`,
  `accept-fit`, and `residual-plot` commands; the Generate panel now
  wires frontier colour through the analytical claim label and hides
  the CFD-in-loop acknowledgement only when graduation returns
  `first_class`; and the listener has a stepped-clock test seam. No
  fixture or fit is promoted, defaults stay byte-stable, and Stage 4
  remains gated on physical rig data.
- Landed RFC 0058 stage 1 as schemas only. New
  `kayakgen/eval/stability/accepted_fit.py` pins
  `FixtureRef`, `HullFamilyScope`, `StabilityFitMetrics`,
  `ReviewerSignature`, `StabilityFitRecord`, and
  `StabilityFixturePromotionPacket` with default fit-threshold
  validators and no filesystem fixture resolution. No fixture or fit is
  promoted; `resolve_analytical_claim_label`,
  `cfd_in_loop_evaluator_status`, the `kayakgen stability` sub-app,
  CFD-in-loop graduation, and any upgrade from
  `unvalidated_hydrostatic_comparison` remain deferred.
- Workflow 0054 cowboy-mode review trail: three review artefacts
  (traceability / claims / ops+tests) + findings ledger + remediation
  patch summary + final review committed under
  `striatum/0054-rfc-0057-stage-4-ui-polish/`. The later daemon-run
  ledger superseded the cowboy zero-must-fix disposition with MF-1,
  remediated above; cowboy successor notes remain historical context
  (per-row Fork buttons,
  redactor snapshot-byte-equality, widget-tree integration tests,
  `REVIEW_TABS` tab-value constants). Final verdict: `accept`. The
  scaffold workflow on `docs/workflows/0054-...` remains re-runnable
  once striatum#24 lands; the cowboy artefacts stand as the
  authoritative review record.
- Landed RFC 0056 schemas (status: `landed (schemas only)`). New
  `kayakgen/eval/stability/measured_fixture.py` ships
  `MeasuredStabilityFixture` plus value objects (`HullIdentityRef`,
  `LoadingConfiguration`, `CalibrationTrace`, `FreeEquilibriumTrace`,
  `HysteresisBound`, `MeasuredStabilityRow`) with validators enforcing
  the RFC 0056 acceptance gates: `intended_use` enumeration, hull
  identity (64-char SHA-256 scan hash), calibration drift below bound
  (default 0.5%), hysteresis bound (default 3% of GZ_max), free-
  equilibrium-trace presence, constrained-trace blocks promotion.
  Defaults to `intended_use="validation_candidate"`; no fixture is
  promoted by this RFC. +15 focused tests in
  `tests/test_measured_stability_fixture.py`.
- Drafted the initial RFC 0058 proposal, now followed by the
  schema-only stage 1 landing above:
  `docs/rfcs/0058-stability-calibration-acceptance.md`. Defines the
  `StabilityFitRecord` aggregate, the
  `resolve_analytical_claim_label(hull, fit_registry)` upgrade contract
  for RFC 0043's analytical `GZCurve` output (default stays
  `unvalidated_hydrostatic_comparison`; only an accepted fit covering
  a hull family upgrades to `validated_hydrostatic_comparison`), the
  `cfd_in_loop_evaluator_status(...)` graduation contract for RFC
  0057's Generate-panel CFD-in-loop opt-in row (default
  `opt_in_only`; first-class only with both analytical and CFD-vs-
  measured accepted fits), and a `kayakgen stability` sub-app
  (`ingest-rig-run`, `promote-fixture`, `accept-fit`, `residual-plot`).
  Mirrors RFC 0027's resistance-side acceptance pattern. No fixture
  or fit promoted by this RFC; the first concrete promotion happens
  in a later workflow once a real measured dataset arrives.
- Landed RFC 0057 stage 4: Generate-panel UI polish, captured against the
  12 operator-affirmed decisions in
  `docs/workflows/0054-rfc-0057-stage-4-ui-polish/STAGE_4_DECISIONS.md`.
  Six new modules under `kayakgen/ui/web/` and `kayakgen/services/`:
  - `generate_spec_form.py` — form-builder primary input (variables,
    NSGA-II/EHVI algorithm radio with per-algorithm sub-forms,
    objectives multi-select filtered live by claim-admissibility, RFC
    0046 CFD-in-loop opt-in row with the pre-vetted ack copy, soft
    advisory at >=4 in-flight jobs, base-hull defaults pre-filled from
    the current single-hull view) plus the collapsible raw-JSON
    escape hatch. `admissible_objective_metrics()` + the
    `GenerateSpecFormError` envelope let tests assert the live filter
    without driving Trame widgets.
  - `generate_frontier_view.py` — 2D scatter synced with a sortable
    table (matplotlib widget with an SVG fallback for headless),
    objective-pair selector + colour-mapped third axis for 3-objective
    EHVI runs, candidate handoff that loads a Pareto candidate into
    the single-hull view with a one-click undo toast.
  - `generate_state_listener.py` — auto-poll listener: 1 s cadence
    while any job is in `{queued, running}`, 10 s otherwise; pauses
    while the Generate tab is not the active review tab; cancellable.
  - `generate_fork_button.py` + `services/generative_jobs_fork.py` +
    new `POST /api/generative-jobs/{job_id}/fork` route — one-click
    "Fork with new seed" for succeeded jobs. The forked job carries a
    new `forked_from` field on `GenerativeJob`; sweep jobs refuse the
    fork (deterministic).
  - `services/generative_jobs._redact_log_text` — strips `$HOME` and
    rewrites paths under `jobs_root` to `<jobs_root>`; routed through
    `generative_job_log_payload`. Byte-stable for redaction-free logs.
  - `kayakgen serve` defaults flipped to the subprocess manager;
    `--jobs-in-process` is the new explicit in-process opt-in. Prints
    the chosen manager kind on startup.
  +49 new tests across `tests/test_generate_spec_form.py` (13),
  `tests/test_generate_frontier_view.py` (9),
  `tests/test_generate_state_listener.py` (11),
  `tests/test_cli_serve.py` (3), `tests/test_log_redaction.py` (11),
  and `tests/test_generative_jobs_fork.py` (6). The RFC 0057 + web +
  boundary slice now totals 274 passed; the forbidden-claim
  scrub-list and ui-theme orphan-color scan stay green. The fork
  + redaction + form-builder modules contribute zero new banned
  tokens. Workflow 0054 scaffold (`docs/workflows/0054-...`) shipped
  on `main` ahead of execution; the actual stage-4 land happened in
  cowboy mode under operator authorisation because the v1.55.0
  `striatum supervise send --packet-id` flow rejected every
  identifier surfaced by `claim-next` (filed upstream as
  halbritt/striatum#24).
- Landed RFC 0057 stage 3: subprocess manager + crash survival.
  `persist_job_to_dir` now writes ``job.json`` atomically (temp-file
  + ``os.replace``) so concurrent readers never observe a truncated
  payload — this also closes a latent race the in-process manager
  could hit when ``resume()`` raced against the worker thread's first
  write. New `SubprocessGenerativeJobManager` spawns each job as a
  detached
  Python subprocess invoking the new
  `kayakgen.services.generative_jobs_runner` entry point
  (`python -m kayakgen.services.generative_jobs_runner <job_id>
  <jobs_root> [--resume]`). The child reads `spec.json` + `job.json`,
  transitions to `running`, drives `run_search` / `run_sweep` with a
  file-backed cancel sink (polls `<job_dir>/cancel.flag`), and writes
  terminal state (`succeeded` / `failed` / `resumable`) back to disk.
  Parent reads are file-only — no IPC. The runner cleans up the
  `cancel.flag` on terminal write so a subsequent resume does not
  immediately re-cancel. Crash-survival: if the child is `SIGKILL`-ed,
  the parent's `get()` and `list()` detect a stale `running` state
  with no live process handle and reconcile to `resumable` on disk so
  a follow-up `resume()` can re-spawn against the persisted
  `state.json` checkpoint. File-store helpers
  (`read_job_from_dir`, `list_jobs_in_dir`, `tail_log_file`,
  `append_log_to_file`, `persist_job_to_dir`, `initialize_job_dir`,
  `classify_runner_error`) are now module-level so both managers and
  the subprocess runner share them. New `kayakgen serve
  --jobs-subprocess` flag threads a `SubprocessGenerativeJobManager`
  through `create_app` and `KayakgenApp`; default (no flag) keeps the
  in-process manager. +7 new tests in
  `tests/test_generative_jobs_subprocess.py` (sweep, search, cancel,
  resume, SIGKILL crash + resume, stale-running reconciliation in
  `list()`, direct resume of a stale-running job). RFC 0057 + web +
  boundary slice 211 passed.
- Landed RFC 0057 stage 2: web routes + Trame Generate panel.
  `register_rest_routes` now accepts a `GenerativeJobManager`
  (defaulting to a lazily-built `InProcessGenerativeJobManager` under
  `~/.local/share/kayakgen/generative_jobs/` or
  `KAYAKGEN_GENERATIVE_JOBS_ROOT`) and mounts eight new routes:
  `GET /api/generative-jobs`,
  `POST /api/generative-jobs/{search,sweep}`,
  `GET /api/generative-jobs/{job_id}`,
  `GET /api/generative-jobs/{job_id}/log`,
  `GET /api/generative-jobs/{job_id}/frontier`,
  `POST /api/generative-jobs/{job_id}/{cancel,resume}`. Every payload
  carries `result_semantics: "raw_unvalidated"`. Service-layer helpers
  (`start_generative_job_payload`, `generative_job_list_payload`,
  `generative_job_full_payload`, `generative_job_log_payload`,
  `generative_job_frontier_payload`, `cancel_generative_job_payload`,
  `resume_generative_job_payload`) plus a structured
  `GenerativeJobWebError` envelope mirror the RFC 0018 CFD-route
  pattern; rejection cases return 400/404/409 with explicit `error`
  tokens. The Trame workspace gains a new "Generate" tab (between CFD
  and Advisories) with a spec-JSON textarea, Submit Search / Submit
  Sweep / Refresh Jobs / Cancel / Resume / Load Log / Load Frontier
  buttons, and three bounded text panels for the jobs index, log
  tail, and resolved Pareto-frontier rows. Forbidden-claim scan stays
  green: no new banned tokens introduced; the panel banner reuses the
  existing "no hosted worker is running" allowed phrase. +13 new web
  tests in `tests/test_generative_jobs_web.py`; full RFC 0057 + web
  + boundary slice 203 passed.
- Landed RFC 0057 stage 1: long-lived generative-job foundation. New
  `kayakgen.services.generative_jobs` module ships `GenerativeJob`,
  `GenerativeJobProgress`, `GenerativeJobError`, `GenerativeJobSummary`
  Pydantic records (schema_version="1", canonical JSON byte-stable);
  the `GenerativeJobProgressSink` protocol; and
  `InProcessGenerativeJobManager` running each job in a background
  `threading.Thread` with cooperative cancel (via an internal
  `threading.Event`) and a bounded 256 KB `log.txt` ring buffer per
  job. `run_search` and `run_sweep` gain an optional
  `progress_sink: GenerativeJobProgressSink | None = None` argument
  that emits `candidate_completed` after every persisted record,
  `checkpoint` after every `state.json` write, and polls
  `should_cancel` between candidate emissions; cancellation maps to
  the existing `operator_stop` termination reason. Default
  (`progress_sink=None`) behavior is byte-equal to before across the
  active-search and sweep regression suites. `SqliteIndex` gains a
  `generative_jobs` table (job_id, kind, state, output_dir,
  run_id/run_hash, started_at, completed_at, evaluation counters,
  updated_at) plus `upsert_generative_job` / `list_generative_jobs`
  helpers; new `kayakgen runs jobs [--state] [--kind] [--limit]` CLI
  surface lists them. +30 tests across
  `tests/test_generative_jobs.py`,
  `tests/test_generative_jobs_progress_sink.py`,
  `tests/test_generative_jobs_index.py`, and
  `tests/test_generative_jobs_manager.py`; full suite previously 930
  passed + 2 skipped before this slice. Web routes + Trame panel land
  as stage 2; subprocess-manager + crash-survival lands as stage 3.
- Landed RFC 0045 ordinary-package solver-readiness promotion. New
  `kayakgen mesh-evidence <hull> --out <dir>` subcommand runs the
  OpenFOAM-v2512 meshing stage against a generated closed-body STL and
  emits a serialized `SnappyHexMeshEvidence` plus the polyMesh artifacts;
  refuses without `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and a sourceable
  bashrc. New `kayakgen mesh-package --bind-evidence <path>` reads the
  evidence and embeds the resulting `VolumeMeshDiagnostic` into the
  manifest. A new `bind_evidence_to_mesh_package(evidence, *,
  closed_body_hash, polymesh_dir)` helper performs three hash checks
  with structured rejection codes (`closed_body_hash_mismatch`,
  `snappy_evidence_body_mismatch`, `polymesh_artifact_drift`, plus
  `evidence_not_recorded` and `evidence_translation_failed`). Default
  `kayakgen mesh-package` JSON is byte-equal to before when
  `--bind-evidence` is absent. +7 tests.
- Landed RFC 0046 non-env-gated OpenFOAM `succeeded` path. Three
  mechanisms admit the real-solver path in precedence order:
  per-job profile flag (`kayakgen cfd prepare
  --allow-real-solver-execution`), persistent setting
  (`~/.config/kayakgen/cfd.json` with
  `allow_real_solver_execution_profiles`), and the existing
  `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` env knob (backwards-compatible).
  Default behavior (no opt-in) stays `solver_success_blocked`.
  `CfdRunRecord` gains a `real_solver_execution_opt_in: Literal[
  "profile_flag","persistent_setting","env_knob"] | None` field and a
  `SolverExecutionAudit` block (bashrc path, provenance summary, locked
  case-template version, mesh seconds, solve seconds). `claim_state`
  stays `raw_unvalidated`; `accepted_uses` stays `[]`. +11 tests across
  `tests/test_cfd_config.py` and `tests/test_cfd_opt_in_resolver.py`.
- Landed RFC 0047 v2 EHVI active-search successor. New
  `kayakgen/search/active/gp.py` ships a vendored Cholesky-factorized
  Gaussian process with Matern 5/2 and RBF kernels and a vendored
  Nelder-Mead marginal-likelihood optimizer (numpy only; no scipy /
  scikit-learn / BoTorch / GPyTorch / scikit-optimize dependency).
  `kayakgen/search/active/ehvi.py` implements EHVI for 1, 2, and 3
  objectives via axis-aligned cell decomposition; raises
  `EhviDimensionError` for 4+. `SearchAlgorithmSpec.kind` accepts a new
  `"ehvi"` literal; `EhviAlgorithmConfig` carries
  `initial_population_size`, `iteration_budget`, `seed`, `gp_kernel`,
  `gp_noise_floor`, `reference_point`, `candidate_pool_size`. The
  runner dispatches on `isinstance(spec.algorithm, EhviAlgorithmConfig)`
  to the new `_run_ehvi_search` path; the RFC 0043 high-angle-GZ
  display-only refusal and the RFC 0044 claim-admissibility gate apply
  unchanged. Seeded determinism is enforced via a single
  `numpy.random.default_rng(seed)` thread through LHS sampling, GP fit,
  candidate-pool draw, and tie-breaking. The synthetic-landscape
  regression test verifies EHVI achieves >=5x hypervolume improvement
  vs random selection at equal budget. Surrogate predictions never
  appear in candidate `summary` or `run.json` objective fields. Default
  NSGA-II behavior is byte-equal. +19 tests across
  `tests/test_active_search_{gp,ehvi,v2_runner}.py`.
- Landed RFC 0043 stage 4 desktop minimal indicator: a new
  `high_angle_gz: cli_only_unvalidated_hydrostatic_comparison` segment
  in the desktop status block points users at the staged opt-in
  surfaces (`kayakgen stability --high-angle-gz`, sweep
  `evaluators.high_angle_gz`, comparison `high_angle_gz_display`, Trame
  web workspace). Per D021 the desktop does not render a curve; the
  segment is a labelled pointer. Forbidden-copy regression in
  `tests/test_desktop_layout.py` confirms no safety / seaworthiness /
  validated / calibrated / final-prediction / design-fitness wording
  leaks onto the desktop status surface.
- Phase 7 of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`:
  modelled the OpenFOAM CFD execution pipeline as explicit named
  stages. New `CfdRunStage` Pydantic record (`name`, `state`,
  `started_at`, `completed_at`, `wall_clock_seconds`, `notes`,
  `error_kind`) with literal-locked names (`mesh_readiness_evidence`,
  `case_render`, `meshing`, `mesh_evidence_binding`,
  `solver_execution`, `parser_post_processing`, `raw_result`,
  `validation_gate`) and an additive `stages: list[CfdRunStage]`
  field on `CfdRunRecord` (default `[]`).
  `OpenFoamLocalAdapter._attempt_real_succeeded_path` populates the
  stages incrementally as each runs; the non-OpenFOAM adapters keep
  `stages=[]`. `validation_gate` is always emitted with
  `state="skipped"` + `notes=["validation_gate_not_implemented"]`
  because no accepted-validation workflow exists. Backwards-compatible
  for existing serialized records. New tests under
  `tests/test_cfd_run_stages.py`. Suite 733 + 2 skipped, ruff clean.

- Drove all 8 proposed RFCs (0048-0055) to landed status in a single
  parallel-subagent wave (2026-05-17). All defaults are byte-stable;
  every new feature is additive or opt-in. Full suite: 914 passed +
  4 skipped (env-gated OpenFOAM smokes), random and stable ordering;
  ruff clean; env-gated CFD pipeline 9/9.
  - **RFC 0048 Geometry V2 (landed v1)**: new
    `geometry_kind="distribution_v2"` on `Hull` with
    `DistributionV2Spec` carrying five `LongitudinalDistribution`
    records, six cross-section families
    (`round`, `shallow_arch`, `shallow_v`, `deep_v`, `hard_chine`,
    `multi_chine` with 2-4 chines), `DistributionV2Geometry`
    producing both canonical closed-body sections and derived open
    inspection surfaces, hydrostatic cross-check (1% volume / 1% Aw
    / 1% LCB / 0.5% GM0; advisory-only), and a
    `kayakgen migrate-geometry` CLI emitting a sibling `*.v2.json`.
    Non-default `bow_rake`/`stern_rake` refused on v2. +77 tests.
  - **RFC 0049 ArtifactStore (landed)**: `Hull.record_hash()` +
    `Hull.design_hash()` (existing `Hull.hash()` aliases
    `record_hash`, byte-stable). New `kayakgen.services.identity`
    (`record_hash`, `design_hash_for_hull`, `run_hash`) and
    `kayakgen.services.artifact_store` (`FilesystemArtifactStore`
    hard-link mirror under `_store/` with copy-on-cross-device
    fallback + missing-mirror warning, `SqliteIndex` auto-creating
    tables at `~/.local/share/kayakgen/index.sqlite` or
    `$KAYAKGEN_INDEX_DB`). Sweep, search, and CFD writers route
    through the store; canonical paths stay byte-stable. New
    `kayakgen runs {list,query,reindex}` Typer sub-app. +17 tests.
  - **RFC 0050 target-draft / target-trim (landed)**: two new CLI
    subcommands `kayakgen target-draft` and `kayakgen target-trim`
    wrapping the existing equilibrium solvers; `--report-only` flag
    on target-draft emits a `TargetDraftMismatchReport`. Refuses
    loads >2× max displaced mass with structured error. +9 tests.
  - **RFC 0051 builder-oriented exports (landed)**: new
    `kayakgen build-export` CLI under a new `[builder]` extras
    group (ezdxf). Seven artifacts: `offsets.csv`, `sections.dxf`,
    `sheer.svg`, `keel.svg`, `waterline.svg`,
    `deck_centreline.svg`, `station_molds.dxf`, plus
    `manifest.json` with per-artifact sha256+bytes. Deterministic
    modulo CAD-library timestamps. +11 tests.
  - **RFC 0052 sensitivity + uncertainty (landed)**: new
    `kayakgen sensitivity` CLI driving central-difference Jacobian
    over the existing evaluators (auto-step `1e-4 * baseline`
    clamped to `[1e-9, 1e-2]`). New `ConvergenceFlag` value object
    populated additively onto `EvaluationResult.convergence` for
    every evaluator. New `PairwiseNote` block on `ComparisonReport`
    flagging Pareto-front pairs whose default-objective metrics
    differ by less than the registry-side
    `within_evaluator_noise_threshold` (default per-metric
    thresholds in `OBJECTIVE_METADATA`). +11 tests.
  - **RFC 0053 turning + edged-waterline metrics (landed)**:
    `TurningMetrics` Pydantic record + `evaluate_turning_metrics`
    over heeled stations; opt-in `--turning [--turning-heel-deg]`
    on `kayakgen evaluate`; sweep `evaluators.turning_metrics`
    flag writes four numeric columns to `summary.csv`. All four
    metrics registered with `role="display_only"` so they are
    refused as Pareto/search objectives. +14 tests.
  - **RFC 0054 calibration-campaign tooling (landed)**: new
    `kayakgen calibration` sub-app with `ingest-tank-test`,
    `ingest-inclining-test`, `accept-fit`, `residual-plot`
    subcommands. New schemas `RightsChecklist`, `GeometryReference`,
    `TankTestRun`/`TankTestCampaign`, `IncliningTestRun`/
    `IncliningTestCampaign`, `AcceptedFitRecord`. The
    `ResistanceSourceReviewPacket` validator now resolves
    `accepted_fit_ref` on disk and refuses below-threshold fits
    with structured tokens. Edinburgh stays at
    `validation_fixture` (synthetic source used for the test).
    +19 tests.
  - **RFC 0055 design-report export (landed)**: new
    `kayakgen design-report` CLI under a new `[report]` extras
    group (jinja2 + optional weasyprint). 10-section single-file
    HTML report (header → parameters → rendered views →
    hydrostatics → stability → resistance → mesh readiness →
    optional comparison position via `--from-run` → artifact refs
    → claim-state explanations) with embedded base64 PNG preview,
    forbidden-copy scan + scrub (named constants
    `FORBIDDEN_COPY_TOKENS`, `FORBIDDEN_COPY_SCRUB_TOKENS`), and a
    structured `ReportForbiddenCopyError` refusal. +8 tests.
- Phase 5 of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`:
  centralised the metric registry. `ObjectiveMetadata` gains
  `display_format`, `availability_conditions`, and
  `default_objective_eligible`. New helpers
  `register_objective_metadata(metadata)` (refuses duplicate
  registration) and `is_objective_metric_admissible(metric, *,
  explicit_exploratory)` return structured rejection codes
  (`objective_metric_unknown`, `high_angle_gz_display_only`,
  `objective_claim_state_not_admissible`). New `ObjectiveRole`
  literal `"display_only"` is applied to `max_gz_m`,
  `heel_at_max_gz_deg`, `range_positive_stability_deg`; the RFC 0043
  token still owns the refusal. `ensure_objectives_claim_admissible_
  for_search` raises `UnknownSearchObjectiveError` for unknown
  metrics unless `objectives_explicit_exploratory: true`. Sweep
  `summary.csv` now writes every registry-known metric the candidate
  reports (legacy ordering preserved); display-only metrics never
  leak in. Web `read_models._format_metric` consults the registry's
  `display_format`. +16 tests in `tests/test_objective_registry.py`.
  Full suite 733 + 2 skipped; ruff clean.
- Executed Phases 0-4 + 6 of
  `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Phase 0+1
  installed ruff (now clean), added `docs/ARCHITECTURE_MAP.md`, and
  filled the previously-scaffold `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/DDD.md`, and `docs/SPEC.md`; added vocabulary-coverage and
  import-boundary regression tests. Phase 2 moved
  `build_high_angle_gz_block` from `kayakgen.cli` to
  `kayakgen.eval.high_angle_gz` (CLI becomes a compat shim), added a
  public `HullGeometry.section_for_closed_body` accessor replacing
  the private `_get_slice_points(..., closed_body_endpoint=True)`
  reach-in, and added a neutral `kayakgen/eval/evidence/` facade
  (re-exports `OpenFoamProvenanceProbe`, `CheckMeshSummary`, claim
  contracts). Phase 3 split four large orchestration files into
  focused sibling modules with byte-stable public surfaces:
  `kayakgen/eval/cfd/jobs.py` 2611 → 180-line shim + 13 modules
  (records, profiles, job_store, manifest_validation, provenance,
  parsers/openfoam_forces, adapters/{unavailable, mock, fixture,
  openfoam_v2512}); `kayakgen/eval/stability.py` 1322 → 9 modules
  under `kayakgen/eval/stability/`;
  `kayakgen/eval/closed_volume.py` 1452 → 6 modules under
  `kayakgen/eval/closed_volume/`; `kayakgen/ui/web/controllers.py`
  1602 → ~297 lines with the orchestration logic moved into a new
  `kayakgen/services/` package (design, evaluation, artifacts,
  cfd_jobs, comparison) — boundary-test-enforced not to import from
  ui/cli. Phase 4 and Phase 6 land as proposed RFCs 0049
  (ArtifactStore + identity normalization) and 0048 (Geometry V2
  distribution model). All 685 prior tests pass plus 32 new
  (vocabulary + import-boundary + services-boundary); full suite
  717 passed + 2 skipped. Ruff clean across `kayakgen` and `tests`.
  OpenFOAM env-gated smoke remains 2/2 in ~10s.
- Promoted the Edinburgh DataShare Pacific-canoe source-review packet
  from `validation_candidate` to `validation_fixture` (RFC 0042 / D025).
  The `ResistanceSourceReviewPacket` validator relaxes in two narrow,
  named ways: `validation_fixture` may carry `non_promotion_reasons`
  describing calibration-fixture blockers (token
  `VALIDATION_FIXTURE_ADMITS_CALIBRATION_BLOCKERS`), and
  `validation_fixture` may have `uncertainty.status == "incomplete"`
  when `uncertainty_notes` is bound and `warnings` carries
  `uncertainty_documented_caveat` (token
  `VALIDATION_FIXTURE_ADMITS_DOCUMENTED_UNCERTAINTY_CAVEAT`).
  `calibration_fixture` still cannot carry non-promotion reasons.
  Edinburgh now binds full `ResistanceSourceRecord` fixture metadata
  (`fixture_id`, `fixture_version="1"`, `accepted_uses=["validation_only"]`,
  `validity_envelope`, `validity_ranges`, `fixture_review_status="accepted"`)
  and keeps `outside_sea_kayak_calibration_envelope` as the lone
  calibration blocker per D013. +2 new tests; the regenerated pinned
  packet JSON lives at
  `tests/fixtures/calibration/edinburgh_review_packet.json`.
- Landed RFC 0044 v1: additive opt-in `kayakgen search` CLI with a vendored
  NSGA-II multi-objective evolutionary algorithm (pure Python, no external
  optimization-library dependency). New subpackage
  `kayakgen/search/active/` ships `SearchSpec`/`SearchAlgorithmSpec`/
  `SearchConstraint`/`SearchBudget`/`SearchLimits`/`SearchVariable`/
  `ObjectiveSpec`/`SearchMetadata` Pydantic records (`spec.py`), the
  vendored NSGA-II implementation with SBX crossover (eta=15) and
  polynomial mutation (eta=20, per-gene probability `1/n_vars`) and binary
  tournament selection (`nsga2.py`), constraint enforcement
  (`constraints.py`), and an orchestrator that reuses the RFC 0009
  candidate-record writer and `pending` lifecycle (`runner.py`). A new
  `ensure_objectives_claim_admissible_for_search` gate in
  `kayakgen/search/pareto.py` (token
  `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`) refuses
  `raw_unvalidated` and `uncalibrated_comparative` objectives unless
  `objectives_explicit_exploratory: true` is set; the existing
  `ensure_objectives_not_high_angle_gz` gate always wins. Constraint
  violations produce `status="constraint_failed"` candidate records that
  stay frontier-ineligible. Seeded determinism is enforced by threading a
  single `random.Random(seed)` through every operator; two independent
  invocations of the same spec produce byte-identical
  `candidates/<key>/record.json`. +32 tests across
  `tests/test_active_search_{spec,nsga2,runner,cli,pareto_gate}.py`.
  Default `kayakgen sweep` and `kayakgen compare` behavior is unchanged
  (single one-line literal extension of `CandidateStatus`).
- Closed D012: landed the real `openfoam-v2512-interfoam-local` `succeeded`
  path under opt-in env knobs. New subpackage
  `kayakgen/eval/cfd/openfoam_v2512_interfoam/` ships a vendored case
  template (15 parameterised dicts derived from the proven OpenFOAM
  DTCHull-style smoke), an `OpenFoamCaseSpec`/`render_case` renderer that
  emits byte-deterministic case files, a `runner` that sources
  `/usr/lib/openfoam/openfoam2512/etc/bashrc` and runs
  `blockMesh + surfaceFeatureExtract + snappyHexMesh + checkMesh` (mesh
  stage) plus `setFields + interFoam` (solve stage), and an
  `evidence` module that binds the rendered dict hashes, real
  `constant/polyMesh/*` artifact checksums, parsed `CheckMeshSummary`,
  patch metadata, and the real `OpenFoamProvenanceProbe` (from
  `interFoam -help` banner) into a fully-populated `SnappyHexMeshEvidence`
  record. `OpenFoamLocalAdapter` now flips to `status="succeeded"` only
  when BOTH `KAYAKGEN_OPENFOAM_LOCAL_RUN=1` and `is_openfoam_available()`
  hold; otherwise the historical `solver_success_blocked` path is
  byte-equal. The returned `CfdOpenFoamRawResult` preserves the locked
  `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`,
  `claim_state="raw_unvalidated"`, and empty `accepted_uses`. +8
  binary-free tests under `tests/test_openfoam_v2512_case_render.py` and
  +2 env-gated tests under `tests/test_openfoam_v2512_smoke.py` (auto-skip
  unless `KAYAKGEN_OPENFOAM_SMOKE=1` and the bashrc is sourceable).
  Observed wall-clock: 6.8s mesh + 1.9s solve = ~10.7s end-to-end on a
  default `Hull()` closed body.
- Acquired the Edinburgh DataShare bundle (DOI 10.7488/ds/3785, CC BY 4.0,
  workbook SHA-256
  `dffbd5d4547c9e1c1f5597d6188dc2a1efffd316ab301451fb818e11a22acade`) and
  vendored it under `tests/fixtures/calibration/edinburgh/` with a
  `DATASHARE_PROVENANCE.md` manifest. Rewrote
  `kayakgen/eval/calibration/extractors/edinburgh_datashare_pacific_canoe.py`
  against the real workbook schema: `Averaged Data` sheet, header row 12,
  data from row 14, columns Day/Model/Test/Yaw/Speed/Stbd Drag/Port Drag/
  FWD Side/AFT Side/Heave/Pitch/Velocity/Time/Comment. The extractor filters
  setup/zero/negative test numbers and emits the pinned
  `EXPECTED_OUTPUT_COLUMNS` schema (58 accepted rows from the vendored
  bundle). The source-review packet for the Edinburgh source now binds the
  workbook checksum, removes `pending_data_acquisition` from
  non-promotion reasons, and reports `is_validation_fixture_ready() = True`;
  calibration promotion remains blocked by
  `outside_sea_kayak_calibration_envelope` per decision D013. `openpyxl` is
  now an optional dependency under the `calibration` extras (and pinned in
  `dev`). +5 calibration tests (replaced the stub-raises test).
- Landed RFC 0040 stage 2 `snappyHexMesh` evidence-harness contract in
  `kayakgen/eval/snappy_hex_mesh.py`: locked
  `SNAPPYHEXMESH_CASE_TEMPLATE_VERSION = "openfoam-v2512-snappyhexmesh-watertight-v1"`,
  `SnappyHexMeshEvidence` Pydantic record with required dictionary-hash set
  (`controlDict`, `snappyHexMeshDict`, `meshQualityDict`,
  `surfaceFeatureExtractDict`, `blockMeshDict`), deterministic scaffold builder
  hashed off the generated body identity, patch metadata, `CheckMeshSummary`,
  artifact checksums, and `OpenFoamProvenanceProbe`. A new
  `snappy_hex_mesh_volume_mesh_diagnostic` translator returns `None` for
  partial evidence and hands off into the existing watertight readiness gate;
  no new `cfd_ready` promotion path is opened. +15 tests in
  `tests/test_snappy_hex_mesh_harness.py`. No real `snappyHexMesh` execution.
- Extended RFC 0043 stage 3 to the web workspace: the Trame comparison panel
  now hides the high-angle GZ section when no candidate has artifacts and
  surfaces a "High-angle GZ (display-only)" section with the fixed caption
  "Unvalidated hydrostatic comparison; not safety, seaworthiness, calibrated,
  validated, or final-prediction claim" when at least one candidate carries a
  block. Each row includes body/load/trim provenance, summary metrics,
  warnings, assumptions, and any `unavailable_reason`. A new
  `kayakgen/ui/web/read_models.py` hosts the `WebHighAngleGzRows` view-model
  so the existing forbidden-claim scan on `app.py`/`controllers.py` stays
  green. +7 web tests across `tests/test_web.py` and
  `tests/test_web_read_models.py`. Desktop GUI is intentionally unchanged
  (stage 4 "desktop minimal"; decision recorded as D021).
- Landed RFC 0043 stage 2 (opt-in sweep evaluator) and stage 3 (display-only
  comparison) for high-angle GZ:
  - Sweep: `evaluators.high_angle_gz: bool` (+ optional
    `evaluators.high_angle_gz_heel_grid_deg`) writes per-candidate
    `candidates/<key>/high_angle_gz.json` via the existing stage-1 block
    builder. Records `high_angle_gz_artifact: {path, bytes, sha256}` on the
    candidate. Failed and pending candidates skip emission; resume preserves
    artifacts byte-for-byte. No high-angle key enters `summary.csv` or
    default Pareto objectives.
  - Comparison: `kayakgen compare` reads per-candidate `high_angle_gz.json`
    when present and attaches a `high_angle_gz_display` block to each row
    (body/load/trim provenance, `max_gz_m`, `heel_at_max_gz_deg`,
    `range_positive_stability_deg`, warnings, assumptions,
    `unavailable_reason`). Report adds a `high_angle_gz_columns: bool` flag
    (true only when at least one row has the block). Pareto frontier
    eligibility, default objectives, and resolved metadata are unchanged; a
    new `HighAngleGzObjectiveRefusedError` (token
    `RFC_0043_HIGH_ANGLE_GZ_DISPLAY_ONLY`) refuses any high-angle metric as a
    Pareto objective. +19 tests across `tests/test_sweep.py`,
    `tests/test_compare.py`, `tests/test_pareto.py`.
- Landed RFC 0040 generated-body parameter-matrix hardening: a new 55-case
  parametrized test surface (`tests/test_generated_closed_body_hardening.py`,
  11 hull cases × 5 invariant assertions) pins generated closed-body
  diagnostics across default, exact-plumb, mixed-rake, waterline-pinch,
  shallow/deep draft, low/high Cp, and low/high Cm cases. Hardening proves
  body-ref hash round-trip, RFC 0021 self-intersection `passed` (non-stub
  algorithm), positive signed volume, and that ordinary generated packages
  stay below `cfd_ready` with the expected `generated_body_missing` and
  `volume_mesh_missing` blockers on both open and watertight readiness
  reports. No new mesher or solver-readiness promotion landed.
- Landed RFC 0041 partial: locked the OpenFOAM-v2512 interFoam case-template
  constant (`openfoam-v2512-interfoam-dtchull-v1`), added a Pydantic
  `OpenFoamProvenanceProbe` plus injectable runner seam that requires
  application/build/API token evidence (explicitly refuses
  `$WM_PROJECT_VERSION`-only evidence), and hardened `parse_openfoam_force_dat`
  to require the v2512 19-field schema (`porous` header token); v2306 legacy
  layout and corrupt/short files are rejected with structured codes. The
  `succeeded` path stays blocked: the adapter still returns
  `error_kind=solver_success_blocked`, and the `CfdOpenFoamRawResult` Literal
  refuses non-locked case templates and non-`raw_unvalidated` payload classes.
  +12 tests under `tests/test_cfd_jobs_openfoam.py` with fixtures under
  `tests/fixtures/openfoam_v2512/`. No real OpenFOAM binary or solver success
  path was enabled.
- Landed RFC 0042 partial: restructured `kayakgen/eval/calibration.py` into a
  package with an `extractors/` subpackage, added 12 new packet fields
  (locators, access date, checksum/pending-reason, license, attribution,
  extraction-script ref, units, Froude basis, uncertainty notes, accepted-fit
  ref), and added validators that (a) refuse `rejected` as a runtime
  `SourceUse`, (b) require both `source_checksum_sha256` (lowercase hex) and
  `extraction_script_ref` before a packet can promote to
  `validation_fixture`, and (c) require `accepted_fit_ref` before any
  promotion to `calibration_fixture`. The Edinburgh DataShare Pacific-canoe
  extractor stub raises `NotImplementedError("requires Edinburgh DataShare
  download; pending data acquisition")`. +11 tests under
  `tests/test_calibration.py`; the Edinburgh packet remains a validation
  candidate with `pending_data_acquisition` and
  `outside_sea_kayak_calibration_envelope` non-promotion reasons.
- Landed RFC 0043 stage 1: opt-in `kayakgen stability --high-angle-gz`
  (optional `--heel-grid-deg`) emits a `high_angle_gz` JSON block with the
  fixed-trim generated-body v1 curve, per-heel records, summary metrics only
  when every required grid point converges, mandatory surface warnings, and a
  structured `unavailable_reason` for synthetic bodies. Default
  `kayakgen stability` output is byte-equal to the prior behavior. No web,
  desktop, sweep summary, or comparison-frontier surfaces changed.
- Landed RFC 0009 sweep-side STL artifact emission: `evaluators.stl: true`
  in a sweep spec writes `candidates/<key>/hull.stl` and
  `candidates/<key>/deck.stl` via the same `kayakgen generate` STL writer.
  Each successful candidate record gains `stl_artifacts.{hull,deck}` with
  `{path, bytes, sha256}`. Failed and pending candidates skip artifact
  emission; resume preserves existing STL files byte-for-byte without
  regeneration. Sweep STLs are open inspection surfaces only and do not
  promote any candidate to watertight `cfd_ready`.
- Landed RFCs 0036-0039 as the post-workflow-0048 UI cleanup safe slice.
  RFC 0036 retains `_state_matches_preset_seed` with a Trame-state listener
  proof that drives the same-seed event sequence end-to-end without invoking
  the private helper. RFC 0037's `EXPORT_MENU_ROWS` schema is subtitle-only
  with no duplicate guidance fields. RFC 0038 polished the disabled mesh-package
  label to "Mesh package (CLI only)". RFC 0039 unified web snapshot keys and
  CFD/mesh-package aliases onto a shared `WebStateSchema`. No backend
  capability, REST payload shape, calibration, watertight readiness,
  real-solver, or hosted operation changed.

- Landed workflow 0053 stage 2: web query bootstrap and slider-safe state
  handling, sweep pending lifecycle reporting, high-angle stability summary
  semantics, and the accompanying roadmap/user-guide/RFC index and workflow
  report updates. This was a workflow and documentation landing; no new solver,
  calibration, or hosted execution capability changed.
- Scaffolded workflow 0053 as the next implementation burn-down stage for the
  remaining roadmap backlog: browser parity, geometry evidence harness,
  OpenFOAM adapter gate, resistance source evidence, high-angle GZ surfacing,
  sweep pending lifecycle, and a docs-sync tail followed by reviews and
  remediation. No runtime behavior, solver execution, or product capability
  changed.
- Integrated workflow 0052's majority decisions as documentation-only design
  records: the first production volume-mesher candidate is an OpenFOAM-v2512
  `snappyHexMesh` evidence harness, OpenFOAM `succeeded` remains blocked behind
  full mesh/provenance/case/parser gates, Edinburgh is the first validation-only
  resistance source-review packet, high-angle `GZ` surfacing is staged and
  opt-in, public demo operation remains deferred until owner/budget/smoke/
  cleanup evidence exists, and RFC 0009 `pending` lifecycle is the next
  sweep/search delta. No runtime behavior, tests, solver execution, public URL,
  calibration, watertight readiness, default high-angle output, desktop rewrite,
  optimization behavior, or product capability changed.
- Scaffolded workflow 0051 as the first implementation burn-down after the
  workflow 0050 decisions: seven parallel Codex implementation lanes for
  docs/status follow-through, UI successor cleanup, sweep objective metadata,
  solver-readiness reporting/schema hardening, OpenFOAM adapter skeleton,
  resistance source-review packets, and high-angle stability v1 gates,
  followed by three independent reviews, a findings ledger, remediation, and
  final review.
- Integrated workflow 0050's majority decisions as documentation-only design
  records: solver readiness is readiness-report-first, the first real solver
  target is OpenFOAM.com v2512 `interFoam` behind watertight evidence,
  resistance source/calibration promotion remains gated, high-angle stability
  has a fixed-trim generated-body v1 design, browser hosting is only a narrow
  server-backed exploratory demo posture, web is the primary UI composition
  target, and sweep/search defaults remain conservative. No runtime behavior,
  tests, solver execution, public URL, calibration, watertight readiness,
  high-angle stability output, desktop rewrite, optimization behavior, or
  product capability changed.
- Scaffolded workflow 0050 as a design-only decision workflow. Each open
  roadmap decision now has a required research packet, independent
  Claude/Codex/Gemini panel votes, strict majority integration, and final
  review before dependent implementation work can begin. No runtime behavior,
  tests, solver execution, calibration, watertight readiness, hosted operation,
  desktop rewrite, optimization behavior, or product capability changed.
- Added `docs/ROADMAP.md` through workflow 0049 as a documentation-only
  reconciliation of outstanding RFCs, stale deferred-queue items, workflow 0048
  successor RFCs, dependency tracks, and future Striatum implementation
  batches. No runtime behavior, tests, API payloads, export availability,
  solver execution, calibration, watertight readiness, final prediction,
  design-fitness, hosted-demo, full-parity, or real high-angle stability
  capability changed.
- Scaffolded workflow 0048 as a docs-only successor RFC backlog workflow with
  parallel Codex RFC drafting lanes for UI follow-up findings, closed-volume/
  solver readiness, real CFD adapter work, resistance calibration fixtures,
  and high-angle `GZ`, followed by traceability, no-claims, ergonomics/design,
  ops/test, integration, and final-review gates.
- Added proposed RFCs 0036-0043 through workflow 0048 as docs-only successor
  backlog scopes: four UI cleanup follow-ups from workflow 0047 plus
  closed-volume solver-readiness, real CFD adapter, resistance calibration
  fixture, and high-angle `GZ` successor gates. No runtime behavior, tests, API
  payloads, export availability, solver execution, calibration, watertight
  readiness, final prediction, or real stability output changed.
- Landed workflow 0047's RFC 0035 UI cleanup slice: web validity badges now
  classify the current hull against canonical web class envelopes before custom
  fallback, preset edit behavior is documented and test-pinned, export-menu
  rows and web state snapshots use declared source-of-truth schemas,
  slider-label CSS/accessibility checks preserve existing tokens and canonical
  labels, and the desktop Matplotlib slider fallback records its removal
  condition. This is maintenance cleanup only; no backend capability, REST
  payload shape, hosted CFD, real solver, calibration, final prediction,
  high-angle `GZ`, web-side mesh-package authoring, watertight `cfd_ready`
  promotion, or desktop parity rewrite landed.
- Landed workflow 0045's RFC 0034 workspace UI follow-up safe slice: web class
  presets reseed canonical hull sliders and narrow ranges, manual hull edits
  return the preset selector to `custom`, the validity badge derives from
  class/envelope state, Resistance and Mesh review cards render existing read
  models, and the Export menu exposes enabled STL rows plus honest local-data or
  unavailable JSON/package states. The slice preserves RFC 0033's no-new-backend
  capability boundary; calibrated drag, final prediction, design fitness,
  high-angle `GZ`, hosted/cloud CFD, real solver adapters, web-side
  mesh-package authoring, watertight `cfd_ready`, and desktop parity rewrite
  remain deferred.
- Published workflow 0034 and 0035 findings ledgers, clearing both backlog
  workflows for conservative Codex implementation lanes: RFC 0023 remains
  evidence-bound on generated-body-derived volume-mesh diagnostics before any
  `cfd_ready` promotion, and RFC 0024 remains limited to generated-body GZ
  handoff contracts, structured unavailable results, fixture-only labeling,
  claim guards, and tests before any real high-angle stability claims.
- Landed RFC 0023 watertight volume-mesh handoff slice: typed manifest,
  diagnostic, artifact, hash, and path-bound evidence records now preserve
  conservative open-surface behavior while allowing `cfd_ready` only for
  matching generated-body fixture volume-mesh evidence. CLI and JSON dispatch
  surfaces expose structured rejection reasons for missing, stale, synthetic,
  mismatched, and unsafe handoff evidence.
- Corrected RFC 0023/RFC 0024 status and user-facing docs after the workflow
  0034/0035 landings so the index now distinguishes fixture-backed
  `cfd_ready` handoff evidence from production solver readiness and real
  high-angle GZ stability claims.
- Scaffolded workflow 0046 for the reported slider-label visibility issue with
  traceability, ergonomics/design, and ops/test review lanes before Codex
  implementation.
- Scaffolded workflow 0047 as a UI follow-up cleanup successor with a Codex
  RFC/scope lane, traceability/no-claims/ergonomics-design/ops first-pass
  reviews, a Codex implementation lane requiring maximal useful sub-agent
  fanout, and a Claude final-review gate.
- Added proposed RFC 0035 through workflow 0047's RFC/scope lane, limiting
  the next UI cleanup pass to workflow 0045 and 0046 final-review findings:
  validity-badge/class semantics, preset edit wording, export/state hygiene,
  slider-label CSS/accessibility maintenance, desktop slider fallback cleanup,
  and focused tests/docs. No runtime product code or new backend, CFD,
  stability, calibration, mesh-readiness, or hosted capability was changed.
- Fixed workflow 0046's desktop and web slider-label visibility issue: desktop
  hull-parameter labels and value text now render legibly without overlapping
  adjacent rows, and web parameter-rail slider labels no longer sit under
  persistent thumb labels while preserving the canonical label text.
- Added the RFC 0024 high-angle GZ handoff envelope: generated closed-body
  diagnostic validation, structured unavailable results, fixture-only synthetic
  math, provenance-safe GZ fields, and tests that keep unavailable or fixture
  curves out of CLI, web, and generated sweep secondary-stability claims.
- Added RFC 0034 and workflow 0045 for the workspace UI follow-up slice:
  dynamic web class presets, dynamic validity badge, resistance and mesh
  read-model wiring, export-menu completion, and broader forbidden-copy
  tests. This successor keeps RFC 0033's no-new-backend-capability boundary
  and leaves calibrated drag, final prediction, high-angle GZ, hosted CFD, and
  watertight `cfd_ready` deferred.
- Added RFC 0033 and workflow 0044 as the workspace UI rework: a single
  three-region desktop/web shell (parameters, geometry, review), a shared
  semantic theme module, claim/readiness/CFD status chips wired to existing
  literals, structured advisory records additive to `DesignAdvisory.warnings`,
  a four-segment status bar, and forbidden-claim regression coverage for the
  Claude Design handoff's no-go strings. No backend capabilities are
  introduced; every existing REST route keeps its JSON shape. Workflow 0044
  now includes a dedicated ergonomics/design review lane before findings are
  ledgered.
- Added workflow 0044's RFC 0033 workspace UI implementation slice: shared UI
  theme tokens, structured advisory records, web workspace regions/status
  copy, mesh/readiness read models, desktop `Cm`/Export STLs touch-ups, user
  guide updates, and regression tests. Current resistance, mesh, and CFD
  outputs remain raw/open-surface/local plumbing, not final prediction,
  watertight-solid, hosted-worker, or calibrated claims.
- Added workflow 0039's RFC 0028 plumb-stem closure safe slice: independent
  `stern_rake`, explicit bow/stern coordinate convention, and exact-plumb
  endpoint/cap semantics for generated closed-body diagnostics while keeping
  open hull/deck STLs labeled as inspection surfaces.
- Added workflow 0033's RFC 0022 generated hull-plus-deck closed-volume
  evaluation body with serialized cap/join policy, waterline metadata,
  positive-volume diagnostics, and RFC 0021 self-intersection gating while
  keeping generated bodies below `cfd_ready`.
- Added workflow 0032's RFC 0021 explicit synthetic closed-volume
  self-intersection diagnostics: serialized `not_checked`, `passed`,
  `failed`, and `inconclusive` status, assembled-body triangle-pair evidence,
  bounded examples, and a new profile that still keeps `cfd_ready` false.
- Added RFC 0025 claim-state metadata to resistance and raw local-CFD records,
  with forbidden-promotion tests for raw CFD, validation-only fixtures,
  uncalibrated resistance, calibrated prediction evidence, and final
  design-fitness claims.
- Added workflow 0029's local web CFD job slice: `/api/cfd/*` routes and a
  compact Trame panel now expose server-local CFD profiles, job preparation,
  status, synchronous local adapter runs, bounded logs, and raw-result lookup
  over RFC 0015 job records while keeping all output raw and unvalidated.
- Documented workflow 0027's closed-volume safe slice: serializable explicit
  synthetic diagnostics and evidence-based watertight dispatch rejection may
  land, while generated hull-plus-deck closure and `cfd_ready` handoff remain
  deferred pending RFC 0016 policy decisions.
- Scaffolded queued roadmap workflows 0027-0031:
  - 0027 closed-volume geometry contract.
  - 0028 real CFD solver adapter.
  - 0029 web CFD job routes.
  - 0030 resistance calibration fixture.
  - 0031 high-angle `GZ` and secondary stability.
- Added the project convention that future RFC/workflow/user-facing changes
  update this changelog.
- Added proposed RFCs 0021-0030 for the remaining roadmap blockers:
  self-intersection diagnostics, generated closed-body construction,
  watertight handoff, high-angle `GZ` handoff, CFD/calibration claim gates,
  fixture-first CFD adapter work, resistance calibration acceptance,
  plumb-stem closure semantics, design-constraint surfacing, and hosted browser
  acceptance.
- Added RFC 0031 and workflow 0042 as the design-constraint surfacing revision,
  narrowing RFC 0029 into an implementation-ready validity-metadata slice with
  an explicit first-pass review remediation cycle.
- Documented workflow 0037's RFC 0026 fixture-adapter choices: a checked-in
  `python -m` module command, `raw-result.json` normalized output,
  `open_wetted_surface_resistance_v1` as the only fixture profile target, and
  continued raw/unvalidated wording while RFC 0017 OpenFOAM/SU2 selection
  remains deferred.
- Added workflow 0037's deterministic `fixture-local-command` CFD profile,
  fixture case files, local command execution, schema-validated raw-result
  parsing, persisted failure records, and CLI warning visibility, all kept
  raw/unvalidated with no solver validation or calibration claim.
- Scaffolded workflows 0032-0042 for those RFCs using the three-lane
  Striatum review pattern and implementer prompts requesting maximal useful
  sub-agent fanout with disjoint write scopes.
- Added RFC 0032 and workflow 0043 as the conservative successor to blocked
  workflow 0041: local browser-acceptance plus hosted-demo documentation scope,
  three first-pass review lanes, and a declared review-revision anchor for
  browser `needs_revision` routing.
- Added workflow 0042's RFC 0031 design-validity metadata across evaluate JSON,
  web payloads, desktop/web warning helpers, sweeps, and comparison reports
  while preserving advisory-only behavior, existing validation boundaries, and
  deferred geometry/CFD claims.
- Landed workflow 0043's local browser-acceptance profile, hosted-demo runbook
  documentation, exact `/paraview/` browser-probe handling, Share/STL/3D
  browser checks, and raw/unvalidated `/api/cfd/*` fixture-success coverage
  while keeping public hosting, real solver execution, validated CFD,
  calibrated resistance, and final design-fitness claims deferred.

### Changed

- Deep-scan doc-sync pass on 2026-05-17 after the eight-RFC wave:
  - `docs/USER_GUIDE.md` documents the 9 new CLI surfaces
    (`target-draft`, `target-trim`, `migrate-geometry`,
    `build-export`, `sensitivity`, `design-report`, `runs`,
    `calibration`, `--turning` flag on `evaluate`) and lists the
    new optional extras (`browser`, `builder`, `calibration`,
    `report`).
  - `docs/ARCHITECTURE_MAP.md` refreshed: package map adds 15 new
    files, CLI table adds 14 rows, durable-artifact catalogue adds
    9 new entries (SQLite index, `_store/` mirror, builder bundle,
    design-report HTML, sensitivity result, calibration campaign
    directories, target-workflow JSON, turning metrics). Public
    JSON record list updated with 14 new entries; no-claim rules
    extended for turning + sensitivity advisories.
  - `docs/DECISION_LOG.md` gains D029-D036 (one row per landed RFC,
    each citing structured tokens and the open-question defaults
    pre-resolved).
  - `docs/DDD.md` aggregates table gains `TankTestCampaign`,
    `IncliningTestCampaign`, `AcceptedFitRecord`, and the
    `ArtifactStore + SqliteIndex` row; Hull aggregate updated with
    `record_hash`/`design_hash`; domain-services section adds the
    eight new RFC entries; read-models section adds Sensitivity,
    DesignReport, BuildExport, Turning, TargetDraftMismatch,
    V2HydrostaticCrossCheck.
  - `docs/SPEC.md` "State the project owns" table adds 9 new rows;
    invariants list extended with hull-identity, geometry-V2
    admissibility, calibration_fixture promotion, display-only
    objective refusal, and pairwise within-evaluator-noise
    semantics; schema catalogue + CLI surface lists updated.
  - `docs/PRD.md` Delivered Today section gains six new bullets
    (Geometry V2 in Geometry, target-workflows + sensitivity +
    builder + turning in Evaluation, design-report + cross-run
    inspection + calibration tooling in Frontends/tooling);
    Roadmap And Deferrals rewritten to reflect what is now landed
    vs still operator-blocked; generative-search bullet moved
    from proposed to landed.
  - `docs/ROADMAP.md` track table refreshed; "Inverse design and
    reporting" + "Geometry V2 distribution model" + "Calibration-
    campaign tooling" track rows added.
  - `AGENTS.md` current-direction paragraph rewritten to reflect
    the 2026-05-17 state.
  - `OPERATOR_REPORT.md` gains a 2026-05-17 wave checkpoint with
    per-RFC summaries + the doc-sync pass.
- Refreshed `docs/PRD.md` "Delivered Today", "Roadmap And Deferrals", and
  success-criteria sections to match the 2026-05-16 landed state:
  high-angle GZ surfacing is now a delivered opt-in display-only path under
  `unvalidated_hydrostatic_comparison` semantics; the OpenFOAM-v2512
  succeeded path is recorded as an opt-in env-gated capability with
  `raw_unvalidated` payloads; the calibration and measured-GZ deferrals are
  re-scoped against the 2026-05-16 null findings; generative search points
  at RFC 0044.
- Refreshed `AGENTS.md` current-direction paragraph and dropped the stale
  "DECISION_LOG is mostly template" negative-space note (D001-D023 are now
  real recorded decisions).
- Added `ARCHITECTURE_REVIEW_2026-05-16.md` at the repo root — an
  operator-authored systems architecture review of kayakgen as of
  2026-05-16 covering verification snapshot, executive summary, what
  the project is trying to be, and architectural risks. Independent of
  the cowboy-session implementation commits; included for shared
  reference.
- Added `docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md` recording
  the two null findings from the 2026-05-16 research investigations
  (in-envelope measured kayak resistance and measured kayak GZ-vs-heel)
  along with the open-access references that were vendored as schema
  examples only.
- Corrected the RFC index/status headers for previously landed safe slices:
  RFC 0016, RFC 0022, RFC 0025, RFC 0027, and RFC 0031 now match their landed
  workflow state instead of stale proposed/accepted-target labels.
- Aligned individual RFC `Status:` headers with the sequential RFC index for
  previously landed/partial slices, including RFC 0021's landed
  self-intersection diagnostic status, and clarified workflow 0034/0035 review
  verdict semantics so pre-implementation gaps route to findings ledgers rather
  than dead-end review revisions.
- Marked RFC 0031 as the accepted implementation target for workflow 0042 and
  clarified in the RFC index that RFC 0029 remains background for that
  narrowed revision slice.
- Removed ambiguous `OPERATOR_REPORT.md` basename forbids from workflow 0042
  job scopes while leaving the root operator report outside those allowed
  paths.
- Clarified that legacy `bow_rake` historically controlled both bow and stern
  and remains the symmetric compatibility behavior for older hull JSON that
  omits `stern_rake`.
- Hardened comparison-report accepted-use provenance so raw comparative
  resistance and forged legacy final-prediction strings cannot become accepted
  calibrated prediction without fixture IDs, model version, fit evidence, and a
  validity envelope.
- Hardened RFC 0027 resistance calibration acceptance gates so only
  `accepted_fit` records with metrics, accepted fixture IDs, model version, and
  validity envelopes can satisfy calibrated-prediction provenance, while weak
  calibration/validation fixture metadata remains rejected.
- `kayakgen evaluate` and compact web metrics now show visible warnings when
  resistance values are the current uncalibrated comparative filter.
- Refreshed project Striatum Claude/Codex skill bundles to the running 1.36.0
  install so `striatum doctor` is clean again.
- Recorded the dependency plan for the next implementation batch:
  start self-intersection diagnostics, claim gates, and local-dispatch web CFD
  routes first; block generated bodies, watertight handoff, and real GZ output
  until their upstream evidence lands.

## 2026-05-13

### Added

- Added the root `README.md` and `docs/USER_GUIDE.md`, documenting current CLI,
  desktop, web, mesh package, and local CFD dispatch behavior without claiming
  calibrated resistance, real solver execution, watertight solids, or high-angle
  stability.
- Added proposed RFCs 0016-0020 to split the remaining roadmap into
  closed-volume geometry, first real CFD adapter, web CFD job routes,
  resistance calibration fixtures, and high-angle secondary stability.
- Added deterministic local CFD dispatch records and CLI surfaces:
  `kayakgen cfd prepare`, `kayakgen cfd status`, `kayakgen cfd run`, and
  `kayakgen cfd profiles`.
- Added a named `watertight_solid_resistance_v1` mesh-readiness profile as a
  blocked future profile, while keeping current generated packages below
  `cfd_ready`.
- Added generalized load components and bounded fixed-body upright trim
  equilibrium for explicit load cases.
- Added compact web analysis and comparison views plus comparison report
  loading.
- Added headless and optional Playwright web verification coverage.
- Added mesh-package diagnostics, manifest/profile metadata, and CLI/test
  coverage for packaging generated hull surfaces.
- Added sweep/candidate report foundations for Pareto-style comparison and
  filtering.
- Added source/provenance metadata for the University of Edinburgh
  Pacific-canoe dataset as validation-only input; no kayak calibration fixture
  was accepted.

### Changed

- Reconciled the PRD, RFC index, backlog queue, and operator report so current
  behavior is separated from roadmap deferrals.
- Reframed resistance output as an uncalibrated raw comparative filter rather
  than an accepted final prediction model.
- Marked RFC 0004 and RFC 0006 as partial safe slices after package/core work,
  with exact plumb-stem closure, asymmetric rake, watertight solid readiness,
  and remaining UI polish deferred.
- Marked RFC 0008 as partial: Trame shell, headless checks, and compact web
  analysis landed; full REST/browser/hosted-demo parity remains deferred.
- Updated Striatum skill/plugin bundles in the target repo.

### Deferred

- Real OpenFOAM/SU2/container/hosted CFD execution.
- Normalized or validated CFD physical outputs.
- Calibrated kayak resistance fixtures and calibrated product claims.
- Closed-volume hull-plus-deck geometry and watertight solid generation.
- High-angle `GZ` and secondary-stability curves.
- Web CFD job routes and full hosted browser acceptance.

## 2026-05-12

### Added

- Added the Striatum-driven RFC completion review/remediation workflow and
  pipeline-pivot RFC set.
- Added RFC 0009-0015 covering sweep records, CFD-ready mesh contracts,
  hydrostatic load cases, resistance calibration, Pareto comparison UI,
  generalized trim/GZ, and CFD solver dispatch.
- Added the accepted RFC 0007 package extraction path:
  `kayakgen/`, CLI entry points, compatibility shims, evaluators, and golden
  regression tests.
- Added `KayakClass` presets and `beam_wl` wiring for design constraints.
- Added the analytical resistance evaluator using Michell-wave and ITTC-style
  components as an exploratory comparative model.
- Added plumb-bow support through the `bow_rake` parameter and blended
  end-decay behavior.
- Added the Trame web frontend shell.
- Added context-hygiene docs and agent orientation for Striatum sessions.

### Changed

- Expanded the PRD from a single desktop hull generator toward a generative
  CFD/evaluation pipeline with desktop and web frontends.
- Audited and completed earlier GUI/layout work from RFC 0002 and RFC 0003,
  including class radio controls and plotting/layout cleanup.

## Initial History

### Added

- Added the original parametric kayak generator, desktop GUI, PyVista preview,
  STL exports, and Striatum scaffolding.
- Added early RFC/workflow scaffolds for GUI usability, layout/station view,
  3D rendering, plumb bow, resistance estimation, design constraints,
  architecture revisit, and web frontend direction.
