# Review prompt — workflow 0034

You are reviewing the implementer's landing of RFC 0061 (desktop
sliders on `HullParameterMetadata`). Closes D043's named "desktop
`SLIDERS` migration to the same registry" follow-up.

Read in order:

1. RFC 0061 (`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`)
   — the spec.
2. `docs/audits/2026-05-22-code-doc-audit/follow-ups/0034/PATCH_SUMMARY.md`
   — the implementer's report.
3. The actual touched files.

## Acceptance criteria (verify each)

1. **Registry extension.** `kayakgen/ui/parameter_metadata.py`:
   - Adds `VIEW_PARAMETER_METADATA` with at least the `target_speed_kt`
     entry; the entry uses `HullParameterMetadata` with
     `label="Target speed"`, `unit="kt"`, and a non-blank description.
   - `label_with_unit` and `description` fall back through both
     registries in order: `HULL_PARAMETER_METADATA` → `VIEW_PARAMETER_METADATA`
     → raw key / `None`.
   - `__all__` includes `VIEW_PARAMETER_METADATA`.

2. **New ranges module.** `kayakgen/ui/desktop_slider_ranges.py` ships
   `SLIDER_RANGES`, `SLIDER_STEPS`, `SLIDER_DEFAULTS` and a module
   docstring naming D043 open question 1. The 12 numeric tuples in
   `SLIDER_RANGES` and the 12 default values in `SLIDER_DEFAULTS` are
   byte-equal to the pre-RFC literals at
   `kayakgen/ui/desktop.py:83-115` — only the keys rename to canonical
   Hull JSON form.

3. **Desktop rewrite.** `kayakgen/ui/desktop.py`:
   - Imports `SLIDER_DEFAULTS`, `SLIDER_RANGES`, `SLIDER_STEPS` from
     `kayakgen.ui.desktop_slider_ranges` and
     `HULL_PARAMETER_METADATA`, `VIEW_PARAMETER_METADATA`,
     `label_with_unit` from `kayakgen.ui.parameter_metadata`. No
     remaining `_GUI_TO_HULL` or `_hull_from_gui_params` imports.
   - `KayakGUI.SLIDERS` is constructed from `SLIDER_RANGES` and
     `label_with_unit`; the 4-tuple shape is preserved. `DEFAULTS`,
     `GLOBAL_RANGES`, `SLIDER_STEPS` derive from the registry module.
     `_NON_HULL_GUI_KEYS = tuple(VIEW_PARAMETER_METADATA.keys())`.
   - `__init__` seeds `self.params` from a `Hull` using canonical Hull
     keys directly (no `_GUI_TO_HULL`).
   - A `_hull_from_params` helper replaces the three
     `_hull_from_gui_params(self.params)` call sites.
   - Short-key reads of `self.params` (`"length"`, `"beam"`,
     `"beam_wl"`, `"draft"`) are updated to canonical Hull names
     (`"length_m"`, `"beam_oa_m"`, `"beam_wl_m"`, `"draft_m"`);
     `"target_speed_kt"` stays unchanged.

4. **PyVista wiring.** `kayakgen/ui/pv_window.py`:
   - No `_hull_from_gui_params` import remaining.
   - Both call sites build a `Hull` directly from `params` filtered
     against `_NON_HULL_GUI_KEYS` sourced from
     `kayakgen.ui.parameter_metadata.VIEW_PARAMETER_METADATA.keys()`.
   - `_update_title` reads canonical Hull keys.

5. **Deprecation shim.** `kayakgen/ui/gui_params.py`:
   - `GUI_TO_HULL` is empty (or removed and any callers updated).
   - `hull_from_gui_params(params)` emits a `DeprecationWarning`
     naming RFC 0061 and returns a `Hull` built from `params` filtered
     against `Hull.model_fields`.

6. **Regression test (new).**
   `tests/test_desktop_sliders_use_registry.py` covers the five RFC
   0061 §5 assertions:
   - every `SLIDER_RANGES` key resolves to one of the two registries;
   - `HULL_PARAMETER_METADATA.keys()` and
     `VIEW_PARAMETER_METADATA.keys()` are disjoint;
   - every Hull-side `SLIDER_RANGES` key resolves to
     `Hull.model_fields`;
   - `KayakGUI.SLIDERS[i][1] == label_with_unit(SLIDERS[i][0])` for
     every row;
   - `KayakGUI.DEFAULTS` filtered through the canonical Hull keys
     produces a valid `Hull`.

7. **Retargeted test.** `tests/test_gui_params.py`:
   - The existing call to `hull_from_gui_params` uses canonical Hull
     keys (`length_m`, `beam_oa_m`, ...).
   - A new test asserts a `DeprecationWarning` is emitted by
     `hull_from_gui_params` and names RFC 0061 (a substring match on
     the warning message is fine).

## Tests to confirm

```bash
.venv/bin/pytest \
  tests/test_desktop_sliders_use_registry.py \
  tests/test_gui_params.py \
  tests/test_hull_parameter_metadata.py \
  tests/test_vocabulary_coverage.py \
  -q
```

All must pass. If `tests/test_desktop_layout.py` was in scope and the
implementer touched it, confirm the label-source change is the only
diff (no weakened layout-geometry assertions).

## Scope check

The implementer MUST NOT have touched `CHANGELOG.md`,
`docs/rfcs/README.md`, `docs/rfcs/0061-*.md`,
`docs/DECISION_LOG.md`, or the audit `FINDINGS.md` files. Flag any
drift.

## Artifact

Write `docs/audits/2026-05-22-code-doc-audit/follow-ups/0034/REVIEW.md`
with: verdict (accept | needs_revision), per-criterion check results
(pass / fail with file:line evidence), and any deferrals.
