# Role: implementer

You close audit batch R2 (AUD-O-003) from the 2026-05-25 full_repo
release_candidate audit by surfacing the RFC 0062
`HYDROSTATICS_ROW_METADATA.description` fields as a tooltip in the
web Hydro tab.

You edit:

- `kayakgen/services/evaluation.py::hydro_rows_from_state` — widen
  the returned dicts from `{"label": ..., "value": ...}` to
  `{"label": ..., "value": ..., "description": ...}`. The
  `description` value comes from the registry; Warning rows (which
  have no registry entry) carry `""` as their description. Do this
  by either (a) threading the row id alongside in
  `analysis_view_model::hydro_rows`, or (b) inverse-lookup against
  the registry using the `label` field. Approach (a) is cleaner
  but touches `analysis_view_model`'s tuple shape (3-tuple →
  4-tuple), which downstream consumers may rely on. Inspect
  `hydro_lines_from_state` and any test that consumes
  `analysis_view_model["hydro_rows"]` directly. Default to (a) and
  update the affected consumers in the same diff IF the widening
  is clean; fall back to (b) (inverse lookup keyed by label) IF
  any downstream consumer would need wider changes.

- `kayakgen/ui/web/app.py` — find the Hydro-tab table row template
  (search for `hydro_table_rows` v-for; around line 1492). Wrap
  the row's `<tr>` (or the label `<th>`) in a Vuetify `v-tooltip`
  slot. Use the `activator` / `default` slot pattern Vuetify v3
  expects. Bind the tooltip text to `{{ row.description }}`.
  Suppress the tooltip when description is empty (`v-if="row.description"`
  or equivalent) so Warning rows do not render an empty tooltip.

- `tests/test_hydrostatics_row_metadata.py` — update the existing
  byte-stable regression in `test_hydro_rows_from_state_byte_stable`
  to include the new `description` key. The intent is an
  intentional schema widening, not a relaxation; the test should
  now assert the full `{label, value, description}` shape (with
  the registry-sourced descriptions) and continue to refuse any
  drift on `label` or `value`. The label list assertion stays
  unchanged.

- `tests/test_hydro_tab_descriptions.py` (NEW) — render-
  verification test asserting:
  - Each of the seven `HYDROSTATICS_ROW_METADATA` entries' `description`
    field appears in the rendered HTML for the corresponding row
    (as a `title=` attribute, a Vuetify tooltip slot, or whatever
    affordance the implementation chose). Iterate the registry to
    drive the assertion.
  - Warning rows (when present) do not render a tooltip activator;
    or, if they do, the tooltip is suppressed.

You do not touch:

- `kayakgen/ui/hydrostatics_metadata.py` — read-only registry.
- `kayakgen/ui/parameter_metadata.py` — read-only sibling.
- `kayakgen/ui/web/generate_spec_form.py`,
  `kayakgen/ui/web/generate_frontier_view.py`,
  `kayakgen/ui/web/controllers.py` — out of scope.
- `kayakgen/ui/desktop.py` and the rest of the desktop UI.
- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  any audit SYNTHESIS / REMEDIATION_PLAN / FINDINGS files,
  `docs/audits/README.md`, `docs/rfcs/`, `docs/SPEC.md` /
  `docs/PRD.md` / `docs/ROADMAP.md` / `docs/ARCHITECTURE_MAP.md` /
  `docs/UBIQUITOUS_LANGUAGE.md` / `docs/WEB_VERIFICATION.md`.

## Forbidden behavior changes

- `build_spec_from_form_state(state)` MUST remain byte-stable.
  This is the read-model side; the submission wire is untouched.
  No regression assertion needed for `build_spec_from_form_state`
  in this workflow (workflow 0037 already pins it).
- The numeric `value` formatting in `hydro_rows_from_state` MUST
  remain unchanged.
- The label strings emitted by `hydro_rows_from_state` MUST remain
  the seven registry-sourced labels (`Displacement`, `Wetted
  surface`, `Waterplane area`, `GM0`, `Cp actual`, `Cm actual`,
  `L/B wl`), plus `Warning` rows when applicable.
- No new claim_state literals; no readiness state shifts; no new
  evaluator contracts. This is a pure presentation widening.

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_hydro_tab_descriptions.py \
  tests/test_hydrostatics_row_metadata.py \
  tests/test_web_inline_help.py \
  tests/test_web_layout.py \
  tests/test_web.py \
  -q
```

All must pass.

## Artifact

Write
`docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/PATCH_SUMMARY.md`
with:

- Files changed (paths only).
- Test counts per file (from `pytest --collect-only -q`).
- Approach chosen for threading description (4-tuple in
  `analysis_view_model` vs inverse lookup in
  `hydro_rows_from_state`).
- Confirmation that `analysis_view_model`'s return dict shape is
  unchanged at top level (`hydro_rows` is still a list of tuples
  with the same arity unless approach (a) was chosen — in that
  case document the widening clearly).
- Confirmation that `build_spec_from_form_state` was not touched.
- Confirmation that the verification suite passes.
