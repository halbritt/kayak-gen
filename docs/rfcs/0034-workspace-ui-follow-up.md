# RFC 0034: Workspace UI Follow-Up

Status: accepted implementation target
Date: 2026-05-14
Context: successor to RFC 0033 and workflow 0044 final review. Uses
`striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md` as the
finding source and keeps RFC 0033's no-new-backend-capability boundary.

## Problem

Workflow 0044 landed the conservative workspace UI safe slice, but the
final review accepted it with follow-up findings. The web workspace now
has the correct regions, status language, theme, and supporting read
models, but several dynamic UI bindings are still static or unwired:
class presets do not reseed or narrow sliders, the validity badge is a
placeholder, the Resistance and Mesh cards do not render their new read
models, the Export menu exposes only STLs, and the forbidden-copy test
does not cover the full RFC 0033 no-go string set.

The failure mode is conservative but user-visible: the UI avoids false
claims, yet it does not fully expose the accepted data shape or
interaction semantics from RFC 0033.

## Goals

- Make web class presets reseed the canonical hull sliders and narrow
  ranges to the selected `KayakClass` envelope, while later manual edits
  return the rail to `custom`.
- Replace the static validity badge with a derived badge mirroring the
  existing class/envelope semantics.
- Wire `resistance_table_view_model` into the Resistance card, including
  fixed sweep rows, target-speed focus row, and raw comparative claim
  language.
- Wire `mesh_diagnostics_lines_from_state` and `mesh_package_view_model`
  into the Mesh tab so welded-primary counts, warnings, profile choice,
  and readiness copy are visible.
- Complete the Export menu entries for Hydro JSON, Stability JSON, and
  Mesh package without inventing hosted storage or new solver capability.
- Expand forbidden-copy regression tests to cover the full RFC 0033 §8
  no-go list.
- Keep docs, changelog, and user guide aligned with the current safe
  behavior and explicit deferrals.

## Non-Goals

- No hosted CFD worker, OpenFOAM/SU2 integration, calibrated drag,
  final prediction, design fitness, high-angle GZ, or watertight
  `cfd_ready` promotion.
- No desktop `QMainWindow`/`QTabWidget` parity rewrite. Desktop remains
  limited to the already-landed safe touch-ups.
- No new REST route shape unless an existing local route already exposes
  the data safely.
- No multi-variant overlay, Pareto plot widget, persistent pinned
  candidates, or multi-user share.

## Proposal

Implement only the dynamic UI and regression-test follow-ups from the
workflow 0044 final review:

1. Add a small web read-model/binding layer for class preset state:
   choosing `touring`, `performance`, `surfski_int`, or `surfski_elite`
   updates the relevant sliders from `KayakClass.default` and constrains
   their visible ranges to the class envelope. Manual slider changes
   switch the selected class to `custom`.
2. Derive the bottom rail validity badge from the active hull and class
   envelope. The badge strings are limited to the RFC 0033 strings:
   `In <class> envelope`, `Custom — sub-touring`,
   `Custom — beyond elite`, or `Custom (L/B_wl=X.X)`.
3. Render the Resistance card from `resistance_table_view_model` rather
   than static copy alone. The target-speed row is highlighted, and the
   card keeps the `uncalibrated_comparative` chip and raw comparative
   warning.
4. Render the Mesh tab from current hull diagnostics and optional mesh
   package manifest state. Welded-primary counts are primary, raw counts
   remain visible as detail, and `watertight-solid` remains disabled
   unless an upstream RFC lands the required geometry.
5. Extend the export affordance with safe local actions for Hydro JSON,
   Stability JSON, and Mesh package where existing code already supports
   the artifact. Unsupported export entries must be disabled or clearly
   unavailable rather than pretending success.
6. Broaden tests so all RFC 0033 no-go strings are asserted absent, with
   explicit allowances only for permitted negations such as "no hosted
   worker is running" and "not watertight cfd_ready".

## Acceptance Criteria

- Selecting a web class preset changes the relevant slider values and
  slider bounds according to `KayakClass`, and manual edits switch the
  selected preset to `custom`.
- The web validity badge changes with hull state and uses only the
  accepted RFC 0033 badge strings.
- The Resistance card displays the fixed sweep speeds, target-speed row,
  and `kt | Fn | Rv N | Rw N | Rt N` data from the read model.
- The Mesh tab displays hull/deck diagnostics and package readiness
  using welded-primary counts and existing readiness vocabulary.
- Export controls include Hull STL, Deck STL, Hydro JSON, Stability
  JSON, and Mesh package entries, with unavailable states honest.
- Tests cover the full RFC 0033 §8 forbidden-copy list and preserve
  existing browser acceptance.
- User-facing docs/changelog describe only current safe behavior.

## Open Questions

- Whether Hydro JSON and Stability JSON should download from a browser
  blob or first land as local server artifacts.
- Whether Mesh package export should invoke existing server-local
  package creation immediately or remain a disabled entry until a
  workflow explicitly accepts web-side package authoring.

## Implementation Path

- Step 1 — First-pass traceability, domain/no-claims,
  ergonomics/design, and ops/test reviews over this RFC and the 0044
  final-review findings.
- Step 2 — Consolidate findings into a ledger that distinguishes
  safe-now UI bindings from any export behavior that requires a later
  RFC.
- Step 3 — Implement the accepted safe-now slice with Codex, using
  parallel sub-agents for disjoint UI, controller/read-model, tests,
  and docs scopes.
- Step 4 — Run focused web/layout/read-model/browser tests and final
  review before merging.

## Domain Modeling

Boundary clarification. This RFC does not create new domain concepts; it
binds existing `KayakClass`, claim-state, mesh-readiness, resistance,
and advisory value objects into the web workspace without changing their
meaning.
