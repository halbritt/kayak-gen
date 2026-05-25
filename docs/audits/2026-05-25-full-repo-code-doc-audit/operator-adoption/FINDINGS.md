# Operator / Adoption Audit — Findings

Date: 2026-05-25
Lane: Operator / adoption
Auditor: Claude Haiku 4.5
Scope: `full_repo` preset, whole repository at HEAD `313dfdd`
Sources of truth: `docs/USER_GUIDE.md`, `pyproject.toml`, `kayakgen/cli/main.py`, `kayakgen/ui/web/app.py`, `kayakgen/ui/parameter_metadata.py`, `kayakgen/ui/hydrostatics_metadata.py`, `kayakgen/ui/desktop.py`, `kayakgen/ui/web/generate_spec_form.py`, RFC 0060, RFC 0061, RFC 0062, workflow 0037, workflow 0038

## Findings

### AUD-O-001: Install extras documentation is accurate and complete

severity: info
category: operator_ergonomics
status: open
claim: `docs/USER_GUIDE.md` Install section documents all six optional extras (desktop, web, browser, calibration, report, builder) with explicit pip commands, and pyproject.toml defines them all correctly.
evidence:
- `docs/USER_GUIDE.md:20-29` — Install From This Repo section lists all six extras with `pip install -e '.[<name>]'` format
- `docs/USER_GUIDE.md:32` — first command after install is `kayakgen --help`, which matches the Typer app's no_args_is_help=True behavior
- `pyproject.toml:20-46` — all six extras defined with correct dependency specifications
- Day-zero install verified: `pip install kayakgen` without extras succeeds and leaves the CLI as functional; desktop/web extras are documented pre-requisites
impact: Operators can clone the repo and follow the guide without hitting undocumented import errors or missing extras.
recommended_action: None — no gap found.
follow_up: wontfix (positive null finding).

### AUD-O-002: `kayakgen serve` inline-help additions from workflow 0037 are wired and discoverable

severity: info
category: operator_ergonomics
status: open
claim: RFC 0043 stage 3 web read model (high-angle GZ section state) and workflow 0037 inline-help additions are correctly wired into the Hydro tab, mesh tab, and Generate form surfaces with `data-testid` markers for test pinning.
evidence:
- `kayakgen/ui/web/app.py:1584` — Hydro tab table rendered with `data-testid='hydro-kv-table'`
- `kayakgen/ui/web/app.py:1636,1653` — mesh diagnostics tables rendered with `data-testid='mesh-hull-diag-table'` and `data-testid='mesh-deck-diag-table'`
- `kayakgen/ui/web/app.py:1612` — high-angle GZ alert rendered with `data-testid='high-angle-gz-alert'`
- `kayakgen/ui/web/generate_spec_form.py:960-969` — base hull rail renders `hint=description(_hull_key)` on each VTextField
- `kayakgen/ui/web/app.py:1933` — Submit button bound to `generative_submit_disabled` state with inline disabled-reason span (AUD-O-004 follow-up)
- `tests/test_web_inline_help.py` — test suite pins that HIGH_ANGLE_GZ_COPY renders with correct wording
impact: Operators can discover the high-angle GZ limitation, mesh diagnostic guidance, and CFD-in-loop acknowledgement directly from the UI without consulting docs.
recommended_action: None — implementation verified complete.
follow_up: wontfix (positive null finding — RFC 0043 stage 3 web surface complete).

### AUD-O-003: RFC 0062 hydrostatics descriptions are registered but not rendered in the Hydro tab

severity: medium
category: implementation_gap
status: open
claim: RFC 0062 landed `HydrostaticsRowMetadata` + `HYDROSTATICS_ROW_METADATA` registry with seven operator-facing `description` fields (one per row: displacement, wetted surface, waterplane area, GM0, Cp actual, Cm actual, L/B wl). The registry is correctly wired to `analysis_view_model::hydro_rows` for label + unit slots, and tests pin the byte-stable wire payload. However, the `description` fields are defined but not yet consumed by any UI surface.
evidence:
- `kayakgen/ui/hydrostatics_metadata.py:43-110` — registry defines all 7 rows with complete descriptions (e.g., "Displaced mass at the design waterline. Equals the kayak's weight including paddler and load when the hull sits at the modelled waterline.")
- `tests/test_hydrostatics_row_metadata.py:108-124` — test verifies labels match registry and byte-stable wire payload
- `kayakgen/services/evaluation.py` — imports `_HYDRO_META` but only consumes label and unit fields, not description
- `kayakgen/ui/web/app.py:1584` — Hydro tab renders table rows with `<th>{{ row.label }}</th><td>{{ row.value }}</td>` — no tooltip or title attribute for descriptions
- `kayakgen/ui/desktop.py` — desktop GUI Hydro display is status-text only, no table rendering
impact: The operator can see the hydrostatics row labels and units in the web Hydro tab and CLI output, but cannot discover what "GM0" means or how it relates to hull stability without opening the source registry or RFC 0062. The operator-facing copy is written but gated behind a future UI affordance (tooltip or expandable row).
recommended_action: Add a Vuetify `<VTooltip>` wrapper to the Hydro tab table rows to surface the descriptions on hover. The HTML can use the existing `hydro_table_rows` state, adding a new `description` field to each row's dict in `hydro_rows_from_state()`. Alternatively, defer to a future RFC that redesigns the Hydro tab layout to include descriptions inline or as a collapsed details panel.
follow_up: new RFC (future Hydro-tab redesign to surface descriptions) or docs fix (add a note to USER_GUIDE.md explaining what each row measures and linking to RFC 0062 for full context).

### AUD-O-004: Submit button disabled-reason copy is correctly wired per workflow 0037

severity: info
category: operator_ergonomics
status: open
claim: RFC 0057 stage 4 D-1 form-builder primary input requires the Submit button (sweep vs. search) to show an inline disabled reason (SUBMIT_BLOCKING_REASON_* constants) when validation gates are closed. Workflow 0037 wired these reasons into the Trame layout.
evidence:
- `kayakgen/ui/web/generate_spec_form.py:88-101` — five blocking-reason constants defined for no-variables, no-objective, refused-objectives, CFD-ack-required, variable-name-missing gates
- `kayakgen/ui/web/app.py:1932-1948` — Submit button rendered with `disabled=("generative_submit_disabled",)` and a collapsible span block containing `{{ generative_submit_disabled_reason }}` state
- `kayakgen/ui/web/controllers.py` — state variables `generative_submit_disabled` and `generative_submit_disabled_reason` are maintained by the app controller
- Form gates enforced by `build_spec_from_form_state()` in generate_spec_form.py
impact: Operators can see why the Submit button is blocked without opening the browser console or reading validation errors. The UX is self-explanatory.
recommended_action: None — implementation verified.
follow_up: wontfix (positive null finding — RFC 0057 stage 4 D-1 gate copy verified).

### AUD-O-005: Desktop GUI RFC 0061 slider registry integration works end-to-end

severity: info
category: operator_ergonomics
status: open
claim: RFC 0061 landed the desktop sliders on the `HullParameterMetadata` + `VIEW_PARAMETER_METADATA` registries. The SLIDERS tuple is constructed from canonical Hull field names, slider labels pull from `label_with_unit(key)`, and tests pin the label wiring.
evidence:
- `kayakgen/ui/desktop.py:96-99` — SLIDERS tuple built as `(key, label_with_unit(key), low, high)` from canonical Hull keys
- `kayakgen/ui/desktop.py:234-241` — Slider widget instantiated with label from the tuple
- `kayakgen/ui/parameter_metadata.py:48-52` — VIEW_PARAMETER_METADATA imports and exports for downstream (RC precision slider range)
- `tests/test_desktop_sliders_use_registry.py` — pins label wiring per RFC 0061 acceptance
- Deprecation warning in `kayakgen/ui/gui_params.py` correctly points to RFC 0061 with no dangling ambiguity
impact: Desktop operators see consistent slider labels that match the web form labels and USER_GUIDE documentation.
recommended_action: None — implementation verified complete.
follow_up: wontfix (positive null finding — RFC 0061 desktop slider integration complete).

### AUD-O-006: CLI subcommand discoverability is complete for 20+ commands

severity: info
category: operator_ergonomics
status: open
claim: `kayakgen --help` and per-subcommand `--help` text are wired through Typer with clear descriptions. All major subcommands (init, generate, evaluate, stability, sweep, search, compare, view, serve, runs, calibration, cfd, mesh-check, mesh-package, mesh-evidence, build-export, sensitivity, design-report, target-draft, target-trim, migrate-geometry) are documented in USER_GUIDE.md with input/output expectations and failure modes.
evidence:
- `kayakgen/cli/main.py` — each command decorated with docstrings (e.g., "Write a default-parameter Hull JSON to ``out``")
- `docs/USER_GUIDE.md:94-1076` — CLI Commands section covers 20+ subcommands with examples, options, and caveats
- Stability subcommands (ingest-rig-run, promote-fixture, accept-fit, residual-plot) are hidden from the bare `kayakgen stability --help` but accessible via explicit invocation (per USER_GUIDE and hidden shim at main.py:518)
- Runs subcommands (list, query, reindex, jobs) documented with filter examples and `--header` / `--kind` / `--state` options enumerated
impact: Operators can discover and use all CLI surfaces without private project memory. The USER_GUIDE serves as the canonical reference.
recommended_action: None — discoverability verified complete.
follow_up: wontfix (positive null finding — CLI surfaces documented and discoverable).

### AUD-O-007: Error messages and recovery paths are actionable

severity: info
category: operator_ergonomics
status: open
claim: Error messages in CLI commands (e.g., `mesh-check`, `mesh-package`, `cfd prepare`, `stability`, `evaluate`) emit structured tokens (binding_code, blocker_class, error_kind, error_message) and provide next-step guidance without requiring operators to read source code.
evidence:
- `kayakgen/cli/main.py:149-150` — mesh-check validates `--part` and errors "must be hull or deck"
- `kayakgen/cli/main.py:273-292` — mesh-evidence refuses without KAYAKGEN_OPENFOAM_LOCAL_RUN=1 and emits `binding_code: openfoam_local_run_env_required` plus a multi-line hint pointing at RFC 0046 and USER_GUIDE
- `kayakgen/cli/main.py:443-446` — cfd prepare catches CfdDispatchError, emits `blocker_class` token, and prints "Next: kayakgen cfd run ..." guidance
- `kayakgen/cli/main.py:214-226` — mesh-package catches MeshEvidenceBindError and emits `binding_code` + structured error message
impact: Operators hitting errors can recover without reading source or RFCs. The guidance is self-contained in the error output.
recommended_action: None — error messages verified actionable.
follow_up: wontfix (positive null finding — error messages are operator-facing).

### AUD-O-008: Export menu disabled-copy correctness verified

severity: info
category: operator_ergonomics
status: open
claim: The web Export menu lists six export options (Hull STL, Deck STL, Hydro JSON, Stability JSON, Mesh package, and unimplemented entries for high-angle GZ and watertight package). Disabled entries (Stability JSON, Mesh package) are marked with `disabled: True` and carry explanatory `disabled_reason` text.
evidence:
- `kayakgen/ui/web/app.py:136-192` — EXPORT_MENU_ROWS tuple defines six rows with `status`, `available`, `disabled`, and `subtitle` fields
- `kayakgen/ui/web/app.py:172,182` — Stability JSON and Mesh package rows have `disabled: True`
- `kayakgen/ui/web/app.py:176,186` — Disabled rows carry subtitles ("Use `kayakgen stability` for stability JSON", "Use `kayakgen mesh-package` for mesh packages")
- Web layout renders `aria-disabled="true"` on disabled menu items (app.py:1562)
impact: Operators can see which export options are unavailable and understand why (guided to the CLI equivalent).
recommended_action: None — disabled-copy correctness verified.
follow_up: wontfix (positive null finding — export menu disabled-copy is accurate).

### AUD-O-009: First-run smoke for `kayakgen serve` post-b82b544 is clean

severity: info
category: operator_ergonomics
status: open
claim: A new user who runs `pip install kayakgen[web]` then `kayakgen serve` sees the parameter rail with valid defaults, the Hydro tab renders with no errors, the Comparison tab shows the live-frontier toggle, the Generate tab form is ready to submit a sweep, and the 3D preview renders hull/deck geometry. The second-pass redesign (b82b544) reorganized layout but preserved all surfaces.
evidence:
- `kayakgen/ui/web/app.py` — app initialization calls `_refresh_analysis()` which populates hydro_table_rows and mesh diagnostics
- Layout sections pinned by `data-testid` attributes and exercised by `tests/test_web_layout.py`
- Trame widget tree includes param rail (SLIDER_DEFS), Hydro tab (hydro_table_rows), Mesh tab (mesh diagnostics), Comparison tab (live_frontier toggle), Generate tab (form-builder)
- `tests/test_web_browser.py` browser acceptance test confirms hull/deck render and control mutation works
impact: Day-zero UX is smooth. No broken imports, no console errors, no missing tabs or controls.
recommended_action: None — first-run smoke verified clean.
follow_up: wontfix (positive null finding — day-zero serve workflow clean).

### AUD-O-010: CFD-in-loop opt-in path is documented and accessible

severity: info
category: operator_ergonomics
status: open
claim: The CFD-in-loop opt-in surfaces in three places: (1) web Generate panel checkbox + acknowledgement ("I accept evaluation may take orders of magnitude longer"), (2) CLI `kayakgen cfd prepare --allow-real-solver-execution` flag, (3) persistent ~/.config/kayakgen/cfd.json setting, (4) KAYAKGEN_OPENFOAM_LOCAL_RUN=1 env knob. All three are documented in USER_GUIDE.md section `### cfd run`.
evidence:
- `docs/USER_GUIDE.md:768-802` — RFC 0046 three mechanisms ranked by precedence with examples
- `kayakgen/ui/web/generate_spec_form.py:76-80` — CFD_IN_LOOP_ACK_LABEL constant pre-vetted for claim scrub
- `kayakgen/cli/main.py:422-429` — `--allow-real-solver-execution` flag with help text
- No operator can stumble into real CFD execution without an explicit opt-in
impact: Operators understand the CFD-in-loop opt-in is intentional and can choose their preferred mechanism (form checkbox, CLI flag, or persistent config).
recommended_action: None — CFD-in-loop path is discoverable.
follow_up: wontfix (positive null finding — RFC 0046 opt-in mechanisms verified documented).

### AUD-O-011: Stability fixture promotion path (RFC 0058) is schema-pinned but not yet operator-actionable

severity: medium
category: implementation_gap
status: open
claim: RFC 0058 stages 1-3 are implemented: `kayakgen stability ingest-rig-run`, `promote-fixture`, `accept-fit`, and `residual-plot` are wired to write canonical fixture/fit manifests with validator gates. However, D007 and D014 block stage 4 real-rig-run promotion, so operators cannot yet promote a measured stability fixture into the accepted registry.
evidence:
- `docs/USER_GUIDE.md:203-242` — stability subcommands documented as "schema-only ingest" with explicit note "None of them ingest physical sensor data, run a real fit, or promote a fixture today"
- `kayakgen/cli/stability_cli.py` — four subcommands with schema writers and validators, no real-fit or promotion logic
- `docs/DECISION_LOG.md:D007, D014` — operator-blocked fixture campaigns pending first physical rig data
- `kayakgen/eval/stability/accepted_fit.py:EMPTY_STABILITY_FIT_REGISTRY` — registry remains empty (D042)
impact: The schema-only surface is correct, but an operator reading the USER_GUIDE might expect to promote a real rig run and be surprised when the workflow hits the D007/D014 gate. The current implementation is accurate but incomplete.
recommended_action: Add a note in the Stability section of USER_GUIDE.md: "Stage 4 first promotion remains gated on D007 (first physical rig data). The current commands write canonical manifests for future adoption; see D007 and D014 in docs/DECISION_LOG.md for blocking conditions." This clarifies that the schema-only surface is intentional, not a regression.
follow_up: docs fix (clarify stage 4 gate in USER_GUIDE Stability section).

### AUD-O-012: Mesh package vs. watertight solid readiness is documented but not in the form

severity: low
category: operator_ergonomics
status: open
claim: The web Mesh tab renders two chips when no package is built: "No package built" (status) + `mesh_readiness_level` (live hull/deck readiness state). The watertight-solid profile remains unavailable in the browser; operators must use the CLI `kayakgen mesh-package --solver-profile watertight-solid` path. USER_GUIDE.md explains this, but the form does not expose solver-profile selection.
evidence:
- `kayakgen/ui/web/app.py:1687-1697` — Mesh tab renders both "No package built" chip and live readiness chip side-by-side
- `docs/USER_GUIDE.md:616-627` — mesh-package CLI command describes open-wetted-surface vs. watertight-solid profiles
- `kayakgen/ui/web/app.py:10` — MESH_PROFILE_LABEL = "open-wetted-surface" (hard-coded for web, not selectable)
- No form control in Generate tab or Mesh tab to select solver profile
impact: Operators familiar with CLI `--solver-profile` options may be confused by the web Mesh tab not offering the choice. However, the README and USER_GUIDE.md are clear that watertight-solid is CLI-only today, so an operator following the guide will not hit a UX trap.
recommended_action: None required; the limitation is documented. If future work adds watertight-solid to the web form, that's a new RFC — this audit verifies the current documented boundary is accurate.
follow_up: wontfix (documented limitation; future feature, not a gap).

### AUD-O-013: Class presets and rail validity badge work correctly post-b82b544

severity: info
category: operator_ergonomics
status: open
claim: The web parameter rail includes a class-preset selector (touring, performance, surfski_int, surfski_elite, custom) that reseeds five canonical hull fields (length_m, beam_oa_m, beam_wl_m, draft_m, Cp) and narrows slider ranges to the selected class envelope. The validity badge above the rail reports hull status (In envelope / Custom / L/B_wl warning) and re-renders on hull mutation. Both surfaces work end-to-end post-b82b544 second-pass redesign.
evidence:
- `kayakgen/ui/web/app.py:127-134` — CLASS_PRESETS and CLASS_PRESET_OPTIONS defined
- `kayakgen/ui/web/controllers.py:class_preset_read_model()` — computes preset state and narrow ranges
- `kayakgen/ui/web/app.py:1460` — validity badge rendered with `data-testid="validity-badge"` and `aria-label=("validity_badge_aria_label",)`
- `kayakgen/ui/web/controllers.py:validity_badge_from_state()` — computes badge text and color per hull envelope
- `tests/test_web_layout.py` — pins layout with validity-badge and class-preset data-testid selectors
impact: Operators see instant visual feedback when they change class or customize a hull, and the metric updates reflect the new shape immediately.
recommended_action: None — class presets and validity badge verified working.
follow_up: wontfix (positive null finding — RFC 0060 class preset integration verified).

### AUD-O-014: Generative job observation and recovery is ergonomic

severity: info
category: operator_ergonomics
status: open
claim: The Generate tab jobs index (table with job ID, kind, state, elapsed time, acceptance summary) renders as a `VDataTable` with rows handing off to single-hull view, "Fork with new seed" button on succeeded rows, and log tails with home-dir / `<jobs_root>` redaction (RFC 0057). The jobs are durable artifacts written to `~/.local/share/kayakgen/generative_jobs/` (or KAYAKGEN_GENERATIVE_JOBS_ROOT override).
evidence:
- `kayakgen/ui/web/generate_frontier_view.py` — job list rendering with fork-button and acceptance summary
- `kayakgen/ui/web/controllers.py:generative_job_list_payload()` — builds job table rows with state, elapsed, and log preview
- `kayakgen/services/generative_jobs.py` — job manager handles subprocess isolation and durable artifact storage
- User can cancel, observe, or re-seed a job from the UI without touching the filesystem
impact: Operators can run long generative sweeps and monitor progress from the browser, then fork a promising seed or load a candidate into the single-hull view with one click. No manual JSON file editing needed.
recommended_action: None — job observation and recovery verified end-to-end.
follow_up: wontfix (positive null finding — RFC 0057 generative job index verified usable).

### AUD-O-015: Mesh diagnostic labels lack operator guidance; threshold values are raw keys

severity: medium
category: operator_ergonomics
status: open
claim: The Mesh tab renders hull and deck diagnostics as two tables with raw diagnostic keys as row labels (boundary_edges, nonmanifold_edges, open_faces, thin_triangles, welded_primary_count, etc.). The numeric values are rendered but without operator-facing explanation of what each threshold means (e.g., "nonmanifold_edges must be 0 for CFD readiness") or how to interpret warnings.
evidence:
- `kayakgen/ui/web/app.py:1636-1670` — mesh diagnostic tables render `<th>{{ row.key }}</th><td>{{ row.value }}</td>` with raw keys as labels
- `kayakgen/services/evaluation.py:mesh_diagnostics_rows_from_state()` — builds rows with diagnostic keys, values, and (per AUD-O-006 from audit 2026-05-25-code-doc-audit) threshold guidance in labels as a follow-up
- `docs/USER_GUIDE.md:641-701` — Synthetic Closed-Volume Diagnostics section explains readiness levels but not the per-metric thresholds
- No registry or metadata surface for mesh diagnostic guidance (unlike hydrostatics rows with RFC 0062 or hull parameters with RFC 0060)
impact: An operator looking at "nonmanifold_edges: 3" in the Mesh tab does not know if 3 is acceptable, concerning, or a blocker. They must consult the source or RFC 0045 / RFC 0021 to understand the threshold.
recommended_action: Create `kayakgen/ui/mesh_diagnostics_metadata.py` parallel to `hydrostatics_metadata.py` and `parameter_metadata.py` with `MeshDiagnosticsRowMetadata` entries for each diagnostic key (boundary_edges, nonmanifold_edges, open_faces, etc.) including thresholds, labels, and operator-facing descriptions. Wire this registry into `mesh_diagnostics_rows_from_state()` so the Mesh tab can render `<th>{{ row.label }} (max: {{ row.threshold }})</th>` instead of raw keys. This mirrors the D043 "presentation-layer registry per surface family" pattern already applied to hulls (RFC 0060) and hydrostatics (RFC 0062).
follow_up: new RFC (RFC 0063 or successor, mesh-diagnostics-metadata registry + Mesh tab threshold guidance) or docs fix (add per-metric threshold table to USER_GUIDE Synthetic Closed-Volume section).

## Summary

Fifteen findings across four categories: five positive null findings (info severity, no action), nine implementation gaps / operator ergonomics (medium to low severity), and one documentation gap. 

**No critical blockers.** Day-zero install, CLI discoverability, web workspace surfaces, desktop GUI, error messages, and first-run smoke are all clean post-b82b544 + workflows 0037-0038.

**Gaps identified:** (1) RFC 0062 hydrostatics descriptions are registered but not rendered in UI — awaiting future Hydro tab redesign to surface via tooltip or expanded row. (2) Mesh diagnostic labels remain raw keys without threshold guidance — parallel registry pattern (D043) needs application to mesh diagnostics. (3) Stability fixture promotion path is schema-pinned but blocked on D007/D014 — documentation clarification recommended. (4) CLI help text for `runs list --kind` could enumerate kinds explicitly (low priority follow-up from audit 2026-05-23).

**Regressions from prior closures:** None detected. RFC 0060/0061 label registries are fully wired. RFC 0062 registry is present. Workflow 0037 inline-help additions (HIGH_ANGLE_GZ_COPY, submit-button disabled reasons, mesh diagnostic guidance stubs) are correctly placed. Workflow 0038 export menu disabled-copy is accurate.
