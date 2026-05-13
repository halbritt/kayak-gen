Verdict intent: accept_with_findings

## Reviewed scope

- `docs/rfcs/0033-workspace-ui-rework.md` (canonical, per
  `docs/workflows/0044-workspace-ui-rework/SOURCES.md`).
- Workflow scaffold: `roles/reviewer_ergonomics_design.md`,
  `prompts/review_ergonomics_design.md`, `SOURCES.md`, and the
  remediation packet at
  `striatum/0044-workspace-ui-rework/review_remediation/REMEDIATION.md`.
- Companion product context: `AGENTS.md`, `docs/PRD.md`,
  `docs/USER_GUIDE.md`, `docs/rfcs/0008-web-frontend.md`,
  `CLAUDE_DESIGN_UI_REWORK_PROMPT.md`.
- Current UI surfaces consulted for integration risk only:
  `kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`,
  `kayakgen/ui/desktop.py`, `kayakgen/ui/gui_params.py`,
  `kayakgen/model/advisory.py`.

The review evaluates whether RFC 0033 plus the workflow scaffold give
implementers enough ergonomics specification to ship a dense, operational
kayak-design workspace without re-deriving intent from the unstored Claude
Design handoff bundle.

## Sub-agent / parallel assistance used

No additional subagents were spawned for this lane. Reading load fit in
the main role and parallelism was applied at the tool-call layer:
required-context files were batched into parallel `Read` calls, and the
ergonomics check was decomposed into four disjoint inspection passes
that were merged into a single findings list:

1. **Scan path / parameter rail grouping** against RFC 0033 §1–§2 and
   `kayakgen/ui/web/app.py` `SLIDER_DEFS`.
2. **Per-tab state coverage and chip language** against RFC 0033 §4 and
   `kayakgen/ui/web/controllers.py` view-model helpers.
3. **Responsive collapse, status bar, and toolbar interaction**
   against RFC 0033 §1 and §5.
4. **Desktop/web conceptual parity and keyboard/focus surface** against
   RFC 0033 §3, §6 and the current `kayakgen/ui/desktop.py` matplotlib
   widget topology.

The four passes were planned to be delegable to disjoint helpers; the
findings below preserve the same partitioning so the ledger can split
remediation across tracks.

## Findings

RFC 0033 is structurally complete enough to land a useful first slice.
The layout regions, tab order, persistent claim copy, status-bar
segments, and forbidden-string guard are concrete and testable. The
gaps that follow are ergonomics-grade implementation findings, not
RFC blockers; none require the workflow to return to
`review_remediation`.

### F1 — Parameter rail lacks group structure for a 12-row stack

RFC 0033 §2 lists every rail control in one flat order: a class
preset radio, twelve sliders (`length_m … target_speed_kt`), a
validity badge, plus advisory dots, numeric inputs, and class-envelope
ticks per row. The current web `SLIDER_DEFS` already shows this density
risk (`kayakgen/ui/web/app.py:54-67`). At rail width ≈320 px and a
target slider density of 12 rows, a flat list is high cognitive load
and forces vertical scroll to reach `bow_rake` / `stern_rake` /
`target_speed_kt`. The RFC does not specify subheadings, dividers, or
collapsible groups. Implementers will guess.

Suggested ledger entry: define three labelled subgroups — *Principal
dimensions* (`length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`,
`deck_height_m`), *Shape coefficients* (`Cp`, `Cm`, `deck_flatness`,
`center_box_ratio`), *Ends and view* (`bow_rake`, `stern_rake`,
`target_speed_kt`) — with the class preset above the first group and
the validity badge pinned at the bottom of the rail (not scrolled
with the slider list).

### F2 — No keyboard/focus specification

RFC 0033 does not mention keyboard navigation, focus order, focus
rings, or shortcut keys anywhere. The current desktop GUI has
arrow-key delta support on the last-touched slider
(`kayakgen/ui/desktop.py:371-377`); the web Trame surface relies on
Vuetify defaults. For a dense operational tool, that is too thin:
no defined Tab order across rail → toolbar → metrics strip → review
tabs → status bar, no defined behavior for advisory-dot focus, no
documented arrow/PgUp/PgDn slider delta, and no shortcut for jumping
between Review tabs or focusing the share toast.

Suggested ledger entry: specify (1) a single deterministic Tab order
that crosses regions in scan order, (2) arrow-key delta = 1% of
slider span, PgUp/PgDn = 10%, Home/End = min/max, (3) visible
2-px focus ring sourced from the theme token, (4) Esc closes any
expanded numeric input or chip popover. Add at least one
`tests/test_web_layout.py` assertion that the rail's first slider is
focusable and that arrow keys mutate its value.

### F3 — Responsive collapse is one breakpoint and leaves the geometry pane underspecified

RFC 0033 §1 specifies one breakpoint: "Below 960 px, Parameters
becomes a top accordion and the Review pane becomes the body." It
does not say what happens to the Geometry pane at <960 px, whether
the Metrics strip wraps or scrolls horizontally, whether the
toolbar's Export ▾ collapses into a kebab, or whether the four
Status-bar segments wrap to a second line. Because the
metrics-strip tokens are click targets (RFC 0033 §3) the wrap
behavior is load-bearing.

Suggested ledger entry: define <960 px behavior for the geometry
pane (collapsed accordion above Review, default-collapsed; 3D
viewport keeps a minimum 320 px square or hides behind an "Open
3D" button), the metrics strip (horizontal scroll inside its row,
not wrap, so token clickability survives), and the status bar
(stacks to two lines with a fixed 32 px tap target). Add a
≥ 320 px viewport assertion in the layout test alongside the
1440×900 first-viewport assertion.

### F4 — Desktop "three-region shell" sits awkwardly on matplotlib widgets

RFC 0033 §1 frames a three-region shell as common to both
surfaces; §3 says desktop "embeds the existing `pv_window.PyVistaWindow`
into the main window via `QDockWidget`"; §6 step 6 directs
`kayakgen/ui/desktop.py` to keep matplotlib but add a Cm slider, theme
plot palette, embed PyVista, and add a four-segment status bar. The
current desktop is a single `plt.figure` with sliders, plots, status
text, and metrics packed into a `GridSpec` (`kayakgen/ui/desktop.py:79-234`).
Adding the structured Review tabs, advisory dots, class-envelope
ticks, validity badge, and four click-targeted status segments inside
a matplotlib figure is not really feasible at the densities §2 and §4
ask for; matplotlib widgets do not give true focus rings, do not tab
between controls, and cannot host Vuetify-like chips or
hover-revealed numeric inputs.

Suggested ledger entry: either (a) explicitly accept a reduced
desktop slice (rail and validity badge in matplotlib widgets, three
embedded plots as today, single-line status text, no Review tab
structure) and capture the parity deferral in the RFC's Open
Questions, or (b) plan a desktop rewrite to a thin `QMainWindow`
with a `QDockWidget` rail + `QTabWidget` Review pane in this same
slice. The ledger should not let the implementer silently invent
either; it should pick a lane and note the parity gap.

### F5 — Disabled, empty, and loading states are partial for the Review tabs

RFC 0033 §2 enumerates rail states well (default, loading shared URL,
invalid hull state, disabled Cm) but §4 only spells out states for the
Mesh `watertight-solid` profile (disabled with the exact tooltip).
Missing:

- **Mesh → Build package**: when no hull is valid, when a build is in
  flight (the RFC §9 Open Question leans synchronous-with-spinner but
  that isn't promoted to a spec line), when the last build failed.
- **Comparison**: empty state (no JSON loaded — copy is in
  `controllers.comparison_view_model_from_json`), file-drop accepted
  types, malformed-JSON error copy, pinned-strip empty state.
- **CFD**: Prepare/Run/Refresh/Logs/Raw Result enablement matrix
  (today the controllers raise on every error path; the rework should
  disable buttons in unreachable states instead of relying on toast
  errors), and the empty `cfd_status_lines` state once a fresh tab is
  opened.
- **Advisories**: empty state when zero advisories exist, count badge
  on the tab itself.

Suggested ledger entry: produce a per-tab state matrix (default /
empty / loading / disabled / error / terminal) with exact copy and
button enablement. Use it as the source for `tests/test_web_layout.py`
assertions.

### F6 — Resistance table off-set handling for non-canonical target speeds

RFC 0033 §4 fixes the sweep speeds at `[2.0, 3.0, 4.0, 5.0, 6.0] kt`
with "the target-speed row highlighted with `--state-focus-row`."
The hull state's `target_speed_kt` is continuous (slider step 0.1) and
will almost never coincide with the fixed table speeds, so the
highlight rule is ambiguous. The RFC does not say whether to insert
an extra interpolated row, snap-highlight the closest row, or render
the target speed as a separate ribbon above the table. The current
`metrics_from_state` already emits a single at-target row alongside
the swept curve (`controllers.metrics_from_state`); the RFC needs to
pick one of those treatments.

Suggested ledger entry: insert a sixth row at `target_speed_kt` (only
when it falls outside ±0.05 kt of an existing row), keep the row
sorted by speed, and apply `--state-focus-row` to that inserted row.
Capture this in a unit test against the resistance view model.

### F7 — Advisory-dot interaction and chip semantics under-specified

RFC 0033 §2 says each rail row "carries an advisory dot (yellow)
when at least one structured advisory cites that field" and §4
(Advisories tab) says "clickable field-name chips that focus the
relevant slider in the rail." Three loose ends:

1. Dot placement (label-side vs value-side), keyboard focusability,
   and tooltip on hover/focus.
2. Mutual navigation: chip → rail focus + scroll + (if the rail is
   collapsed in responsive layout) expand the accordion. RFC is
   silent on the expand step.
3. Severity: the §6 §7 contract reserves orange for
   "unavailable / raw / uncalibrated" — but the advisory dot is
   yellow. Two near-identical warm colours one click apart is a
   readability risk if the theme palette isn't carefully separated.

Suggested ledger entry: position the dot left of the slider label,
make it part of the row's Tab stop with a tooltip listing advisory
codes, define the chip → rail handoff to include accordion-expand,
and assert in `tests/test_ui_theme.py` that the advisory-yellow and
unavailable-orange tokens meet a minimum perceptual delta (e.g.
ΔE ≥ 20 in CIELAB) so they are not confusable for users with
mild colour-vision deficiency.

### F8 — Status-bar click target affordance and toolbar overflow not specified

RFC 0033 §5 lists four middot-separated segments and says each is
clickable to focus the matching Review tab, but does not specify
minimum tap-target (24 px is the rough WCAG floor), hover/focus
treatment, or whether a segment should also expose the underlying
read-model number on hover (e.g. resistance claim chip hover →
"uncalibrated_comparative"). The Toolbar's Export ▾ has five items
on web but no spec for the narrow-viewport collapse path or
keyboard behavior of the menu.

Suggested ledger entry: status-bar segments are buttons with a
32 px min height, persistent focus ring, and an `aria-label` that
expands the chip token to its full claim word. Toolbar Export ▾
collapses into a single icon-button kebab below 1200 px with the
same items.

### F9 — Theme palette tokens enumerated, contrast not asserted

RFC 0033 §6 enumerates token *roles* (`--surface-viewport-bg`,
`--data-hull`, `--data-deck`, `--state-focus-rail`,
`--state-delta-pos/neg`, `--state-focus-row`) and forbids one-note
palettes (no dominant purple, beige/tan, slate/blue, brown/orange)
per `CLAUDE_DESIGN_UI_REWORK_PROMPT.md`. The acceptance criteria
enforce that all hex literals live in `kayakgen/ui/theme.py` but do
not enforce contrast. For a dense operational tool the contrast
floor is load-bearing: chips on top of the metrics strip, focus
rings on top of slider tracks, and the orange "raw / uncalibrated"
chip on the light surface all need to clear WCAG AA at minimum.

Suggested ledger entry: add a `tests/test_ui_theme.py` assertion that
every (foreground, background) pair listed in a theme-token
contrast manifest passes WCAG AA (`≥ 4.5:1` for text under 18 pt;
`≥ 3:1` for the focus ring and large chip text) for both light
and dark variants.

### F10 — Scan order inside the first viewport is implied, not stated

RFC 0033 §1 enumerates what must appear in the first 1440×900
viewport (rail, viewport, metrics strip, first Review tab, status
bar) but not the *order* the user is supposed to read them, nor the
typographic hierarchy that drives it. A dense engineering tool needs
an explicit scan path so implementers do not equalise typographic
weight across regions and dilute the entry point. The handoff prompt
in `CLAUDE_DESIGN_UI_REWORK_PROMPT.md` is explicit about
"dense but readable information hierarchy" and "operational
engineering tool, not a marketing page", so this is a real
implementation risk if left unspecified.

Suggested ledger entry: name the canonical scan as Toolbar
breadcrumb → Parameters rail (class + first slider) → Geometry pane
(3D viewport, then metrics strip) → Review pane (active tab card
header) → Status bar. Tie that order to a single, named type ramp
in `theme.py` (`--type-display`, `--type-heading`, `--type-body`,
`--type-mono`) so weight reinforces order.

## Required actions

These are flagged for the ledger to triage into the implementation
slice. None of them blocks RFC 0033 from leaving review.

1. Add per-tab and per-rail **state matrices** (default / empty /
   loading / disabled / error / terminal) with exact copy, button
   enablement, and chip behavior. Source for new
   `tests/test_web_layout.py` assertions. (F5, F7, F8)
2. Add a **keyboard/focus specification** covering Tab order across
   regions, slider key deltas, focus-ring token, and at least one
   browser-acceptance assertion. (F2)
3. Promote the **rail grouping** decision out of implementer
   discretion: three subgroups with the class preset above and the
   validity badge pinned. (F1)
4. Resolve the **desktop parity** ambiguity in the ledger: either
   accept a reduced matplotlib slice with named parity gaps or
   commit to a `QMainWindow` rewrite in this workflow. (F4)
5. Define **responsive behavior** for the geometry pane, metrics
   strip, status bar, and toolbar overflow below 960 px and
   below 1200 px. (F3, F8)
6. Decide and document the **target-speed row** treatment in the
   resistance sweep table. (F6)
7. Add a **theme contrast manifest** and tests asserting WCAG AA
   for both light and dark variants, including a perceptual-distance
   check between the advisory-yellow and unavailable-orange chip
   tokens. (F7, F9)
8. State the **first-viewport scan order** and the type ramp it
   relies on as part of the §1 acceptance criteria. (F10)

## Residual risk

- RFC 0033 hands the Open Questions decision on light/dark toggle to
  the implementer; if the theme contrast assertion (action 7) is not
  enforced before that toggle ships, a dark-only or light-only
  contrast regression can land silently.
- Even with the above actions, desktop/web *behavioural* parity will
  remain partial because Trame Vuetify chips and matplotlib widgets
  do not share a focus-ring or chip primitive. The acceptance
  criteria can verify region presence and copy, but not interaction
  parity, on the desktop side.
- The Comparison drop-zone and Paste JSON toggle interaction is the
  least specified surface in the RFC and the most likely to be
  re-invented at implementation time; ledger should consider
  pulling its specification forward even though it is not currently
  on the blocking-findings list.
