# Findings Ledger - Workflow 0046 Slider Label Visibility

## Gate Verdict

`accept_with_findings`

Implementation may proceed as a narrow view-layer remediation. The three review
artifacts agree that no new RFC is required: the accepted requirements already
cover fully legible slider labels, non-overlap, canonical label text, and
testable UI proof. This workflow is not a backend, physics, CFD, stability,
read-model, or capability-claim change.

The implementation lane must treat the existing tests as baseline health only.
They do not currently prove desktop rendered label visibility, web DOM label
non-overlap, or slider-label contrast on the actual rail. The patch must add
focused proof for every surface it changes.

## Source Reviews

| Review artifact | Verdict intent | Ledger treatment |
| --- | --- | --- |
| `traceability/REVIEW_TRACEABILITY.md` | `accept` | Accept the RFC mapping and scope boundaries. Desktop is required; web must be fixed only within the parameter rail and without changing labels, bindings, or claims. |
| `ergonomics/REVIEW_ERGONOMICS_DESIGN.md` | `accept_with_findings` | Accept the concrete desktop and web rendering fixes: bottom labels, 7.5 pt slider text, non-persistent web thumb labels, scoped label CSS, and no broader layout redesign. |
| `ops/REVIEW_OPS.md` | `accept_with_findings` | Accept the test-proof requirement: bbox tests for desktop and DOM geometry/contrast tests for web if the web surface changes. |

## Safe-Now Findings

### F1 - Desktop Slider Labels Overlap The Next Row

Severity: High

- Source review: traceability RFC 0002/RFC 0003 mapping; ergonomics E1.
- Scope: `kayakgen/ui/desktop.py`, `KayakGUI._build_sliders`, plus focused
  desktop layout tests.
- Expected behavior: every `KayakGUI.SLIDERS` label is fully readable at the
  default 16:9 desktop figure and at the RFC anchors `1440x900` and
  `1920x1080`. No label is clipped by the figure edge or occluded by adjacent
  slider tracks, neighboring labels, value text, buttons, class radio, metrics,
  status text, or plot axes.
- Implementation direction: construct each matplotlib `Slider` with
  `label_location="bottom"` and delete
  `s.label.set_position((0.5, -1.8))`. Do not replace it with a smaller manual
  offset.
- Validation command:

```bash
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
```

### F2 - Desktop Slider Label And Value Text Are Too Small/Loose

Severity: High

- Source review: ergonomics E2-E3; ops O1.
- Scope: `kayakgen/ui/desktop.py`, `KayakGUI._build_sliders`, and the same
  desktop layout proof as F1.
- Expected behavior: slider labels and right-hand value text are readable and
  do not bleed into the next row. The class radio, metrics block, and status
  block remain visually unchanged unless a bbox proof shows a direct collision
  introduced by this fix.
- Implementation direction: set both `s.label` and `s.valtext` to `7.5` pt.
  Keep the default `valtext` position; right-align value text if needed. Do not
  change value formatting, slider ranges, defaults, steps, `valstep`, `valinit`,
  or `on_changed` wiring.
- Validation command:

```bash
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
```

### F3 - Web Persistent Thumb Labels Obscure Parameter Labels

Severity: High

- Source review: ergonomics E4; traceability web rail question; ops O2/O4.
- Scope: `kayakgen/ui/web/app.py`, parameter-rail `VSlider` rows only, plus
  browser geometry proof if this surface is edited.
- Expected behavior: at rest, each `.kg-param-slider` label is visible, has a
  positive rendered box, is not clipped outside the parameter rail, and does not
  intersect the track or any visible `.v-slider-thumb__label`. Slider values
  remain available while the control is dragged or focused.
- Implementation direction: use `thumb_label=True`, not
  `thumb_label="always"`, for parameter-rail sliders. This ledger resolves the
  traceability/design tension by treating hover/focus thumb labels as the
  accepted value surface for this narrow fix. Do not add a persistent inline
  value unless DOM geometry proof shows `thumb_label=True` is insufficient.
- Validation command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py \
  -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
```

### F4 - Web Slider Label Typography And Overflow Need A Scoped Rule

Severity: Medium

- Source review: ergonomics E5-E7; ops O3; traceability RFC 0033/RFC 0034
  canonical label checks.
- Scope: `kayakgen/ui/web/app.py` row classes and, if needed,
  `kayakgen/ui/theme.py` through the existing CSS/theme injection path.
- Expected behavior: web parameter labels use the shared label voice, preserve
  contrast on the rail, stay single-line, and do not wrap into neighboring
  rows. Visible label strings and `aria-label` values remain the canonical
  source strings.
- Implementation direction: change slider row spacing from `mt-2` to `mt-3`
  and add one scoped rule for `.kg-param-slider .v-slider__label`:
  `font: var(--type-label); color: var(--text-secondary); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;`. Use existing tokens only.
- Validation command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_web_layout.py tests/test_ui_theme.py -q -p no:cacheprovider
```

If web rendering changes, also run the browser command from F3.

### F5 - Desktop Visibility Needs Rendered Bounding-Box Proof

Severity: High

- Source review: ops O1 and validation matrix; traceability acceptance checks.
- Scope: add `tests/test_desktop_layout.py`.
- Expected behavior: the test monkeypatches `matplotlib.pyplot.show`,
  instantiates `KayakGUI`, forces `fig.canvas.draw()`, and compares
  `Text.get_window_extent(renderer)` and `Axes.get_window_extent()` rectangles.
  It asserts each canonical desktop label is present, inside the figure, and
  non-overlapping with slider tracks, neighboring labels, value text, buttons,
  metrics/status axes, class controls, and plot axes.
- Implementation direction: prefer geometry assertions over screenshot
  matching. Do not launch a full interactive PyQt event loop.
- Validation command:

```bash
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_desktop_layout.py tests/test_gui_params.py -q -p no:cacheprovider
```

### F6 - Web Label Proof Needs DOM Geometry And Theme Checks

Severity: Medium

- Source review: ops O2-O4; ergonomics accessibility notes.
- Scope: `tests/test_web_browser.py` for DOM geometry if web rendering changes;
  `tests/test_web_layout.py`/`tests/test_ui_theme.py` for canonical labels,
  CSS variables, and contrast-manifest coverage.
- Expected behavior: browser acceptance verifies every visible web parameter
  label has a positive box, is not clipped outside the rail, and does not
  intersect the track or visible thumb label at rest. Static/theme tests verify
  canonical labels are unchanged, full `aria-label` strings remain intact, CSS
  uses `var(--type-label)` and `var(--text-secondary)`, and any slider-label
  contrast pair uses existing tokens such as `text-secondary` on
  `surface-rail`.
- Implementation direction: screenshots may be kept as debug artifacts but are
  not the assertion.
- Validation commands:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_web_layout.py tests/test_ui_theme.py -q -p no:cacheprovider
```

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_web_browser.py \
  -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
```

### F7 - Existing Labels, Claims, Bindings, And Desktop Affordances Must Not Drift

Severity: High

- Source review: traceability acceptance checks 3-8; ops paths-to-avoid.
- Scope: all implementation and tests.
- Expected behavior: the fix changes rendering only. Desktop labels remain the
  existing `KayakGUI.SLIDERS` strings. Web labels remain the existing
  `SLIDER_DEFS` strings. RFC 0034 web bindings, validity badge behavior,
  Resistance/Mesh/Export behavior, forbidden-copy assertions, desktop
  debounce/loading/window-title/metrics/arrow-nudge/STL-dialog affordances, and
  theme-token discipline continue to work as before.
- Implementation direction: do not abbreviate labels, rename groups, change
  class-preset behavior, alter controller/read-model state, or introduce any
  new capability language.
- Validation commands:

```bash
git diff --check
```

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_web_layout.py tests/test_ui_theme.py tests/test_gui_params.py \
  -q -p no:cacheprovider
```

If both desktop and web are touched, run the full non-browser suite before final
review:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

## Explicit Deferrals

- No new RFC is needed unless implementation discovers it must change
  claim-language, read-model shape, backend behavior, or capability state to
  fix labels.
- If implementation proves the web surface is not observably broken before
  editing it, web rendering changes may be deferred. That deferral must include
  the proof command/evidence and must not claim web labels were fixed.
- Desktop focus rings, a Qt-native slider rewrite, a matplotlib aria layer, web
  hover tooltips, persistent inline numeric values, and metric/status redesign
  are deferred.
- Do not widen the desktop GridSpec or rail unless bbox proof shows the accepted
  `label_location="bottom"` plus 7.5 pt text cannot satisfy F1/F2.
- Desktop behavior below roughly `600px` high remains a pre-existing practical
  limit; a user-guide note about a `720px` minimum height is optional and not a
  blocker.
- The status block's `6.2` pt font, class radio `7` pt font, and metrics block
  `7.5` pt font are out of scope unless directly affected by the slider-label
  fix.
- Do not promote high-angle GZ, hosted CFD, calibrated drag, final prediction,
  design fitness, web-side mesh authoring, or any RFC 0033/0034 deferred
  capability.

## Implementation Write-Scope Guardrails

Allowed paths for this workflow:

- `kayakgen/ui/desktop.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/theme.py`
- focused tests under `tests/`, especially `tests/test_desktop_layout.py`,
  `tests/test_web_browser.py`, `tests/test_web_layout.py`,
  `tests/test_ui_theme.py`, and `tests/test_gui_params.py`
- `docs/USER_GUIDE.md`, at most one sentence if documenting the desktop minimum
  height or arrow-key context
- `CHANGELOG.md`
- workflow-local artifacts under `striatum/0046-slider-label-visibility/`

Forbidden paths and behaviors:

- Do not edit `.striatum/`, mutate Striatum state, run Striatum commands,
  commit, push, or add `author:`, `byline:`, or `Co-Authored-By` metadata.
- Do not touch hull geometry, model, evaluator, CFD, mesh, CLI, IO, REST, or
  package paths such as `generator.py`, `kayakgen/model/**`,
  `kayakgen/eval/**`, `kayakgen/io/**`, or CLI modules.
- Do not change `kayakgen/ui/web/controllers.py`,
  `kayakgen/ui/web/state.py`, `SLIDER_DEFS`, `PARAMETER_GROUPS`, validity badge
  semantics, class-preset binding logic, `evaluation_summary`, Resistance,
  Mesh, Export, status-bar, claim-chip, or forbidden-copy behavior.
- Do not change desktop `_on_change`, `_on_class_select`,
  `_on_view_param_change`, slider ranges, defaults, step sizes, class-preset
  seeding, or `gui.py` shim behavior.
- Do not add new color tokens, typography tokens, responsive hooks, layout test
  IDs, or hex color literals for this fix.
- Do not add or newly expose copy containing `OpenFOAM`, `SU2`, `hosted`,
  `cloud`, `worker queue`, `calibrated drag`, `final prediction`,
  `design fitness`, `GZ_max`, `heel_angle_max_deg`, or bare `cfd_ready` outside
  already-documented negations.

## Required Patch Summary Contents

The implementation lane must write
`striatum/0046-slider-label-visibility/implementation/PATCH_SUMMARY.md` with:

- changed files;
- findings addressed, mapped to F1-F7 above;
- exact implementation choices, including whether desktop used
  `label_location="bottom"`, whether `s.label`/`s.valtext` are `7.5` pt,
  whether web uses `thumb_label=True`, and where the scoped web label CSS lives;
- validation commands and results, including `git diff --check`, desktop bbox
  tests, web static/theme tests, browser acceptance if web changed, and the
  full non-browser suite if both surfaces changed;
- explicit deferrals and residual risks;
- any exact operator follow-up wording, especially if web changes are deferred
  or browser acceptance cannot be run;
- confirmation that no Striatum state, commits, pushes, attribution metadata,
  claim language, backend capability, CFD, stability, or calibration behavior
  was changed.
