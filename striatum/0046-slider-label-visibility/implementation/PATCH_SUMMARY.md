# Patch Summary - Workflow 0046 Slider Label Visibility

## Changed Files

- `kayakgen/ui/desktop.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/theme.py`
- `tests/test_desktop_layout.py`
- `tests/test_web_browser.py`
- `tests/test_web_layout.py`
- `tests/test_ui_theme.py`
- `CHANGELOG.md`
- `striatum/0046-slider-label-visibility/implementation/PATCH_SUMMARY.md`

Pre-existing operator/report artifacts under `OPERATOR_REPORT.md` and
`striatum/0046-slider-label-visibility/{traceability,ergonomics,ops,ledger}/`
were already present in the worktree and were left untouched by this
implementation lane.

## Findings Addressed

- F1: Desktop slider labels are moved below the track and are tested against
  figure edges, slider tracks, neighboring labels, value text, buttons, class
  controls, metrics/status axes, and plot axes.
- F2: Desktop slider labels and value text are both set to `7.5` pt and the
  rendered bbox test verifies value text does not bleed into adjacent rows.
- F3: Web parameter-rail sliders now use `thumb_label=True` instead of
  persistent `thumb_label="always"` labels.
- F4: Web slider rows use `mt-3`, and scoped slider-label CSS uses the shared
  label/secondary-text tokens with single-line overflow handling.
- F5: Added rendered desktop bbox proof for default size plus `1440x900` and
  `1920x1080`.
- F6: Added web DOM geometry proof, canonical label/aria checks, scoped CSS
  checks, and `text-secondary` on `surface-rail` contrast-manifest coverage.
- F7: Kept desktop `KayakGUI.SLIDERS`, web `SLIDER_DEFS`, bindings, ranges,
  defaults, steps, value formatting, class-preset behavior, claim copy,
  backend behavior, and capability state unchanged.

## Implementation Choices

- Desktop sliders set `s.label.set_fontsize(7.5)` and
  `s.valtext.set_fontsize(7.5)`.
- Desktop uses `label_location="bottom"` when the installed Matplotlib
  `Slider` API supports that argument. The current validation environment's
  Matplotlib 3.10.9 does not expose `label_location`, so `desktop.py` keeps a
  compatibility branch that places the label below the track and is covered by
  the bbox tests.
- Desktop removed the previous `s.label.set_position((0.5, -1.8))`.
- Desktop gained a headless Matplotlib fallback to `agg` only when `qtagg`
  cannot load without a display, so the layout proof can run under pytest.
- Web parameter rows now wrap `VSlider` in a `kg-param-slider kg-param-{key}
  mt-3` row carrying the canonical `aria-label`; the visible `VSlider` label
  still comes directly from `SLIDER_DEFS`.
- Web `VSlider` uses `thumb_label=True`.
- The scoped CSS lives in `kayakgen/ui/web/app.py` as `PARAMETER_RAIL_CSS` and
  is injected with `html_widgets.Style(...)`. It contains:
  `.kg-param-slider .v-slider__label { font: var(--type-label); color:
  var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow:
  ellipsis; }`.
- `kayakgen/ui/theme.py` adds the contrast manifest pair
  `slider.label.rail`: `text-secondary` on `surface-rail`.
- `CHANGELOG.md` records only the user-visible slider-label legibility fix.

## Validation

- `git diff --check`
  - Passed; no output.
- `PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider`
  - Passed: `4 passed in 3.18s`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_layout.py tests/test_ui_theme.py -q -p no:cacheprovider`
  - Passed: `23 passed in 5.17s`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_layout.py tests/test_ui_theme.py tests/test_gui_params.py -q -p no:cacheprovider`
  - Passed: `24 passed in 5.18s`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider`
  - Passed: `1 passed in 10.21s`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
  - Passed: `328 passed in 84.93s`.

The desktop extra was installed into the local `.venv` during implementation
so the desktop bbox proof could run instead of skipping.

## Deferrals And Residual Risks

- No desktop Qt-native slider rewrite, focus-ring work, metric/status redesign,
  web hover tooltip, persistent inline numeric value, backend capability,
  CFD behavior, stability behavior, solver-readiness behavior, or calibration
  claim was added.
- The desktop label-position compatibility branch exists because the installed
  Matplotlib `Slider` API lacks `label_location`. The rendered bbox proof is
  the acceptance evidence for the active branch in this environment.
- Browser geometry proof scrolls each parameter row into view and checks the
  label at rest; it does not add screenshot assertions.

## Operator Follow-Up Wording

No operator follow-up is required.

## Scope Confirmation

No Striatum state, commits, pushes, attribution metadata, claim language,
backend capability, CFD behavior, stability behavior, solver-readiness behavior,
or calibration behavior was changed.
