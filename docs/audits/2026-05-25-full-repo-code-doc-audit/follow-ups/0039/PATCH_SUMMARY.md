# PATCH_SUMMARY — workflow 0039 (AUD-O-003 closeout)

Workflow `0039-hydro-tab-description-rendering` closes audit batch R2
(AUD-O-003: RFC 0062 `HydrostaticsRowMetadata.description` fields
were registered but not rendered in any UI surface) from the
2026-05-25 full_repo code+doc audit.

## Files changed

- `kayakgen/services/evaluation.py` — widened the
  `analysis_view_model::hydro_rows` row-tuple from
  `(label, value, unit)` to `(label, value, unit, description)` and
  threaded the new description slot through
  `hydro_rows_from_state` (which now emits
  `{label, value, description}` dicts). Updated both downstream
  text-view consumers (`analysis_lines_from_state`,
  `hydro_lines_from_state`) to unpack the widened tuple
  (`_description` discard).
- `kayakgen/ui/web/app.py` — extended the Hydro-tab table-row
  template (`_render_hydro_tab`) to bind `:title='row.description'`
  on the `<tr>` and added per-row `data-testid` hooks
  (`hydro-row-label`, `hydro-row-<label>`). Empty descriptions
  suppress the browser tooltip naturally.
- `tests/test_hydrostatics_row_metadata.py` — widened the
  `test_hydro_rows_from_state_byte_stable` regression to assert the
  full `{label, value, description}` wire-payload shape (with
  registry-sourced descriptions) and to pin
  `description == ""` for Warning rows. Intentional schema
  widening, not a relaxation: the existing label byte-stability
  assertion is unchanged.
- `tests/test_hydro_tab_descriptions.py` — NEW render-verification
  test that (1) the Hydro-tab template carries the
  `:title='row.description'` Vue binding, (2) the runtime
  `hydro_table_rows` state carries the correct registry description
  for every `HYDROSTATICS_ROW_METADATA` row, and (3) Warning rows
  emit `description == ""`.
- `docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/PATCH_SUMMARY.md`
  — this file.

## Approach chosen

**Approach (a) — 4-tuple in `analysis_view_model`** was chosen over
the inverse-lookup-by-label approach (b). Rationale:

- The registry is the source of truth for the description; threading
  the description alongside the label/value/unit at the point where
  the registry is already consulted (in `_row()`) keeps the wiring
  symmetric with how label and unit are sourced today.
- The inverse-lookup approach (b) would have re-keyed the registry
  by label inside `hydro_rows_from_state`, introducing a second
  source of truth (the label-to-id reverse map) that could silently
  drift if a future label edit landed without a reverse-map update.
- The 4-tuple widening is constrained to the in-process tuple shape
  emitted by `analysis_view_model::hydro_rows`; no external consumer
  reads that field over the wire. The downstream effects are local:
  three call sites (`analysis_lines_from_state`,
  `hydro_lines_from_state`, `hydro_rows_from_state`) all updated in
  the same diff.

## `analysis_view_model` return-dict shape

The **top-level** return-dict keys are **unchanged**:
`{"hydro_rows", "resistance_rows", "design_warnings",
"design_validity", "resistance_warnings", "warnings",
"resistance_metadata"}`. Only the **arity of each tuple inside
`hydro_rows`** widened from 3 to 4
(`(label, value, unit, description)`). The only in-tree consumer
that indexes individual tuple positions is
`tests/test_hydrostatics_row_metadata.py::test_analysis_view_model_labels_match_registry`,
which reads `row[0]` (label) — unaffected by the widening.

## `build_spec_from_form_state` is untouched

This workflow only edits the read-model surface
(`hydro_rows_from_state`). The form-submission wire payload built
by `kayakgen.ui.web.generate_spec_form.build_spec_from_form_state`
is **not** touched in this diff. The byte-stable regression for that
function (`test_build_spec_from_form_state_wire_payload_stable` in
`tests/test_web_inline_help.py`) still passes.

## Tooltip surface excerpt

`kayakgen/ui/web/app.py:1586` — Hydro-tab v-for row now binds the
description as a Vue title attribute:

```python
"<tr v-for='row in hydro_table_rows' :key='row.label'"
" :title='row.description'"
" :data-testid=\"'hydro-row-' + row.label\">"
```

## Test counts (from `pytest --collect-only -q`)

- `tests/test_hydro_tab_descriptions.py` — **3 tests** (new):
  - `test_hydro_tab_template_binds_title_to_row_description`
  - `test_hydro_tab_state_carries_description_for_each_registered_row`
  - `test_hydro_tab_warning_rows_have_empty_description`
- `tests/test_hydrostatics_row_metadata.py` — **12 tests** (5
  parametrised + 7 standalone; one of those — the byte-stable
  regression — was widened in this diff).

Combined collect total across the new + widened files: **15 tests**.

## Verification

Ran the canonical suite per `prompts/implement.md` §Verification:

```bash
.venv/bin/pytest tests/test_hydro_tab_descriptions.py \
                 tests/test_hydrostatics_row_metadata.py \
                 tests/test_web_inline_help.py \
                 tests/test_web_layout.py \
                 tests/test_web.py -q
```

Result: **84 passed in 44.96s**. All required tests green.

Broader sanity sweep (`-k "hydro or analysis or evaluation"`):
**89 passed, 1122 deselected in 22.31s** — no collateral
regressions in hydro / analysis / evaluation suites.

## Scope discipline

No forbidden paths were touched. Confirmed read-only:

- `kayakgen/ui/hydrostatics_metadata.py` (registry) — read only.
- `kayakgen/ui/parameter_metadata.py` — read only.
- `kayakgen/ui/web/generate_spec_form.py`,
  `kayakgen/ui/web/generate_frontier_view.py`,
  `kayakgen/ui/web/controllers.py` — not touched.
- `kayakgen/ui/desktop.py`, `kayakgen/ui/desktop_slider_ranges.py`,
  `kayakgen/ui/gui_params.py` — not touched.
- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/WEB_VERIFICATION.md`, `docs/audits/README.md`, the audit
  SYNTHESIS / REMEDIATION_PLAN / FINDINGS files, and `docs/rfcs/`
  — not touched.
