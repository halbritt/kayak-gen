# Workflow 0034 — Patch summary

RFC 0061 (desktop sliders on `HullParameterMetadata`) landed. Closes
D043's named "desktop `SLIDERS` migration to the same registry"
follow-up.

## Files changed

| File | Change |
|---|---|
| `kayakgen/ui/parameter_metadata.py` | Added `VIEW_PARAMETER_METADATA` (one entry: `target_speed_kt`). Updated `label_with_unit` and `description` to fall back through both registries. Extended `__all__`. |
| `kayakgen/ui/desktop_slider_ranges.py` | NEW. Owns `SLIDER_RANGES`, `SLIDER_STEPS`, `SLIDER_DEFAULTS`. Module docstring names D043 open question 1. |
| `kayakgen/ui/desktop.py` | Replaced imports (`gui_params._GUI_TO_HULL` / `_hull_from_gui_params` → `desktop_slider_ranges` + `parameter_metadata`). Rewrote `KayakGUI.SLIDERS` / `DEFAULTS` / `GLOBAL_RANGES` / `SLIDER_STEPS` / `_NON_HULL_GUI_KEYS` to derive from the registry. Renamed short-key reads (`length`/`beam`/`beam_wl`/`draft`) to canonical Hull keys (`length_m`/`beam_oa_m`/`beam_wl_m`/`draft_m`). Added `_hull_from_params` helper. Replaced three `_hull_from_gui_params(self.params)` call sites. |
| `kayakgen/ui/pv_window.py` | Dropped `_hull_from_gui_params` import. Added local `_hull_from_params(params)` helper sourcing `_NON_HULL_GUI_KEYS` from `VIEW_PARAMETER_METADATA`. Updated `_update_title` to read canonical Hull keys. |
| `kayakgen/ui/gui_params.py` | Shrunk to a deprecation shim. `GUI_TO_HULL` is now empty. `hull_from_gui_params` emits a `DeprecationWarning` naming RFC 0061 and filters `params` against `Hull.model_fields`. |
| `tests/test_desktop_sliders_use_registry.py` | NEW. Five §5 assertions, 16 test cases (parametric). |
| `tests/test_gui_params.py` | Updated input to canonical Hull keys (the old short-key form would now be filtered out). Added a new test asserting the RFC 0061 `DeprecationWarning` fires. |
| `tests/test_desktop_layout.py` | Added an extra assertion that the slider label equals `label_with_unit(key)` (the registry-driven path). Label-source string changed (registry-driven), so the literal expectation now reads from the registry; layout-geometry assertions unchanged. |

## Test counts (per file)

```
tests/test_desktop_sliders_use_registry.py    16 passed   (NEW)
tests/test_gui_params.py                       2 passed   (was 1; updated input + added deprecation test)
tests/test_hull_parameter_metadata.py         38 passed   (unchanged)
tests/test_vocabulary_coverage.py             43 passed   (unchanged)
tests/test_desktop_layout.py                   4 passed   (added 1 inline assertion per slider row)
```

Full repo suite: 1159 passed, 4 skipped (OpenFOAM smoke, opt-in).

## Tests updated for the label-source change

- `tests/test_desktop_layout.py::test_desktop_slider_labels_are_visible_and_unobstructed`
  — added `assert slider.label.get_text() == label_with_unit(key)` so a
  regression in the SLIDERS-construction path trips here too. The
  pre-existing `slider.label.get_text() == expected_label` assertion
  still passes because `expected_label` is now sourced from
  `KayakGUI.SLIDERS` (which itself is built from `label_with_unit`).

## Byte-equality check (SLIDER_RANGES / SLIDER_DEFAULTS)

Verified by `.venv/bin/python` against the literal block at the
pre-RFC `kayakgen/ui/desktop.py:83-115`:

```
ranges byte-equal: True
defaults byte-equal: True
slider_steps: {'Cm': 0.005}
count ranges: 12, count defaults: 12
```

All 12 range tuples and 12 default values match the pre-RFC literals
exactly; only the dict keys rename from the short GUI form (`length`,
`beam`, ...) to canonical Hull JSON form (`length_m`, `beam_oa_m`,
...). The single slider-step override (`Cm = 0.005`) is preserved.

## DeprecationWarning confirmation

Direct invocation confirms the warning fires:

```
DeprecationWarning fires: kayakgen.ui.gui_params.hull_from_gui_params
is deprecated by RFC 0061; the desktop GUI now uses canonical Hull
field names directly. Pass `params` straight to `Hull(**params)`
after filtering view-only keys.
```

`tests/test_gui_params.py::test_hull_from_gui_params_emits_rfc_0061_deprecation_warning`
pins this with `pytest.warns(DeprecationWarning, match="RFC 0061")`.

## Workflow validator output

```
{"data":{"valid":true,"workflow_id":"0034-desktop-sliders-on-registry"},"ok":true}
```

## Scope discipline

Not touched (parent agent owns):
- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/*/FINDINGS.md`
- `docs/rfcs/README.md`
- `docs/rfcs/0061-*.md`
- `docs/DECISION_LOG.md`
