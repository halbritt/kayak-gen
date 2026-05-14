# Ops/Test Review — Workflow 0046 Slider Label Visibility

Verdict intent: accept_with_findings

The workflow is narrow enough to proceed, but the implementation ledger should
not treat the existing tests as proof of the reported failure. Current coverage
proves web state/layout contracts, theme-token discipline, and browser smoke
operation. It does not prove desktop slider-label visibility, rendered web
label non-overlap, or actual slider-label contrast.

## Findings

### O1 — Desktop slider visibility has no behavioral test coverage

`kayakgen/ui/desktop.py` builds the twelve parameter sliders in
`KayakGUI._build_sliders`, but the only desktop-adjacent test today is
`tests/test_gui_params.py`, which verifies parameter conversion and never
constructs the figure. RFC 0002's visible-label acceptance therefore has no
regression guard.

Ledger addition: add `tests/test_desktop_layout.py` that monkeypatches
`matplotlib.pyplot.show`, instantiates `KayakGUI`, forces `fig.canvas.draw()`,
and compares `Text.get_window_extent(renderer)` / `Axes.get_window_extent()`
rectangles. Assert every `KayakGUI.SLIDERS` label is present, inside the figure
at a 16x9 default size, and not overlapping slider tracks, neighboring labels,
value text, buttons, metrics/status axes, or plot axes. This is preferred over
screenshot matching.

### O2 — Web layout tests prove structure, not rendered label visibility

`tests/test_web_layout.py` covers parameter grouping, class-preset bounds,
responsive hooks, persistent copy, export rows, and forbidden-claim strings.
`tests/test_web_browser.py` waits for text such as `Length (m)` and exercises
slider mutation, but it does not measure label bounding boxes, clipping, or
overlap with Vuetify thumb/value elements.

Ledger addition: if `kayakgen/ui/web/app.py` or web slider CSS changes, extend
the browser-acceptance profile with a DOM geometry assertion over
`.kg-param-slider` rows. Check each visible `.v-slider__label` has a positive
box, is not clipped outside the parameter rail, and does not intersect the
track or any visible `.v-slider-thumb__label` at rest. Keep screenshots as
debug artifacts only, not the assertion.

### O3 — Contrast tests cover tokens, not the slider-label application

`tests/test_ui_theme.py::test_contrast_manifest_clears_thresholds` verifies the
declared token pairs, and `test_no_orphan_color_literals_under_kayakgen_ui`
keeps color literals centralized. That is useful, but no test currently proves
that web slider labels use `var(--text-secondary)` or that
`text-secondary` clears contrast on the actual rail background.

Ledger addition: if web label CSS is added, assert the CSS uses existing theme
variables, and add a contrast-manifest pair for slider labels on the rail, for
example `text-secondary` on `surface-rail`. Do not add new color tokens for
this fix.

### O4 — Existing browser acceptance is runnable here, but should be scoped

The required browser profile is available in this venv and passed in this
review. Browser acceptance should be required for any web slider-label change
or any claim that the web labels were fixed. It can remain optional for a
desktop-only implementation, provided the desktop bbox test is added and the
ledger explicitly defers web with a reason.

## Validation Matrix

| Risk | Existing coverage | Gap | Ledger-ready addition |
| --- | --- | --- | --- |
| Desktop label text | `KayakGUI.SLIDERS` is the source; no test reads rendered labels | No assertion that labels survive layout construction | New desktop layout test asserts rendered label strings equal `KayakGUI.SLIDERS` labels |
| Desktop visibility | None | No figure-edge, row, value-text, or plot-axis bbox checks | `tests/test_desktop_layout.py` using Matplotlib extents after draw |
| Web label text | `tests/test_web_layout.py` verifies grouped fields; browser waits for `Length (m)` | Does not assert every canonical label is rendered and accessible | Static test over `SLIDER_DEFS` plus browser check that visible labels and `aria-label`s match |
| Web non-overlap | Existing browser test exercises sliders and 3D | No DOM bbox checks for labels, tracks, or thumb labels | Browser-acceptance helper comparing `getBoundingClientRect()` for `.kg-param-slider` internals |
| Theme/color discipline | `tests/test_ui_theme.py` token, contrast, and orphan-color tests | No slider-label-specific rail contrast pair or CSS application check | Add slider-label contrast pair and assert CSS uses `var(--type-label)` / `var(--text-secondary)` |
| Claim/capability hygiene | `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces` | Good existing guard; do not weaken | Keep unchanged; new label tests must not edit claim-copy assertions |
| Browser operation | `tests/test_web_browser.py -m browser_acceptance --browser-acceptance` | Current pass is smoke plus state, not label geometry | Required if web changes; add label geometry checks to same profile |

## Practical Commands

Baseline commands run during this review:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_web_layout.py tests/test_ui_theme.py tests/test_gui_params.py \
  -q -p no:cacheprovider
# 21 passed in 5.06s
```

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py \
  -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
# 1 passed in 9.97s
```

Recommended implementation validation:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_web_layout.py tests/test_ui_theme.py -q -p no:cacheprovider
```

If web slider rendering changes:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py \
  -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
```

Before final review, run the focused tests above plus the full non-browser
suite if the implementation touches both desktop and web:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

The `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` flags are useful for
this workflow because review jobs should avoid leaving pytest cache or bytecode
artifacts in the repo.

## Paths To Avoid

- Do not touch hull geometry, model, evaluator, CFD, mesh, CLI, or IO paths:
  `generator.py`, `kayakgen/model/**`, `kayakgen/eval/**`,
  `kayakgen/io/**`, and CLI command modules are outside a label-visibility fix.
- Do not change web controllers or state for label rendering:
  `kayakgen/ui/web/controllers.py` and `kayakgen/ui/web/state.py` should remain
  unchanged unless the ledger discovers a separate accepted finding.
- Do not rename or abbreviate slider labels in `SLIDER_DEFS` or
  `KayakGUI.SLIDERS` to make them fit. Preserve canonical labels and fix
  layout/styling.
- Do not alter Resistance, Mesh, Export, status-bar, claim-chip, CFD, or
  forbidden-copy behavior.
- Do not edit `.striatum/`, mutate workflow state, commit, push, or add
  attribution metadata.
