# RFC 0061: Desktop Sliders on `HullParameterMetadata`

Status: landed
Date: 2026-05-22
Context:
[`RFC 0060`](0060-web-generate-panel-form-labels-and-tooltips.md),
[`D043`](../DECISION_LOG.md) (HullParameterMetadata presentation-layer pattern),
[`AUD-O-003`](../audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md)
follow-up,
[`kayakgen/ui/desktop.py`](../../kayakgen/ui/desktop.py)
`SLIDERS` table,
[`kayakgen/ui/gui_params.py`](../../kayakgen/ui/gui_params.py)
`GUI_TO_HULL` translation,
[`kayakgen/ui/parameter_metadata.py`](../../kayakgen/ui/parameter_metadata.py)
registry,
[`kayakgen/ui/pv_window.py`](../../kayakgen/ui/pv_window.py)
consumer,
[`tests/test_gui_params.py`](../../tests/test_gui_params.py)

## Problem

RFC 0060 landed `HullParameterMetadata` as the canonical source of
friendly labels + descriptions for hull parameters, scoped to the web
Generate panel. The desktop GUI has its own parallel `SLIDERS` table at
`kayakgen/ui/desktop.py:83-94` carrying:

- A short GUI key per parameter (`length`, `beam`, `beam_wl`, `draft`,
  `deck_height`, `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`,
  `bow_rake`, `stern_rake`, plus the view-only `target_speed_kt`).
- A friendly label (`"Length (m)"`, `"Beam OA (m)"`, ...).
- A `(vmin, vmax)` slider range.

The GUI keys differ from canonical Hull JSON keys (`length` vs
`length_m`, `beam` vs `beam_oa_m`, ...), and the translation lives in a
third module (`kayakgen/ui/gui_params.py:9` `GUI_TO_HULL`). The labels
also differ in style from RFC 0060's registry entries (`"Prismatic
Coeff"` desktop vs `"Prismatic coefficient (Cp)"` web; `"Bow Rake
(1=raked)"` desktop vs `"Bow rake"` web).

Three downstream costs follow:

1. **Drift surface**: two label tables for the same parameters means
   either kept in sync (manual work, easy to miss) or allowed to
   diverge (operator confusion across desktop and web).
2. **Extra indirection**: every desktop site that touches a Hull field
   has to go through `GUI_TO_HULL`. New maintainers re-derive the
   mapping each time.
3. **Glossary bypass**: D043 records `HullParameterMetadata` as the
   pattern for "UI-facing labels and tooltips on hull-parameter form
   fields". The desktop GUI is exactly that surface, but does not
   consume the registry.

D043 already names "Desktop `SLIDERS` migration to the same registry"
as the recommended follow-up to RFC 0060.

## Goals

- Make `HULL_PARAMETER_METADATA` the single source of truth for friendly
  labels on the eleven hull parameters the desktop GUI exposes.
- Rename the desktop SLIDERS / DEFAULTS / `GLOBAL_RANGES` keys to the
  canonical Hull JSON names (`length` -> `length_m`, etc.).
- Retire the `GUI_TO_HULL` indirection and the
  `hull_from_gui_params(params)` translator. The desktop's `params` dict
  becomes a Hull-shaped dict that can be passed directly to `Hull(**...)`.
- Keep the desktop's slider ranges in a parallel desktop-local module
  (`kayakgen/ui/desktop_slider_ranges.py` or similar). Per D043 open
  question 1, ranges are explicitly NOT moving into
  `HullParameterMetadata` in this RFC.
- Handle `target_speed_kt` as a view-only parameter, owned by a small
  parallel `VIEW_PARAMETER_METADATA` registry in the same
  `kayakgen/ui/parameter_metadata.py` module. It is NOT a Hull field,
  so it does not belong in `HULL_PARAMETER_METADATA`.
- Preserve the desktop GUI's runtime behavior: the rendered hull
  geometry, the printed resistance summary, the export menu wiring, the
  slider step (`Cm = 0.005`), and the `_NON_HULL_GUI_KEYS` exclusion
  all stay byte-identical.
- Add a small regression test covering the desktop's
  `params -> Hull(...)` round-trip post-rename.

## Non-Goals

- Adding range fields to `HullParameterMetadata`. D043 open question 1
  explicitly defers this; the desktop slider ranges are UI-tuned and
  differ from `Hull` validator ranges.
- Internationalization, operator-configurable labels, or richer tooltip
  rendering in the desktop GUI (matplotlib widgets do not natively
  support hover tooltips the way Vuetify does).
- Touching the web Generate panel. RFC 0060 already wired the registry
  there; this RFC just adds the desktop consumer.
- Renaming or relocating `Hull.model_fields`. The canonical Hull schema
  is unchanged.
- Migrating `pyvista_view.py`. It is not on the import path the desktop
  GUI actually uses today (`kayakgen/ui/pv_window.py` is). If a future
  RFC consolidates the two PyVista surfaces, the registry can be wired
  there in the same pass.
- Deleting `kayakgen/ui/gui_params.py` entirely. The
  `hull_from_gui_params(params)` helper is exercised by
  `tests/test_gui_params.py`; the test gets retargeted at the new
  Hull-shaped `params` dict and the helper becomes a thin shim or is
  removed once no consumer remains.

## Proposal

### 1. Extend `kayakgen/ui/parameter_metadata.py`

Add a `VIEW_PARAMETER_METADATA` dict for desktop-only viewing
parameters that are NOT Hull fields. V1 carries exactly one entry:

```python
VIEW_PARAMETER_METADATA: dict[str, HullParameterMetadata] = {
    "target_speed_kt": HullParameterMetadata(
        parameter="target_speed_kt",
        label="Target speed",
        unit="kt",
        description=(
            "Forward speed used by the desktop resistance summary; "
            "not a Hull field. Used only by the GUI; sweep / search "
            "specs carry their own speed sweeps."
        ),
    ),
}
```

`HullParameterMetadata` is reused as-is; the value object is generic
over "one parameter exposed by a UI form". The class name stays the
same because (a) it already lives in a `kayakgen.ui.parameter_metadata`
module and (b) renaming the class is a much bigger blast radius than
the small naming-overload cost.

`label_with_unit(...)` and `description(...)` gain a fallback chain:
look up the parameter in `HULL_PARAMETER_METADATA` first, then
`VIEW_PARAMETER_METADATA`, then return the raw key. The two registries
must not share keys (asserted in the regression test below).

### 2. Add `kayakgen/ui/desktop_slider_ranges.py`

A small module owning the desktop-tuned slider ranges and the slider
step overrides:

```python
"""Desktop matplotlib slider ranges and step overrides.

Kept separate from ``HullParameterMetadata`` per D043 open question 1:
ranges are UI-tuned and differ from ``Hull`` validator ranges. The
registry is presentation-only; the slider ranges are presentation +
input-shape.
"""

from __future__ import annotations

SLIDER_RANGES: dict[str, tuple[float, float]] = {
    "length_m": (2.0, 6.5),
    "beam_oa_m": (0.30, 0.90),
    "beam_wl_m": (0.30, 0.90),
    "draft_m": (0.05, 0.25),
    "deck_height_m": (0.15, 0.40),
    "Cp": (0.45, 0.70),
    "Cm": (0.65, 0.95),
    "deck_flatness": (2.0, 16.0),
    "center_box_ratio": (0.10, 0.60),
    "bow_rake": (0.0, 1.0),
    "stern_rake": (0.0, 1.0),
    "target_speed_kt": (1.0, 6.0),
}

SLIDER_STEPS: dict[str, float] = {"Cm": 0.005}

SLIDER_DEFAULTS: dict[str, float] = {
    "length_m": 4.5,
    "beam_oa_m": 0.55,
    "beam_wl_m": 0.55,
    "draft_m": 0.12,
    "deck_height_m": 0.23,
    "Cp": 0.55,
    "Cm": 0.85,
    "deck_flatness": 8.0,
    "center_box_ratio": 0.33,
    "bow_rake": 1.0,
    "stern_rake": 1.0,
    "target_speed_kt": 3.5,
}
```

The numeric values are lifted verbatim from today's `SLIDERS` /
`DEFAULTS` in `kayakgen/ui/desktop.py`; only the keys rename. A small
schema test asserts every key in `SLIDER_RANGES` appears in either
`HULL_PARAMETER_METADATA` or `VIEW_PARAMETER_METADATA`.

### 3. Rewrite `KayakGUI.SLIDERS` / `DEFAULTS` / `GLOBAL_RANGES`

In `kayakgen/ui/desktop.py`, replace the 12-row literal table with a
construction from the registry plus the desktop-local ranges:

```python
from kayakgen.ui.desktop_slider_ranges import (
    SLIDER_DEFAULTS,
    SLIDER_RANGES,
    SLIDER_STEPS,
)
from kayakgen.ui.parameter_metadata import (
    HULL_PARAMETER_METADATA,
    VIEW_PARAMETER_METADATA,
    label_with_unit,
)

class KayakGUI:
    SLIDERS = [
        (key, label_with_unit(key), low, high)
        for key, (low, high) in SLIDER_RANGES.items()
    ]
    DEFAULTS = dict(SLIDER_DEFAULTS)
    GLOBAL_RANGES = dict(SLIDER_RANGES)
    SLIDER_STEPS = dict(SLIDER_STEPS)
    _NON_HULL_GUI_KEYS = tuple(VIEW_PARAMETER_METADATA.keys())
```

The 4-tuple SLIDERS shape stays the same so the matplotlib widget
construction at line ~135+ does not change.

### 4. Retire `GUI_TO_HULL`

With the rename in §3, `self.params` is now a dict keyed by canonical
Hull field names plus `target_speed_kt`. Replace the three call sites:

- `kayakgen/ui/desktop.py:125` initializer: drop the dict
  comprehension that uses `_GUI_TO_HULL`. Replace with a direct
  `{key: getattr(hull, key) for key in _GUI_TO_HULL.values()
  if hasattr(hull, key)}` — actually simpler, just iterate Hull's
  model_fields filtered against the slider key set.
- `kayakgen/ui/desktop.py:371,412,467`: every call to
  `_hull_from_gui_params(self.params)` becomes a direct
  `Hull(**{k: v for k, v in self.params.items()
  if k not in self._NON_HULL_GUI_KEYS})`. A small helper on `KayakGUI`
  (e.g. `_hull_from_params`) keeps the call sites tidy.
- `kayakgen/ui/pv_window.py:17,76,112`: same replacement; the
  `_hull_from_gui_params` import becomes a no-op once removed.

`kayakgen/ui/gui_params.py` shrinks to a deprecation shim: keep the
module so `tests/test_gui_params.py` can import + re-target, but the
`GUI_TO_HULL` table becomes an empty dict with a docstring naming RFC
0061. `hull_from_gui_params(params)` becomes a thin pass-through to
`Hull(**...)` that emits a DeprecationWarning. Delete in a successor
RFC.

### 5. Regression tests

`tests/test_desktop_sliders_use_registry.py` (new):

- Assert every key in `SLIDER_RANGES` resolves to either a
  `HULL_PARAMETER_METADATA` entry or a `VIEW_PARAMETER_METADATA`
  entry; no key is unowned.
- Assert `HULL_PARAMETER_METADATA.keys()` and
  `VIEW_PARAMETER_METADATA.keys()` are disjoint.
- Assert every Hull-side key in `SLIDER_RANGES` (i.e. excluding
  `_NON_HULL_GUI_KEYS`) resolves to a real `Hull` field via
  `Hull.model_fields`.
- Assert `KayakGUI.SLIDERS[i][1]` matches `label_with_unit(key)` for
  each row.
- Assert `KayakGUI.DEFAULTS` round-trips through
  `Hull(**{k: v for k, v in DEFAULTS.items() if k not in
  _NON_HULL_GUI_KEYS})` to produce a valid `Hull`.

`tests/test_gui_params.py` is updated: keep the test asserting that
the legacy short keys are no longer needed (the new `params` dict goes
straight into `Hull(**...)`). The deprecation-warning path is covered
by a single test that calls `hull_from_gui_params(...)` and asserts
the warning is emitted.

`tests/test_vocabulary_coverage.py` extends its
`_RFC_0060_PRESENTATION_TERMS` (or a new `_RFC_0061_VIEW_TERMS`) list
to include `VIEW_PARAMETER_METADATA` if a glossary entry is added (see
acceptance criteria).

## Acceptance Criteria

- `kayakgen/ui/parameter_metadata.py` gains `VIEW_PARAMETER_METADATA`
  with at least the `target_speed_kt` entry; `label_with_unit` and
  `description` fall back through both registries.
- `kayakgen/ui/desktop_slider_ranges.py` lands with `SLIDER_RANGES`,
  `SLIDER_STEPS`, `SLIDER_DEFAULTS`.
- `kayakgen/ui/desktop.py` `SLIDERS` / `DEFAULTS` / `GLOBAL_RANGES`
  derive from the new modules. The 12 numeric ranges and 12 default
  values are byte-equal to today's literals. The rendered slider
  labels are sourced from the registry (so e.g. `"Prismatic Coeff"`
  becomes `"Prismatic coefficient (Cp)"`).
- `kayakgen/ui/gui_params.py` `GUI_TO_HULL` is emptied (or removed);
  `hull_from_gui_params` becomes a deprecation shim.
- `kayakgen/ui/pv_window.py` and `kayakgen/ui/desktop.py` consume
  `Hull(**self.params filtered ...)` directly; no remaining
  `_GUI_TO_HULL` imports.
- `tests/test_desktop_sliders_use_registry.py` pins the registry
  contract; `tests/test_gui_params.py` retargeted; full repo suite
  remains green.
- The rendered desktop hull geometry, the resistance summary, the
  export menu wiring, and the slider step behavior are byte-identical
  to the pre-RFC desktop run.
- D043 follow-up note in `docs/DECISION_LOG.md` D043 row is updated to
  cite this RFC as the named "desktop migration" follow-up that
  closed.

## Open Questions

- Should `VIEW_PARAMETER_METADATA` live in
  `kayakgen/ui/parameter_metadata.py` (proposed) or a sibling
  `kayakgen/ui/view_parameter_metadata.py`? Recommended: same module,
  same import path, since the consumer set is identical and the
  separation is purely conceptual.
- Should `VIEW_PARAMETER_METADATA` use a separate `ViewParameterMetadata`
  value object class? Recommended: no, reuse `HullParameterMetadata`
  with a generic name interpretation. Splitting hairs adds blast
  radius without value.
- Should the desktop slider labels gain a description tooltip too?
  Matplotlib Slider does not natively support hover tooltips; could
  use `mplcursors` or a status-bar string. Defer to a successor RFC if
  desired.
- Should `kayakgen/ui/gui_params.py` and `tests/test_gui_params.py` be
  removed entirely in this RFC? Recommended: keep the shim + a single
  deprecation test for one release, delete in a successor.
- Should `pyvista_view.py` (separate from `pv_window.py`) be migrated
  in the same RFC? Recommended: no, it is not on the active import
  path; flag for a future consolidation RFC.

## Implementation Path

- Step 1 — Land this RFC as `proposed` and add its row to
  `docs/rfcs/README.md`.
- Step 2 — Scaffold `docs/workflows/0034-desktop-sliders-on-registry/`
  mirroring `docs/workflows/0033-web-generate-panel-labels/` (single
  implement -> review pair, lane diversity: claude / gemini).
- Step 3 — Drive workflow 0034: land §1, §2, §3, §4, §5; verify the
  desktop GUI renders correctly with `kayakgen view` (manual smoke,
  not a CI gate since the desktop GUI is not headless-testable here).
- Step 4 — Promote this RFC to `landed`; update D043's "Revisit" cell
  to cite this RFC as the closed follow-up; add a `CHANGELOG.md
  ### Changed` entry.

## Domain Modeling

This RFC does not add a domain aggregate, claim state, or
acceptance gate. It is purely a presentation-layer consolidation:

- `HullParameterMetadata` already exists; this RFC reuses it.
- `VIEW_PARAMETER_METADATA` is a new presentation-layer catalog of
  view-only parameters that the desktop GUI surfaces. View parameters
  do not participate in any `Hull` invariant.
- `kayakgen.ui.desktop_slider_ranges` is a presentation + input-shape
  catalog (slider ranges, step overrides, default values). Per D043
  open question 1, ranges stay out of `HullParameterMetadata` so the
  value object's contract stays presentation-only.

The `kayakgen/ui/gui_params.py` translation table is a deprecated
indirection that should disappear once no consumer remains. The
desktop GUI now uses the canonical `Hull` field names directly, which
matches both the web Generate panel and the `Hull` JSON serialization
boundary.
