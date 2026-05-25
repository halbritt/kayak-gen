# Implement prompt — workflow 0038

You are closing audit batch R3 (AUD-O-005) from the 2026-05-25
release_candidate audit by landing RFC 0062 and the third
application of the D043 "presentation-layer registry per surface
family" pattern: a `HydrostaticsRowMetadata` registry for the
hydro rows surfaced by `analysis_view_model`.

Read first:

- `docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md` (batch R3)
- `docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`
  AUD-O-005.
- `docs/workflows/0038-hydrostatics-row-metadata-registry/SOURCES.md`
  for the per-run context manifest.
- `docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md` —
  the shape your RFC mirrors.
- `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md` —
  the second application of the same pattern.
- `kayakgen/ui/parameter_metadata.py` — the sibling registry you
  mirror (read-only here).
- `kayakgen/services/evaluation.py:97-148` (`analysis_view_model`)
  and `:420-449` (`hydro_lines_from_state` /
  `hydro_rows_from_state`) — the source of the hardcoded labels you
  replace.
- `tests/test_hull_parameter_metadata.py` — the regression-net
  shape you mirror.

## Deliverables

### 1. `kayakgen/ui/hydrostatics_metadata.py` (new)

A `HydrostaticsRowMetadata` value object + `HYDROSTATICS_ROW_METADATA`
registry. Mirror the structure of `kayakgen/ui/parameter_metadata.py`
exactly:

```python
"""Presentation-layer label / unit / description registry for
hydrostatics rows.

RFC 0062: the Hydro tab and `hydro_rows_from_state` need a single
source of truth for human-readable labels, units, and descriptions
of the rows surfaced by `analysis_view_model::hydro_rows`. The
registry is a sibling to `kayakgen.ui.parameter_metadata`
(RFC 0060) and the desktop slider registry consumed by RFC 0061.

Closes audit finding `AUD-O-005` from
`docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HydrostaticsRowMetadata(BaseModel):
    """Presentation-layer label / unit / description for one
    hydrostatics row surfaced by the Hydro tab.

    Fields are presentation-only; the underlying numeric values
    come from the evaluator.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str | None = None
    description: str = Field(min_length=1)


HYDROSTATICS_ROW_METADATA: dict[str, HydrostaticsRowMetadata] = {
    "displacement": HydrostaticsRowMetadata(
        parameter="displacement",
        label="Displacement",
        unit="kg",
        description=(
            "Displaced mass at the design waterline. Equals the "
            "kayak's weight including paddler and load when the "
            "hull sits at the modelled waterline."
        ),
    ),
    # ... fill in the remaining six rows.
}
```

Required keys (these are the ids `analysis_view_model` will use):

| id | label | unit |
|---|---|---|
| `displacement` | Displacement | kg |
| `wetted_surface` | Wetted surface | m^2 |
| `waterplane_area` | Waterplane area | m^2 |
| `gm0` | GM0 | m |
| `cp_actual` | Cp actual | (None) |
| `cm_actual` | Cm actual | (None) |
| `l_over_bwl` | L/B wl | (None) |

Descriptions: one or two sentences per row, in the same voice as
the RFC 0060 hull-parameter descriptions. See SOURCES.md for
suggested wordings; refine as you see fit.

### 2. `kayakgen/services/evaluation.py::analysis_view_model` edit

Replace the inline tuple construction in `hydro_rows` (around
lines 113-121) with registry lookups. The pattern:

```python
from kayakgen.ui.hydrostatics_metadata import (
    HYDROSTATICS_ROW_METADATA as _HYDRO_META,
)

# ... inside analysis_view_model ...

def _row(key: str, value_str: str) -> tuple[str, str, str]:
    meta = _HYDRO_META[key]
    return (meta.label, value_str, meta.unit or "")

hydro_rows = [
    _row("displacement", f"{hydro.displaced_mass_kg:.1f}"),
    _row("wetted_surface", f"{hydro.wetted_surface_m2:.3f}"),
    _row("waterplane_area", f"{hydro.waterplane_area_m2:.3f}"),
    _row("gm0", f"{hydro.GM0_m:.3f}"),
    _row("cp_actual", f"{hydro.Cp_actual:.3f}"),
    _row("cm_actual", f"{hydro.Cm_actual:.3f}"),
    _row("l_over_bwl", f"{advisory.l_over_bwl:.2f}"),
]
```

Constraints:

- The return-value dict shape of `analysis_view_model` MUST be
  unchanged.
- The numeric value formatting MUST be unchanged
  (`f"{...:.1f}"` / `f"{...:.3f}"` / `f"{...:.2f}"`).
- The tuple shape `(label, value, unit)` MUST be unchanged (so
  downstream `hydro_lines_from_state` and `hydro_rows_from_state`
  do not need to change).
- The `unit` slot uses `meta.unit or ""` so the existing "no unit"
  cases (Cp actual, Cm actual, L/B wl) still produce `""` for the
  tuple.

### 3. `tests/test_hydrostatics_row_metadata.py` (new)

Mirror `tests/test_hull_parameter_metadata.py`:

```python
"""Regression net for the HydrostaticsRowMetadata registry."""

from __future__ import annotations

import pytest

from kayakgen.ui.hydrostatics_metadata import (
    HYDROSTATICS_ROW_METADATA,
    HydrostaticsRowMetadata,
)

EXPECTED_KEYS: tuple[str, ...] = (
    "displacement",
    "wetted_surface",
    "waterplane_area",
    "gm0",
    "cp_actual",
    "cm_actual",
    "l_over_bwl",
)


def test_registry_covers_expected_keys() -> None:
    assert set(HYDROSTATICS_ROW_METADATA.keys()) == set(EXPECTED_KEYS)


@pytest.mark.parametrize("key", EXPECTED_KEYS)
def test_registry_entries_are_well_formed(key: str) -> None:
    meta = HYDROSTATICS_ROW_METADATA[key]
    assert isinstance(meta, HydrostaticsRowMetadata)
    assert meta.parameter == key
    assert meta.label
    assert meta.description
    # unit is allowed to be None for dimensionless quantities


def test_analysis_view_model_label_matches_registry() -> None:
    from kayakgen.geometry import Hull
    from kayakgen.services.evaluation import analysis_view_model
    from kayakgen.ui.web.state import hull_to_state_payload

    state = hull_to_state_payload(Hull())
    rows = analysis_view_model(state)["hydro_rows"]
    expected_labels = [HYDROSTATICS_ROW_METADATA[k].label for k in EXPECTED_KEYS]
    actual_labels = [row[0] for row in rows]
    assert actual_labels == expected_labels


def test_hydro_rows_from_state_byte_stable() -> None:
    """Regression net: hydro_rows_from_state output must remain
    byte-stable across the registry refactor. The expected list
    is the b82b544 baseline; if the registry-sourced labels
    change in the future, update this fixture in lockstep with
    the registry edit (intentional change) or the test fails."""
    from kayakgen.geometry import Hull
    from kayakgen.services.evaluation import hydro_rows_from_state
    from kayakgen.ui.web.state import hull_to_state_payload

    state = hull_to_state_payload(Hull())
    rows = hydro_rows_from_state(state)
    labels = [row["label"] for row in rows if row["label"] != "Warning"]
    assert labels == [
        "Displacement",
        "Wetted surface",
        "Waterplane area",
        "GM0",
        "Cp actual",
        "Cm actual",
        "L/B wl",
    ]
```

The byte-stable test pins the post-b82b544 / pre-0038 baseline.
Any future intentional label change requires updating this list
in the same commit as the registry edit.

### 4. `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` (new)

Follow the RFC 0060 / RFC 0061 structure. Sections:

- **Status**: `landed`
- **Date**: `2026-05-25`
- **Context** (links): RFC 0060, RFC 0061, D043, audit
  AUD-O-005, the affected source files, and
  `kayakgen/ui/parameter_metadata.py`.
- **Problem**: cite the audit finding. The hardcoded labels in
  `analysis_view_model` reduce changeability and prevent a
  documentation surface from listing what each hydrostatics row
  means. Same pattern as the AUD-O-003 finding that produced RFC
  0060 for hull parameters.
- **Goals**: third application of the D043 pattern, byte-stable
  wire payload, per-row description, regression-net test
  mirroring `test_hull_parameter_metadata.py`.
- **Non-Goals**: changing computed values, adding new rows,
  consolidating mesh-tab labels (those live in
  `mesh_diagnostics_rows_from_state` and have their own
  conventions — out of scope), internationalization.
- **Proposal**: the value object (`label`, `unit`, `description`),
  the `HYDROSTATICS_ROW_METADATA` registry, the
  `analysis_view_model` wiring, the regression test.
- **Acceptance**: the registry-coverage test passes; the byte-
  stable regression assertion holds; the new RFC row appears in
  `rfcs/README.md`; the audit finding AUD-O-005 is marked closed
  in the next audit cycle.
- **Open Questions**: none; this is a narrow follow-up. Possible
  future-pass siblings (mesh-diagnostic metadata, evaluator-status
  metadata, resistance-row metadata) are listed but not in scope.

### 5. `docs/rfcs/README.md` row

Add a row after the 0061 row:

```
| [0062](0062-hydrostatics-row-metadata-registry.md) | landed | Hydrostatics row metadata registry — third application of the D043 "presentation-layer registry per surface family" pattern after RFC 0060 and RFC 0061. `HydrostaticsRowMetadata` + `HYDROSTATICS_ROW_METADATA` under `kayakgen/ui/hydrostatics_metadata.py`; `analysis_view_model::hydro_rows` consumes the registry; presentation-only (wire payload byte-stable). Closes audit finding AUD-O-005 via workflow `docs/workflows/0038-hydrostatics-row-metadata-registry/`. |
```

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_hydrostatics_row_metadata.py \
  tests/test_hull_parameter_metadata.py \
  tests/test_web_layout.py \
  tests/test_vocabulary_coverage.py \
  -q
```

All must pass.

## Scope discipline

You MUST NOT touch:

- `CHANGELOG.md`
- `docs/USER_GUIDE.md`
- `docs/DECISION_LOG.md`
- `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`
- `docs/audits/README.md`, `docs/audits/2026-05-25-code-doc-audit/`
  SYNTHESIS / REMEDIATION_PLAN / FINDINGS files
- `kayakgen/ui/parameter_metadata.py` (sibling registry; read-only)
- `kayakgen/ui/web/` (workflow 0037 territory)
- `kayakgen/ui/desktop.py`, `kayakgen/ui/desktop_slider_ranges.py`,
  `kayakgen/ui/gui_params.py`
- `kayakgen/services/evaluation.py::mesh_diagnostics_rows_from_state`
  (workflow 0037 owns this function body)
- `kayakgen/services/evaluation.py::hydro_rows_from_state` (passes
  through; do not touch)

These are encoded in the workflow's `forbidden_paths`. The
`mesh_diagnostics_rows_from_state` / `hydro_rows_from_state`
carve-outs are enforced by code review.

## Artifact

Write
`docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/PATCH_SUMMARY.md`
with:

- Files changed (paths only).
- Test counts per file.
- Confirmation that `analysis_view_model` returns the same dict
  shape (cite the test).
- Confirmation that `hydro_rows_from_state` output is byte-stable
  (cite the regression assertion).
- Confirmation that `mesh_diagnostics_rows_from_state` was not
  touched.
- Confirmation that the verification suite passes.
