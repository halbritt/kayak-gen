# RFC 0065: UI Polish Redesign

Status: proposed
Date: 2026-06-01
Context: successor visual-system pass over the workspace-UI spine. Builds
directly on the landed surface of
[RFC 0033](0033-workspace-ui-rework.md) (three-region shell, semantic
theme module, claim/readiness/status chips),
[RFC 0034](0034-workspace-ui-follow-up.md) (dynamic presets, review-card
wiring), and [RFC 0035](0035-ui-follow-up-cleanup.md) (validity/state
hygiene), plus the Generate-panel content added by
[RFC 0057](0057-generative-search-jobs-and-web-workspace.md) and the
presentation-layer label registries of
[RFC 0060](0060-web-generate-panel-form-labels-and-tooltips.md),
[RFC 0061](0061-desktop-sliders-on-hull-parameter-metadata.md), and
[RFC 0062](0062-hydrostatics-row-metadata-registry.md). Honors the
claim-truthfulness gates of
[RFC 0025](0025-cfd-calibration-claim-gates.md) and
[RFC 0043](0043-high-angle-gz-successor.md), the RFC 0032 web-analysis
boundary, and the verification discipline in
[`docs/WEB_VERIFICATION.md`](../WEB_VERIFICATION.md). Touches
`kayakgen/ui/theme.py`, `kayakgen/ui/web/` layout/partials, and the
`tests/test_web_*` suite only; it does not change `kayakgen/model`,
`kayakgen/eval`, or `kayakgen/search`. Adds DECISION_LOG row D047
(committed screenshot baselines as the redesign's visual-regression
strategy). Glossary terms (`UBIQUITOUS_LANGUAGE.md`) are cited verbatim;
this RFC introduces no new domain term.

## Problem

The web workspace reached the present shape by accretion of safe slices.
RFC 0033 landed the three-region shell, the semantic theme module
(`kayakgen/ui/theme.py`), and the persistent claim/readiness/status
chips. RFC 0034 and RFC 0035 wired the dynamic bindings and cleaned up
validity/state semantics. RFC 0057 bolted a whole Generate panel
(form-builder, jobs table, 2D Pareto scatter, log tail) onto the same
shell. RFC 0060/0061/0062 added friendly labels and tooltips through
presentation-layer registries.

Each slice was individually correct and individually conservative. The
sum is not a coherent visual system:

- **Tokens are partial.** `theme.py` owns the colour palette
  (`COLORS_LIGHT` / `COLORS_DARK`), a typography map (`TYPOGRAPHY`), a
  plot palette, chip specs (`CHIP_SPECS`), and a `CONTRAST_MANIFEST`.
  There is no spacing scale, no density token set, no elevation/border
  token, and no named focus-ring token. Spacing, padding, and radii are
  therefore expressed as ad-hoc CSS literals scattered across the
  layout partials and the Generate-panel modules, drifting between
  panels.
- **Hierarchy is inconsistent.** The Parameters rail, the Geometry
  metrics strip, the five Review tabs, and the Generate panel each chose
  their own heading weights, section rhythm, and label casing as they
  landed. Nothing enforces a single information hierarchy across the
  shell, so a user scanning the workspace cannot rely on size/weight to
  signal importance.
- **Control and empty/loading/error states are uneven.** Some panels
  (Mesh, Comparison) render explicit "no package" / "no report" states;
  others (Generate jobs table, frontier scatter, CFD) handle the empty
  and in-flight cases differently or implicitly. Hover/focus/active/
  disabled treatment of buttons, selects, and sliders is not uniform.
- **Accessibility is unverified beyond chips.** Focus order, a visible
  focus ring, hit-target sizing, and contrast outside the
  `CONTRAST_MANIFEST` pairs are not asserted. The browser-acceptance
  profile checks behaviour (nonblank 3D, Share reload, STL bytes,
  console cleanliness) but not appearance or a11y.
- **No visual-regression net.** Because there is no screenshot baseline,
  a restyle cannot be landed safely: a change that silently breaks the
  layout, the chip colours, or the claim copy at a given viewport would
  pass the existing tests.

The failure mode is not a missing feature and not a false claim — RFC
0033/0034/0035 already hold the claim line. It is that the workspace
*looks* assembled rather than designed, and that there is no harness to
let a designer iterate on appearance without regressing behaviour or
truthfulness. This RFC scopes a coherent polish pass and the
Playwright/Chromium visual-regression harness that makes it landable in
safe slices.

## Goals

- Extend `kayakgen/ui/theme.py` into a complete visual system: the
  existing colour/typography/chip/contrast tokens **plus** a named
  spacing scale, density tokens, elevation/border/radius tokens, and a
  focus-ring token. Every spacing/radius/elevation literal under
  `kayakgen/ui/` moves into the module, mirroring the RFC 0033 §6
  "theme module is the only authorised home for colour literals" rule
  and its `tests/test_ui_theme.py` orphan-literal lint.
- Establish one information hierarchy across the three-region shell and
  the Generate panel: a single typographic scale (display / heading /
  label / body / caption / metric) applied consistently, consistent
  section rhythm, and consistent card/strip density.
- Define consistent control states (default / hover / focus / active /
  disabled) and explicit, uniform empty / loading / error states for
  every panel that has data to wait on or fail to load.
- Make accessible focus and keyboard behaviour observable: deterministic
  focus order, a visible focus ring sourced from the focus-ring token,
  hit-target minimum sizing, and contrast that satisfies the extended
  `CONTRAST_MANIFEST` in both light and dark palettes.
- Preserve claim truthfulness verbatim: every claim/readiness/status
  chip (`CHIP_SPECS` / `CHIP_LABELS`), every
  raw/local/unvalidated/uncalibrated caption, and the RFC 0033 §8
  no-go list survive the restyle unchanged. No restyle may make an
  unvalidated result look like a confident, validated, or calibrated
  claim.
- Land a Playwright/Chromium screenshot visual-regression harness inside
  the RFC 0032 browser-acceptance profile, with committed baselines, a
  documented tolerance, and a documented baseline-update procedure.
- Keep the RFC 0032 web-analysis boundary exactly where it is. This is a
  presentation pass; it adds no analysis capability, no REST route, and
  no claim-state / readiness / `accepted_uses` literal.

## Non-Goals

- **No new analysis capability.** No new evaluator, metric, chart kind,
  or data surface. The Review tabs, the metrics strip, and the Generate
  panel show exactly the data they show today. The RFC 0032
  web-analysis boundary (compact analysis/comparison surface; no full
  plot tabs, no larger dashboards) is preserved, not silently widened.
- **No claim-line change.** No new `claim_state`, `Readiness` level, or
  `accepted_uses` literal. No promotion of any result. Resistance stays
  `uncalibrated_comparative`; high-angle GZ stays
  `unvalidated_hydrostatic_comparison`; CFD stays `raw_unvalidated`. The
  hosted demo stays deferred per D023.
- **No desktop layout redesign in the core slices.** Per D009 (web is
  the primary UI composition + browser-acceptance target; desktop parity
  means shared core/claim boundaries, not pixel/widget parity) and D021
  (desktop intentionally minimal), the PyVista/PyQt desktop
  (`gui.py` / `pyvista_view.py` shims → `kayakgen/ui/desktop.py` +
  `kayakgen/ui/pv_window.py`) is **out of scope for Slices 1–4 except
  for token-level inheritance**: because the desktop already sources its
  palette and fonts from `theme.py` via `matplotlib_rc_params()` and
  `vtk_background_rgb()`, the Slice 1 token extension flows to the
  desktop automatically and is verified only by keeping the existing
  desktop rendered-bbox tests green. A genuine desktop visual polish
  pass is sequenced as the explicitly-deferred, operator-gated **Slice 5**
  (see Implementation Path); it is not authorised by this RFC's core.
- **No `data-testid` promotion to a public API.** The hook contract
  stays internal (`docs/WEB_VERIFICATION.md`). This RFC may rename, move,
  or remove hooks, but does not turn them into a supported external
  surface (see Open Questions for the stable-public-selector decision).
- **No backend, hosted, worker, real-solver, or calibration work.** No
  OpenFOAM/SU2, no hosted CFD, no calibrated drag, no final prediction,
  no watertight `cfd_ready` promotion, no real high-angle `GZ`.
- **No framework swap.** Trame + Vuetify 3 stays. This is not the RFC
  0008-reserved React/three.js rewrite.

## Proposal

The redesign is a presentation-layer pass over the landed workspace,
sequenced into independently verifiable slices. It changes how the
existing surfaces look and how their states are expressed; it changes
nothing about what they compute or claim.

### 1. Visual system: complete the theme module (Slice 1)

`kayakgen/ui/theme.py` is already the single source for colour,
typography, the plot palette, `CHIP_SPECS` / `CHIP_LABELS` /
`CHIP_CLASSES`, and the `CONTRAST_MANIFEST`. Extend it — additively — so
that *every* visual primitive is a named token:

- **Spacing scale.** A `SPACING` map (e.g. `space-0 … space-7` on a
  consistent step) so panel padding, gaps, and inset rhythm reference
  tokens, not literals.
- **Density tokens.** A `DENSITY` map for control heights, row heights,
  and table row padding, so the desktop-first dense layout and the
  ≤960 px collapse share one definition.
- **Radius / elevation / border tokens.** `RADII`, `ELEVATION`, and
  `BORDERS` maps so cards, chips, selects, and the metrics strip share
  corner and edge treatment.
- **Focus-ring token.** A `--state-focus-ring` colour + width definition
  used by every focusable control, with a `CONTRAST_MANIFEST` entry
  guaranteeing it is visible against `surface-panel` and
  `surface-viewport-bg` in both palettes.
- **State tokens.** Named hover / active / disabled surface and text
  tokens so control states are defined once.

The existing helpers stay the public surface and grow to emit the new
tokens: `css_root_block(dark=False)` includes the new CSS variables,
`vuetify_theme_config()` maps them onto the Vuetify 3 theme registry,
`matplotlib_rc_params()` and `vtk_background_rgb(dark=False)` continue
to serve the desktop. The RFC 0033 §6 invariant is widened: the theme
module is the only authorised home for colour **and now spacing /
radius / elevation / focus** literals under `kayakgen/ui/`, enforced by
extending the `tests/test_ui_theme.py` orphan-literal lint.

Both `COLORS_LIGHT` and `COLORS_DARK` already exist; every new semantic
token MUST resolve in both palettes, and `CONTRAST_MANIFEST` gains the
pairs needed to keep the new tokens (focus ring, state surfaces) within
their minimum ratios.

### 2. Information hierarchy across the shell (Slice 2)

Re-flow the three-region shell — `region-params`, `region-geometry`,
`region-review` — the toolbar, the four status-bar segments, and the
Generate panel onto the Slice 1 tokens, with one hierarchy:

- A single typographic scale applied consistently (the `TYPOGRAPHY`
  `type-display` / `type-heading` / `type-label` / `type-body` /
  `type-caption` / `type-metric` roles), so heading weight signals
  section importance the same way in every panel.
- Consistent section rhythm and card density across the Parameters rail,
  the Geometry metrics strip + 2D accordion, the five Review tabs
  (Hydro / Mesh / Comparison / CFD / Advisories), and the Generate
  panel's build / watch / pick modes.
- The RFC 0033 first-viewport contract is preserved: at 1440×900 the
  first viewport still shows the full Parameters rail, the 3D viewport,
  the metrics strip, the first Review tab, and the status bar; below
  960 px the rail collapses to an accordion and Review becomes the body
  (`kg-collapse-under-960`, `kg-geometry-accordion-under-960`,
  `kg-review-body-under-960`, `kg-status-wrap-under-960` behaviour is
  retained, restyled, not removed).

This slice may rename or move `data-testid` hooks and `kg-*` class hooks
to fit the new structure; see §6.

### 3. Control states and empty / loading / error states (Slice 3)

- **Control states.** Every button, select, slider, toggle, and tab
  gets a uniform default / hover / focus / active / disabled treatment
  from the Slice 1 state + focus-ring tokens. The disabled treatment
  must remain honestly disabled (e.g. the `watertight-solid` profile
  option, the unavailable Export rows from `EXPORT_MENU_ROWS`, the Cm
  reserved-preset case) — disabling is a truthfulness affordance and
  keeps its explanatory copy.
- **Empty / loading / error states.** Each panel that waits on or can
  fail to load data renders an explicit, consistent state with a stable
  hook:
  - Generate jobs table: empty (no jobs), running (in-flight progress),
    failed (`GenerativeJobError.kind` surfaced), cancelled, resumable.
  - Pareto frontier scatter: loading, empty (job not yet `succeeded`),
    rendered.
  - Comparison: no report loaded vs report present.
  - Mesh: `mesh-no-package-chip` vs `mesh-live-readiness-chip`.
  - CFD: no job vs status states, with both persistent banners intact.
  - Share-URL load and invalid-hull-state banners (RFC 0033 §2).
  These states are restyled for consistency; their *copy* — especially
  any claim/availability copy — is unchanged.

### 4. Claim truthfulness is a hard invariant (cross-cutting)

Every slice is gated on the claim line surviving intact:

- All `CHIP_SPECS` keys keep their `CHIP_LABELS` text and semantic class
  (`kg-chip--raw` / `--info` / `--advisory` / `--success` / `--error`).
  A restyle may change a chip's geometry; it may not recolour an
  unvalidated/raw chip into the success palette or drop its label.
- The persistent captions survive byte-for-byte: the resistance card's
  "Raw comparative filter; not final prediction." and uncalibrated
  caption; the high-angle GZ caption "Unvalidated hydrostatic
  comparison; not safety, seaworthiness, calibrated, validated, or
  final-prediction claim." (the exact RFC 0043 stage-3 string); the CFD
  banners "Local filesystem CFD jobs on this server only; no hosted
  worker is running." and "Raw solver artifact only; not calibrated or
  validated."; and the "not watertight cfd_ready" negation.
- The RFC 0033 §8 no-go list stays absent from rendered output. The
  existing `tests/test_web_forbidden_copy.py` regression scan is the
  gate and is extended to cover any new rendered string the redesign
  introduces (state messages, ARIA labels, tooltips).

### 5. Visual-regression harness in the browser-acceptance profile (Slice 4)

Extend the RFC 0032 browser-acceptance profile
(`tests/test_web_browser.py`, run with
`-m browser_acceptance --browser-acceptance`; the
`_browser_acceptance_required` gate already treats missing tooling as a
hard failure in this profile and a skip otherwise):

- **Screenshot visual regression.** Capture the three-region workspace
  at representative viewports — at minimum the desktop-first 1440×900,
  an intermediate 1024×768, and a ≤960 px collapsed width — and compare
  against **committed PNG baselines** with a documented per-viewport
  pixel-difference **tolerance** (to absorb anti-aliasing / font-hinting
  jitter). The nondeterministic 3D `VtkRemoteView` region is **masked
  out** of the pixel diff (its liveness is asserted separately by the
  existing nonblank-3D check, not by pixels). A documented
  baseline-update procedure lands in `docs/WEB_VERIFICATION.md`:
  the canonical-render environment (OS + Chromium build), the
  `--update-visual-baselines` (or equivalent) regeneration command, and
  the review expectation that a baseline change is a reviewed diff, not
  an unexplained binary churn. This is the D047 decision.
- **Assertions that survive the restyle.** The behavioural checks the
  current profile already makes are retained and must pass after the
  restyle: nonblank 3D before *and* after a representative control
  mutation; Share-URL reload round-trip (same `Hull.hash()`); STL bytes
  via the browser-facing API path (`POST /api/stl?part=hull`); and
  console / page-error / network cleanliness. No new network allowlist
  entry is added without the documented URL pattern, expected status,
  rationale, and removal condition note the profile already requires.
- **Accessibility checks.** Deterministic focus order across the shell;
  a visible focus ring (the Slice 1 token) on the focused control;
  contrast satisfying the extended `CONTRAST_MANIFEST`; and a minimum
  hit-target size on interactive controls.
- **Lighthouse Best-Practices ≥ 90.** Retained as the appearance-adjacent
  quality gate at its current threshold (workflow 0020 recorded 92).

**Mandatory vs optional, matching how `WEB_VERIFICATION.md` frames it
today:**

| Check | Optional smoke | Acceptance profile |
| --- | --- | --- |
| Screenshot visual regression | SKIP if Playwright/Chromium absent | **HARD FAILURE** if absent or diff exceeds tolerance |
| Focus order / visible ring / hit targets | SKIP if absent | **HARD FAILURE** if absent |
| Contrast vs `CONTRAST_MANIFEST` | runs in unit tests regardless | **mandatory pytest gate** (no browser needed for the manifest check) |
| Lighthouse Best-Practices ≥ 90 | optional, tool-dependent | **optional, tool-dependent** (Lighthouse + Chromium); recorded, not a mandatory pytest gate |

Missing Playwright/Chromium remains a SKIP in the optional smoke and a
HARD FAILURE in the acceptance profile — unchanged from today and
explicitly extended to the new screenshot and a11y checks.

### 6. The `data-testid` hook contract (cross-cutting)

The `data-testid` hooks (`region-params`, `region-geometry`,
`region-review`, `validity-badge`, `frontier-view-section`,
`generative-jobs-table`, `generative-objective-picklist`,
`generative-submit`, `generative-variable-name`, `param-*`,
`mesh-no-package-chip`, `mesh-live-readiness-chip`, the `kg-*` class
hooks, etc.) are an **internal test contract, not a public API**, exactly
as `docs/WEB_VERIFICATION.md` states. The redesign is permitted to
rename, move, or remove these hooks as the structure changes — but every
renamed / removed / moved hook MUST be reflected in
`tests/test_web_layout.py` and `tests/test_web_inline_help.py` in the
same slice, so the change is caught at verification time rather than
silently breaking the layout contract. This RFC does not turn the hooks
into a supported external surface; whether to add a separate stable
public selector layer instead of leaning on `data-testid` is an Open
Question.

## Acceptance Criteria

- This RFC lands as documentation only and authorises no runtime
  behaviour change by itself. Its slices are landed by later
  implementation passes, each its own commit.
- **Slice 1 observable:** `theme.py` exposes named spacing, density,
  radius/elevation/border, focus-ring, and state tokens; every new
  semantic token resolves in both `COLORS_LIGHT` and `COLORS_DARK`
  (or the light/dark variant maps); the extended
  `tests/test_ui_theme.py` orphan-literal lint fails if any
  spacing/radius/elevation/focus/colour literal lives outside the
  module; `CONTRAST_MANIFEST` covers the focus-ring and state tokens and
  every pair meets its minimum ratio in both palettes; desktop
  rendered-bbox tests stay green (token inheritance verified).
- **Slice 2 observable:** the shell still exposes `region-params`,
  `region-geometry`, `region-review` and the four status-bar segments;
  the 1440×900 first-viewport contract and the ≤960 px collapse
  behaviour hold; `tests/test_web_layout.py` passes after any hook
  rename/move (all renamed hooks reflected in the test).
- **Slice 3 observable:** every panel renders an explicit empty /
  loading / error state with a stable, tested hook; control
  hover/focus/active/disabled states derive from theme tokens; honestly
  disabled controls keep their explanatory copy;
  `tests/test_web_inline_help.py` reflects any hook change.
- **Claim line observable (cross-cutting):** every `CHIP_SPECS` key
  keeps its `CHIP_LABELS` text and semantic class; the resistance,
  high-angle GZ, and CFD captions are byte-identical to today; the RFC
  0033 §8 no-go list is absent; `tests/test_web_forbidden_copy.py`
  passes and is extended to cover every new rendered string.
- **Slice 4 observable:** the browser-acceptance profile captures
  committed-baseline screenshots at the representative viewports with a
  documented tolerance and masks the 3D region; nonblank-3D
  (before/after mutation), Share reload round-trip, STL-bytes-via-API,
  and console/page/network cleanliness all still pass; focus order,
  visible focus ring, contrast, and hit-target checks pass; Lighthouse
  Best-Practices ≥ 90 is recorded; missing Playwright/Chromium is a SKIP
  in optional smoke and a HARD FAILURE in the acceptance profile;
  `docs/WEB_VERIFICATION.md` documents the baseline-update procedure and
  the mandatory-vs-optional gate table.
- **Boundary observable:** no new REST route, no new `claim_state` /
  `Readiness` / `accepted_uses` literal, no new evaluator or analysis
  surface; the RFC 0032 web-analysis boundary text is unchanged.
- **Docs observable:** when a slice lands, `CHANGELOG.md`,
  `docs/WEB_VERIFICATION.md`, and `docs/USER_GUIDE.md` are updated to
  describe only the polish behaviour and the new verification gate;
  DECISION_LOG row D047 is present.

## Open Questions

- **Desktop parity timing.** When, if ever, does Slice 5 (a genuine
  desktop visual polish pass beyond automatic token inheritance) land?
  Lean: defer until a desktop need is recorded, consistent with D009 /
  D021; the core slices deliberately give the desktop token-level
  inheritance only.
- **Visual-regression baseline storage and flake tolerance.** Commit PNG
  baselines directly in-repo (simple, but binary churn and repo growth),
  via Git LFS, or as a downloaded artifact set? What per-viewport
  pixel-diff tolerance absorbs anti-aliasing without hiding real
  regressions, and which canonical OS + Chromium build renders the
  baselines (font rendering differs across platforms and is the usual
  source of screenshot flake)? Should the baselines be full-shell or
  per-region/component (component baselines are more stable but more
  numerous)? D047 commits to *committed baselines + tolerance*; the
  storage mechanism and exact tolerance are for the harness slice.
- **Dark / light theming.** Ship a user-facing light/dark toggle now
  (both palettes already exist in `theme.py`) or follow OS preference
  only with a toggle in the toolbar overflow (the RFC 0033 lean)? Either
  way, both palettes must pass the visual-regression and contrast gates.
- **Mobile / responsive scope.** Keep the RFC 0033 "inspect-and-triage
  only below 960 px" posture and merely restyle the collapse, or invest
  in genuine mobile editing polish (out of the conservative scope)?
- **Stable public selector surface.** Should the project introduce a
  separate, documented stable selector layer (e.g. ARIA roles/names, or
  a `data-kg-*` attribute set) so external automation has a supported
  target — letting `data-testid` stay purely internal and freely
  renamable — or keep the status quo where `data-testid` is internal and
  external automation is steered to the `/api/*` REST surface?
- **Slice granularity for screenshots.** Should the visual-regression
  baseline be introduced in Slice 4 against the *post-redesign* shell
  only, or captured first against today's shell (Slice 0) so each
  intermediate slice's diff is reviewable? Lean: capture a pre-redesign
  baseline early so Slices 2–3 produce reviewable visual diffs.

## Implementation Path

Each slice lands as its own commit per the one-phase-per-RFC rule and is
independently verifiable. Behaviour and claim copy stay byte-stable
across all of them.

- **Slice 0 — Pre-redesign baseline (optional, recommended).** Land the
  screenshot-capture scaffolding and commit a baseline of *today's*
  shell so Slices 2–3 produce reviewable visual diffs. No appearance
  change.
- **Slice 1 — Theme/visual-system foundation.** Extend `theme.py` with
  spacing/density/radius/elevation/border/focus-ring/state tokens;
  widen the `tests/test_ui_theme.py` orphan-literal lint to cover the
  new literal classes; extend `CONTRAST_MANIFEST`; confirm desktop
  rendered-bbox tests stay green. No layout change.
- **Slice 2 — Shell layout & information hierarchy.** Re-flow the
  three-region shell, toolbar, status bar, and Generate panel onto the
  Slice 1 tokens and one typographic hierarchy; preserve the 1440×900
  first-viewport contract and the ≤960 px collapse; reflect every
  renamed/moved `data-testid` / `kg-*` hook in
  `tests/test_web_layout.py`.
- **Slice 3 — Control + empty/loading/error states.** Apply uniform
  control states and explicit per-panel empty/loading/error states;
  keep honestly-disabled controls and their copy; reflect hook changes
  in `tests/test_web_inline_help.py`; extend
  `tests/test_web_forbidden_copy.py` to cover any new rendered string.
- **Slice 4 — Visual-regression + a11y harness.** Extend the
  browser-acceptance profile with committed-baseline screenshot
  regression (masking the 3D region) at the representative viewports,
  focus-order / visible-ring / hit-target / contrast checks, and the
  Lighthouse gate; document the baseline-update procedure and the
  mandatory-vs-optional table in `docs/WEB_VERIFICATION.md`. This slice
  ratifies D047 in practice.
- **Slice 5 — Desktop visual polish (deferred, operator-gated).**
  Out of scope for this RFC's core; sequenced for a later workflow only
  if an operator records the need, per D009 / D021.

## Domain Modeling

This RFC adds no domain concept. Per `DDD.md § "Adding to the model"`,
the change is a **boundary clarification** of the existing presentation
context: the web workspace remains a presentation surface over the same
`Hull` aggregate and the same `EvaluationResult` / `ComparisonReport` /
`GenerativeJob` read models, and over the same `ClaimState` /
`Readiness` literals — none of which this RFC touches. It is the same
posture RFC 0033/0034/0035 took.

The new theme tokens are presentation-catalog entries in the spirit of
the D043 "presentation-layer registry per surface family" pattern
(`HullParameterMetadata`, `HydrostaticsRowMetadata`): a single source of
truth the UI consults, owning no aggregate invariant. They are CSS
variables and Python token maps, not domain value objects, so per the
glossary-first principle they do **not** earn a
`docs/UBIQUITOUS_LANGUAGE.md` entry on their own. If a slice later
introduces a named presentation concept that a future contributor must
use unambiguously (e.g. a "density mode" selector), that concept lands
in the glossary first, then the code — and this RFC's Acceptance
Criteria require it.

The committed screenshot baselines are a **durable test artifact**, not
a domain durable: they live under the test tree, are regenerated by a
documented procedure, and carry no claim. They are the visual analogue
of the golden-regression fixtures the project already maintains, and
their adoption is recorded as DECISION_LOG row D047 rather than as a new
aggregate.
