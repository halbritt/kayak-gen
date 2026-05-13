# RFC 0033: Workspace UI Rework

Status: proposed
Date: 2026-05-13
Context: distills the Claude Design "UI Rework Handoff" bundle for
`kayak-gen`. Companion to RFC 0008 (web frontend), RFC 0013 (Pareto
comparison UI), RFC 0018 (web CFD job routes), and RFC 0031 (design
constraint surfacing revision). The handoff itself is captured in
`docs/workflows/0044-workspace-ui-rework/SOURCES.md`. See `striatum/0044-workspace-ui-rework/`
for run artifacts once the workflow lands.

## Problem

The kayakgen desktop and web frontends have diverged into ad-hoc
panels around a parametric-hull-plus-local-CFD pipeline. RFCs 0005,
0006, 0010, 0013, 0015, 0018, 0025, and 0031 have each landed a
backend slice (resistance, class presets, mesh packages, comparison,
local CFD, claim gates, design validity), but no UI layer turns those
slices into a single, dense, truthful workspace.

Today:

- Web `app.py` is a Trame drawer plus three flat tabs (Analysis,
  Comparison, CFD). It has no parameter rail per the design intent, no
  toolbar, no status bar, no claim/readiness/status chips, and no
  shared theme.
- Desktop `desktop.py` mixes matplotlib widgets with hardcoded plot
  colours (`steelblue`, `seagreen`, `crimson`) and pops PyVista into a
  separate window. The metrics panel is a free-text block, not a
  structured Review.
- Both surfaces show resistance numbers, CFD job state, and mesh
  readiness without the persistent claim/readiness language RFC 0025
  and RFC 0010 require, so users can — and do — misread raw
  comparative numbers as design fitness.
- The VTK background is a brand-flavoured dark slate-blue
  (`(0.10, 0.10, 0.18)`), which is on the explicit avoid list from the
  handoff design constraints.

The failure mode is not a missing feature: it is that the existing
features are present but visually disconnected, inconsistently
labelled, and silent about their claim boundary. A user can render a
mesh package, prepare a CFD job, and read a Rt(N) value without ever
seeing "raw comparative filter; not final prediction" in the same
viewport.

## Goals

- Land a single three-region workspace shell — parameters,
  geometry, review — that both desktop and web surfaces map onto.
- Surface every existing backend slice (hydrostatics, stability,
  resistance, mesh diagnostics, mesh package readiness, comparison,
  local CFD) inside the workspace, using the existing controllers and
  payloads.
- Anchor every numeric output to its claim state (RFC 0025) and every
  package to its readiness level (RFC 0010) via persistent chips and
  status-bar segments.
- Replace ad-hoc plot colours and the slate-blue VTK background with a
  shared semantic theme.
- Keep the rework primarily frontend-only. Backend touches are limited
  to a structured advisory record and a handful of read-model helpers
  for the new view models.
- Make every "do not claim" string from the handoff visible to a
  regression test, so future copy edits can not quietly reintroduce
  forbidden language.
- Preserve every existing REST route and CLI behaviour.

## Non-Goals

- New backend capabilities. No hosted CFD worker, no multi-user
  share, no real-time collaboration, no calibrated-model resistance.
- Multi-variant 2D geometry overlay in the geometry pane. Defer to a
  follow-up RFC; today the geometry pane shows the focused hull only.
- Web-side mesh-package authoring API. The web Build action wraps the
  existing `kayakgen mesh-package` semantics server-locally; it does
  not introduce a new authoring API surface.
- Pareto plot widget on Comparison. Out of scope; the candidate table
  and pinned strip stay table-shaped.
- Persisting pinned candidates in the share URL. In-session only.
- High-angle GZ visualisation, calibrated drag chips, validity
  envelopes. RFCs 0020/0024 and 0012/0019/0027 remain backlog.

## Proposal

### 1. Three-region workspace shell

Replace `SinglePageWithDrawerLayout` on web (and the matplotlib
`GridSpec` on desktop) with a three-region shell:

```
┌──── Toolbar: kayakgen ▸ <hull>      [Class] [Reset] [Share] [Export ▾] ┐
│ Parameters rail  │  Geometry pane                  │  Review pane     │
│  ≈ 320 px        │  flex, ≥ 560 px wide            │  ≈ 420–520 px   │
└──── Status bar:  package · readiness · resistance · cfd ──────────────┘
```

At 1440×900 the first viewport must show the entire Parameters rail,
the 3D viewport (≥ 480 px square), the Metrics strip, the first
Review tab (Hydro → Hydrostatics), and the Status bar. Below 960 px,
Parameters becomes a top accordion and the Review pane becomes the
body — the rework is desktop-first; mobile is inspect-and-triage
only.

### 2. Parameter rail

Drive `Hull` editing with constraints visible.

- Class preset radio group at top: `touring`, `performance`,
  `surfski_int`, `surfski_elite`, `custom`. Selecting a preset
  reseeds five sliders and narrows their ranges to the class
  envelope (existing `KayakClass`). Any subsequent edit flips to
  Custom; this preserves the desktop semantics today.
- One slider per Hull field in the order documented in the handoff:
  `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`,
  `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`,
  `stern_rake`, plus the view-only `target_speed_kt`. `Cm` is
  currently web-only; desktop adopts it here. `LCB_frac`,
  `rocker_bow_m`, and `rocker_stern_m` stay hidden — they ride RFC
  0031's `unsupported` channel.
- `beam_wl_m` continues to clamp to `beam_oa_m` live via the existing
  `clamp_beam_wl_state` controller helper.
- Each row carries an advisory dot (yellow) when at least one
  structured advisory cites that field, plus a numeric input on
  hover/focus and class-envelope ticks when a preset is active.
- A bottom Validity badge summarises the hull: `In <class> envelope`,
  `Custom — sub-touring`, `Custom — beyond elite`, or `Custom
  (L/B_wl=X.X)`. The kind is derived from existing logic in
  `desktop._classify`.
- States: `default`, `loading shared URL`, `invalid hull state`
  (banner pinned above; per-field red border with
  `validation_error_payload` detail), and the disabled Cm slider when
  the active preset does not surface Cm yet (note: "Cm — reserved for
  future preset surfacing").

### 3. Geometry pane

- 3D view embedded, not popped. Trame `VtkRemoteView` on web; desktop
  embeds the existing `pv_window.PyVistaWindow` into the main window
  via `QDockWidget`.
- VTK renderer background switches from `(0.10, 0.10, 0.18)` to the
  shared `--surface-viewport-bg` token.
- Camera toolbar (top-right): reset, front, side, top, iso, toggle
  deck visibility, toggle wireframe.
- Metrics strip below the viewport — one monospace row:

  ```
  Δ 95.4 kg · Sw 1.812 m² · Awp 1.244 m² · Cp 0.553 · Cm 0.802 · L/B_wl 9.0 · Fn 0.31 · Rt 11.4 N
  ```

  Each token is clickable and scrolls the Review pane to the matching
  detail. The strip is sourced from `metrics_from_state(...)`; no new
  read model is required.
- 2D triple (cross-section, sheer plan, plan view) renders below the
  3D view in a collapsible accordion. Hardcoded `steelblue`,
  `seagreen`, `crimson` literals are replaced with the
  `--data-hull`, `--data-deck`, and `--state-focus-rail` tokens.

### 4. Review pane

Five tabs, in order: Hydro, Mesh, Comparison, CFD, Advisories.

**Hydro**: three sub-cards.

- **Hydrostatics** — label/value/unit rows from
  `analysis_view_model(...)["hydro_rows"]` plus a footer chip
  `Computed from integrated geometry (60 stations)`.
- **Stability** — `GM₀` headline with the chip "Primary stability
  (analytic from waterplane)". An optional load-case form (mass /
  hull mass / cargo / KG) drives the bounded fixed-body equilibrium
  readout; the trim/sinkage result carries the
  `uncalibrated_comparative` claim chip. A permanent **High-angle GZ
  unavailable** block reproduces the exact handoff copy and cites RFC
  0020 / RFC 0024 by number only.
- **Resistance** — header "Resistance — raw comparative filter" with
  the persistent caption "Uncalibrated; no accepted final-prediction
  validity envelope. Compare nearby candidates, do not report as
  drag." Sweep table at speeds `[2.0, 3.0, 4.0, 5.0, 6.0] kt` plus
  the target-speed row highlighted with `--state-focus-row`. Columns
  `kt | Fn | Rv N | Rw N | Rt N` plus an inline Rv/Rw mini-bar.
  Footer chip strip mirrors `resistance_metadata.warnings`.

**Mesh**: three cards.

- **Hull diagnostics** — boundary edges, non-manifold edges,
  degenerate faces, readiness chip, warnings list, sourced from
  `MeshDiagnostics`.
- **Deck diagnostics** — same shape.
- **Package readiness** — profile select (`open-wetted-surface`
  default; `watertight-solid` disabled with the tooltip "Current
  generated packages do not satisfy watertight-solid readiness."),
  readiness chip, warnings list, the persistent side-caption "Open
  wetted-surface profile; not watertight cfd_ready." when the level
  is `cfd_surface_candidate`, and a `Build package` action wired to
  the existing `kayakgen mesh-package` semantics. Manifest field
  names follow `MeshPackageManifest`.

**Comparison**: drop zone + `Paste JSON` toggle, candidate table with
columns `idx | status | pareto | key | objectives… | warnings`, a
pinned-strip area (up to 4 candidates) showing per-row deltas with
`--state-delta-pos` / `--state-delta-neg`, and a report footer with
the `spec_hash` (monospace, selectable) and any report-level
warnings.

**CFD**: the existing setup → status → artifact panel surfaces, with
exact chip and banner copy from the handoff (top banner: "Local
filesystem CFD jobs on this server only; no hosted worker is
running.", post-status strapline: "Raw solver artifact only; not
calibrated or validated."). Status chips and error-kind copy follow
the §6 tables.

**Advisories**: a flat list of `design_advisory` warnings with
clickable field-name chips that focus the relevant slider in the rail.
This is the first consumer of the structured Advisory record below.

### 5. Toolbar and status bar

Toolbar contents are: workspace breadcrumb (`kayakgen ▸ <hull.name>`,
inline-editable; persists to `Hull.name`), class preset
quick-select (mirrors the rail radio), `Reset`, `Share` (existing
`encode_hull_query`; surface only a toast, not a permanent URL
field), `Export ▾` (`Hull STL`, `Deck STL`, `Hydro JSON`, `Stability
JSON`, `Mesh package…`).

Status bar surfaces four segments separated by middots:

```
package: <profile> · readiness: <level> · resistance: <claim_state> · cfd: <status>
```

Each segment is clickable and focuses the matching Review tab. Chip
colour follows the semantic palette.

### 6. Semantic theme module

Introduce `kayakgen/ui/theme.py` as the single source for colour
tokens, typography stacks, and chip text.

- Colour tokens follow the §7.6 contract: teal-anchored neutral with
  green success. Orange is reserved for unavailable / raw /
  uncalibrated chips and the wave-resistance data colour; it never
  tints surfaces. Both `COLORS_LIGHT` and `COLORS_DARK` are exposed.
- Typography tokens follow §7.2: a mono stack (JetBrains Mono / IBM
  Plex Mono / ui-monospace) for metrics strips and tables, and a
  condensed sans stack (Inter Tight / IBM Plex Sans / system-ui) for
  labels, captions, and buttons.
- Helpers: `css_root_block(dark=False)` for CSS variable injection,
  `vuetify_theme_config()` for the Vuetify3 theme registry,
  `matplotlib_rc_params()` for the desktop plots, and
  `vtk_background_rgb(dark=False)` for the 3D viewport.
- The theme module is the only authorised home for hex colour
  literals and named colours under `kayakgen/ui/`. Acceptance §10
  enforces this with a lint test.

### 7. Structured advisory record

The single backend touch: upgrade `DesignAdvisory` so the parameter
rail can attach advisory dots to specific fields.

- Add an `Advisory` record `{code: str, message: str, field_refs:
  tuple[str, ...]}` carrying the same band guidance currently
  expressed as strings.
- Keep `DesignAdvisory.warnings: tuple[str, ...]` unchanged for
  callers and tests that already depend on the string list (this is a
  RFC 0031 compatibility constraint).
- Add `DesignAdvisory.advisories: tuple[Advisory, ...]` alongside.
- Wire one optional helper into `controllers.py`,
  `evaluation_summary(state)`, that bundles hydrostatics, advisories,
  readiness, resistance claim, and the current CFD job status for the
  Status bar. No new persistence; this is a pure read-model.

### 8. Forbidden-claim guard

The rework must not introduce forbidden strings into normal UI
output. The handoff §1 and §6 enumerate the no-go list; the
acceptance tests below convert each into a grep-style assertion so
this constraint is enforced going forward.

### 9. Compatibility

- All existing REST routes keep their JSON shape (`/api/evaluate`,
  `/api/stl`, `/api/cfd/*`, `/api/hulls/*`).
- All existing controller helpers keep their callable signatures.
  `analysis_lines_from_state`, `cfd_status_lines_from_payload`, etc.
  remain valid and used by their current callers, in addition to the
  new tab-specific view models.
- Existing share URL round-trip (`encode_hull_query` /
  `decode_hull_query`) is unchanged.
- The desktop "Generate STLs" button is renamed "Export STLs" but
  still writes the same `<stem>_hull.stl` / `<stem>_deck.stl` files
  via `geom.generate_stl(...)`.

## Acceptance Criteria

- Workspace shell renders three regions on desktop and web with the
  test ids `region-params`, `region-geometry`, `region-review`, and
  the four status-bar segments documented in §5.
- Parameter rail includes every `HULL_STATE_FIELDS` slider plus
  `target_speed_kt` and class radio; `beam_wl_m` continues to clamp
  to `beam_oa_m`.
- Review tab order is Hydro, Mesh, Comparison, CFD, Advisories.
- Resistance card carries the persistent caption "Raw comparative
  filter; not final prediction." and tags every `Rt` value with the
  `uncalibrated_comparative` claim chip.
- Stability sub-tab carries the exact block heading "High-angle GZ
  unavailable" and does not render any numeric `GZ_max` or
  `heel_angle_max_deg`.
- Mesh tab does not render the bare word `cfd_ready` outside the
  explanatory negation "not watertight cfd_ready" for the current
  generated packages.
- CFD tab renders both persistent banners ("Local filesystem CFD
  jobs on this server only; no hosted worker is running." and "Raw
  solver artifact only; not calibrated or validated.") and does not
  contain `hosted`, `cloud`, `worker queue`, `OpenFOAM`, or `SU2`
  outside the no-hosted-worker notice.
- `kayakgen/ui/theme.py` exists; every hex literal and named colour
  under `kayakgen/ui/` lives in that module; matplotlib rcParams and
  VTK background are sourced from it.
- Desktop GUI exposes a `Cm` slider with the same range/step as the
  web rail.
- Sharing toasts "Shareable URL copied" instead of pinning the URL
  in a text field.
- `evaluation_summary(state)` exists and returns
  `{package, readiness, resistance_claim, cfd_status,
  advisories}` for the Status bar.
- Every existing `tests/test_web.py` test passes unchanged.
- New `tests/test_web_layout.py` covers the §10 assertions below.

## Open Questions

- Should the desktop frontend ship the same status bar or only the
  rail-pinned validity badge? Lean: ship both; desktop already has a
  matplotlib status text area, so the migration is cheap.
- Should the toolbar surface a light/dark toggle, or follow OS
  preference only? Lean: follow OS preference by default; expose a
  toggle in the toolbar overflow.
- Should the Mesh tab's `Build package` button block on a long-running
  manifest write or stay synchronous like the CLI? Lean: synchronous
  with a spinner, matching the CLI behaviour.

## Implementation Path

1. Land `kayakgen/ui/theme.py` with the §7.6 token contract and the
   four helpers, and route matplotlib rcParams + VTK background
   through it.
2. Add structured `Advisory` records to `kayakgen/model/advisory.py`
   while keeping `warnings: tuple[str, ...]` intact.
3. Add `evaluation_summary(state)`,
   `mesh_diagnostics_lines_from_state(part)`, and
   `mesh_package_view_model(path)` to
   `kayakgen/ui/web/controllers.py`.
4. Refactor `kayakgen/ui/web/app.py` into a three-region workspace
   shell: new `kayakgen/ui/web/layout/` partials for `ToolbarBar`,
   `ParameterRail`, `GeometryViewport`, `MetricsStrip`,
   `ReviewTabs`, and `StatusBar`. Existing Vue state keys remain
   stable so the controllers do not move.
5. Build the five Review tabs against the existing read models, with
   chips and persistent banners sourced from `theme.py`.
6. Update `kayakgen/ui/desktop.py`: rename "Generate STLs" → "Export
   STLs", add the `Cm` slider through `gui_params.GUI_TO_HULL`, embed
   the PyVista view via `QDockWidget`, replace hardcoded plot
   colours with `theme.PLOT_PALETTE`, and add the four-segment status
   bar.
7. Add `tests/test_web_layout.py` for the new layout, chip, and
   forbidden-string assertions, plus a `tests/test_ui_theme.py`
   covering the orphan-colour-literal lint.
8. Update `CHANGELOG.md`, `docs/USER_GUIDE.md`, and `OPERATOR_REPORT.md`
   to describe the new workspace.

## Domain Modeling

The new `Advisory` record is a **value object** in
`kayakgen/model/advisory.py`: an immutable bundle of (code, message,
field references) attached to the existing `DesignAdvisory` aggregate
output. It is not a new aggregate root; it is shape-compatible with
RFC 0031's `DesignValidityFinding` and may collapse into that record
in a future revision once the validity-finding model fully covers the
advisory band content.

The workspace itself is not a domain concept — it is a **boundary
clarification**: every domain output (hydrostatics, resistance, mesh
diagnostics, mesh package readiness, comparison report, CFD run
record) is presented through one consistent presentation contract
defined by `kayakgen/ui/theme.py` plus the read models in
`kayakgen/ui/web/controllers.py`.

Refer to `DDD.md § "Adding to the model"` when promoting `Advisory`
into the shared validity model; the migration window is RFC 0031's
implementation pass.
