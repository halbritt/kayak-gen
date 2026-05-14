---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Review — Ergonomics And Interaction Design (RFC 0034)

## Verdict Intent

`accept_with_findings`

RFC 0034 is well-scoped against the six workflow 0044 final-review follow-ups
(`striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md` F1-F6) and stays
inside RFC 0033's no-new-backend-capability boundary. The packet, prompts,
and write-scope clarifications from
`striatum/0045-workspace-ui-follow-up/review_remediation/REMEDIATION.md` give
reviewers correct verdict routing. The findings below are
implementation-scope ergonomics refinements for the ledger; none of them
prevent a fair implementation review and none require a remediation cycle.

## Ergonomics And Design Findings (ordered by severity)

### E1 — High: Preset reseed must avoid the `custom` feedback loop

The web rail currently binds two preset controls to the same key — a toolbar
`VSelect` (`kayakgen/ui/web/app.py:613-620`) and a rail `VRadioGroup`
(`kayakgen/ui/web/app.py:661-669`) — but neither one mutates sliders or
narrows ranges. RFC 0034 acceptance criterion 1 requires both reseed and
range narrowing on preset change, plus a flip back to `custom` on manual
slider edit. The desktop already does this in
`kayakgen/ui/desktop.py:159-207` with an `_applying_class` guard around
`set_val()` calls so the chain `preset → sliders → on_change → custom`
does not collapse the preset back to Custom while it is still being
applied.

The web path has the analogous risk: `KayakgenApp._on_param_change`
(`kayakgen/ui/web/app.py:416-431`) re-fires for every preset-driven slider
mutation through `self.state.change(*watched)`, so a naive preset handler
that just writes the five class defaults will appear to immediately flip
back to `custom`. The desktop guard pattern (or an equivalent
suspend-listeners helper) needs to be replicated explicitly in the
implementation slice. Without it, the preset is unusable.

How to apply: implement a `_on_class_preset_change(label)` reactor that
(a) seeds `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `Cp` from
`KayakClass.<name>.default`, (b) updates per-slider min/max via state
constants the rail consumes (e.g. `state.<key>_min` / `state.<key>_max`
re-bound to `VSlider.min` / `VSlider.max`), and (c) wraps the assignments
with a `_applying_class_preset = True` guard so `_on_param_change` skips
the manual-edit→`custom` flip during programmatic seeding. The reactor
should run when `class_preset != "custom"`. The clamp
`clamp_beam_wl_state` must still apply after seed values land.

Source: `kayakgen/ui/web/app.py:240-247,416-435,661-695`;
`kayakgen/ui/desktop.py:148-207`; `kayakgen/model/classes.py:53-94`; RFC 0034
goal 1 and acceptance criterion 1.

### E2 — High: Resistance card must own the sweep table; remove the duplicate pre-block

The Hydrostatics card currently renders `analysis_lines` as a `<pre>` block
(`kayakgen/ui/web/app.py:763-767`), and `analysis_lines_from_state`
emits both Hydrostatics rows and a `Resistance curve (raw comparative
filter)` table inside the same string
(`kayakgen/ui/web/controllers.py:414-442`). The dedicated Resistance card
right below it (`kayakgen/ui/web/app.py:778-786`) only renders the
heading, caption, detail copy, and the `uncalibrated_comparative` chip.
A user therefore sees the resistance numbers in the wrong card and an
empty-looking Resistance card next to it. This is the most visible
ergonomics regression today and is the same gap F3 of the prior workflow
0044 final review.

How to apply: when the Resistance card is wired to
`resistance_table_view_model` per RFC 0034 acceptance criterion 3, scope
the Hydrostatics pre-block back to `hydro_rows` only (i.e. add an
`hydro_lines_from_state` analogue or pass `include_resistance=False`),
keep `RAW_COMPARATIVE_CAPTION` and the `uncalibrated_comparative` chip on
the Resistance card, and apply the focus token to the target row using
the `is_target` flag from the view model. The `kt | Fn | Rv N | Rw N |
Rt N` column header must be present so the table is meaningful without
the chip context. The `--state-focus-row` token from `kayakgen/ui/theme.py`
is the correct visual anchor for the target row.

Source: `kayakgen/ui/web/app.py:752-786`;
`kayakgen/ui/web/controllers.py:200-259,414-442`;
`tests/test_web_read_models.py:126-146`; RFC 0034 acceptance criterion 3
and RFC 0033 §4 Resistance.

### E3 — High: Mesh-profile select must surface both options with `watertight-solid` disabled

`kayakgen/ui/web/app.py:802-811` renders the profile select with
`readonly=True`, which hides the existence of the second option from the
user entirely. The `mesh_package_view_model` already returns a
`profile_options` array carrying `{label, profile_id, disabled, tooltip}`
for each entry (`kayakgen/ui/web/controllers.py:906-921`), and the RFC
0033 §4 Mesh acceptance criteria require `watertight-solid` to render as
a disabled option with the `WATERTIGHT_SOLID_DISABLED_TOOLTIP` so users
understand the path exists and is gated. A `readonly` select is
indistinguishable from a constant label and removes the affordance.

How to apply: bind a Vuetify `VSelect` whose `items` is built from the
view-model's `profile_options` (passing each entry's `disabled`/`tooltip`
into the option slot). Keep `state.mesh_profile_label` as the bound
value, only allow selection of non-disabled entries, and surface the
tooltip on hover and on keyboard focus. The `disabled` row must remain
keyboard-reachable for screen-reader users so the explanation is
discoverable. Manifest `profile_name` still tracks `mesh_profile_id`.

Source: `kayakgen/ui/web/app.py:802-819`;
`kayakgen/ui/web/controllers.py:49-58,906-921`;
`tests/test_web_read_models.py:86-107`; RFC 0034 acceptance criterion 4
and RFC 0033 §4 Mesh.

### E4 — Medium: Validity badge must mirror the exact RFC 0033 string set and be screen-reader announced

The static `VChip` at `kayakgen/ui/web/app.py:691-695` always renders
`Custom (L/B_wl from current hull)`. RFC 0034 acceptance criterion 2 and
RFC 0033 §2 require the badge text to be derived from the active hull and
must be one of: `In <class> envelope`, `Custom — sub-touring`,
`Custom — beyond elite`, `Custom (L/B_wl=X.X)`. The desktop classification
helper at `kayakgen/ui/desktop.py:362-376` already implements three of the
four cases; it falls back to a longer
`Custom — sub-touring (L/B_wl=…)` string. The web implementation should
not import the desktop helper directly (cross-frontend coupling), but it
should call a shared helper to keep the four canonical strings centralized,
and the string set must match RFC 0033 exactly — including the em dash —
so the workflow 0044 ledger forbidden-copy guard cannot accidentally drift.

How to apply: add a small `kayakgen/ui/web/controllers.py` helper
(`hull_validity_badge(state) -> str`) that returns one of the four
canonical strings (the existing `design_advisory` already computes the
`l_over_bwl` ratio); bind it to a reactive `state.validity_badge` and
update on every `_on_param_change`. Render the badge in an element with
`role="status"` and `aria-live="polite"` so assistive tech announces
changes when the hull class slips out of envelope. Keep `size="small"`
and the neutral surface color — the badge is informational, not a
pass/fail state, and must not co-opt the `state-success` or `state-raw`
chip vocabulary.

Source: `kayakgen/ui/web/app.py:690-695`;
`kayakgen/ui/desktop.py:362-376`; `kayakgen/model/classes.py:53-94`;
`kayakgen/model/advisory.py:44-79`; RFC 0033 §2 and RFC 0034 acceptance
criterion 2.

### E5 — Medium: Toolbar export must collapse into a single `Export ▾` menu with honest disabled entries

Today the toolbar exposes two flat buttons — `Export Hull STL` and
`Export Deck STL` (`kayakgen/ui/web/app.py:623-632`) — and the responsive
hook `kg-export-menu-under-1200` is applied to each button rather than to
a single menu. RFC 0033 §5 and RFC 0034 acceptance criterion 5 require a
single dropdown `Export ▾` with five rows: `Hull STL`, `Deck STL`,
`Hydro JSON`, `Stability JSON`, `Mesh package…`. The current two-button
layout cannot accommodate the additional three rows without consuming
toolbar width, and there is no scan anchor for the export affordance —
users have to read each button label rather than recognising the menu.

The four sub-rows have asymmetric readiness today, and the menu must
expose that honestly without inventing storage or capability:

- `Hull STL` and `Deck STL` — already wired through `ctrl.export_stl` and
  `stl_bytes_for_part`; remain enabled.
- `Hydro JSON` — `analysis_view_model` already returns `hydro_rows` and
  `evaluation_for_state` returns a full `EvaluationResult`; downloading
  as JSON does not require a new REST shape. Enabled, with a `.json`
  filename suggestion.
- `Stability JSON` — the web Stability sub-card has no load-case form
  today (RFC 0033 §4 Stability mentions one as optional). A zero-load
  initial-stability JSON is the safe-now scope, mirroring `kayakgen
  evaluate` minus a `--load-case`. Enable only the initial-stability
  variant; do not pretend the menu carries the full bounded fixed-body
  equilibrium output.
- `Mesh package…` — RFC 0034 open question 2 explicitly says this can
  remain a disabled entry until a workflow accepts web-side authoring.
  Render the row disabled with a tooltip such as
  `Mesh package authoring is not enabled in the browser; use kayakgen
  mesh-package.` This is the safest interpretation and aligns with RFC
  0033 §Non-Goals.

How to apply: replace the two `VBtn`s with a single `VMenu` activator
labeled `Export ▾` and `kg-toolbar-action kg-export-menu-under-1200` on
the activator only; the menu items use `disabled` per the table above
with a tooltip surface for disabled rows. Keyboard support must allow
the menu to open with Enter/Space and navigate items with arrow keys
(Vuetify `VMenu` + `VList` already gives this; the implementation just
needs to use it instead of two flat buttons).

Source: `kayakgen/ui/web/app.py:622-632,140-150,477-483`;
`kayakgen/ui/web/controllers.py:147-198,521-559`; RFC 0033 §5 and §4
Stability; RFC 0034 acceptance criterion 5 and open question 2.

### E6 — Medium: Forbidden-copy regression must keep the documented negations

The forbidden-copy test today only covers `GZ_max`, `heel_angle_max_deg`,
and a `cfd_ready` count assertion (`tests/test_web_layout.py:94-100`). RFC
0033 §8 and RFC 0034 acceptance criterion 6 expand the no-go list to
include `OpenFOAM`, `SU2`, `cloud`, `worker queue`, `calibrated drag`,
`final prediction`, and `design fitness`. The current
`kayakgen/ui/web/app.py` source contains `final prediction` twice
intentionally — inside `RAW_COMPARATIVE_CAPTION = "Raw comparative filter;
not final prediction."` and inside
`RESISTANCE_DETAIL_COPY = "Uncalibrated; no accepted final-prediction
validity envelope. …"`. The widening assertion needs an explicit
allow-list of negations or sub-strings so the safe-now copy stays valid:

- `not final prediction` (in `RAW_COMPARATIVE_CAPTION`)
- `no accepted final-prediction` (in `RESISTANCE_DETAIL_COPY`)
- `not watertight cfd_ready` (single negation already permitted by the
  existing `cfd_ready` count assertion)
- `no hosted worker is running` (in `CFD_LOCAL_FILESYSTEM_NOTICE`)

How to apply: extend `test_web_layout.py` with assertions that the bare
forbidden strings do not appear in `kayakgen/ui/web/app.py` and
`kayakgen/ui/web/controllers.py`, with a tight allow-list checked before
the bare-string assertion. Keep the existing `cfd_ready` count test as
is. Source any extra strings the rest of the workflow 0044 final review
F6 enumerates — `calibrated drag`, `final prediction`, `design fitness`,
`hosted`, `cloud`, `worker queue`, `OpenFOAM`, `SU2` — so the regression
is the canonical RFC 0033 §8 set, not a partial copy.

Source: `tests/test_web_layout.py:94-100`;
`kayakgen/ui/web/app.py:152-181`;
`kayakgen/ui/web/controllers.py:46-48,255-258`;
`striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md` F6.

### E7 — Low: Class preset labels in the rail are machine names, not human labels

The radio group at `kayakgen/ui/web/app.py:661-669` iterates
`CLASS_PRESETS = ("touring", "performance", "surfski_int",
"surfski_elite", "custom")` and uses each tuple value as both the radio
value and the displayed label. The `KayakClass.label` field on the canonical
classes already carries human-readable text ("Touring sea kayak",
"Performance sea kayak", etc., per `kayakgen/model/classes.py:53-94`),
which the desktop frontend uses verbatim (`kayakgen/ui/desktop.py:148-157`).
Web users currently read `surfski_int` and have to translate to
"Intermediate surfski" themselves; screen readers announce the bare
identifier. This is a small but real ergonomics regression versus the
desktop.

How to apply: render labels from `KayakClass.label` (and "Custom" for the
custom value) while keeping the radio's stored value as the class id, so
the wiring in E1 and the existing state code still see `touring`,
`performance`, etc. The toolbar `VSelect` should also display labels and
return ids, with `item-title`/`item-value` props.

Source: `kayakgen/ui/web/app.py:83-89,613-620,661-669`;
`kayakgen/model/classes.py:24-93`;
`kayakgen/ui/desktop.py:148-157`.

### E8 — Low: Status segment buttons need fuller `aria-label` text and the validity badge should not move into status

`kayakgen/ui/web/app.py:954-973` renders the status bar buttons with
`aria-label` set to short phrases like `"package profile status"` while
the visible text is `package: open-wetted-surface`. A screen reader user
reading the button announces "package profile status, button" without
the actual current value. RFC 0033 §5 and the workflow 0044 ledger P1
"Read Models, Status Bar, And Chip Plumbing" require the accessible label
to expand the compact token into its underlying meaning. The status bar
also should not be the home for the validity badge — keep the badge
pinned to the rail per RFC 0033 §2 so the spatial scan order is still
Toolbar → Rail (with badge) → Geometry → Review → Status.

How to apply: compute `aria-label` reactively per segment, e.g.
`f"{label}: {{{{ {state_key} }}}}; opens {target_tab} tab"`, mirroring
the visible text plus the navigation hint. Keep the existing
`data-testid` so layout tests do not regress. Do not move the validity
badge into the status bar — it is a rail anchor.

Source: `kayakgen/ui/web/app.py:99-125,954-973`;
`striatum/0044-workspace-ui-rework/ledger/FINDINGS.md` P1 Read Models;
RFC 0033 §2 and §5.

## Accessibility And Responsive Considerations

- **Tab order:** confirm Tab through Toolbar (`breadcrumb → class select
  → Reset → Share → Export ▾`) → drawer rail (`class radio group →
  groups of sliders → validity badge`) → geometry pane (metrics-strip
  tokens are clickable per RFC 0033 §3 and should be tab-stops if
  surfaced) → review tabs → review card → status bar segments. The
  hidden share-state probe at `kayakgen/ui/web/app.py:640-655` already
  removes itself from the tab order with `tabindex="-1"` and is
  `aria-hidden="true"`; keep this.
- **Sliders:** Vuetify `VSlider` already supports ArrowLeft/Right and
  PageUp/PageDown by default; the existing `data-testid` and `aria-label`
  per slider remain correct. The workflow 0044 ledger P0 Parameter Rail
  prescribed `Home`/`End` deltas — RFC 0034 does not need to re-litigate
  this, but the implementation slice should not regress current Vuetify
  defaults. The `target_speed_kt` slider is a view-only control and must
  not be persisted to `Hull`.
- **Focus visibility:** the `state-focus-rail` and `state-focus-row`
  tokens in `kayakgen/ui/theme.py` already exist; the implementation
  must apply them to the Resistance target row (E2) and to the active
  validity-badge surface, not introduce new color literals.
- **Live regions:** the validity badge should be `role="status"
  aria-live="polite"`; the share toast already uses Vuetify
  `VSnackbar`, which is announced; the CFD `cfd_status_lines` block is
  text and refreshes on action — no live region needed unless asynchronous
  status polling is added.
- **Reduced motion / color independence:** the resistance focus row
  cannot rely on `--state-focus-row` color alone; pair the highlight with
  a visible marker (e.g. a bullet glyph in the first column, or a bold
  cell weight) so users without color perception can still locate the
  target row.
- **Responsive collapse (<960 px):** the existing CSS hooks
  (`kg-collapse-under-960`, `kg-geometry-accordion-under-960`,
  `kg-review-body-under-960`, `kg-status-wrap-under-960`,
  `kg-export-menu-under-1200`, `kg-metrics-strip-scroll`) need to remain
  applied to the matching containers when the export menu collapses to
  a single icon and the rail becomes a top accordion. The drawer is
  currently 360 px wide (`kayakgen/ui/web/app.py:658`); below 960 px the
  drawer must collapse to a top accordion per RFC 0033 §1, not stay as a
  modal drawer that occludes the viewport.
- **Color discipline:** all new chip/badge work must source from
  `theme.CHIP_SPECS` and `COLORS_LIGHT`/`COLORS_DARK`. The mesh-profile
  disabled tooltip must not invent a new "raw"-toned surface — disabled
  rows should reuse the neutral surface plus reduced opacity (`Vuetify
  disabled-opacity` is already wired in `vuetify_theme_config`).

## Acceptance Refinements

These tighten RFC 0034 acceptance criteria 1–6 without changing scope:

1. **AC1 — preset reseed:** add the explicit "manual slider edits flip
   `class_preset` back to `custom` only when no preset reseed is in
   progress" clause, matching the desktop's `_applying_class` guard. The
   browser acceptance test should drive both a preset selection (assert
   five sliders change values) and a subsequent manual slider edit
   (assert `class_preset == "custom"`).
2. **AC2 — validity badge:** require the badge to be exactly one of the
   four RFC 0033 strings, with the em dash preserved, and rendered with
   `role="status" aria-live="polite"`. Confirm in the layout test that
   no other string variant ships.
3. **AC3 — Resistance card:** require the Resistance card to own the
   sweep table and the target-speed focus row, and require the
   Hydrostatics card pre-block to omit the resistance section (no
   duplication). The browser test should locate the table by
   `data-testid="resistance-table"` or equivalent.
4. **AC4 — Mesh tab:** require the mesh profile picker to render
   `watertight-solid` as visible-but-disabled with the
   `WATERTIGHT_SOLID_DISABLED_TOOLTIP`, not hidden behind `readonly`.
   Require welded-primary counts in the displayed diagnostics with raw
   counts surfaced as the secondary detail line.
5. **AC5 — Export ▾:** require a single dropdown activator labeled
   `Export ▾` with five rows in this order: Hull STL, Deck STL,
   Hydro JSON, Stability JSON, Mesh package…; the latter two carry
   honest disabled states (Stability JSON when no load-case form is
   present beyond the zero-load default; Mesh package… disabled with the
   "use kayakgen mesh-package" tooltip).
6. **AC6 — forbidden copy:** widen the regression test to the RFC 0033
   §8 string set with the explicit allow-list of documented negations
   listed under E6, and assert it across both `app.py` and
   `controllers.py`.

## Concrete Source References

- RFC packet — `docs/rfcs/0034-workspace-ui-follow-up.md`,
  `docs/rfcs/0033-workspace-ui-rework.md`.
- Workflow packet — `docs/workflows/0045-workspace-ui-follow-up/workflow.json`,
  `docs/workflows/0045-workspace-ui-follow-up/prompts/review_ergonomics_design.md`,
  `docs/workflows/0045-workspace-ui-follow-up/roles/reviewer_ergonomics_design.md`.
- Remediation context —
  `striatum/0045-workspace-ui-follow-up/review_remediation/REMEDIATION.md`.
- Prior workflow context —
  `striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md` (F1-F6),
  `striatum/0044-workspace-ui-rework/ledger/FINDINGS.md`,
  `striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md`.
- Implementation — `kayakgen/ui/web/app.py:83-150,240-247,416-435,
  606-973`, `kayakgen/ui/web/controllers.py:46-58,147-260,
  309-411,906-921`, `kayakgen/ui/theme.py:60-69,318-351`,
  `kayakgen/ui/desktop.py:148-207,362-376`,
  `kayakgen/model/classes.py:53-94`, `kayakgen/model/advisory.py:44-79`.
- Tests — `tests/test_web_layout.py:75-138`,
  `tests/test_web_read_models.py:25-146`, `tests/test_web_browser.py:307-397`.
- User-facing doc — `docs/USER_GUIDE.md` (workspace section).

## Commands And Checks Run

- `.venv/bin/python -m json.tool docs/workflows/0045-workspace-ui-follow-up/workflow.json`
  → workflow.json valid.
- Source-level forbidden-string scan over `kayakgen/ui/web/app.py`:
  `cfd_ready` count = 1 (negated form), `final prediction` count = 2
  (both inside permitted negations), `calibrated drag`/`design fitness`/
  `worker queue`/`OpenFOAM`/`SU2` all absent.
- `grep` over `kayakgen/` for `aria-live` returned no matches, confirming
  the live-region accessibility gap behind E4.
- File reads on `kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`,
  `kayakgen/ui/theme.py`, `kayakgen/ui/desktop.py`,
  `kayakgen/model/classes.py`, `kayakgen/model/advisory.py`,
  `tests/test_web_layout.py`, `tests/test_web_read_models.py`,
  `tests/test_web_browser.py`, `docs/USER_GUIDE.md`,
  `docs/rfcs/0033-workspace-ui-rework.md`,
  `docs/rfcs/0034-workspace-ui-follow-up.md`.
- No product code, tests, docs, `.striatum`, or Striatum mutation
  commands were touched. No commit, branch, or push occurred. No byline
  was added.

## Sub-Agent And Parallel Helper Use

This pass used direct file reads, parallel reads where independent, and
local `grep` checks rather than spawning helper sub-agents. The review
surface (one RFC, one remediation note, one prior final review, one
prior ledger, ~6 implementation files, 3 test files, 1 user guide) fits
inside the main session context, and the ergonomics questions are tightly
coupled — splitting them across sub-agents would have produced
inconsistent severity ordering and acceptance refinements. Tool calls
were issued in parallel where the targets were independent.
