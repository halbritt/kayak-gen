# Traceability Review — Workflow 0046 (Slider Label Visibility)

## Verdict

`accept`

The workflow as scaffolded targets the right problem and is correctly scoped
as a narrow legibility remediation against the already-accepted UI surface.
Every requirement and acceptance criterion needed to land a fix is already
present in RFC 0002, RFC 0003, RFC 0033, and RFC 0034. A new RFC is not
necessary; this is a regression repair against an existing landed
acceptance criterion (RFC 0002 §Acceptance, "Slider labels are fully legible
at 1440×900 and 1920×1080 without resizing the window") plus a small
binding tightening on the RFC 0033 parameter rail.

## Issue ↔ RFC Mapping

User report: "slider labels are not visible." The two surfaces with
parametric sliders are the desktop matplotlib GUI
(`kayakgen/ui/desktop.py`) and the web Vuetify rail
(`kayakgen/ui/web/app.py`). Both are in scope for legibility verification;
the implementation slice should touch only whichever surface is observably
broken.

- **RFC 0002 (GUI Usability Improvements, landed).** §Problem item 1
  ("Slider panel occlusion"), §Goals first bullet ("Slider labels are
  fully legible at default window size without resizing"), §Proposal §1
  ("Fix slider label clipping"), and §Acceptance first bullet ("Slider
  labels are fully visible at 1440×900 and 1920×1080 without resizing the
  window") are the canonical anchors. The desktop code at
  `kayakgen/ui/desktop.py:209-228` (`_build_sliders`) currently sets
  `s.label.set_position((0.5, -1.8))` with `fontsize=6.5` to push each
  matplotlib Slider's label *below* its 0.018-high axes. With 12 sliders
  in a 0.93→0.46 figure band (step ≈ 0.0392, far smaller than the 1.8 ×
  0.018 = 0.0324 vertical offset of each label below its track), the
  labels of every slider land on top of the next slider's track and are
  visually swallowed. That is a direct violation of RFC 0002's acceptance
  bullet and is the most concrete instance of the user complaint.
- **RFC 0003 (Layout Fix, Sheer Plan, Interactive Station View,
  landed).** §1 ("Fix layout coordinate conflicts") and the matching
  §Acceptance ("At 1440×900, no slider track, value label, or button
  bounding box overlaps any plot axes bounding box") govern horizontal
  clearance between the control column and the plot region. The current
  desktop layout uses GridSpec `left=0.38` and a slider column at
  `[0.07, y, 0.26, 0.018]`, which honours RFC 0003 horizontally; the
  failure mode is vertical density inside the slider column, not the
  RFC 0003 left-margin claim. RFC 0003's principle ("widgets visually
  separated … at any window size between 1280×800 and 2560×1440") still
  applies and the fix must not regress it.
- **RFC 0033 (Workspace UI Rework, partial landed safe-slice).** §2
  ("Parameter rail") enumerates the slider set the rail must surface —
  `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`,
  `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`,
  `stern_rake`, plus `target_speed_kt` — and requires that each row be
  legible with class-envelope ticks, advisory dots, and per-field
  numeric inputs. Visible labels are a precondition for every one of
  those affordances; the §3 metrics strip and §5 status-bar segments
  rely on each slider being identifiable by its visible label. There is
  no language in RFC 0033 sanctioning hidden or sub-6pt labels.
- **RFC 0034 (Workspace UI Follow-Up, landed safe-slice).** §Proposal
  items 1 and 2 wire the class preset to reseed canonical hull sliders
  and narrow their visible ranges; §Acceptance requires `KayakClass`
  bounds to be reflected in the rail. The narrowed range only matters
  if the slider track and label are readable. RFC 0034 does not modify
  any label-rendering decisions, and `striatum/0045-workspace-ui-follow-up/
  final/FINAL_REVIEW.md` does not list label legibility as a deferred
  item — so this workflow is closing a residual rendering gap, not
  re-opening an accepted decision.

## Why No New RFC Is Required

- The acceptance criterion the implementation must satisfy already
  exists verbatim in RFC 0002 §Acceptance bullet 1 and is reinforced
  by RFC 0033 §2's parameter-rail expectations.
- No new domain concept, claim state, readiness level, or REST shape
  is introduced. The fix is purely view-layer label rendering and
  optional Vuetify density/CSS within `kayakgen/ui/` and `theme.py`.
- RFC 0033 explicitly classifies the parameter rail as the surface
  responsible for legible per-field labels (§2 and §4 Domain Modeling:
  "boundary clarification ... presented through one consistent
  presentation contract defined by `kayakgen/ui/theme.py`").
- RFC 0034's safe-slice posture (no new backend capabilities, no
  multi-variant overlay, no claim-language changes) is preserved by a
  legibility-only patch; nothing in this workflow promotes a deferred
  capability.
- The workflow 0045 final review (F1–F5) lists no slider-label finding,
  so this is not a re-litigation of a closed concern.

If the implementation lane discovers that an unhidden bare-`cfd_ready`
string, a claim-language change, or a new read model is needed to fix
labels, that finding *would* require a successor RFC. The traceability
review's expectation is that no such promotion is needed and the fix
stays inside view-layer rendering.

## Safe Implementation Boundaries

These are the only paths a label-visibility patch should touch. Anything
outside these boundaries requires a successor RFC or workflow expansion.

### Desktop (matplotlib + PyQt6) — required

Allowed:

- `kayakgen/ui/desktop.py` — `_build_sliders` (lines ~209–228) for label
  position, font size, vertical packing, and adding either matplotlib
  3.7+ `label_location="bottom"` or an inline-with-track placement that
  does not collide with adjacent sliders. The `_build_button`,
  `_build_class_selector`, status, metrics, and station-slider axes
  (lines ~230–291) may have their y-anchors nudged if the slider band
  needs to be relaxed from the current 0.93→0.46 figure range; any such
  change must preserve the RFC 0003 horizontal-clearance invariant
  (controls stay at `x ≤ 0.33`, GridSpec `left=0.38`).
- Optional addition of matplotlib `valtext` font/position cleanup on
  the same Slider widgets if value text now collides with the new label
  position. No content change to the values themselves.
- `kayakgen/ui/theme.py` may grow a single `slider_label_rc_params()`
  helper if a font-size constant must move into the theme to honour
  RFC 0033 §6's "theme module is the only authorised home for hex
  colour literals" — but the existing `matplotlib_rc_params()` already
  exposes `font.size` and `axes.labelsize`, so the cheaper path is a
  fontsize bump in `_build_sliders` without touching theme tokens.

Forbidden:

- No change to slider ranges, defaults, step sizes, class-preset
  seeding, or `_apply_slider_ranges` semantics (those are RFC 0034
  surface).
- No change to `_on_change`, `_on_class_select`, `_on_view_param_change`
  business logic. The handlers must be byte-identical.
- No new PyQt6 widgets, no QMainWindow/QTabWidget migration (RFC 0034
  non-goal).
- No new claim-language or status-bar segment edits (RFC 0033 §5,
  §8).
- No change to `gui.py` shim (already a one-liner re-export).

### Web (Trame + Vuetify3) — verify first, touch only if observably broken

Allowed *if* a Playwright probe shows the `kg-param-slider` labels are
clipped, overlapping the `thumb_label`, or otherwise unreadable at
1440×900 in either light or dark theme:

- `kayakgen/ui/web/app.py` — VSlider props on the rail (lines
  ~956–970). Tightenings limited to `density`, `thumb_label`,
  `tick_size`, and adding a class-only CSS hook on
  `classes="kg-param-slider kg-param-{key}"`. The Vuetify `label=`
  prop content must not change (each slider's label string is part of
  RFC 0033 §2's canonical name set and asserted in
  `tests/test_web_layout.py`).
- `kayakgen/ui/theme.py` may grow a Vuetify slider style snippet
  emitted by `css_root_block(...)` or `vuetify_theme_config(...)` if
  a CSS rule is required. Any new CSS must be sourced from the
  existing theme tokens — no new hex literals. RFC 0033 §6 enforces
  this and `tests/test_ui_theme.py` (per workflow 0044 final review)
  encodes the orphan-literal lint.

Forbidden:

- No edits to the SLIDER_DEFS tuple, PARAMETER_GROUPS, the validity
  badge, or class-preset binding logic. Workflow 0045 is the source
  of truth for those bindings.
- No removal of `thumb_label="always"` without an equivalent
  always-visible value surface (the value is part of the parameter
  rail UX in RFC 0033 §2 "numeric input on hover/focus").
- No new state keys, no controller-layer changes, no read-model
  edits, no Resistance/Mesh/Export wiring changes (RFC 0034 §Proposal
  §3-§5 scope).
- No change to the status-bar segments, validity badge, or
  `evaluation_summary(state)` (RFC 0033 §5, §7).
- No edits to forbidden-copy regression assertions
  (`tests/test_web_layout.py`); they remain authoritative.

### Tests, docs, and changelog — required if code changes

- `tests/` may grow focused legibility checks for whichever surface
  is modified. The ops lane will own the test contract; the
  traceability review's expectation is that those tests assert label
  visibility/non-overlap without re-asserting claim-language or
  introducing brittle pixel-screenshot diffs.
- `docs/USER_GUIDE.md` — at most a one-sentence clarification under
  the workspace section. Must not introduce new capability claims.
- `CHANGELOG.md` — single "Unreleased" entry describing the
  legibility fix; honours the RFC 0033/0034 no-go list.

## Acceptance Checks the Implementation Must Satisfy

These translate the issue and existing RFCs into pass/fail conditions
for the final reviewer. Each maps to an existing RFC anchor; none
introduce new claim language.

1. **Label legibility (RFC 0002 §Acceptance bullet 1).** At 1440×900 and
   1920×1080 default desktop window sizes, every desktop slider in
   `kayakgen/ui/desktop.py` has its label fully readable — no clipping
   by the figure edge, no occlusion by adjacent slider tracks, font
   size readable on a standard DPI display. Same legibility check for
   the web `kg-param-slider` rail VSlider labels at 1440×900 if the
   web surface is touched.
2. **Non-overlap (RFC 0003 §Acceptance bullet 1, RFC 0002 §Goals).**
   No desktop slider label bounding box overlaps the bounding box of
   any other slider track, button, status block, metrics block, class
   radio, or plot axes. Verifiable by `ax.get_position()` /
   text bounding-box comparison without launching the full PyQt event
   loop.
3. **Canonical label content unchanged (RFC 0033 §2).** Every slider's
   label text on both surfaces is exactly the existing canonical
   string (e.g. `Length (m)`, `Beam OA (m)`, `Beam WL (m)`,
   `Draft (m)`, `Deck Height (m)`, `Prismatic Cp`, `Midship Cm`,
   `Deck Flatness`, `Parallel Mid-Body`, `Bow Rake (1=raked)`,
   `Stern Rake (1=raked)`, `Target Speed (kt)`). Web labels remain
   the existing `SLIDER_DEFS` strings; desktop labels remain the
   existing `KayakGUI.SLIDERS` strings. No abbreviations introduced
   to "fit" smaller real estate.
4. **No false capability claims (RFC 0033 §8 forbidden-claim guard,
   RFC 0034 §Acceptance bullet 6).** The fix introduces no new copy
   that could read as a claim. Specifically: no addition of
   `OpenFOAM`, `SU2`, `hosted`, `cloud`, `worker queue`,
   `calibrated drag`, `final prediction`, `design fitness`,
   `GZ_max`, `heel_angle_max_deg`, or bare `cfd_ready` outside the
   four already-documented negations. The existing
   `tests/test_web_layout.py` forbidden-copy assertions continue to
   pass unchanged.
5. **No regression to RFC 0034 dynamic bindings.** Class-preset
   reseed, narrowed slider bounds, manual-edit `custom` flip, the
   validity badge string set, target-speed view-only handling, the
   Resistance card sweep, the Mesh tab diagnostics, and the Export
   menu honest disabled states all behave exactly as before the
   patch. Specifically the `_apply_slider_bounds`,
   `_on_hull_param_change`, `_on_view_param_change`, and
   `_applying_class_preset` guard semantics in
   `kayakgen/ui/web/app.py` are unchanged.
6. **No regression to RFC 0002 §3–§7 desktop affordances.** The
   debounced 3D update, "Opening…" loading state, PyVista window
   title linkage, derived-metrics text (now sourced from
   `evaluate_hydrostatics`), arrow-key nudge, and STL filename
   dialog continue to work. Verifiable by smoke-running the desktop
   GUI in CI-safe fashion (matplotlib `Agg` backend test harness)
   or by reading the existing test_desktop assertions if present.
7. **Theme discipline (RFC 0033 §6 §Acceptance bullet 7).** Any new
   colour or size literal lives in `kayakgen/ui/theme.py`. The
   orphan-colour-literal lint (`tests/test_ui_theme.py`) continues
   to pass.
8. **Workflow scope discipline (RFC 0034 §Non-Goals, workflow 0046
   OPERATOR_REPORT.md).** No edit lands outside `gui.py`,
   `kayakgen/ui/`, `tests/`, `docs/USER_GUIDE.md`, `CHANGELOG.md`,
   and the workflow-local `striatum/0046-slider-label-visibility/`
   tree. No promotion of any RFC 0033/0034 deferred capability.

## Open Traceability Questions For The Ledger

These are not blockers — they are notes the findings ledger should
resolve before implementation begins.

- **Surface scope.** Did the user report originate from the desktop
  matplotlib GUI, the web Trame UI, or both? The ergonomics-design
  and ops lanes should produce visual evidence so the implementation
  lane does not touch a surface that does not actually exhibit the
  bug. If only one surface is affected, the other must not be
  edited.
- **Desktop fix shape.** RFC 0002 §Proposal §1 explicitly recommended
  matplotlib `label_location="bottom"`; the current code instead uses
  `set_position((0.5, -1.8))`. The ledger should decide whether to
  adopt the original RFC 0002 recommendation (cleanest), increase
  vertical pitch between sliders by relaxing the 0.93→0.46 band, or
  use both. Either is in-scope; the choice is an ergonomics decision.
- **Numeric value visibility.** matplotlib `Slider` exposes
  `s.valtext`. If the chosen layout pushes labels into the
  `valtext` region, the ledger should specify whether to relocate or
  hide `valtext` and how that interacts with RFC 0033 §2's
  "numeric input on hover/focus" expectation.
- **`thumb_label="always"` on the web rail.** If the web surface is
  affected, the ergonomics lane should confirm whether the always-on
  Vuetify thumb label is clashing with the slider's static label at
  compact density. The fix may be a CSS rule on `.kg-param-slider`
  rather than dropping `thumb_label="always"`.

## Verdict Intent

Verdict intent: accept
