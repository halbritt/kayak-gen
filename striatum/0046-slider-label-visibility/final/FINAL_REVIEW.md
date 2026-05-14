# Final Review - Workflow 0046 Slider Label Visibility

Run: `run_cec0311f06dd4484a8743c329f4dca61`
Branch: `striatum/0046-slider-label-visibility`

Verdict intent: `accept_with_findings`

## Summary

The implementation is a narrow view-layer remediation that matches the ledger's
allowed scope. All seven safe-now findings (F1-F7) are addressed with concrete
desktop and web rendering changes plus rendered geometry tests. Backend, CFD,
stability, mesh, controller/read-model, claim, and forbidden-copy surfaces are
untouched. The patch summary's validation table is consistent with the
implementation diff inspected here, and the test code is structured to fail
loudly if the targeted regressions return.

Two minor, non-blocking deviations from ledger directives are recorded below as
findings (M1, M2). Neither is a behavioural regression - both are pragmatic
compromises that the new tests gate.

## Verification Against Findings

### F1 - Desktop label placement (High)

- `kayakgen/ui/desktop.py:233-248` passes `label_location="bottom"` to
  `widgets.Slider` only when the installed Matplotlib exposes that argument.
  The legacy `s.label.set_position((0.5, -1.8))` is gone. When
  `label_location` is unavailable, the implementation falls back to a smaller
  manual offset `(0.5, -0.52)` plus center/top alignment.
- `tests/test_desktop_layout.py:31-132` asserts each canonical label is inside
  the figure, does not overlap its own track or value text, does not overlap
  any other label/track/value, and does not collide with the three buttons,
  class radio, metrics axes, status axes, or any of the three plot axes - at
  the default size, `1440x900`, and `1920x1080`.
- The visible label strings still come from `KayakGUI.SLIDERS` and the test
  asserts `slider.label.get_text() == expected_label` (line 50).

Result: behavioural intent of F1 is satisfied and proved. See M1 about the
fallback path.

### F2 - Slider label and value text size (High)

- `kayakgen/ui/desktop.py:243-244` sets both `s.label` and `s.valtext` to
  `7.5` pt.
- `tests/test_desktop_layout.py:51-52` asserts both font sizes are `7.5`.
- Value-text bbox assertions (lines 110-131) cover that value text stays inside
  the figure and does not overlap its own track, neighbouring tracks, labels,
  or other value text.
- Value formatting, ranges, defaults, steps, `valstep`, `valinit`, and
  `on_changed` wiring are unchanged.

### F3 - Web persistent thumb labels (High)

- `kayakgen/ui/web/app.py:990` uses `thumb_label=True`. The previous
  `thumb_label="always"` is gone and `tests/test_web_layout.py:78-79` asserts
  the string `'thumb_label="always"'` is absent and `'thumb_label=True'` is
  present in the module source.
- The browser acceptance helper
  `tests/test_web_browser.py:_assert_parameter_slider_label_geometry`
  iterates every parameter row and, after scrolling it into view, asserts the
  label's `getBoundingClientRect` is positive, lies inside the rail boundary,
  and does not intersect the track or any *visible* `.v-slider-thumb__label`.
  Hover/focus thumb labels are therefore tolerated by design.

### F4 - Scoped web label CSS and row spacing (Medium)

- `kayakgen/ui/web/app.py:201-210` defines `PARAMETER_RAIL_CSS`. The rule
  `.kg-param-slider .v-slider__label { font: var(--type-label); color:
  var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow:
  ellipsis; }` uses only existing tokens.
- Row classes changed from `mt-2` to `mt-3` on the new wrapper `Div`
  (`app.py:982`). `tests/test_web_layout.py:80-81` asserts the new class
  string is present and the old one is gone.
- `tests/test_web_layout.py:91-101` asserts each token usage (`var(--type-
  label)`, `var(--text-secondary)`) and confirms that
  `theme.css_root_block()` exposes the matching custom-property definitions
  (`--type-label`, `--text-secondary`, `--surface-rail`).
- The CSS is injected via `html_widgets.Style(PARAMETER_RAIL_CSS)` inside
  `_build_layout` (`app.py:919`), which matches the ergonomics review's
  request that the scoped rule go through an existing CSS/theme path.

### F5 - Desktop rendered bbox proof (High)

- `tests/test_desktop_layout.py` is new and monkeypatches `pyplot.show`,
  instantiates `KayakGUI`, forces a draw, and asserts geometry rather than
  screenshot matching. Parametrized over default plus `1440x900` and
  `1920x1080`. No interactive Qt event loop is launched.

### F6 - Web label proof (Medium)

- DOM geometry: `tests/test_web_browser.py:320-426`
  (`_assert_parameter_slider_label_geometry`) checks every visible parameter
  label has a positive box, is not clipped outside the rail, does not
  intersect the track or visible thumb labels, and that
  `aria-label` values across the row's element subtree include the canonical
  label text.
- Static/theme checks: `tests/test_web_layout.py:60-101` and
  `tests/test_ui_theme.py:139-145` (canonical label list, scoped CSS tokens,
  and a new `slider.label.rail` contrast manifest pair pointing
  `text-secondary` at `surface-rail`).
- `kayakgen/ui/theme.py:340` registers the contrast pair, which the existing
  contrast-clearance test (`tests/test_ui_theme.py:test_contrast_manifest_
  clears_thresholds`) automatically gates.

### F7 - No drift in labels, claims, bindings, affordances (High)

- Desktop `KayakGUI.SLIDERS`, ranges, defaults, `SLIDER_STEPS`,
  `_on_change`, `_on_class_select`, `_on_view_param_change`, class-preset
  seeding, and button affordances are untouched.
- Web `SLIDER_DEFS`, `PARAMETER_GROUPS`, validity badge wiring, Resistance,
  Mesh, Export, claim copy, and forbidden-copy negations are untouched. The
  `v_model=(key,)` binding, min/max state aliases, `step`, and `density` are
  preserved at `app.py:984-993`.
- The visible label text inside each row is still passed directly to
  `VSlider(label=label, ...)` and the wrapper `Div`'s `aria-label` reuses the
  same canonical string. No abbreviation, no rename, no new capability
  language.
- `CHANGELOG.md` adds a single user-visible legibility entry; it does not
  introduce new backend, CFD, stability, or calibration claims.

## Findings

### M1 - Desktop fallback uses a manual offset the ledger discouraged

Severity: Low (non-blocking)

The ledger F1 implementation direction said to use
`label_location="bottom"` and explicitly "Do not replace it with a smaller
manual offset." The implementation does replace the removed
`(0.5, -1.8)` with `(0.5, -0.52)` plus center/top alignment when
`widgets.Slider` does not accept `label_location` (the active branch in this
environment, per `PATCH_SUMMARY.md`).

This is justified: the `label_location` kwarg is not present on the installed
Matplotlib's `widgets.Slider`, so the prescribed direction cannot be applied
verbatim. The new bbox tests in `tests/test_desktop_layout.py` are the
acceptance evidence for the fallback path and would fail if the manual offset
ever started clipping or overlapping any obstacle in the layout.

Recommended follow-up (not a blocker):

- When the project's Matplotlib floor moves to a version that exposes
  `label_location` on `Slider`, drop the fallback branch and the
  `_SLIDER_SUPPORTS_LABEL_LOCATION` shim.

File/line refs: `kayakgen/ui/desktop.py:47-49,233-248`.

### M2 - Web row gets a new wrapper `Div` with role="group"

Severity: Low (non-blocking)

The row's `aria-label` was previously on the `VSlider` itself; it is now on a
wrapping `html_widgets.Div` carrying `role="group"`. The visible label inside
the slider still renders the same canonical text, and the browser-level
geometry check accepts the `aria-label` whether it sits on the wrapper or any
descendant. This is an intentional structural change (it gives the scoped CSS
selector a stable container), but it does introduce an extra DOM node and a
new `group` role that was not present before.

This is within the ledger's allowed scope (it lives in `kayakgen/ui/web/app.py`
and does not change `SLIDER_DEFS`, controllers, or read-model). Worth flagging
only so the next reviewer or accessibility audit sees the intentional shift.

File/line refs: `kayakgen/ui/web/app.py:246-254,980-993`.

### M3 - `PARAMETER_RAIL_CSS` re-emits `:root` tokens already supplied by the Vuetify theme path

Severity: Low (non-blocking)

`PARAMETER_RAIL_CSS` prepends `theme.css_root_block()` (`app.py:201-210`) so
the new rule can rely on `--type-label`, `--text-secondary`, etc. Those
variables are already established on the page by the Vuetify theme + RFC 0033
plumbing. Duplicating the `:root` block is harmless (last definition wins,
identical values), but the simpler alternative - a one-line scoped rule
referencing existing variables - would avoid the duplication. Leaving as-is
because the implementation explicitly verifies token presence in
`tests/test_web_layout.py:99-101`.

File/line refs: `kayakgen/ui/web/app.py:201-210`.

## Scope and Guardrails

- Changed files match the ledger's allowed paths: `kayakgen/ui/desktop.py`,
  `kayakgen/ui/web/app.py`, `kayakgen/ui/theme.py`, focused tests, and
  `CHANGELOG.md`. `striatum/0046-slider-label-visibility/implementation/
  PATCH_SUMMARY.md` is a workflow-local artifact.
- No edits to `kayakgen/ui/web/controllers.py`, `kayakgen/ui/web/state.py`,
  `SLIDER_DEFS`, `PARAMETER_GROUPS`, `evaluation_summary`, Resistance, Mesh,
  Export, status-bar, claim-chip, validity-badge logic, `_on_change`,
  `_on_class_select`, `_on_view_param_change`, slider ranges/defaults/steps,
  class-preset seeding, or `gui.py`.
- No new color tokens, typography tokens, responsive hooks, layout test IDs,
  or hex literals. The new contrast manifest entry reuses
  `text-secondary` and `surface-rail`.
- No introduction or re-exposure of `OpenFOAM`, `SU2`, `hosted`, `cloud`,
  `worker queue`, `calibrated drag`, `final prediction`, `design fitness`,
  `GZ_max`, `heel_angle_max_deg`, or bare `cfd_ready` strings.
- `CHANGELOG.md` records only the user-visible legibility fix and does not
  claim any new backend, CFD, stability, mesh, or calibration capability.
- `OPERATOR_REPORT.md` was updated with workflow checkpoints; these read as
  supervise-lane lifecycle entries (run/session/artifact IDs and timestamps)
  rather than implementation-lane edits, and the implementation patch summary
  states the file was left untouched by the implementation lane. Out of scope
  for this review.

## Tests And Validation

Per `PATCH_SUMMARY.md`, the following ran clean (not re-executed here):

- `git diff --check` - no output.
- `tests/test_desktop_layout.py tests/test_gui_params.py` - 4 passed.
- `tests/test_web_layout.py tests/test_ui_theme.py` - 23 passed.
- `tests/test_web_layout.py tests/test_ui_theme.py tests/test_gui_params.py` -
  24 passed.
- `tests/test_web_browser.py -m browser_acceptance --browser-acceptance` -
  1 passed.
- Full non-browser suite - 328 passed.

The new test code is reviewed above and is structured to enforce F1-F6
properties on every run.

## Verdict

`accept_with_findings`. The implementation faithfully satisfies F1-F7 within
the ledger's narrow view-layer scope, adds maintainable rendered geometry
tests, leaves all backend/CFD/stability/calibration surfaces untouched, and
does not promote any new capability claims. Findings M1-M3 are documentation /
forward-looking notes and do not block landing.
