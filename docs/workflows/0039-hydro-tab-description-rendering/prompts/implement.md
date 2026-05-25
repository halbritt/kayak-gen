# Implement prompt — workflow 0039

You are closing audit batch R2 (AUD-O-003) from the 2026-05-25
full_repo audit by rendering the
`HYDROSTATICS_ROW_METADATA.description` fields as hover tooltips
in the web Hydro tab.

Read first:

- `docs/audits/2026-05-25-full-repo-code-doc-audit/REMEDIATION_PLAN.md`
  (batch R2).
- `docs/audits/2026-05-25-full-repo-code-doc-audit/operator-adoption/FINDINGS.md`
  AUD-O-003.
- `docs/workflows/0039-hydro-tab-description-rendering/SOURCES.md`
  for the per-run context manifest.
- `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` — the
  RFC that defines the registry contract.
- `kayakgen/ui/hydrostatics_metadata.py` — the registry the
  implementer reads from (read-only here).
- `kayakgen/services/evaluation.py:97-148` (`analysis_view_model`)
  and `:420-449` (`hydro_lines_from_state` /
  `hydro_rows_from_state`).
- `kayakgen/ui/web/app.py` — find the `hydro_table_rows` v-for
  template (around line 1492).
- `tests/test_hydrostatics_row_metadata.py` — the existing
  regression net you extend.
- `tests/test_web_layout.py` and `tests/test_web_inline_help.py`
  — the layout-introspection pattern.

## Deliverables

### 1. `kayakgen/services/evaluation.py` edit — `hydro_rows_from_state`

Widen the returned dicts to include `description`. Two viable
approaches:

**Approach (a) — 4-tuple in `analysis_view_model`** (cleaner):

```python
from kayakgen.ui.hydrostatics_metadata import (
    HYDROSTATICS_ROW_METADATA as _HYDRO_META,
)

# inside analysis_view_model:
def _row(key: str, value_str: str) -> tuple[str, str, str, str]:
    meta = _HYDRO_META[key]
    return (meta.label, value_str, meta.unit or "", meta.description)

hydro_rows = [
    _row("displacement", f"{hydro.displaced_mass_kg:.1f}"),
    # ... etc.
]
```

Then `hydro_rows_from_state` unpacks the 4-tuple:

```python
for label, value, unit, description in model["hydro_rows"]:
    display_value = f"{value} {unit}".strip() if unit else str(value)
    rows.append({
        "label": label,
        "value": display_value,
        "description": description,
    })
for warning in model.get("design_warnings", []):
    rows.append({"label": "Warning", "value": str(warning), "description": ""})
```

You MUST update `hydro_lines_from_state` (line ~420) in the same
diff to handle the widened tuple — its current
`for label, value, unit in model["hydro_rows"]` line will fail
unpacking. Either change to
`for label, value, unit, _description in model["hydro_rows"]` or
discard the description there (`for label, value, unit, _ in ...`).

**Approach (b) — inverse lookup in `hydro_rows_from_state`** (less
invasive):

Keep `analysis_view_model::hydro_rows` as 3-tuples. Inside
`hydro_rows_from_state`, build a label-to-id reverse map from
the registry once, then look up the description by the label
field:

```python
_LABEL_TO_ID = {meta.label: meta.parameter for meta in HYDROSTATICS_ROW_METADATA.values()}

# ... inside hydro_rows_from_state:
for label, value, unit in model["hydro_rows"]:
    display_value = f"{value} {unit}".strip() if unit else str(value)
    row_id = _LABEL_TO_ID.get(label)
    description = HYDROSTATICS_ROW_METADATA[row_id].description if row_id else ""
    rows.append({
        "label": label,
        "value": display_value,
        "description": description,
    })
```

Default to approach (a) for clarity. Document your choice in
PATCH_SUMMARY.

### 2. `kayakgen/ui/web/app.py` edit — Hydro tab template

Find the existing template around line 1490-1500. It looks like:

```html
<table ...>
  <tbody>
    <tr v-for='row in hydro_table_rows' :key='row.label'>
      <th>{{ row.label }}</th>
      <td>{{ row.value }}</td>
    </tr>
  </tbody>
</table>
```

Wrap the row (or the `<th>`) in a Vuetify v-tooltip activator
pattern. The simplest approach in Trame's vuetify3 wrapper is
to use the inline `title=` attribute on `<tr>` (which most
browsers render as a hover tooltip) AND/OR a `v-tooltip`
component:

```html
<tr v-for='row in hydro_table_rows' :key='row.label' :title='row.description'>
  <th data-testid="hydro-table-label">{{ row.label }}</th>
  <td>{{ row.value }}</td>
</tr>
```

The `:title='row.description'` binding will produce no tooltip
when description is `""` (browser convention). If you want a
Vuetify `v-tooltip` styled component instead, use the activator
slot pattern; either is acceptable as long as the rendered HTML
contains the description text for each registered row.

Add a `data-testid="hydro-row-description-{label}"` or similar
hook on the description-carrying element so the new test can
pin it directly.

### 3. `tests/test_hydrostatics_row_metadata.py` update

Find `test_hydro_rows_from_state_byte_stable` and extend it to
assert the new `description` key. Example shape:

```python
def test_hydro_rows_from_state_byte_stable() -> None:
    from kayakgen.geometry import Hull
    from kayakgen.services.evaluation import hydro_rows_from_state
    from kayakgen.ui.hydrostatics_metadata import HYDROSTATICS_ROW_METADATA
    from kayakgen.ui.web.state import hull_to_state_payload

    state = hull_to_state_payload(Hull())
    rows = hydro_rows_from_state(state)
    non_warning = [r for r in rows if r["label"] != "Warning"]

    # Labels unchanged
    labels = [r["label"] for r in non_warning]
    assert labels == [
        "Displacement", "Wetted surface", "Waterplane area",
        "GM0", "Cp actual", "Cm actual", "L/B wl",
    ]

    # Descriptions now present and registry-sourced
    expected_descriptions = [
        HYDROSTATICS_ROW_METADATA[k].description
        for k in ("displacement", "wetted_surface", "waterplane_area",
                  "gm0", "cp_actual", "cm_actual", "l_over_bwl")
    ]
    actual_descriptions = [r["description"] for r in non_warning]
    assert actual_descriptions == expected_descriptions

    # Warning rows (if any) carry empty description
    for row in rows:
        if row["label"] == "Warning":
            assert row["description"] == ""
```

### 4. `tests/test_hydro_tab_descriptions.py` (new)

Render-verification test that the Hydro-tab template surfaces the
descriptions. Pattern (using existing `tests/test_web_layout.py`
introspection):

```python
"""Render-verification: Hydro tab tooltips surface RFC 0062 descriptions."""

from __future__ import annotations

import pytest

trame = pytest.importorskip("trame", reason="kayakgen[web] not installed")
pytest.importorskip("vtk", reason="vtk not installed")


def test_hydro_tab_renders_description_per_registered_row() -> None:
    from kayakgen.geometry import Hull
    from kayakgen.ui.hydrostatics_metadata import HYDROSTATICS_ROW_METADATA
    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())
    rendered = web._html if hasattr(web, "_html") else str(web.layout.html)

    for meta in HYDROSTATICS_ROW_METADATA.values():
        assert meta.description in rendered, (
            f"Description for {meta.parameter!r} not found in rendered Hydro tab. "
            f"Expected substring: {meta.description!r}"
        )


def test_hydro_tab_warning_rows_have_no_tooltip_text() -> None:
    """Warning rows should not carry a misleading empty tooltip activator."""
    # Implementation depends on the chosen tooltip approach;
    # this is a finger-test that the suppression worked.
    # If using :title='row.description' with empty string, the
    # rendered HTML may still include title="" which is acceptable
    # (browsers do not show empty tooltips).
    pass
```

Adjust the implementation based on what `create_app` returns and
how the layout HTML is exposed in the existing
`tests/test_web_layout.py` (read it to follow the established
pattern exactly).

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

## Scope discipline

You MUST NOT touch any of: `CHANGELOG.md`, `docs/USER_GUIDE.md`,
`docs/DECISION_LOG.md`, audit FINDINGS/SYNTHESIS/REMEDIATION_PLAN
files, `docs/audits/README.md`, `docs/rfcs/`, the SPEC/PRD/
ROADMAP/ARCHITECTURE_MAP/UBIQUITOUS_LANGUAGE/WEB_VERIFICATION docs,
`kayakgen/ui/hydrostatics_metadata.py` (read-only registry),
`kayakgen/ui/parameter_metadata.py`,
`kayakgen/ui/web/generate_spec_form.py`,
`kayakgen/ui/web/generate_frontier_view.py`,
`kayakgen/ui/web/controllers.py`, or any of the desktop UI files.

## Artifact

Write
`docs/audits/2026-05-25-full-repo-code-doc-audit/follow-ups/0039/PATCH_SUMMARY.md`
with:

- Files changed (paths only).
- Approach chosen (a or b) and why.
- Test counts per file (from `pytest --collect-only -q`).
- One-line excerpt from each new tooltip surface (file:line).
- Confirmation that `analysis_view_model`'s top-level return
  dict shape is unchanged; if approach (a) was taken, document
  the `hydro_rows` tuple widening clearly.
- Confirmation that `build_spec_from_form_state` was not touched.
- Confirmation that the verification suite passes.
