---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Review — Slider Label Ergonomics And Visual Design (Workflow 0046)

## Verdict Intent

`accept_with_findings`

The user-reported failure mode — slider labels not being legible — reproduces
on inspection of `kayakgen/ui/desktop.py:209-228` and
`kayakgen/ui/web/app.py:956-970`. On both surfaces the shipped widget structure
(matplotlib `Slider` rows on desktop; Vuetify `VSlider` rows in the rail
drawer on web) is fundamentally sound and consistent with the RFC 0033 / RFC
0034 workspace shell. The visibility problem is local to four specific
properties — label font size, vertical label placement, the matplotlib value
text, and the persistent `thumb_label` overlap — and can be repaired without
re-laying out the parameter rail, changing the slider widget family,
introducing new color tokens, or expanding any read-model contract.

This review identifies the narrowest set of changes that restores legibility,
preserves the existing RFC 0033 visual system, and keeps the workflow 0044
final-review acceptance (preset reseed, validity badge, claim chips,
forbidden copy) intact.

## Reproduction Surface (read from current code)

Desktop slider construction in `kayakgen/ui/desktop.py`:

- Twelve sliders (`SLIDERS`, lines 63-76) are stacked in the 0.07-0.33
  horizontal band between `top_start=0.93` and `bot_end=0.46`
  (`_build_sliders`, lines 209-228), giving per-row vertical step
  `(0.93 - 0.46) / 12 ≈ 0.0392` in figure coordinates.
- Each `Slider` axes is `0.018` tall (`add_axes([0.07, y, 0.26, 0.018])`),
  leaving a ~0.021-fig-coord gap between adjacent slider tracks.
- The label is explicitly displaced below the track by
  `s.label.set_position((0.5, -1.8))` in axes-relative units, i.e.
  `1.8 × 0.018 = 0.0324` figure-coord units below the track's bottom edge.
  That places the label centre roughly `0.0392 − 0.0324 = 0.0068` fig-coord
  units (~6 px at a 900 px figure height) above the next slider's track,
  well inside the 6.5 pt glyph height (~8.5 px) being drawn there.
- The label font is set to 6.5 pt (`s.label.set_fontsize(6.5)`). The matplotlib
  `Slider.valtext` (the right-hand value indicator) is left at the
  matplotlib default of ~10 pt — taller than the label, taller than the
  axes, and prone to clipping the slider beneath it for long values such as
  the formatted `Bow Rake (1=raked)` or `Target Speed (kt)` numbers.
- The same scaling problem repeats for the class radio (font 7), status
  block (font 6.2), and metrics block (font 7.5) immediately under the
  sliders (`_build_button`, lines 230-284), so any whitespace freed up by
  fixing the slider labels does not collide with neighbouring widgets.

Web slider construction in `kayakgen/ui/web/app.py`:

- The Parameters drawer is fixed at `360 px` (line 939) and renders one
  `VSlider` per hull field within three labelled groups
  (`PARAMETER_GROUPS`, lines 82-92).
- Each slider is built with `thumb_label="always"`, `density="compact"`,
  `classes=f"kg-param-slider kg-param-{key} mt-2"`, and an `aria-label`
  equal to the human label (lines 956-970).
- `density="compact"` puts the label and value in close vertical proximity
  to the track; `thumb_label="always"` lifts a tooltip-shaped value bubble
  above each thumb that sits exactly in the `mt-2` vertical gutter between
  slider rows. With twelve sliders stacked, the persistent thumb bubble
  visually fuses with the row above when the thumb is anywhere near the
  centre of its range — particularly painful for long labels such as
  `Parallel Mid-Body`, `Deck Flatness`, and `Bow Rake (1=raked)`.
- The shared `theme.TYPOGRAPHY["type-label"]` token (`kayakgen/ui/theme.py:147-153`)
  already defines a `0.78rem / 1.25` slider-appropriate label style, but it
  is not applied via the `kg-param-slider` class today — Vuetify uses its
  default label sizing.

## Findings (Severity-Ordered)

### E1 — High: Desktop slider labels collide with the next slider row

`s.label.set_position((0.5, -1.8))` on every Slider in `_build_sliders`
(`kayakgen/ui/desktop.py:225`) places the label `1.8 × axis-height` below
each track. Given the `0.018` axes height and the `0.0392` row pitch, the
label centre lands ~6 px above the next track at the canonical 16×9 figure
size — and inside the next track at narrower window heights. This is the
mechanical root cause of the user-reported "labels not visible" complaint
on desktop: labels overlap or sit behind the next slider's handle.

How to apply: drop the manual `set_position`/`set_horizontalalignment`
pair and pass `label_location="bottom"` to `widgets.Slider(...)` instead
(matplotlib ≥3.7 supports this; the project pins `matplotlib>=3.8` per
`pyproject.toml`). matplotlib then places the label one text-height below
the track with no manual offset — for a 6.5 pt label that is ~3 px below
the bottom edge, well inside the existing 21 px inter-slider gap. Keep
the existing `valstep` for `Cm`, the `valinit` from `self.params`, and
the post-construction `s.on_changed(...)` wiring untouched. This is a
two-line change per slider plus a one-line removal.

Source: `kayakgen/ui/desktop.py:209-228`; matplotlib `Slider` API; RFC
0002 §Proposal 1 (already calls out `label_location="bottom"` as the
recommended remedy for the original clipping issue).

### E2 — High: Desktop slider value text (`valtext`) is unstyled and clips into the next row

`Slider.valtext` is left at the matplotlib default font size (~10 pt) and
draws to the right of the track at axes-relative `(1.02, 0.5)`. For value
strings such as `0.550` (Cp), `0.85` (Cm), or `3.5` (target speed) at
10 pt this comfortably exceeds the 0.018-tall axes box and bleeds into
the row below — especially when E1 still has the prior row's *label*
displaced into that gap.

How to apply: after constructing each slider, also call
`s.valtext.set_fontsize(7.5)` to match the corrected label (E3) and add
`s.valtext.set_horizontalalignment("right")` so multi-digit values do not
push past the right edge of the rail (the rail right edge is at
`x ≈ 0.33`; the next region starts at `x = 0.38`). Keep the default
right-of-track position — moving the value text adds risk and the
default is what RFC 0002 acceptance was written against. One added line
per slider; no widget-family change.

Source: `kayakgen/ui/desktop.py:209-228`; matplotlib `Slider.valtext`
default behaviour.

### E3 — High: Desktop slider label font is below readable size

6.5 pt at 96 DPI renders at ~8.5 px tall, which is below the 12 px floor
RFC 0033 §Acceptance implies for body text and is the secondary driver of
the legibility complaint. Once E1 stops the label from sitting on top of
the next track, raising the font from 6.5 pt to 7.5 pt (matching
`type-label`'s 0.78 rem at 16 px = ~10 px height) restores legibility
without overflowing horizontally — the longest label is `Bow Rake
(1=raked)` at 18 characters; at 7.5 pt monospace-equivalent in the Inter
Tight stack that is ~110 px wide, well inside the 0.26-fig-coord (≈250
px) rail width.

How to apply: change `s.label.set_fontsize(6.5)` to
`s.label.set_fontsize(7.5)` in `_build_sliders`. Keep the class-radio
font at 7 pt (the labels there are short class names) and the metrics
font at 7.5 pt (it is already readable). The status block at 6.2 pt is
out of this workflow's scope — it is a multi-line monospace cluster, not
a slider label.

Source: `kayakgen/ui/desktop.py:224`; `kayakgen/ui/theme.py:147-153`
(`type-label` token as the shared anchor).

### E4 — High: Web `thumb_label="always"` visually overlaps the row above

The Vuetify persistent thumb tooltip is positioned ~10–14 px above the
thumb. With twelve `density="compact"` sliders in a fixed 360 px drawer
and a `mt-2` (8 px) row gutter, the bubble for slider N sits at the
baseline of slider N-1's label whenever its thumb is near the visible
centre. This is the dominant ergonomics complaint on the web surface:
the bubble obscures the label of the parameter immediately above.

How to apply: drop `thumb_label="always"` and replace with
`thumb_label=True` (Vuetify default: bubble appears only while the thumb
is being dragged or focused). The value remains visible whenever the
user is actually interacting with the control, and the rail recovers
its persistent vertical rhythm at rest. If a permanently visible numeric
value is judged essential, render it as an inline append slot using
Vuetify's `append` slot or a small `<span class="kg-param-value">` to
the right of the label — but the simpler, narrower fix is to remove the
`always` modifier.

Source: `kayakgen/ui/web/app.py:962`; Vuetify 3 VSlider `thumb-label`
prop semantics. Note that the existing browser acceptance
(`tests/test_web_browser.py:314-388`) reads slider state via
`aria-valuenow`, not via the thumb bubble, so the `always` → `True`
change does not regress any assertion.

### E5 — Medium: Web slider label typography should pin to `type-label` and the row gutter should grow with the value bubble removed

With `thumb_label="always"` gone (E4) the row gutter can — and should —
be tightened just a little so the rail still fits twelve sliders without
scrolling at 1280×900 (the viewport used by
`tests/test_web_browser.py:328`). Today `mt-2` is 8 px; with the bubble
gone, the visible header-to-track distance shrinks and `mt-3` (12 px) is
the right resting state to keep the label, track, and ticks visually
grouped per slider. Pair this with applying `var(--type-label)` to the
slider label so the rail uses the shared `0.78rem / 1.25` token rather
than the Vuetify default — that is the established label voice across
the workspace.

How to apply: change `classes=f"kg-param-slider kg-param-{key} mt-2"` to
`classes=f"kg-param-slider kg-param-{key} mt-3"`. Add a single CSS rule
(injected via the existing `theme.css_root_block` path or a small static
stylesheet — whichever the implementation slice chooses without expanding
scope) of the form `.kg-param-slider .v-slider__label { font: var(--type-label); color: var(--text-secondary); }`.
No new color tokens. No new CSS hooks.

Source: `kayakgen/ui/web/app.py:956-970`; `kayakgen/ui/theme.py:140-153,372-381`;
RFC 0033 §2 parameter rail definition.

### E6 — Medium: Long label strings need a single horizontal-overflow strategy on web

`Bow Rake (1=raked)`, `Parallel Mid-Body`, `Target Speed (kt)`, and
`Prismatic Cp` are the four labels that approach the rail's text budget.
At 360 px drawer width minus Vuetify's default 16 px inner padding minus
the slider track minimum, the label column has ~200 px of usable space.
Today the label can wrap to two lines on narrow widths because Vuetify
allows that by default, and a two-line label re-introduces the same
overlap with the row above that E4 fixes.

How to apply: enforce single-line label rendering with ellipsis on
overflow via the same CSS rule introduced for E5:
`.kg-param-slider .v-slider__label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`.
Tooltips are not required — every label is also exposed via
`aria-label` (already wired at line 968), so screen-reader users get
the full string and sighted users see the canonical short form. Do not
abbreviate the source strings themselves; the labels are referenced by
test text matching (e.g. `Length (m)`,
`tests/test_web_browser.py:333`) and by the workflow 0044 forbidden-copy
contract.

Source: `kayakgen/ui/web/app.py:67-80,956-970`;
`tests/test_web_browser.py:333`.

### E7 — Medium: Contrast — keep both surfaces inside `text-secondary` on `surface-panel`/`surface-rail`

`kayakgen/ui/theme.CONTRAST_MANIFEST` (`kayakgen/ui/theme.py:337-351`)
already asserts ≥4.5:1 for `text.secondary` on `surface-bg` and
`text.muted.panel` on `surface-panel`. The desktop slider label inherits
the default matplotlib axes label colour, which after
`theme.matplotlib_rc_params()` resolves to `text-secondary` (`#43524d`
light / `#becac4` dark) on `surface-bg`. That meets the 4.5:1 floor and
should stay as-is — the legibility regression is not a contrast bug, it
is a size/placement bug. On web, the same `text-secondary` token should
be the explicit label colour via the CSS rule introduced for E5, so the
implementation does not accidentally inherit a higher-contrast
`text-primary` (which would steal visual weight from the metrics strip
and the validity badge) or a lower-contrast Vuetify "medium-emphasis"
opacity that drops below 4.5:1.

How to apply: include `color: var(--text-secondary);` in the CSS rule
from E5. Do not introduce a new token; do not change matplotlib
`axes.labelcolor` (which the metrics already depend on).

Source: `kayakgen/ui/theme.py:337-351,423-447`;
`kayakgen/ui/web/app.py:956-970`.

### E8 — Low: Keyboard focus affordance on the desktop slider should stay readable too

The desktop already wires arrow-key nudge through `_on_key`
(`kayakgen/ui/desktop.py:428-434`) and tracks the most-recently-touched
slider in `_track_slider`. That is sufficient — RFC 0002 §Acceptance is
met. The only adjacent ergonomics note is that when E1 + E3 land, the
focused slider's label needs to remain visually distinct on hover/focus
so the user can confirm which row they are nudging. matplotlib does not
draw a focus ring on `Slider`, so the existing track recolouring on
hover is what users have. Do not invent a focus ring — that is a
desktop-wide change and out of scope for label visibility.

How to apply: no code change. Document in the user guide (within the
implementer's scope, not this review's) that arrow-key nudge follows
the most recently moved slider and the label colour does not change on
focus. Web keyboard focus is handled by Vuetify defaults — `VSlider`
already renders a focus ring on `:focus-visible` from the framework CSS,
and the existing `aria-label` per slider remains correct.

Source: `kayakgen/ui/desktop.py:428-434`; Vuetify 3 `VSlider`
keyboard/focus defaults.

## Responsive Behaviour

- **Desktop, single matplotlib figure:** the GridSpec uses
  `left=0.38, right=0.97` (`kayakgen/ui/desktop.py:112-122`) which leaves
  the leftmost 0.38 fig-coord (~38 % of the 16-inch figure) for the rail.
  At the canonical 16×9 default and at the smallest practical
  matplotlib window (1024×768) the 0.07-0.33 slider band stays inside the
  drawable area, so E1's `label_location="bottom"` fix needs no
  GridSpec change. Do not widen the rail; the geometry pane already
  shrinks to its minimum at smaller windows.
- **Web, drawer fixed at 360 px:** the existing
  `RESPONSIVE_CLASS_HOOKS` (`kayakgen/ui/web/app.py:189-198`) cover the
  rail collapse-to-accordion under 960 px via `kg-collapse-under-960`.
  E5 + E6 keep label rendering identical between the side-drawer and
  the top-accordion forms, since `white-space: nowrap` + ellipsis works
  the same in either layout. No new hook is required.
- **Narrow desktop window (e.g. 1280×720):** with E1's bottom-placed
  label, twelve sliders at the 0.0392 row pitch still fit cleanly. If a
  user resizes vertically below ~600 px the rail compresses to the
  matplotlib default, and labels will collide again — but that is the
  pre-existing behaviour, not a regression introduced by this fix.
  Recommend documenting a minimum desktop window height of 720 px in the
  user guide (already implied by RFC 0033's "1440×900" anchor).

## Accessibility Considerations Specific To This Slice

- The `aria-label` already populated per web slider
  (`kayakgen/ui/web/app.py:968`) must remain identical to the visible
  label so screen-reader announcements match what sighted users see.
  Ellipsis truncation (E6) is a visual-only fold; the aria string is
  the full text. Verify no implementation step changes the
  `aria-label` to the ellipsised form.
- The validity badge below the sliders already carries
  `role="status"` and `aria-live="polite"` (lines 977-980). Nothing
  in this slice should change that — the badge is the rail's anchor
  for "did my changes leave the class envelope" feedback, and label
  legibility fixes do not touch it.
- The matplotlib desktop has no role/aria layer; keyboard nudge
  (`_on_key`) is the only assistive affordance. This slice does not
  add one — that would be a larger refactor — and the user-reported
  problem is visual, not assistive.

## Acceptance Refinements (Narrow)

These tighten the workflow 0046 implementation slice without expanding
scope:

1. **Desktop label placement:** every entry in `SLIDERS` is constructed
   with `label_location="bottom"` and no `set_position(...)` override.
   The line `s.label.set_position((0.5, -1.8))` must be deleted, not
   replaced with a smaller offset — partial offsets are how this
   regression entered.
2. **Desktop font sizing:** `s.label.set_fontsize(7.5)` and
   `s.valtext.set_fontsize(7.5)` for every slider. The class radio
   stays at 7 pt; the metrics block stays at 7.5 pt; the status block
   stays at 6.2 pt (out of scope).
3. **Web persistent value bubble:** `thumb_label` is `True` (not
   `"always"`) on every `VSlider` in the parameter rail. The station
   slider, if it gains a `thumb_label`, must follow the same rule.
4. **Web label typography:** a single CSS rule scoped to
   `.kg-param-slider .v-slider__label` sets `font: var(--type-label);
   color: var(--text-secondary); white-space: nowrap; overflow:
   hidden; text-overflow: ellipsis;`. The rule lives next to the
   existing `theme.css_root_block(...)` injection path so no new asset
   pipeline appears.
5. **Row gutter:** the rail uses `mt-3` per slider after `thumb_label`
   becomes hover/focus-only. No other Vuetify density change.
6. **No new tokens or hooks:** the implementation does not introduce
   new entries in `COLORS_LIGHT`, `COLORS_DARK`, `TYPOGRAPHY`,
   `RESPONSIVE_CLASS_HOOKS`, or `LAYOUT_TEST_IDS`.

## Out Of Scope (Explicit)

- A focus ring on the desktop matplotlib slider.
- Replacing `widgets.Slider` with a Qt-native slider widget.
- Adding tooltips on hover for web slider values.
- Re-ordering, re-grouping, or renaming the twelve hull parameter
  sliders.
- Touching the station slider at the bottom of the geometry pane
  beyond the same `label_location="bottom"` correctness fix if it
  reuses the same `widgets.Slider` construction path.
- High-angle GZ, hosted CFD, calibrated drag, or any of the deferred
  RFC 0033 follow-ups.
- Redesigning the metrics or status panels.

## Concrete Source References

- Desktop slider build — `kayakgen/ui/desktop.py:63-76` (slider table),
  `:209-228` (`_build_sliders`), `:230-291` (`_build_button` neighbours),
  `:428-434` (`_on_key`).
- Web slider build — `kayakgen/ui/web/app.py:67-92` (`SLIDER_DEFS`,
  `PARAMETER_GROUPS`), `:938-982` (drawer/rail), `:956-970` (`VSlider`
  call site).
- Shared theme — `kayakgen/ui/theme.py:16-137` (color tokens),
  `:140-153` (`TYPOGRAPHY`, `type-label`),
  `:337-351` (`CONTRAST_MANIFEST`), `:372-381` (`css_root_block`),
  `:423-447` (matplotlib rcParams).
- RFC packet — `docs/rfcs/0002-gui-usability.md` (original "labels not
  visible" goal and `label_location="bottom"` remedy),
  `docs/rfcs/0033-workspace-ui-rework.md` §2 (parameter rail),
  `docs/rfcs/0034-workspace-ui-follow-up.md` §Acceptance.
- Prior context — `striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md`
  (workflow 0044/0045 verdict, no slider-label regression flagged →
  this is a post-land legibility complaint, not a re-litigation).
- Tests touching slider DOM — `tests/test_web_browser.py:314-388`
  (slider locator via `.kg-param-{key} [role='slider']`, `aria-valuenow`,
  `aria-valuemin`, `aria-valuemax`). `tests/test_web_layout.py:181-218`
  (preset reseed and bound assertions).
- User guide — `docs/USER_GUIDE.md` (rail and slider sections).

## Commands And Checks Run

- File reads on `kayakgen/ui/desktop.py`, `kayakgen/ui/web/app.py`,
  `kayakgen/ui/theme.py`, `kayakgen/ui/gui_params.py`,
  `kayakgen/ui/web/state.py` (skimmed), `tests/test_web_layout.py`,
  `tests/test_web_browser.py`,
  `docs/rfcs/0002-gui-usability.md`,
  `docs/rfcs/0033-workspace-ui-rework.md`,
  `docs/rfcs/0034-workspace-ui-follow-up.md`,
  `docs/workflows/0046-slider-label-visibility/{RUNBOOK,OPERATOR_REPORT,SOURCES,workflow}.{md,json}`,
  `docs/workflows/0046-slider-label-visibility/prompts/review_ergonomics_design.md`,
  `docs/workflows/0046-slider-label-visibility/roles/reviewer_ergonomics_design.md`,
  `striatum/0045-workspace-ui-follow-up/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`,
  `striatum/0045-workspace-ui-follow-up/final/FINAL_REVIEW.md` (partial).
- Source-level inspection of the slider geometry: per-row pitch
  `(0.93 - 0.46) / 12 ≈ 0.0392`, axes height `0.018`, label offset
  `1.8 × 0.018 = 0.0324`, residual `0.0068` fig-coord = ~6 px overlap
  budget at the canonical 9-inch / 900-pixel figure height — i.e.
  smaller than the rendered 6.5 pt glyph.
- Grep for `kg-param-slider`, `VSlider`, `thumb_label`, `label.set_`,
  `valtext`, and `valfmt` confirmed the four constructor sites
  identified above are the only renderers of slider labels in the
  project.
- Cross-checked `matplotlib>=3.8` pin in `pyproject.toml`, so
  `label_location="bottom"` (matplotlib ≥3.7) is available.
- No product code, tests, docs, `.striatum`, or Striatum mutation
  commands were touched. No commit, branch, or push occurred. No
  byline was added.

## Sub-Agent And Parallel Helper Use

This pass used direct file reads with independent reads run in
parallel where targets did not depend on each other. The surface
(two implementation files, one theme file, two RFCs, one user guide,
two layout tests, one browser test, the workflow packet, and one prior
ergonomics review) fits inside the main session, and the slider
geometry argument requires a single coherent thread — splitting it
across sub-agents would risk inconsistent dimensional analysis. No
helper sub-agents were spawned.
