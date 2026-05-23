# Sources for workflow 0035 — render tests for registry label surfaces

> Operator: this file is the per-run context manifest. Each job reads it
> as required context. Keep entries short and link to the canonical
> source rather than duplicating it.

## Audit batch in scope

- [`docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md`](../../audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md)
  batch R4. Two medium-severity findings:

  - **AUD-O-009** — web Vuetify `:hint` rendering not asserted on any
    test surface.
  - **AUD-O-010** — desktop matplotlib `Slider(label=...)` not asserted
    on any test surface.

  Findings live at
  [`docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md).

## Antecedent RFCs

- [`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`](../../rfcs/0060-web-generate-panel-form-labels-and-tooltips.md)
  — landed the `HullParameterMetadata` registry and wired it into the
  web Generate panel form.
- [`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`](../../rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md)
  — landed the desktop slider migration onto the same registry.

## Upstream context

The b82b544 "Land WEB_UI_REWORK_2026-05-22 second-pass redesign"
commit significantly rewired `kayakgen/ui/web/generate_spec_form.py`
(+130 lines) and added `tests/test_web_layout.py` (+225 lines). Read
the current post-b82b544 state of both files; the existing
`tests/test_web_layout.py` provides the introspection patterns the
new tests should mirror (parsing the layout source string for
testid markers, plus runtime checks of state-seeded picklist items).

## Source files NOT touched by this workflow

The workflow is tests-only. The implementer reads these files but
does not write to them:

- `kayakgen/ui/parameter_metadata.py` (registry — read-only)
- `kayakgen/ui/web/generate_spec_form.py` (form-builder — read-only;
  just rewired by upstream b82b544)
- `kayakgen/ui/desktop.py` (desktop GUI — read-only)

Also off-limits (parent-agent owned):

- `CHANGELOG.md`
- `docs/audits/2026-05-23-code-doc-audit/*/FINDINGS.md`
- `docs/rfcs/0060-*.md`, `docs/rfcs/0061-*.md`, `docs/rfcs/README.md`
- `docs/DECISION_LOG.md`

## Files added by this workflow

| Path | Purpose |
|---|---|
| `tests/test_generate_panel_label_rendering.py` | Render verification for the web Generate panel (AUD-O-009) |
| `tests/test_desktop_slider_labels.py` | Render verification for the desktop matplotlib sliders (AUD-O-010) |
| `docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/PATCH_SUMMARY.md` | Implementer artifact |
| `docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/REVIEW.md` | Reviewer artifact |

## Render-verification approach

Per the audit's R4 recommendation, the cheapest approach to web-side
render verification is to **inspect the v3.VTextField (and VSelect)
constructor arguments at form-build time**. The new test monkeypatches
`trame.widgets.vuetify3.VTextField.__init__` (and `VSelect.__init__`)
around a `create_app(initial_hull=Hull())` call to capture the
keyword arguments each widget was constructed with, then asserts the
`hint` / `label` / `items` keys carry the expected registry-sourced
values keyed by the `data-testid` attribute.

The desktop-side test is direct: the matplotlib `Slider` widget
exposes `.label.get_text()` on the constructed object, so the test
constructs `KayakGUI()` under `matplotlib.use("Agg")` and reads the
text back.

## Where the artifacts land

`docs/audits/2026-05-23-code-doc-audit/follow-ups/0035/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
