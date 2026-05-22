# Implement prompt — workflow 0034

You are landing RFC 0061 (desktop sliders on `HullParameterMetadata`).
Read the RFC first; it is the spec. Read `SOURCES.md` for the per-run
context manifest. Closes D043's named "desktop `SLIDERS` migration to
the same registry" follow-up.

## Deliverables

1. **`kayakgen/ui/parameter_metadata.py`** — per RFC 0061 §1:
   - Add `VIEW_PARAMETER_METADATA: dict[str, HullParameterMetadata]`
     after the existing `HULL_PARAMETER_METADATA` dict. V1 carries one
     entry: `target_speed_kt` with `label="Target speed"`, `unit="kt"`,
     and a description naming the registry separation (it is a
     view-only parameter, not a `Hull` field).
   - Update `label_with_unit(parameter)` and `description(parameter)`
     so they fall back through both registries: check
     `HULL_PARAMETER_METADATA` first, then `VIEW_PARAMETER_METADATA`,
     then return the raw key (for `label_with_unit`) or `None` (for
     `description`).
   - Add `VIEW_PARAMETER_METADATA` to `__all__`.

2. **`kayakgen/ui/desktop_slider_ranges.py`** — per RFC 0061 §2:
   - Module docstring explaining the separation from
     `HullParameterMetadata` per D043 open question 1 (ranges are
     UI-tuned and differ from `Hull` validator ranges).
   - `SLIDER_RANGES: dict[str, tuple[float, float]]` with the 12 rows
     keyed by canonical Hull JSON name plus `target_speed_kt`. The
     numeric tuples must be byte-equal to today's desktop literals at
     `kayakgen/ui/desktop.py:83-115`.
   - `SLIDER_STEPS: dict[str, float] = {"Cm": 0.005}`.
   - `SLIDER_DEFAULTS: dict[str, float]` with the 12 default values
     (also byte-equal to today's literals).
   - `__all__` listing the three exports.

3. **`kayakgen/ui/desktop.py`** — per RFC 0061 §3-§4:
   - Replace the import block: add
     `from kayakgen.ui.desktop_slider_ranges import (SLIDER_DEFAULTS, SLIDER_RANGES, SLIDER_STEPS)`
     and
     `from kayakgen.ui.parameter_metadata import (HULL_PARAMETER_METADATA, VIEW_PARAMETER_METADATA, label_with_unit)`.
     Remove the `_GUI_TO_HULL` / `_hull_from_gui_params` imports.
   - Replace `KayakGUI.SLIDERS`, `DEFAULTS`, `GLOBAL_RANGES`,
     `SLIDER_STEPS`, `_NON_HULL_GUI_KEYS` with the registry-driven
     form per RFC 0061 §3. The slider 4-tuple shape stays the same so
     the matplotlib widget construction does not change.
     `label_with_unit(key)` is the label source.
   - Rewrite `KayakGUI.__init__` to seed `self.params` from a `Hull`
     using canonical Hull keys directly (no `_GUI_TO_HULL`); iterate
     `self.DEFAULTS` keys, skip `_NON_HULL_GUI_KEYS`, and use
     `getattr(hull, key)` when the attribute is present.
   - Add a tiny helper
     `_hull_from_params(self) -> Hull` that does
     `Hull(**{k: v for k, v in self.params.items() if k not in self._NON_HULL_GUI_KEYS})`.
   - Replace the three `_hull_from_gui_params(self.params)` call sites
     (export, refresh-metrics, geometry) with `self._hull_from_params()`.
   - Update the `_on_class_select` / `_apply_slider_ranges` /
     `_on_change` / `_build_button` / `_refresh_metrics` bodies so the
     short keys (`length`, `beam`, `beam_wl`, `draft`, `target_speed_kt`)
     read as their canonical Hull names (`length_m`, `beam_oa_m`,
     `beam_wl_m`, `draft_m`, `target_speed_kt`). `target_speed_kt`
     stays as-is (it is the only `_NON_HULL_GUI_KEYS` member).

4. **`kayakgen/ui/pv_window.py`** — per RFC 0061 §4:
   - Remove the `_hull_from_gui_params` import.
   - Replace the two call sites with `Hull(**{k: v for k, v in params.items() if k not in _NON_HULL_GUI_KEYS})`,
     where `_NON_HULL_GUI_KEYS` is sourced from
     `kayakgen.ui.parameter_metadata.VIEW_PARAMETER_METADATA.keys()`.
   - Update `_update_title` so it reads `length_m` and `beam_oa_m`.

5. **`kayakgen/ui/gui_params.py`** — per RFC 0061 §4:
   - Empty out `GUI_TO_HULL` (an empty dict with a docstring naming
     RFC 0061).
   - `hull_from_gui_params(params)` becomes a thin pass-through that
     emits a `DeprecationWarning` naming RFC 0061, filters `params`
     against `Hull.model_fields`, and returns `Hull(**filtered)`.

6. **`tests/test_desktop_sliders_use_registry.py`** — per RFC 0061 §5:
   - Every `SLIDER_RANGES` key resolves to either
     `HULL_PARAMETER_METADATA` or `VIEW_PARAMETER_METADATA`.
   - `HULL_PARAMETER_METADATA.keys()` and
     `VIEW_PARAMETER_METADATA.keys()` are disjoint.
   - Every Hull-side `SLIDER_RANGES` key (i.e. excluding
     `_NON_HULL_GUI_KEYS`) resolves to a real `Hull.model_fields` name.
   - `KayakGUI.SLIDERS[i][1] == label_with_unit(SLIDERS[i][0])` for
     each row.
   - `KayakGUI.DEFAULTS` filtered through the canonical hull keys
     produces a valid `Hull`.

7. **`tests/test_gui_params.py`** — per RFC 0061 §4-§5:
   - Update the existing `hull_from_gui_params` test so its input uses
     canonical Hull keys (`length_m`, `beam_oa_m`, ...) — the old short
     keys would be filtered out now that `GUI_TO_HULL` is empty.
   - Add a new test asserting the `DeprecationWarning` is emitted by
     `hull_from_gui_params(...)` and names RFC 0061.

8. **`tests/test_desktop_layout.py`** (only if needed) — the slider
   labels now come from `label_with_unit(key)`, so the literal
   `expected_label` strings in
   `test_desktop_slider_labels_are_visible_and_unobstructed` must be
   regenerated from the registry. Update the assertion to source the
   expected label from `label_with_unit(key)` rather than the old
   `SLIDERS` 4-tuple's second column — the test still validates layout
   geometry; only the string-equality source changes.

## Verification

Run in the project venv:

```bash
.venv/bin/pytest \
  tests/test_desktop_sliders_use_registry.py \
  tests/test_gui_params.py \
  tests/test_hull_parameter_metadata.py \
  tests/test_vocabulary_coverage.py \
  -q
```

All must pass. If `tests/test_desktop_layout.py` is also in scope in
the implementer's environment, run it too.

## Scope discipline

You MUST NOT touch:

- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/*/FINDINGS.md`
- `docs/rfcs/README.md`
- `docs/rfcs/0061-*.md`
- `docs/DECISION_LOG.md`

Those are the parent agent's job. The workflow's `forbidden_paths`
encodes this contract; do not work around it.

## Artifact

Write
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0034/PATCH_SUMMARY.md`
with: files changed, test counts per file (and which tests you updated
for the label-source change), the byte-equality check on
`SLIDER_RANGES` / `SLIDER_DEFAULTS` vs the pre-RFC desktop literals,
and confirmation that the `DeprecationWarning` fires when
`hull_from_gui_params(...)` is called.
