# Sources for workflow 0038 — hydrostatics row metadata registry

> Operator: this file is the per-run context manifest. Each job
> reads it as required context. Keep entries short and link to the
> canonical source rather than duplicating it.

## Audit batch in scope

- [`docs/audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md`](../../audits/2026-05-25-code-doc-audit/REMEDIATION_PLAN.md)
  batch R3 closes:

  | ID | Severity | Theme |
  |---|---|---|
  | AUD-O-005 | low | hydro labels not registry-sourced (D043 follow-up) |

  The finding text lives at
  [`docs/audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-25-code-doc-audit/operator-adoption/FINDINGS.md).

## Antecedent RFCs (the pattern this workflow extends)

- [`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`](../../rfcs/0060-web-generate-panel-form-labels-and-tooltips.md)
  — introduced the `HullParameterMetadata` value object + the
  `HULL_PARAMETER_METADATA` registry under
  `kayakgen/ui/parameter_metadata.py`. The Trame Generate panel's
  base-hull rail consumes this registry for labels + tooltips.
- [`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`](../../rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md)
  — migrated the desktop matplotlib sliders onto the same registry,
  plus a sibling `VIEW_PARAMETER_METADATA` registry for view-only
  parameters (`target_speed_kt`).
- D043 in
  [`docs/DECISION_LOG.md`](../../DECISION_LOG.md) records the
  accepted "presentation-layer registry per surface family" pattern.

RFC 0062 (drafted by this workflow) makes hydrostatics rows the
third application of the pattern.

## Antecedent code paths

- `kayakgen/services/evaluation.py:113-121` —
  `analysis_view_model::hydro_rows` constructs `(label, value,
  unit)` tuples inline. The labels and units are hardcoded today.
- `kayakgen/services/evaluation.py:420-432` —
  `hydro_lines_from_state` text view consumes
  `analysis_view_model(state)["hydro_rows"]`.
- `kayakgen/services/evaluation.py:435-449` —
  `hydro_rows_from_state` (post-`b82b544`) consumes the same
  `hydro_rows` and renders `{label, value}` dicts.
- `kayakgen/ui/parameter_metadata.py` — the RFC 0060 registry shape
  to mirror.
- `tests/test_hull_parameter_metadata.py` — the regression-net
  shape to mirror for the new registry.

## Hydro rows in scope

These are the rows `analysis_view_model` currently emits:

| Internal id (proposed) | Current label | Current unit |
|---|---|---|
| `displacement` | Displacement | kg |
| `wetted_surface` | Wetted surface | m^2 |
| `waterplane_area` | Waterplane area | m^2 |
| `gm0` | GM0 | m |
| `cp_actual` | Cp actual | (none) |
| `cm_actual` | Cm actual | (none) |
| `l_over_bwl` | L/B wl | (none) |

The registry stores `(id, label, unit, description)` for each row.
Descriptions are net-new; the implementer drafts them with the
same operator-facing voice as the RFC 0060 hull-parameter
descriptions.

## Source files modified by this workflow

| Path | Why |
|---|---|
| `kayakgen/ui/hydrostatics_metadata.py` (new) | `HydrostaticsRowMetadata` value object + registry. |
| `kayakgen/services/evaluation.py` | `analysis_view_model::hydro_rows` consumes the registry. **No change to `hydro_rows_from_state`**: it stays a pass-through. **No change to `mesh_diagnostics_rows_from_state`** (R2 territory). |
| `tests/test_hydrostatics_row_metadata.py` (new) | Registry coverage + wire-payload stability regression. |
| `docs/rfcs/0062-hydrostatics-row-metadata-registry.md` (new) | The RFC itself. |
| `docs/rfcs/README.md` | One-row index update. |

## Source files NOT touched

The workflow's `forbidden_paths` encodes the read-only contract:

- `CHANGELOG.md`, `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`,
  `docs/SPEC.md`, `docs/PRD.md`, `docs/ROADMAP.md`,
  `docs/ARCHITECTURE_MAP.md`, `docs/UBIQUITOUS_LANGUAGE.md`,
  `docs/audits/README.md`, all 2026-05-25 audit FINDINGS / SYNTHESIS /
  REMEDIATION_PLAN files — parent agent's job.
- `kayakgen/ui/web/` — entirely off-limits (R2 territory).
- `kayakgen/ui/parameter_metadata.py` — sibling registry, read-only.
- `kayakgen/ui/desktop.py`, `kayakgen/ui/desktop_slider_ranges.py`,
  `kayakgen/ui/gui_params.py` — desktop is unaffected.

## RFC 0062 outline (for the implementer)

The RFC should follow the RFC 0060 / RFC 0061 shape:

- **Status**: landed (set when the implementer completes).
- **Date**: 2026-05-25.
- **Context**: RFC 0060, RFC 0061, D043, audit AUD-O-005, the
  affected source files.
- **Problem**: hardcoded labels in `analysis_view_model` reduce
  changeability and prevent a documentation surface from listing
  what each hydrostatics row means.
- **Goals**: third application of the "presentation-layer registry
  per surface family" pattern; byte-stable wire payload; per-row
  description.
- **Non-Goals**: changing computed values, adding new rows, moving
  desktop / mesh-tab labels into the registry (mesh tab has its own
  conventions today).
- **Proposal**: the value object (`label`, `unit`, `description`);
  the `HYDROSTATICS_ROW_METADATA` registry; the
  `analysis_view_model` wiring; the regression test.
- **Acceptance**: registry coverage test, byte-stable
  `hydro_rows_from_state` snapshot test, the audit finding's
  recommended-action box ticked.

## Where the artifacts land

`docs/audits/2026-05-25-code-doc-audit/follow-ups/0038/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
