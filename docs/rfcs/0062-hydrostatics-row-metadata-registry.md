# RFC 0062: Hydrostatics Row Metadata Registry

Status: landed
Date: 2026-05-25
Context:
[`RFC 0060`](0060-web-generate-panel-form-labels-and-tooltips.md)
(introduced `HullParameterMetadata` + the `HULL_PARAMETER_METADATA`
registry under `kayakgen/ui/parameter_metadata.py`),
[`RFC 0061`](0061-desktop-sliders-on-hull-parameter-metadata.md)
(second application of the same pattern: desktop sliders on the RFC 0060
registry + sibling `VIEW_PARAMETER_METADATA`),
[`D043`](../DECISION_LOG.md) (the accepted "presentation-layer registry
per surface family" pattern),
[`AUD-O-005`](../audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md)
(2026-05-25 release_candidate audit, batch R3),
[`kayakgen/services/evaluation.py`](../../kayakgen/services/evaluation.py)
`analysis_view_model::hydro_rows` and `hydro_rows_from_state`,
[`kayakgen/ui/parameter_metadata.py`](../../kayakgen/ui/parameter_metadata.py)
(sibling registry shape),
[`tests/test_hull_parameter_metadata.py`](../../tests/test_hull_parameter_metadata.py)
(regression-net shape mirrored).

## Problem

The 2026-05-25 release_candidate audit's operator-adoption lane logged
`AUD-O-005` (low) against `analysis_view_model::hydro_rows`. The
function builds the seven-row hydrostatics table the web Hydro tab and
the text-mode `hydro_lines_from_state` view consume:

```python
hydro_rows = [
    ("Displacement", f"{hydro.displaced_mass_kg:.1f}", "kg"),
    ("Wetted surface", f"{hydro.wetted_surface_m2:.3f}", "m^2"),
    ("Waterplane area", f"{hydro.waterplane_area_m2:.3f}", "m^2"),
    ("GM0", f"{hydro.GM0_m:.3f}", "m"),
    ("Cp actual", f"{hydro.Cp_actual:.3f}", ""),
    ("Cm actual", f"{hydro.Cm_actual:.3f}", ""),
    ("L/B wl", f"{advisory.l_over_bwl:.2f}", ""),
]
```

The labels and units are inline literals. That has three costs:

1. **No documentation surface.** Operators reading the table see
   `"Cp actual"` with no hover-for-description or per-row explanation
   of what the number means or how to interpret it against the rail
   inputs.
2. **D043 drift.** D043 records "presentation-layer registry per
   surface family" as the accepted pattern. RFC 0060 applied it to the
   web Generate panel; RFC 0061 applied it to the desktop sliders.
   `analysis_view_model::hydro_rows` is the same kind of presentation
   surface and should follow the same pattern.
3. **Changeability.** Any future intentional label tweak (e.g.
   `"GM0"` → `"GM₀"` or adding the unit in the label string) requires
   editing the function body rather than a single registry row, and
   the regression net does not pin the user-facing copy.

The wire payload (`[{"label", "value"}]` dicts emitted by
`hydro_rows_from_state`) is byte-stable today and must remain so —
this is a label-source refactor, not a copy change.

## Goals

- Third application of the D043 "presentation-layer registry per
  surface family" pattern, after RFC 0060 (web Generate panel) and
  RFC 0061 (desktop sliders).
- Land `HydrostaticsRowMetadata` (frozen Pydantic value object) +
  `HYDROSTATICS_ROW_METADATA` registry under
  `kayakgen/ui/hydrostatics_metadata.py`, mirroring the
  `kayakgen/ui/parameter_metadata.py` shape.
- Wire `analysis_view_model::hydro_rows` to consume the registry for
  the label + unit slots while preserving the existing `value`
  formatting (`f"{...:.1f}"` / `f"{...:.3f}"` / `f"{...:.2f}"`) and
  the `(label, value, unit)` tuple shape.
- Per-row `description` text in the operator-facing voice already
  established by RFC 0060, ready for a future Hydro-tab tooltip
  affordance.
- Land a regression-net test under
  `tests/test_hydrostatics_row_metadata.py` mirroring the
  `tests/test_hull_parameter_metadata.py` shape: registry-coverage
  assertions + a byte-stable assertion on
  `hydro_rows_from_state(state)` output for a fixed `Hull()` input.
- Keep `hydro_rows_from_state` and `hydro_lines_from_state` unchanged
  in body — they continue to consume
  `analysis_view_model(state)["hydro_rows"]`.

## Non-Goals

- Changing any computed hydrostatics value, threshold, or formatting
  precision. The numeric value formatting in the tuple is preserved
  byte-for-byte.
- Adding or removing rows. The seven rows are exactly the seven
  emitted today.
- Consolidating mesh-tab labels. The
  `mesh_diagnostics_rows_from_state` function has its own conventions
  (it embeds threshold guidance in row labels per AUD-O-006) and is
  out of scope for this RFC. Workflow 0037 owns that surface.
- Wiring tooltips into the web Hydro tab UI. The registry stores
  `description` as a forward-looking field; the actual `<VTooltip>`
  attachment can land in a successor RFC if a Hydro-tab redesign
  takes it on.
- Internationalization or operator-configurable labels.
- Adding `HydrostaticsRowMetadata` to `docs/UBIQUITOUS_LANGUAGE.md`.
  The glossary already documents `HullParameterMetadata` (RFC 0060);
  a separate glossary entry for the hydrostatics sibling can land in
  the next docs cycle and is not gated by this RFC.

## Proposal

### 1. Value object

Add `kayakgen/ui/hydrostatics_metadata.py`:

```python
from pydantic import BaseModel, ConfigDict, Field


class HydrostaticsRowMetadata(BaseModel):
    """Presentation-layer label / unit / description for one
    hydrostatics row surfaced by the Hydro tab.

    Fields are presentation-only; the underlying numeric values
    come from the evaluator. ``unit`` is ``None`` for dimensionless
    rows (Cp actual, Cm actual, L/B wl).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str | None = None
    description: str = Field(min_length=1)
```

This mirrors `HullParameterMetadata` exactly so the two value
objects share a shape. (D043 open question 2 considered a shared
class; the RFC 0061 decision was to keep them separate per surface
family. RFC 0062 follows that precedent.)

### 2. Registry

Same module:

```python
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
    "wetted_surface": ...,
    "waterplane_area": ...,
    "gm0": ...,
    "cp_actual": ...,
    "cm_actual": ...,
    "l_over_bwl": ...,
}
```

Seven rows, keyed by an internal id (the registry key is not on the
wire and not user-visible). `unit` is `None` for `cp_actual`,
`cm_actual`, and `l_over_bwl`; the `analysis_view_model` wiring
maps `None` to the empty string `""` to keep the tuple shape
identical.

The seven descriptions match the operator-facing voice already
established by `HULL_PARAMETER_METADATA`: one or two sentences per
row, explaining what the number means and (where relevant) how it
relates to a rail input or a downstream consumer.

### 3. `analysis_view_model` wiring

In `kayakgen/services/evaluation.py`, replace the seven-tuple literal
with registry lookups:

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

The tuple shape `(label, value, unit)` is unchanged. The numeric
formatting (`.1f` / `.3f` / `.2f`) is unchanged. The `unit or ""`
fallback keeps the empty-string sentinel for dimensionless rows so
`hydro_rows_from_state` and `hydro_lines_from_state` (downstream
consumers) need no edits.

### 4. Regression test

Add `tests/test_hydrostatics_row_metadata.py` mirroring the
`tests/test_hull_parameter_metadata.py` shape:

- **Schema coverage**: assert
  `set(HYDROSTATICS_ROW_METADATA.keys()) == set(EXPECTED_KEYS)`.
- **Count pin**: assert `len(HYDROSTATICS_ROW_METADATA) == 7` so an
  accidental add/remove is loud.
- **Value-object well-formedness**: for each key, assert
  `parameter` matches the registry key, and `label` / `description`
  / (non-`None`) `unit` are non-blank trimmed strings.
- **Wiring assertion**: assert
  `analysis_view_model(state_dict_from_hull(Hull()))["hydro_rows"]`
  emits the registry labels in the expected order.
- **Byte-stable wire-payload assertion**: assert the
  `hydro_rows_from_state(state)` label list (filtering out
  `"Warning"` rows) matches the post-`b82b544` / pre-RFC 0062
  baseline. Any future intentional copy change updates the constant
  in the same commit as the registry edit.
- **Unit-suffix preservation**: assert
  `hydro_rows_from_state` still appends the unit to the `value`
  field for dimensional rows and does not append a stray space for
  dimensionless rows. Pins the `unit or ""` decoding step.

## Acceptance Criteria

- `kayakgen/ui/hydrostatics_metadata.py` lands with the value object
  and the seven-row registry.
- `kayakgen/services/evaluation.py::analysis_view_model` consumes
  the registry; the function's return-value dict shape is unchanged
  (top-level keys + value types).
- `kayakgen/services/evaluation.py::hydro_rows_from_state` and
  `hydro_lines_from_state` are not touched; their byte-output is
  pinned by the new test.
- `kayakgen/services/evaluation.py::mesh_diagnostics_rows_from_state`
  is not touched (workflow 0037 territory).
- `tests/test_hydrostatics_row_metadata.py` lands and pins the
  registry contract.
- `docs/rfcs/README.md` gains a 0062 row after 0061.
- The audit finding `AUD-O-005` is marked closed in the next audit
  cycle (the audit FINDINGS file itself stays read-only per
  `docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md` R3).

## Open Questions

None for this RFC; the scope is narrow and the pattern is already
twice-validated by RFC 0060 and RFC 0061.

Possible future-pass siblings that could apply the same D043 pattern,
listed for the record but explicitly out of scope:

- Mesh-diagnostic row metadata (currently embeds threshold guidance
  in the row labels per AUD-O-006; would need a `guidance` field on
  the value object before migration).
- Evaluator-status metadata (the readiness/claim_state labels
  surfaced by `cfd_in_loop_evaluator_status` and friends).
- Resistance-row metadata (the resistance table emitted by
  `analysis_view_model::resistance_rows` — today the rows are
  keyed dicts, not `(label, value, unit)` tuples, so the migration
  shape is different).

Each successor RFC, if pursued, would be a separate audit follow-up
landing one surface at a time.

## Implementation Path

- Step 1 — Workflow `0038-hydrostatics-row-metadata-registry` lands
  this RFC, the registry, the evaluation wiring, the test, and the
  README row in one commit (status `landed` from the outset; the
  implementation lands together with the RFC).
- Step 2 — The 2026-05-25 audit follow-up artifact
  `docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/PATCH_SUMMARY.md`
  records the exact files changed and confirms the verification
  suite passes.
- Step 3 — A successor audit cycle marks `AUD-O-005` closed.

## Domain Modeling

`HydrostaticsRowMetadata` is a value object in DDD terms: frozen,
`extra="forbid"` Pydantic model, no identity. The
`HYDROSTATICS_ROW_METADATA` registry is a service catalog — a single
source of truth for the presentation layer over the hydrostatics
row family. It does not participate in any aggregate boundary; the
underlying hydrostatics values continue to come from the
`evaluate_hydrostatics` evaluator on the `Hull` aggregate.

The presentation layer now has three sibling catalogs, all rooted at
`kayakgen.ui.*`:

- `HULL_PARAMETER_METADATA` (RFC 0060) — web Generate panel + the
  RFC 0061 desktop slider labels.
- `VIEW_PARAMETER_METADATA` (RFC 0061) — view-only parameters that
  are not `Hull` fields (currently just `target_speed_kt`).
- `HYDROSTATICS_ROW_METADATA` (this RFC) —
  `analysis_view_model::hydro_rows` labels + units + descriptions.

The catalogs share a `parameter / label / unit / description` shape
but live in separate modules per D043's "registry per surface
family" decision: each catalog corresponds to one logical UI
surface, and merging them would couple unrelated copy concerns.
