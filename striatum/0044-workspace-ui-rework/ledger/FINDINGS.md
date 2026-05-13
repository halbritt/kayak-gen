# Findings Ledger - RFC 0033 Workspace UI Rework

## Gate Result

RFC 0033 should proceed as `accept_with_findings`.

The first-pass reviews found no blockers requiring review remediation. The
implementation lane should treat this ledger as the conservative scope boundary:
land the workspace shell, theme module, structured advisory record, status/chip
read models, bounded desktop touch-ups, and regression tests; do not expand into
new CFD, calibrated physics, high-angle stability, multi-variant overlays, or
new mesh-authoring APIs.

## Review Stats And Source Summary

Required sources read for this ledger:

- `AGENTS.md`
- `docs/workflows/0044-workspace-ui-rework/SOURCES.md`
- `docs/workflows/0044-workspace-ui-rework/roles/ledger.md`
- `docs/workflows/0044-workspace-ui-rework/prompts/findings_ledger.md`
- `docs/rfcs/0033-workspace-ui-rework.md`
- `striatum/0044-workspace-ui-rework/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0044-workspace-ui-rework/domain/REVIEW_DOMAIN.md`
- `striatum/0044-workspace-ui-rework/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`
- `striatum/0044-workspace-ui-rework/ops/REVIEW_OPS.md`

Review verdicts:

| Source review | Verdict intent | Ledger treatment |
| --- | --- | --- |
| Traceability | `accept_with_findings` | Accept; carry implementation wiring choices forward. |
| Domain | `accept` | Accept; preserve exact claim/readiness/safety language. |
| Ergonomics/design | `accept_with_findings` | Accept; tighten interaction, layout, focus, responsive, and parity details. |
| Ops | `accept_with_findings` | Accept; carry validation and scaffold hygiene forward. |

Input finding count:

- 21 explicit review findings/actions were deduplicated: 7 traceability findings,
  10 ergonomics/design findings, and 4 ops findings.
- The domain review contributed no blockers; its domain-safety checks are folded
  into the required implementation guidance.
- This ledger reduces those inputs to 12 safe-now implementation findings, 3
  test/docs/scaffold findings, and 8 explicit deferrals/residual risks.

Source artifact summary:

- `REVIEW_TRACEABILITY.md` confirms RFC 0033 is grounded in current code and
  flags the only concrete payload ambiguities: mesh raw-vs-welded labels,
  mesh-profile label/ID mapping, `target_speed_kt` staying out of `Hull`,
  structured advisory compatibility, and RFC 0008 supersession hygiene.
- `REVIEW_DOMAIN.md` accepts the domain wording and safety posture: exact
  `ClaimState`, `ReadinessLevel`, and `CfdRunStatus` vocabulary; strict
  forbidden-claim handling; hidden unsupported parameters; and permanent
  high-angle GZ deferral copy.
- `REVIEW_ERGONOMICS_DESIGN.md` accepts the RFC but requires implementable
  details for first-viewport scan order, rail grouping, focus/keyboard behavior,
  warning triage, responsive collapse, Review-tab states, resistance target-row
  handling, theme contrast, and desktop/web parity.
- `REVIEW_OPS.md` accepts scaffold runability and requires an explicit validation
  matrix because default test commands can skip optional web/browser acceptance.

## Prioritized Implementation Findings

### P0 - Workspace Shell And First Viewport

Implement the three-region shell with `region-params`, `region-geometry`, and
`region-review`, plus the four status-bar segments from RFC 0033. At 1440x900 the
first viewport must show the full parameter rail, 3D viewport, metrics strip,
first Review tab, and status bar.

Pin the canonical scan order as: Toolbar breadcrumb -> Parameters rail -> Geometry
viewport -> Metrics strip -> active Review tab card -> Status bar. The type ramp
in `kayakgen/ui/theme.py` should reinforce this order.

Sources: RFC 0033 sections 1 and 5; `REVIEW_ERGONOMICS_DESIGN.md` F10, F3, F8;
`REVIEW_TRACEABILITY.md` F6.

### P0 - Parameter Rail Grouping And Editing

Keep the RFC field order, but group the rail into:

- Principal dimensions: `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`,
  `deck_height_m`
- Shape coefficients: `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`
- Ends and view: `bow_rake`, `stern_rake`, `target_speed_kt`

Keep the class preset radio above the groups and pin the validity badge at the
bottom of the rail. Preserve live `beam_wl_m` clamping to `beam_oa_m`. Treat
`target_speed_kt` as view/UI state only; do not add it to `Hull`.

Add deterministic keyboard behavior for sliders: Tab follows the scan order,
arrow keys move by 1 percent of slider span, PageUp/PageDown by 10 percent, and
Home/End move to min/max. Esc closes expanded numeric inputs and chip popovers.

Sources: RFC 0033 section 2; `REVIEW_ERGONOMICS_DESIGN.md` F1, F2;
`REVIEW_TRACEABILITY.md` F4; `REVIEW_DOMAIN.md` unsupported-parameter checks.

### P0 - Responsive Collapse

Below 960 px, make the parameter rail a top accordion and the Review pane the
body. Geometry must not become an undefined orphan: collapse it into its own
accordion above Review, default-collapsed, with either a 320 px minimum 3D square
when opened or a clear `Open 3D` action.

Keep the metrics strip horizontally scrollable rather than wrapping, so token
click targets remain stable. Stack the status bar to two lines with 32 px minimum
tap targets. Below 1200 px, collapse `Export` into a single icon/menu control
with the same actions.

Sources: RFC 0033 sections 1 and 5; `REVIEW_ERGONOMICS_DESIGN.md` F3, F8.

### P0 - Review Pane State Matrices

Before implementing the five tabs, define state matrices for default, empty,
loading, disabled, error, and terminal states. The matrix must include exact copy,
button enablement, chip behavior, and the focus target for each click action.

Minimum coverage:

- Mesh: invalid hull, build in flight, build failed, disabled `watertight-solid`.
- Comparison: no JSON, malformed JSON, empty pinned strip, accepted file/drop
  types, Paste JSON toggle.
- CFD: setup, prepared, queued, running, succeeded, failed, unavailable, plus
  Prepare/Run/Refresh/Logs/Raw Result enablement.
- Advisories: zero advisories, advisory count badge, field-chip navigation.

Sources: RFC 0033 section 4; `REVIEW_ERGONOMICS_DESIGN.md` F5, F7, F8.

### P0 - Exact Claim, Readiness, And Forbidden-Copy Handling

Every displayed resistance value must remain attached to
`uncalibrated_comparative` and the persistent raw-filter copy. CFD must keep the
no-hosted-worker and raw-solver-artifact banners. Mesh must not render the bare
word `cfd_ready` outside the explanatory negation `not watertight cfd_ready`.
Stability must keep `High-angle GZ unavailable` and must not render `GZ_max` or
`heel_angle_max_deg`.

Use existing `ClaimState`, `ReadinessLevel`, and `CfdRunStatus` literals. Keep
`LCB_frac`, `rocker_bow_m`, and `rocker_stern_m` hidden except through RFC 0031's
unsupported channel.

Sources: RFC 0033 sections 4 and 8; `REVIEW_DOMAIN.md` claim/readiness and
forbidden-language findings; `REVIEW_TRACEABILITY.md` F6.

### P0 - Theme Module And Color Discipline

Add `kayakgen/ui/theme.py` as the only home for color literals and named colors
under `kayakgen/ui/`. Route Vuetify theme configuration, matplotlib rcParams, and
VTK background through the theme helpers. Replace hardcoded plot colors and the
slate-blue VTK background with semantic tokens.

Add theme validation, not just linting: test text/chip/focus contrast against a
small manifest for light and dark themes, and ensure advisory yellow and
raw/unavailable orange are perceptually distinct enough to avoid warning-triage
confusion.

Sources: RFC 0033 section 6; `REVIEW_ERGONOMICS_DESIGN.md` F7, F9;
`REVIEW_TRACEABILITY.md` F6.

### P0 - Structured Advisory Record And Warning Triage

Add an immutable `Advisory` value object with `code`, `message`, and
`field_refs`, and add `DesignAdvisory.advisories` alongside the existing
`DesignAdvisory.warnings`. Do not change or remove `warnings`; current callers
and RFC 0031 compatibility depend on it.

Advisory dots belong left of the slider label, must be keyboard focusable, and
must expose advisory codes on hover/focus. Advisories-tab field chips must focus
and scroll the matching rail row; on narrow layouts they must also expand the
parameter accordion.

Sources: RFC 0033 section 7; `REVIEW_TRACEABILITY.md` F5;
`REVIEW_ERGONOMICS_DESIGN.md` F7; `REVIEW_DOMAIN.md` safety checks.

### P1 - Read Models, Status Bar, And Chip Plumbing

Add `evaluation_summary(state)` as a pure read model returning `{package,
readiness, resistance_claim, cfd_status, advisories}` for the Status bar. Preserve
existing REST route JSON shapes, existing controller signatures, and existing
share URL round-trip behavior.

Status-bar segments are buttons, not passive text: give each a 32 px minimum
height, visible theme focus ring, and an accessible label that expands compact
tokens to their underlying claim/readiness/status meaning. Clicking a segment
focuses the matching Review tab.

Sources: RFC 0033 sections 5, 7, and Compatibility; `REVIEW_ERGONOMICS_DESIGN.md`
F8; `REVIEW_DOMAIN.md`; `REVIEW_TRACEABILITY.md` F6.

### P1 - Mesh Diagnostics And Mesh Profile Mapping

Use welded counts as the primary displayed counts for boundary and non-manifold
diagnostics because they align with topology after the configured weld tolerance
and solver-readiness interpretation. Keep raw counts available in an expanded
detail row or tooltip so raw-only defects are still inspectable. Apply the same
choice to Hull and Deck diagnostics.

Map UI labels to canonical profile IDs explicitly:

- `open-wetted-surface` -> `open_wetted_surface_resistance_v1`
- `watertight-solid` -> `watertight_solid_resistance_v1`

The UI label may be compact, but manifest `profile_name` and chip/detail copy
must remain traceable to the canonical ID.

Sources: RFC 0033 section 4 Mesh; `REVIEW_TRACEABILITY.md` F1, F2.

### P1 - Resistance Target-Speed Row

The fixed resistance sweep rows are `[2.0, 3.0, 4.0, 5.0, 6.0] kt`, while
`target_speed_kt` is continuous. Insert a sorted target-speed row when
`target_speed_kt` is more than 0.05 kt away from every fixed sweep speed, and
apply the focus-row token to the inserted row. If it is within 0.05 kt, highlight
the matching fixed row.

Sources: RFC 0033 section 4 Resistance; `REVIEW_ERGONOMICS_DESIGN.md` F6.

### P1 - Desktop Touch-Ups And Parity Boundary

Use the reduced desktop slice for this workflow. Land the safe parity work:

- Rename `Generate STLs` to `Export STLs` without changing generated filenames.
- Add the `Cm` control through the existing desktop parameter mapping.
- Route matplotlib colors through `theme.py`.
- Embed or dock the existing PyVista surface where feasible.
- Add the four-segment status-bar vocabulary, even if desktop interaction is
  less rich than web.

Do not attempt a full desktop Review-tab/chip/focus parity rewrite inside the
matplotlib figure. A full `QMainWindow`/`QTabWidget` rewrite is future work unless
implementation discovers it is the only practical way to satisfy the safe
touch-ups above.

Sources: RFC 0033 sections 3, 6, and 9; `REVIEW_ERGONOMICS_DESIGN.md` F4;
`REVIEW_TRACEABILITY.md` F6.

### P1 - Comparison And CFD Interaction Tightening

The Comparison tab is the least specified interaction surface. Pull forward only
the minimal state behavior needed to keep it predictable: empty state, Paste JSON
error copy, pinned-strip empty state, accepted drop types, report warning display,
and selectable `spec_hash`.

For CFD, make unavailable actions disabled in the UI rather than relying on
controller errors and toasts for every impossible transition. Keep the existing
`CfdRunStatus` literals and RFC 0033 banner copy.

Sources: RFC 0033 section 4; `REVIEW_ERGONOMICS_DESIGN.md` F5 and residual risk;
`REVIEW_DOMAIN.md` CFD literal checks.

### P2 - RFC And Scaffold Hygiene

After RFC 0033 lands, add a status/cross-link so RFC 0008's two-column layout is
not read as a co-equal current commitment. This is hygiene, not a blocker for
implementation.

Future scaffold edits should clarify ops verdict vocabulary and add CLI/test
inputs to ops source guidance (`kayakgen/cli/main.py`, `tests/test_cli.py`,
`pyproject.toml`). Do not update `.striatum` or root `OPERATOR_REPORT.md` as
part of this ledger job.

Sources: `REVIEW_TRACEABILITY.md` F3; `REVIEW_OPS.md` findings 2, 3, 4.

## Required Implementation Guidance

- Keep the rework primarily frontend-only. Backend changes are limited to the
  structured `Advisory` addition and pure read-model helpers.
- Preserve all existing REST route JSON shapes: `/api/evaluate`, `/api/stl`,
  `/api/cfd/*`, and `/api/hulls/*`.
- Preserve existing controller helper signatures and existing share URL
  encode/decode behavior.
- Keep `DesignAdvisory.warnings` unchanged and additive.
- Keep `target_speed_kt` out of `Hull`.
- Keep unsupported geometry parameters hidden except through the unsupported
  validity/advisory channel.
- Treat theme tokens as the single source for UI color, typography, focus, and
  chip styling.
- Add forbidden-claim regression tests so future copy edits cannot accidentally
  claim hosted CFD, calibrated drag, final prediction, high-angle GZ, or
  watertight `cfd_ready` support.
- Make ergonomics choices testable: first viewport, responsive collapse, focus
  order, status click targets, advisory chip-to-slider navigation, and per-tab
  state matrices must be covered by assertions or explicit review checklist
  entries.

## Validation Matrix

Minimum command matrix from ops review:

```bash
git diff --check
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_ui_theme.py -q
.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q
```

Validation expectations:

| Area | Required checks |
| --- | --- |
| Web layout | Region test ids, Review tab order, 1440x900 first viewport, <960 px collapse, status segments, toolbar overflow. |
| Parameter editing | Rail groups, `beam_wl_m` clamp, `target_speed_kt` view-only behavior, keyboard slider deltas, focus ring. |
| Advisories | `Advisory` record shape, `warnings` compatibility, field refs, dot tooltip, chip-to-slider navigation, accordion expansion. |
| Domain copy | Raw comparative resistance copy, claim chips, CFD banners, high-angle GZ unavailable block, forbidden-string grep assertions. |
| Mesh | Welded primary counts with raw detail, profile label/ID mapping, no bare `cfd_ready` except allowed negation. |
| Resistance | Inserted/sorted target-speed row behavior and focus-row token. |
| Theme | Orphan color lint under `kayakgen/ui/`, VTK/matplotlib routing, WCAG contrast manifest, advisory-yellow vs raw-orange separation. |
| Desktop | `Cm` control, `Export STLs` label, same STL filenames, themed plot colors, status vocabulary, PyVista docking if feasible. |
| Browser acceptance | Run with web/browser extras and Playwright Chromium when available; document skips explicitly if the environment lacks optional dependencies. |

## Explicit Deferrals

These remain out of scope for this implementation slice:

- Hosted/cloud CFD workers, worker queues, or multi-user execution.
- Calibrated drag, final-prediction validity envelopes, or design-fitness claims.
- High-angle GZ visualization or numeric `GZ_max` / `heel_angle_max_deg` outputs.
- Multi-variant 2D geometry overlay and Pareto plot widget work.
- Web-side mesh-package authoring API beyond wrapping current server-local
  `kayakgen mesh-package` semantics.
- Claiming current generated packages satisfy `watertight-solid` or bare
  `cfd_ready` readiness.
- Full mobile workspace authoring; narrow screens remain inspect-and-triage.
- Full desktop behavioral parity with web chips/tabs/focus behavior unless a
  later RFC commits to a real Qt main-window rewrite.

## Residual Risks

- The desktop surface may still diverge behaviorally because matplotlib widgets
  do not provide the same chip, tab, focus-ring, and hover affordances as web.
- The Comparison drop-zone and Paste JSON flow is under-specified relative to the
  rest of the RFC; the minimal state matrix should be implemented now, but richer
  compare ergonomics may need a follow-up.
- Browser acceptance can be skipped silently if optional web/browser dependencies
  or Playwright Chromium are unavailable; final review must distinguish true
  passes from environment skips.
- RFC 0008 will remain a possible source of layout confusion until the accepted
  RFC index and cross-links are updated after RFC 0033 lands.
- Theme contrast regressions are likely if the implementation only checks that
  color literals live in `theme.py`; the contrast manifest is required to close
  that gap.

## Sub-Agent And Parallel Assistance Summary

Three read-only sub-agents were used for independent ledger extraction:

- Traceability/domain/ops synthesis: extracted implementation wiring choices,
  gate implications, validation guidance, and residual risks from the
  traceability, domain, and ops reviews.
- Ergonomics/design synthesis: extracted first-viewport layout, parameter
  editing, warning triage, responsive collapse, focus/keyboard, resistance-row,
  theme, and desktop/web parity findings.
- Workflow/RFC checklist synthesis: checked the ledger role, prompt, source list,
  RFC 0033, required artifact shape, no-byline rule, and final verification
  checklist.

Local parallel reads were also used for the required source files and the small
code cross-checks needed to resolve mesh diagnostics, profile IDs, advisory shape,
and `target_speed_kt` ownership. No Striatum mutation commands were run, no
commits were made, `.striatum` was not edited, and root `OPERATOR_REPORT.md` was
not touched.
