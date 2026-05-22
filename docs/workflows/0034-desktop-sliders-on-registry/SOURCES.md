# Sources for workflow 0034 — desktop sliders on `HullParameterMetadata`

> Operator: this file is the per-run context manifest. Each job reads it
> as required context. Keep entries short and link to the canonical
> source rather than duplicating it.

## RFC in scope

- [`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`](../../rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md)
  is the spec. §1 extends `parameter_metadata.py` with
  `VIEW_PARAMETER_METADATA`. §2 adds `desktop_slider_ranges.py`. §3
  rewrites `KayakGUI.SLIDERS` / `DEFAULTS` / `GLOBAL_RANGES`. §4 retires
  `GUI_TO_HULL`. §5 lists the regression assertions.

## Decision-log follow-up addressed

- `D043` (HullParameterMetadata presentation-layer pattern) — the
  "Revisit" cell names "Desktop `SLIDERS` migration to the same
  registry" as the recommended follow-up. See
  [`docs/DECISION_LOG.md`](../../DECISION_LOG.md).

## Antecedent RFC

- [`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`](../../rfcs/0060-web-generate-panel-form-labels-and-tooltips.md)
  landed the `HullParameterMetadata` registry that this RFC extends and
  consumes on the desktop side.

## Source files touched

| Surface | Paths |
|---|---|
| Registry extension | `kayakgen/ui/parameter_metadata.py` |
| New module | `kayakgen/ui/desktop_slider_ranges.py` |
| Rewritten consumer | `kayakgen/ui/desktop.py` |
| Updated consumer | `kayakgen/ui/pv_window.py` |
| Deprecation shim | `kayakgen/ui/gui_params.py` |
| New test | `tests/test_desktop_sliders_use_registry.py` |
| Retargeted test | `tests/test_gui_params.py` |
| Label-source fix-up | `tests/test_desktop_layout.py` (if needed) |

## Files NOT touched by this workflow

The parent agent owns these surfaces:

- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/*/FINDINGS.md`
- `docs/rfcs/README.md`
- `docs/rfcs/0061-*.md`
- `docs/DECISION_LOG.md` (D043 "Revisit" cell update)

## Byte-equality invariant

RFC 0061 acceptance criterion: the 12 slider range tuples and 12
default values in `kayakgen/ui/desktop_slider_ranges.py` must be
byte-equal (numerically identical literals) to today's
`kayakgen/ui/desktop.py:83-115` literals. Only the keys rename from the
short GUI form (`length`, `beam`, ...) to canonical Hull JSON form
(`length_m`, `beam_oa_m`, ...). The implementer's PATCH_SUMMARY.md
states the byte-equality check explicitly.

## Where the artifacts land

`docs/audits/2026-05-22-code-doc-audit/follow-ups/0034/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
