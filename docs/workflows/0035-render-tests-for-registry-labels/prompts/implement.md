# Implement prompt — workflow 0035

You are closing audit batch R4 from the 2026-05-23 release_candidate
audit: two medium-severity findings that the registry-label wiring on
the web Generate panel (AUD-O-009) and the desktop matplotlib sliders
(AUD-O-010) is not exercised by any render-verification test.

Read first:

- `docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md` (batch R4)
- `docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md`
  for the two finding IDs.
- `docs/workflows/0035-render-tests-for-registry-labels/SOURCES.md`
  for the per-run context manifest.
- `kayakgen/ui/web/generate_spec_form.py` end-to-end (post-b82b544
  state).
- `kayakgen/ui/desktop.py` end-to-end.
- `tests/test_web_layout.py` (just landed by b82b544) — pattern for
  web-layout introspection.
- `tests/test_desktop_layout.py` — pattern for the desktop test
  fixture.

The workflow is tests-only. The source modules
(`kayakgen/ui/parameter_metadata.py`,
`kayakgen/ui/web/generate_spec_form.py`, `kayakgen/ui/desktop.py`) are
read-only and the workflow's `forbidden_paths` encodes that contract.

## Deliverables

### 1. `tests/test_generate_panel_label_rendering.py` (new)

Closes AUD-O-009. The test captures the actual rendered widget
constructor arguments by monkeypatching
`trame.widgets.vuetify3.VTextField.__init__` (and `VSelect.__init__`
where applicable) around a `create_app(initial_hull=Hull())` call.
Use `pytest.importorskip("trame", reason="kayakgen[web] not installed")`
and `pytest.importorskip("vtk", ...)` for the import-safety guard
that the existing `tests/test_web_layout.py` uses.

The test asserts:

(a) For every key in `BASE_HULL_KEYS` (imported from
    `kayakgen.ui.web.generate_spec_form`) the captured `VTextField`
    constructor call for that key (identified via the
    `data-testid="generative-base-hull-{key}"` attribute) has
    `hint == description(key)` (from
    `kayakgen.ui.parameter_metadata.description`) and
    `label == label_with_unit(key)` (from the same module).

(b) The objectives picklist items list — sourced at runtime from
    `web.state.generative_objective_picklist_items` (seeded by
    `initialize_form_state`) — has, for each item,
    `title == f"{OBJECTIVE_METADATA[item['value']].label} ({OBJECTIVE_METADATA[item['value']].unit})"`
    where `OBJECTIVE_METADATA` is imported from
    `kayakgen.search.objectives`.

(c) The variable-selector picklist items list — sourced at runtime
    from `web.state.generative_variable_picklist_items` (seeded by
    `initialize_form_state`) — has, for each item,
    `title == label_with_unit(item["value"])`.

The (a) check is the load-bearing one for AUD-O-009 — it asserts the
actual rendered widget arguments. The (b) and (c) checks pin the
state-seeded picklist items, which are the upstream truth value the
Vue template renders from. Together they cover the full
registry-to-render path.

If any post-b82b544 form-builder change makes one of these checks
impossible to verify directly (e.g. the form is constructed only at
request time rather than at `create_app` time, or the `:hint` prop has
been replaced with a different affordance like a `VTooltip` wrapper),
document the change in the test file's module docstring and
`pytest.skip(...)` the impossible case with a clear recommended-action
comment. Do NOT fake-pass a test you cannot actually verify.

### 2. `tests/test_desktop_slider_labels.py` (new)

Closes AUD-O-010. Kept as a separate file from `test_desktop_layout.py`
for traceability to AUD-O-010 (the audit references a new file in its
R4 recommendation). Use `pytest.importorskip("matplotlib", ...)` and
`pytest.importorskip("PyQt6", ...)` for the import-safety guard.

The test constructs a `KayakGUI()` headlessly (mirror
`tests/test_desktop_layout.py`: `monkeypatch.setattr(plt, "show", lambda *a, **k: None)`)
and asserts:

(a) For every row in `KayakGUI.SLIDERS`, the constructed matplotlib
    `Slider` widget's `.label.get_text()` returns the same string as
    `label_with_unit(SLIDERS[i][0])`. Iterate the SLIDERS tuple
    directly so a future change to `_NON_HULL_GUI_KEYS` or the row
    order is followed automatically.

(b) Three named spot checks (these are stable, easy-to-read fixtures
    the audit explicitly calls out): for `Cp`, `length_m`, and
    `target_speed_kt`, assert
    `gui.sliders[key].label.get_text() == label_with_unit(key)` plus a
    bare-string assertion on the expected human label (e.g.
    `"Prismatic coefficient (Cp)"`). The bare-string check is the
    finger-test that catches a registry-side label rename without
    requiring the test to be rerun — if the registry label changes
    intentionally, this assertion must be updated in lockstep with
    `kayakgen/ui/parameter_metadata.py`.

Always close the figure (`plt.close(gui.fig)`) at the end of the test
to keep the matplotlib state clean for the rest of the suite.

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_generate_panel_label_rendering.py \
  tests/test_desktop_slider_labels.py \
  tests/test_web_layout.py \
  tests/test_desktop_layout.py \
  tests/test_hull_parameter_metadata.py \
  tests/test_generate_spec_form.py \
  -q
```

All must pass.

## Scope discipline

You MUST NOT touch:

- `CHANGELOG.md`
- `docs/audits/2026-05-23-code-doc-audit/*/FINDINGS.md`
- `docs/rfcs/0060-*.md`, `docs/rfcs/0061-*.md`, `docs/rfcs/README.md`
- `docs/DECISION_LOG.md`
- `kayakgen/ui/parameter_metadata.py`
- `kayakgen/ui/web/generate_spec_form.py`
- `kayakgen/ui/desktop.py`

These are the parent agent's (or upstream's) job. The workflow's
`forbidden_paths` encodes this contract; do not work around it.

## Artifact

Write
`docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/PATCH_SUMMARY.md`
with:

- Files changed (paths only).
- Test counts per file (each new file's collected test count from
  `pytest --collect-only -q`).
- The exact assertion shape used for the `:hint` render check (a one-
  or two-line code excerpt is fine — the parent agent needs to be
  able to reason about whether the assertion really inspects the
  rendered widget).
- Any `pytest.skip(...)` cases with their reason and recommended
  action.
- Confirmation that the six-test verification suite passes.
