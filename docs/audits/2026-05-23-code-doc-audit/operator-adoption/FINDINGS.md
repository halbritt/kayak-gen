# Operator / Adoption Audit — Findings

Date: 2026-05-23
Lane: Operator / adoption
Auditor: Claude Haiku 4.5
Scope: `release_candidate` preset, commits f78e478..HEAD (10 commits)
Sources of truth: RFC 0060, RFC 0061, workflow 0032-0034, `kayakgen/ui/web/generate_spec_form.py`, `kayakgen/ui/parameter_metadata.py`, `kayakgen/ui/desktop.py`, `kayakgen/cli/runs_cli.py`, `kayakgen/ui/gui_params.py`, `prompts/web_ui_second_pass_rework_2026-05-22.md`

## Findings

### AUD-O-009: RFC 0060 web form labels are fully wired in code but render-verification test coverage is missing

severity: medium
category: implementation_gap
status: open
claim: RFC 0060 landed HullParameterMetadata as the label/unit/description source and integrated it into generate_spec_form.py, but the test suite does not verify that `VTextField` widgets actually render the hint prop (description text) — only that the form state serializes correctly.
evidence:
- `kayakgen/ui/web/generate_spec_form.py:960-969` — base-hull rail renders `hint=description(_hull_key)` on each VTextField.
- `kayakgen/ui/web/generate_spec_form.py:789-792` — variable-selector picklist items sourced from `label_with_unit(parameter)`.
- `kayakgen/ui/web/generate_spec_form.py:763-769` — objectives picklist sources labels from OBJECTIVE_METADATA.
- `tests/test_hull_parameter_metadata.py` — pins registry contract (label/unit/description fields trimmed/non-blank).
- `tests/test_generate_spec_form.py` — tests form serialization payload, not rendered VTextField props.
- No test file (`test_web_layout.py`, `test_web.py`, etc.) asserts that `render_spec_form_section(app)` actually emits VTextField children with populated hint attributes.
impact: The code implements RFC 0060 correctly per the static audit, but an operator loading `kayakgen serve` in a browser would be the first to discover if Vuetify's `:hint` prop actually surfaces the description text. A failed render (e.g. wrong prop name, missing v-model binding) would be invisible to the test suite.
recommended_action: Add a lightweight test under `tests/test_web_layout.py` that mocks a Trame app, calls `render_spec_form_section(app)`, and inspects the emitted widget tree for VTextField children with non-empty hint attributes matching the registry descriptions. This does not need to be a full browser test; a Trame widget-tree inspection is sufficient.
follow_up: test coverage (low-effort regression for RFC 0060 acceptance).

### AUD-O-010: Desktop slider labels are wired to label_with_unit() but no test verifies the rendered label string

severity: medium
category: implementation_gap
status: open
claim: RFC 0061 landed the desktop SLIDERS rename to canonical Hull keys and wired each slider's label to `label_with_unit(key)` at construction time, but there is no test that checks the actual matplotlib Slider widget label property.
evidence:
- `kayakgen/ui/desktop.py:96-99` — SLIDERS tuple constructed as `(key, label_with_unit(key), low, high)`.
- `kayakgen/ui/desktop.py:234-241` — Slider widget constructed with `label=label` from the tuple.
- `kayakgen/ui/desktop_slider_ranges.py` — separate module for ranges; registry integration is correct per static analysis.
- `tests/test_desktop_sliders_use_registry.py` — pins that the SLIDERS tuple consumes the registry correctly.
- No test inspects `s.label.get_text()` or similar to confirm the rendered matplotlib label reads "Prismatic coefficient (Cp)" instead of raw "Cp".
impact: Same as AUD-O-009: the code is correct per static analysis, but the rendered label on the desktop GUI would be the actual surface an operator sees. If matplotlib's Slider label assignment is broken or the fontsize/positioning interferes with readability, the test suite would not catch it.
recommended_action: Add an assertion in `tests/test_desktop_sliders_use_registry.py` that instantiates a KayakGUI or directly constructs a Slider widget and checks `slider.label.get_text()` for the expected `label_with_unit()` output. Spot-check at least "Cp" ("Prismatic coefficient (Cp)") and "beam_wl_m" ("Beam WL (m)").
follow_up: test coverage (low-effort regression for RFC 0061 acceptance).

### AUD-O-011: `kayakgen runs list --header` and `kayakgen runs jobs --header` do not enumerate filter-key options in help text

severity: low
category: operator_ergonomics
status: closed (partial)
claim: RFC 0032 workflow added the `--header` flag to both commands with clear help text explaining what the flag does, and the `runs jobs` command explicitly enumerates valid `--state` and `--kind` values in the option help. However, `runs list` has no equivalent `--kind` enumeration, creating asymmetry.
evidence:
- `kayakgen/cli/runs_cli.py:62-73` — `runs_list_command` accepts `--kind` with generic help "Filter by run kind: sweep | search | cfd | comparison."
- `kayakgen/cli/runs_cli.py:102-122` — `runs_jobs_command` accepts `--state` with explicit list "queued | running | succeeded | failed | cancelled | resumable" and `--kind` with "sweep | search."
- `.venv/bin/kayakgen runs list --help` output shows only "Filter by run kind: sweep | search | cfd | comparison" without the `--header` help mentioning which columns will be printed.
- `.venv/bin/kayakgen runs jobs --help` output shows explicit enumeration in both `--state` and `--kind` option help.
impact: Low — the kind filter is documented inline and the asymmetry is minor. But an operator using `--header` cannot ask `--help` for the column names; they must read the source or run once to see the output.
recommended_action: Backport the explicit enumeration from `runs jobs` to `runs list` for consistency. Add one line to the `--header` help text on both commands: "When --header is set, the columns are: run_id, kind, name, timestamp, status_str."
follow_up: source change (one-line addition, already landed via workflow 0032; minor follow-up for polish).

### AUD-O-012: GUI deprecation warning in `kayakgen/ui/gui_params.py` is developer-facing, not operator-facing

severity: low
category: operator_ergonomics
status: open
claim: RFC 0061 added a DeprecationWarning to the `hull_from_gui_params(params)` shim that names RFC 0061 and explains the migration path. The warning is correct from a maintainer's perspective but references internal implementation details that an external operator who hits the warning would not understand.
evidence:
- `kayakgen/ui/gui_params.py:39-46` — DeprecationWarning text: "kayakgen.ui.gui_params.hull_from_gui_params is deprecated by RFC 0061; the desktop GUI now uses canonical Hull field names directly. Pass `params` straight to `Hull(**params)` after filtering view-only keys."
- The warning assumes the reader knows what "RFC 0061" is, what "view-only keys" means, and that `Hull(**params)` is the right refactor target.
- External consumers of this shim (if any) would see the RFC number but have no breadcrumb to the RFC itself or the migration plan in USER_GUIDE.
impact: Low — the shim is an internal compatibility layer. But if a downstream user or test suite gets this warning, they have no actionable guidance without reading the RFC or the source comment above the function.
recommended_action: Augment the warning with one sentence: "For details, see docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md and the `kayakgen/ui/parameter_metadata.py` registry." This does not need to be in the warning itself; a docstring cross-reference is sufficient since this is not operator-facing in the happy path.
follow_up: docs fix (one-line docstring addition).

### AUD-O-013: `prompts/web_ui_second_pass_rework_2026-05-22.md` brief accurately targets existing pain surfaces

severity: info
category: operator_ergonomics
status: open
claim: The prompt brief lists "Generate panel density and hierarchy", "Pareto frontier readability", "jobs index ergonomics", "class preset selector + rail validity badge", and "vocabulary surface" as pain points. Cross-checking against the code and the previous audit (AUD-O-003 closed by RFC 0060) shows the brief identifies real surfaces but does not confirm whether the pain remains post-landing.
evidence:
- `prompts/web_ui_second_pass_rework_2026-05-22.md:46-73` — lists suspected pain surfaces with code file references.
- `docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md:75-98` — AUD-O-003 closed RFC 0060 landing the label/tooltip registry; no mention of the Generate panel's vertical density or hierarchy as a residual pain point.
- `kayakgen/ui/web/generate_spec_form.py:908-1232` — form emission shows vertical stacking of sections (spec name, job kind, base hull rail, variables, algorithm, objectives, evaluators, CFD-in-loop, budget, raw JSON).
- No operator feedback is recorded in the remediation plan or elsewhere on whether the vertical density is actually a blocker after RFC 0060.
impact: Informational only — the brief is reasonable and grounded in prior audit work. Recording the null finding to confirm that the second-pass rework is addressing residual ergonomics issues, not re-inventing what RFC 0060 already fixed.
recommended_action: None — this is a valid null finding confirming the brief's scope is accurate.
follow_up: wontfix (positive informational finding).

### AUD-O-014: Audit run discoverability — no README or index in docs/audits/

severity: low
category: operator_ergonomics
status: closed (R1, same commit, see CHANGELOG ### Changed)
claim: An operator looking at `docs/audits/` for the first time sees two dated directories (2026-05-22 and 2026-05-23) with no index or README explaining which audit is the canonical one, what the naming convention is, or whether to read FINDINGS.md or SYNTHESIS.md first.
evidence:
- `ls -la /home/halbritt/git/kayak-gen/docs/audits/` shows only two date-stamped directories; no INDEX.md, README.md, or .LATEST symlink.
- `docs/audits/2026-05-22-code-doc-audit/SYNTHESIS.md` and `docs/audits/2026-05-23-code-doc-audit/SOURCES.md` are present but an operator cannot tell which is "the one to read" without opening both.
- `docs/USER_GUIDE.md` does not mention where audit artifacts land or how to navigate `docs/audits/`.
impact: Low — remediation plans and synthesis artifacts exist and are discoverable by date. But operator onboarding friction: someone looking for "what changed in kayak-gen since I last checked" has to guess the directory structure rather than following a breadcrumb.
recommended_action: Create `docs/audits/README.md` with a one-sentence explanation of the audit cadence (per RFC 0059), a list of recent runs with their preset and date, and a pointer to "read SOURCES.md for scope, then the three FINDINGS.md artifacts, then SYNTHESIS.md, then REMEDIATION_PLAN.md for actions." Mark the most recent run as "canonical current" so operators know which to prioritize.
follow_up: docs fix (light-touch README).

### AUD-O-015: Workflow 0029-0034 SOURCES.md files are scaffolds with TODO placeholders, not filled-in context

severity: low
category: implementation_gap
status: closed (R2, same commit; SOURCES.md template-ness made explicit + audits/README.md provides worked examples)
claim: RFC 0059 describes workflow scaffolds 0029-0034 as runnable by an operator using `striatum workflow plan`. The SOURCES.md files in each workflow are templates with TODO markers (e.g., "TODO — paths under kayakgen/eval/") rather than filled-in context that would unblock a re-runner.
evidence:
- `docs/workflows/0029-code-doc-audit/SOURCES.md` — contains "TODO" 7 times in the key input sections.
- `docs/workflows/0030-stability-claim-gate-literal/SOURCES.md:1-50` — filled in with actual file references and RFC/finding citations.
- `docs/workflows/0031-*` through `docs/workflows/0034-*` — workflows 0031-0034 have filled-in SOURCES.md (they have been run as part of the 2026-05-22 audit).
- `docs/workflows/0029-code-doc-audit/SOURCES.md:13-17` — placeholder entries for each lane's input paths.
impact: Low to Medium — workflow 0030 shows the pattern is achievable. But workflow 0029 (the template audit itself) remains a scaffold. A future operator wanting to run a release-candidate audit using the 0029 workflow as a base would have to fill in the SOURCES.md from scratch rather than following a worked example.
recommended_action: Fill in the workflow 0029 SOURCES.md based on the 2026-05-23 run artifact (`docs/audits/2026-05-23-code-doc-audit/SOURCES.md`), showing an operator exactly what the "release_candidate" preset scope looks like. Workflows 0030-0034 are past-tense implementation records (already run, now closed); 0029 should be a reusable template.
follow_up: docs fix (backfill SOURCES.md for the audit-workflow scaffold).

## Summary

Six findings across test coverage (2), operator ergonomics (2), docs/discoverability (2), and implementation gaps (1). All are low to medium severity; no critical blockers found. RFC 0060 and RFC 0061 control surfaces are correctly wired in code and registry but lack end-to-end render tests. CLI improvements from workflow 0032 landed successfully with minor asymmetries. Audit artifacts exist but lack navigational scaffolding for future operators.
