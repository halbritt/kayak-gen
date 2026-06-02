author: operator [self-declared: 0057-slice1-implementer-finalize]

# RFC 0065 Slice 1 Patch Summary

## Scope

- Extended `kayakgen/ui/theme.py` additively with `SPACING`, `DENSITY`,
  `RADII`, `ELEVATION`, and `BORDERS` maps.
- Added palette-resolved focus/state color tokens:
  `state-focus-ring`, hover/active/disabled surface tokens, and
  hover/active/disabled text tokens in both light and dark palettes.
- Added focus-ring width and border/dimension tokens without changing
  `matplotlib_rc_params()` or `vtk_background_rgb()` behavior.
- Grew `css_root_block()` and `vuetify_theme_config()` to emit/map the
  new token families.
- Extended `CONTRAST_MANIFEST` for focus ring visibility against
  `surface-panel` and `surface-viewport-bg`, plus hover/active/disabled
  state text/surface pairs.
- Migrated the existing inline visual literals in
  `kayakgen/ui/web/app.py` and
  `kayakgen/ui/web/generate_frontier_view.py` to source their values
  from the new theme maps. The rendered CSS values remain the same
  literals they replaced.
- Widened `tests/test_ui_theme.py` orphan-literal lint from color-only
  to visual literals: raw `px`/`rem`/`em` dimensions, `border-radius`,
  `box-shadow`, `outline`/`outline-width`, and focus/focus-ring
  property literals outside `theme.py`.
- Added a planted-literal negative test for the widened lint.
- Added a `CHANGELOG.md` entry under `Unreleased`.

## Invariants

- No `CHIP_*` entries were renamed, retyped, recolored, or edited.
- No persistent claim/readiness/status captions were changed.
- No `data-testid` or `kg-*` hook was renamed or moved.
- No REST route, `claim_state`, `Readiness`, or `accepted_uses` literal
  was added.
- `docs/USER_GUIDE.md` and `docs/WEB_VERIFICATION.md` were not touched.

## Verification

- `.venv/bin/pytest tests/test_ui_theme.py -q`
  - `12 passed in 0.10s`
- `.venv/bin/pytest tests/test_ui_theme.py tests/test_web.py tests/test_web_layout.py -q`
  - `70 passed in 36.31s`
- `.venv/bin/ruff check kayakgen/ui/theme.py tests/test_ui_theme.py kayakgen/ui/web/app.py kayakgen/ui/web/generate_frontier_view.py`
  - `All checks passed!`
  - Ruff also reports existing warnings for the custom
    `# noqa: kg-orphan-color` annotations in
    `kayakgen/ui/web/generate_frontier_view.py`.
- `.venv/bin/pytest tests/test_web_browser.py::test_kayakgen_serve_browser_acceptance -q`
  - The VTK nonblank/sizing assertion passed after switching inline
    height styles to render literal values sourced from `theme.DENSITY`.
  - The test then failed on the pre-existing
    `.kg-class-preset-radio input[type='radio'][value='surfski_elite']`
    expectation; `kayakgen/ui/web/app.py` already documents that the
    rail `VRadioGroup` was removed and class selection now lives in the
    toolbar `VSelect`.
- `.venv/bin/pytest -q`
  - `1295 passed, 4 skipped, 2 failed in 456.35s`
  - Residual failures:
    - `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
      reports the existing `kayakgen/services/evaluation.py` import from
      `kayakgen.ui.hydrostatics_metadata`.
    - `tests/test_web_browser.py::test_kayakgen_serve_browser_acceptance`
      initially exposed the zero-height VTK frame regression from CSS
      custom properties not being present on `documentElement`; this
      patch fixed that specific regression. The focused rerun now
      advances to the pre-existing class-preset-radio expectation
      described above.
