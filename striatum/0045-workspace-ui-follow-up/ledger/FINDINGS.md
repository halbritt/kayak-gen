# Findings Ledger - RFC 0034 Workspace UI Follow-Up

## Gate Verdict

`accept_with_findings`

RFC 0034 is reviewable and implementation-ready as a conservative follow-up
slice. The first-pass reviews found no packet blocker that requires a
`needs_revision` remediation cycle. The implementation lane should treat this
ledger as the scope boundary: wire the dynamic web UI behavior and regression
tests left by workflow 0044 final review F1-F6, while preserving RFC 0033's
no-new-backend-capability and no-claims constraints.

The safest interpretation is presentation and browser/controller wiring only:
class preset behavior, validity badge derivation, Resistance and Mesh card
read-model rendering, honest Export menu entries, broader forbidden-copy tests,
and factual docs/changelog updates. Do not expand RFC 0034 into hosted CFD,
calibrated physics, watertight readiness, high-angle stability, web-side mesh
authoring, or desktop parity rewrites.

## Review Stats And Source Summary

Required and supporting sources read for this ledger:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/design/kayak_hull_design_constraints.md`
- `docs/rfcs/README.md`
- `generator.py`
- `docs/CONTEXT_HYGIENE.md`
- `docs/workflows/0045-workspace-ui-follow-up/roles/ledger.md`
- `docs/workflows/0045-workspace-ui-follow-up/prompts/findings_ledger.md`
- `docs/workflows/0045-workspace-ui-follow-up/workflow.json`
- `docs/rfcs/0034-workspace-ui-follow-up.md`
- `docs/rfcs/0033-workspace-ui-rework.md`
- `docs/USER_GUIDE.md`
- `striatum/0045-workspace-ui-follow-up/review_remediation/REMEDIATION.md`
- `striatum/0045-workspace-ui-follow-up/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0045-workspace-ui-follow-up/domain/REVIEW_DOMAIN.md`
- `striatum/0045-workspace-ui-follow-up/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`
- `striatum/0045-workspace-ui-follow-up/ops/REVIEW_OPS.md`
- `striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md`
- `striatum/0044-workspace-ui-rework/ledger/FINDINGS.md`
- `striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md`

Review verdicts:

| Source | Verdict intent | Ledger treatment |
| --- | --- | --- |
| Review remediation | `accept_with_findings` intent | Accept packet readiness; carry export and forbidden-copy caveats forward. |
| Traceability review | `accept_with_findings` | Accept; use T1-T6 to pin implementation ambiguities. |
| Domain/no-claims review | `accept_with_findings` | Accept; preserve no-claims copy, chips, and deferrals as hard boundary. |
| Ergonomics/design review | `accept_with_findings` | Accept; carry interaction, accessibility, and layout refinements into scope. |
| Ops/test review | `accept_with_findings` | Accept; carry export safety, test matrix, browser coverage, and manifest containment checks forward. |
| Workflow 0044 final review | `accept_with_findings` | Use F1-F6 as source findings; exclude F7 cosmetic mismatch and keep F8 deferred. |
| Workflow 0044 ledger | `accept_with_findings` | Preserve explicit deferrals and validation discipline. |

Input review volume:

- 25 explicit first-pass review findings/actions were deduplicated: 6
  traceability findings, 2 domain findings, 8 ergonomics/design findings, and
  9 ops/test findings.
- Workflow 0044 final-review F1-F6 are the canonical residual source findings.
  F7 is a cosmetic patch-summary/changelog mismatch and is not a product
  requirement. F8 desktop region/test-id parity remains an explicit deferral.
- The 25 first-pass findings reduce to 8 implementation findings, 1 safe-now
  scope definition, 1 validation matrix, and 1 successor-risk list.

Source artifact summary:

- `REVIEW_TRACEABILITY.md` confirms one-for-one mapping from workflow 0044
  F1-F6 to RFC 0034 and flags export, forbidden-copy allowances, badge
  normalization, manual-edit semantics, mesh live-vs-manifest binding, and
  resistance chip placement as implementation-scope choices.
- `REVIEW_DOMAIN.md` accepts the packet but requires every resistance, mesh,
  stability, and CFD surface to keep explicit no-claim language attached.
- `REVIEW_ERGONOMICS_DESIGN.md` accepts the packet and tightens preset event
  handling, Resistance card ownership, Mesh profile affordance, exact badge
  strings, Export menu shape, forbidden-copy allow-listing, and touched
  accessibility/responsive behavior.
- `REVIEW_OPS.md` accepts the packet and identifies export scope, preset
  binding, mesh/readiness overclaim risk, browser coverage gaps, forbidden-copy
  target scoping, manifest containment, and STL filename/header assertions.
- `REMEDIATION.md` confirms no RFC 0034 product code was changed during packet
  remediation and highlights export behavior and forbidden-copy coverage as
  caveats for this ledger.

## Deduplicated Findings

### P0 - Export Menu Is The Main Capability Boundary Risk

Severity: High

RFC 0034 requires Export controls for `Hull STL`, `Deck STL`, `Hydro JSON`,
`Stability JSON`, and `Mesh package`, but the safe behavior differs by row. The
implementation must not imply hosted storage, a new REST route shape, web-side
mesh-package authoring, high-angle stability export, or successful package
creation.

Ledger decision:

- `Hull STL` and `Deck STL` remain enabled through the existing STL behavior.
- `Hydro JSON` may be enabled only if it is sourced from existing local/current
  evaluation data without changing existing REST shapes.
- `Stability JSON` must be disabled unless it is explicitly limited to the
  current safe primary/initial-stability data already available. If enabled, it
  must not imply high-angle GZ, secondary-stability peak, or a full load-case
  equilibrium export unless that data is actually present.
- `Mesh package...` remains disabled/unavailable in this RFC unless the
  implementation only exposes an already-existing, safe server-local artifact.
  The conservative default is disabled with copy directing users to
  `kayakgen mesh-package`.

Sources: RFC 0034 proposal/acceptance/open questions; `REMEDIATION.md` caveats;
`REVIEW_TRACEABILITY.md` T1; `REVIEW_DOMAIN.md` P1; `REVIEW_ERGONOMICS_DESIGN.md`
E5; `REVIEW_OPS.md` High export finding; workflow 0044 final review F5.

### P0 - Web Preset Binding Needs Reseed, Range Narrowing, And A Guard

Severity: High

Selecting a non-custom web class preset must reseed the canonical hull sliders
from `KayakClass` defaults and narrow visible slider ranges to the selected
class envelope. Manual edits must switch the selected preset back to `custom`,
but preset-driven programmatic slider writes must not immediately trigger that
custom flip.

Ledger decision:

- Seed `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, and `Cp` from the
  selected `KayakClass.default`.
- Bind per-slider min/max to the selected class range; when returning to
  `custom`, restore the global `SLIDER_DEFS` bounds.
- Define "manual edit" as a user change to a `HULL_STATE_FIELDS` slider.
  `target_speed_kt` is view/UI state and must not flip the preset to `custom`
  or persist to `Hull`.
- Use a web-side `_applying_class_preset` guard or equivalent listener
  suspension around programmatic preset writes.
- Preserve live `beam_wl_m` clamping to `beam_oa_m`.
- Render human labels from `KayakClass.label` while keeping stable preset ids.

Sources: RFC 0034 AC1; `REVIEW_TRACEABILITY.md` T4; `REVIEW_ERGONOMICS_DESIGN.md`
E1/E7; `REVIEW_OPS.md` High preset finding; workflow 0044 final review F1.

### P0 - Resistance Card Must Own The Read-Model Table

Severity: High

The Resistance card must render the `resistance_table_view_model` data directly,
not leave the sweep table inside the Hydrostatics pre-block while the dedicated
card shows only static copy.

Ledger decision:

- Render fixed sweep speeds `[2.0, 3.0, 4.0, 5.0, 6.0] kt` plus target-speed
  focus behavior from the existing read model.
- Include columns `kt | Fn | Rv N | Rw N | Rt N`.
- Highlight the target row with `--state-focus-row` and a non-color marker or
  weight change so the row remains identifiable without color perception.
- Keep `RAW_COMPARATIVE_CAPTION`, raw comparative warning copy, and the
  `uncalibrated_comparative` chip in the Resistance card.
- Use card-scope claim-chip rendering for this slice; defer per-`Rt` chip
  variance until a future calibration/claim RFC has row-specific semantics.
- Remove duplicate resistance sweep text from the Hydrostatics pre-block so the
  scan path is Hydrostatics -> Resistance, not duplicated output.

Sources: RFC 0034 AC3; RFC 0033 Resistance acceptance; `REVIEW_TRACEABILITY.md`
T6; `REVIEW_ERGONOMICS_DESIGN.md` E2; `REVIEW_OPS.md` read-model finding;
workflow 0044 final review F3.

### P0 - Mesh Diagnostics And Package Readiness Must Avoid Overclaim

Severity: High

The Mesh tab and status segments must display current diagnostics and package
readiness from existing read models without implying `watertight-solid`
readiness or package selection before there is a package/manifest-backed state.

Ledger decision:

- Bind Hull and Deck diagnostics to `mesh_diagnostics_lines_from_state(...)`
  when no package is selected.
- When a package is selected, prefer manifest quality-report data and label any
  stale/current-hull distinction explicitly.
- Display welded-primary counts as the primary counts and raw counts as detail.
- Render `open-wetted-surface` and `watertight-solid` profile choices, with
  `watertight-solid` visible-but-disabled and explained by the existing disabled
  tooltip.
- Drive package/readiness/status copy from `evaluation_summary`,
  `mesh_diagnostics_lines_from_state`, and `mesh_package_view_model`; do not
  show `cfd_surface_candidate` as selected package readiness unless that value
  comes from current diagnostics or a manifest-backed package state.
- Before exposing package manifest readback more prominently, contain manifest
  artifact refs: resolve refs under the package directory, reject absolute or
  parent-traversal paths, and add a malicious-manifest regression test.

Sources: RFC 0034 AC4; RFC 0033 Mesh acceptance; `REVIEW_TRACEABILITY.md` T5;
`REVIEW_DOMAIN.md` P0; `REVIEW_ERGONOMICS_DESIGN.md` E3; `REVIEW_OPS.md` mesh,
read-model, and manifest findings; workflow 0044 final review F4.

### P1 - Validity Badge Needs A Web Helper With Exact Strings

Severity: Medium

The validity badge must be derived from current hull/class state and must use
only the RFC 0033/RFC 0034 accepted string set. Desktop `_classify` is close but
does not return the exact web badge strings, so direct reuse would drift from
acceptance wording.

Ledger decision:

- Add a web/controller helper such as `validity_badge_from_state(state)` or
  `hull_validity_badge(state)`.
- Return exactly one of:
  - `In <class> envelope`
  - `Custom — sub-touring`
  - `Custom — beyond elite`
  - `Custom (L/B_wl=X.X)`
- Keep the badge pinned to the rail, not moved into the status bar.
- Render it with `role="status"` and `aria-live="polite"`.
- Treat the badge as informational; do not co-opt success/raw chip vocabulary
  unless a later validity-design RFC changes that claim model.

Sources: RFC 0034 AC2; RFC 0033 Parameter rail acceptance;
`REVIEW_TRACEABILITY.md` T3; `REVIEW_ERGONOMICS_DESIGN.md` E4/E8;
`REVIEW_OPS.md` validity finding; workflow 0044 final review F2.

### P1 - Forbidden-Copy Tests Need A Precise Render-Surface Contract

Severity: Medium

RFC 0034 must broaden the regression tests from the current narrow guard to the
full RFC 0033/workflow 0044 no-go list, but a simple blanket grep will flag
permitted negations and possibly unused vocabulary tables.

Ledger decision:

- Test the full no-go set: `OpenFOAM`, `SU2`, `cloud`, `worker queue`,
  `calibrated drag`, `final prediction`, `design fitness`, `GZ_max`,
  `heel_angle_max_deg`, and bare `cfd_ready`.
- Allow only documented negations/phrases:
  - `not final prediction`
  - `no accepted final-prediction`
  - `not watertight cfd_ready`
  - `no hosted worker is running`
- Scope the grep/assertions to rendered web/controller text surfaces, or remove
  unused positive vocabulary entries before broadening to all `kayakgen/ui`.
- Preserve existing browser acceptance while adding the broader copy guard.

Sources: RFC 0034 AC6; RFC 0033 forbidden-claim guard; `REMEDIATION.md` caveats;
`REVIEW_TRACEABILITY.md` T2; `REVIEW_DOMAIN.md` P0; `REVIEW_ERGONOMICS_DESIGN.md`
E6; `REVIEW_OPS.md` forbidden-copy finding; workflow 0044 final review F6.

### P1 - Browser, Accessibility, And Responsive Coverage Must Grow With The Touched Surface

Severity: Medium

Existing browser acceptance launches and smoke-tests the web app, but it does
not exercise RFC 0034's dynamic surface. The implementation should add coverage
where behavior changes, while preserving RFC 0033's responsive hooks and
accessible scan path.

Ledger decision:

- Add browser coverage for: selecting a class preset, changed slider values,
  narrowed bounds, manual slider edit returning to `custom`, dynamic validity
  badge update, Resistance table row rendering, Mesh diagnostics/profile
  rendering, all five Export menu rows, disabled/unavailable export states, and
  1440x900 plus sub-960 responsive behavior.
- Treat browser skips as missing coverage, not success.
- Keep Export as one keyboard-operable `Export` menu.
- Make disabled Mesh/Export explanations discoverable on hover and keyboard
  focus.
- Ensure status segment `aria-label`s include current values and target tabs.
- Preserve responsive hooks when replacing two export buttons with one menu.

Sources: RFC 0034 acceptance/implementation path; `REVIEW_ERGONOMICS_DESIGN.md`
E5/E8/accessibility notes; `REVIEW_OPS.md` browser acceptance finding and matrix;
workflow 0044 ledger validation matrix.

### P2 - Docs, Changelog, And Release Notes Must Stay Factual

Severity: Low

RFC 0034 implementation should update user-facing docs and `CHANGELOG.md` only
for behavior that actually lands. Documentation must not turn disabled entries
or future capabilities into present-tense product claims.

Ledger decision:

- Update `docs/USER_GUIDE.md` and `CHANGELOG.md` when implementation changes
  user-facing behavior or workflow status.
- Describe Export menu rows, disabled/unavailable states, and no-claims
  constraints factually.
- Do not promote workflow 0044 F7's patch-summary/changelog mismatch into an
  RFC 0034 product requirement.
- Keep root `OPERATOR_REPORT.md` out of this ledger job and leave global
  reporting to the operator.

Sources: `AGENTS.md` project conventions; RFC 0034 docs/changelog goal;
`REMEDIATION.md` packet changes/caveats; `REVIEW_OPS.md` docs/changelog finding;
workflow 0044 final review F7.

## Safe-Now Implementation Scope

Implement only the following in the RFC 0034 build lane:

1. Web class preset behavior for `touring`, `performance`, `surfski_int`, and
   `surfski_elite`: seed five canonical hull sliders, narrow bounds, clamp
   `beam_wl_m`, guard programmatic writes, and flip to `custom` only after
   manual `HULL_STATE_FIELDS` edits.
2. A derived web validity badge helper with the exact RFC 0033/RFC 0034 string
   set and rail-pinned accessible rendering.
3. Resistance card rendering from `resistance_table_view_model`, including fixed
   sweep rows, target-speed focus row, `kt | Fn | Rv N | Rw N | Rt N` columns,
   raw comparative copy, and card-scope `uncalibrated_comparative` chip.
4. Mesh tab/status rendering from existing diagnostics and package read models,
   including welded-primary counts, raw detail, warnings, visible disabled
   `watertight-solid`, honest package/readiness state, and manifest path
   containment before browser exposure.
5. A single `Export` menu with five rows: enabled Hull STL and Deck STL, Hydro
   JSON only from current existing evaluation data, Stability JSON disabled or
   strictly limited to current safe primary/initial-stability data, and Mesh
   package disabled/unavailable unless an already accepted server-local artifact
   path is used without new capability.
6. Full forbidden-copy regression coverage for the RFC 0033/workflow 0044 no-go
   strings with explicit allowed negations.
7. Focused browser/layout/read-model tests for the dynamic surface and factual
   docs/changelog updates describing only current safe behavior.

## Explicit Deferrals

These remain out of scope for RFC 0034 implementation:

- Hosted/cloud CFD workers, worker queues, public hosted execution, or
  multi-user execution.
- OpenFOAM/SU2 integration, Docker/container solver execution, real solver
  adapters, normalized solver outputs, or cancellation guarantees.
- Calibrated drag, final-prediction validity envelopes, or design-fitness
  claims.
- High-angle GZ visualization, numeric `GZ_max`, numeric `heel_angle_max_deg`,
  secondary-stability peak metrics, or full capsize-range stability.
- Watertight-solid readiness promotion or bare `cfd_ready` claims for current
  generated packages.
- Web-side mesh-package authoring API beyond an already accepted server-local
  path.
- New REST route shapes unless an existing local route already exposes the data
  safely.
- Multi-variant 2D geometry overlay, Pareto plot widget, persistent pinned
  candidates, multi-user share, or richer comparison ergonomics.
- Full mobile authoring; narrow screens remain inspect-and-triage.
- Desktop `QMainWindow`/`QTabWidget` parity rewrite, desktop region/test-id
  parity, or full desktop chip/tab/focus behavior.
- Per-row resistance claim variance or calibrated resistance semantics.
- RFC 0008/RFC 0033 cross-link cleanup beyond factual docs/status updates needed
  for this slice.

## Validation Matrix

Minimum validation for the implementation lane:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_web_read_models.py tests/test_mesh_package.py -q -p no:cacheprovider
.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q -p no:cacheprovider
.venv/bin/python -m pytest -q -p no:cacheprovider
```

Validation expectations:

| Area | Required checks |
| --- | --- |
| Presets | Unit/state and browser tests for each non-custom preset: five slider values seed from `KayakClass`, bounds narrow to class ranges, `beam_wl_m` clamps, and one manual hull-slider edit flips to `custom`. |
| Validity badge | Unit tests for in-envelope, sub-touring, beyond-elite, and custom L/B cases; browser/layout check that the rendered badge uses exactly the allowed strings and `role="status" aria-live="polite"`. |
| Resistance | Unit and browser/layout checks for fixed speeds, optional inserted target row, target highlight/non-color marker, columns `kt | Fn | Rv N | Rw N | Rt N`, raw comparative copy, and no duplicate sweep table in Hydrostatics. |
| Mesh | Unit and browser/layout checks for hull/deck welded-primary counts, raw detail, warnings, missing package state, selected package/manifest state, disabled `watertight-solid` tooltip, and no unsupported readiness claim. |
| Manifest safety | Regression test with malicious absolute/parent-traversal manifest refs proving readback stays inside the package directory or fails closed. |
| Export | Browser/layout checks for one `Export` menu with rows in order: Hull STL, Deck STL, Hydro JSON, Stability JSON, Mesh package; assertions for enabled/disabled states, honest unavailable copy, keyboard opening/navigation, STL filename/header behavior, and no new route shape unless accepted. |
| Forbidden copy | Render-surface assertions over `kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`, and browser/static output as appropriate for the full no-go set, with explicit allowed negations. |
| Browser layout | 1440x900 first-viewport visibility for parameters, geometry, metrics, first Review card, and status; sub-960 usable collapse; export overflow below 1200; browser skips treated as missing coverage. |
| Accessibility | Status segment aria labels include current values and target tabs; disabled export/profile explanations available on keyboard focus; target row not color-only. |
| Docs/changelog | Checklist review that `docs/USER_GUIDE.md` and `CHANGELOG.md` describe only landed behavior and explicit deferrals. |

## Risks Requiring Successor RFCs

| Risk | Why it needs a successor RFC |
| --- | --- |
| Web-side mesh-package authoring or mesh-package browser download | Can create new filesystem/API/product capability and imply package generation success. |
| Full Stability JSON with load cases, high-angle GZ, or secondary stability | Current accepted slice does not provide high-angle/capsize-range outputs or a web load-case workflow. |
| Watertight-solid readiness or `cfd_ready` promotion | Requires upstream generated-body, volume-mesh, and readiness evidence beyond current open-surface packages. |
| Calibrated resistance, final prediction, or design fitness | Requires calibration/claim-gate RFCs and validation fixtures. |
| Hosted/cloud CFD, OpenFOAM/SU2, worker queues, or real solver dispatch | Crosses RFC 0033/0034's no-new-backend-capability boundary. |
| Desktop workspace parity rewrite | Needs a Qt main-window/tab design instead of hidden obligations inside a web follow-up. |
| Rich Comparison/Pareto UI or multi-variant overlays | Deferred by RFC 0033/RFC 0034 and not required to close F1-F6. |
| Per-row resistance claim chips | Meaningful only once future claim states can vary by row/speed/calibration tier. |
| RFC 0008 layout/status reconciliation beyond current docs | Should be a doc/RFC hygiene pass if older web layout commitments keep conflicting with RFC 0033/0034. |

## Concise Implementation Sequencing Guidance

1. Pin Export behavior first. Build the single menu and decide each row's
   enabled/disabled state before adding broader docs, so no route/API ambiguity
   leaks into UI copy.
2. Add controller/read-model helpers for preset state, slider bounds, and the
   validity badge. Keep class/default/range semantics in helpers, with `app.py`
   acting as renderer and event coordinator.
3. Wire existing Resistance and Mesh read models into the cards. Keep
   diagnostics, package parsing, and resistance calculations out of layout code;
   add manifest containment before expanding package readback.
4. Expand tests alongside each UI binding: unit/read-model tests first, then
   browser acceptance for the dynamic workflow and export/menu states.
5. Broaden forbidden-copy assertions after the final copy is in place, using the
   explicit allowed-negation fixture.
6. Update docs and changelog last, after behavior is implemented and validated,
   keeping current safe behavior separate from deferred roadmap capability.

## Sub-Agent And Parallel Assistance Summary

Four read-only helper agents were used for independent extraction:

- Traceability/remediation helper: gate verdict, F1-F6 mapping, export
  ambiguity, forbidden-copy allowances, safe-now scope, deferrals, validation,
  and successor risks.
- Domain/no-claims helper: claim-language attachment, no-new-capability
  boundaries, export no-claims risk, mesh readiness semantics, and docs risk.
- Ergonomics/design helper: preset guard, Resistance card ownership, Mesh
  profile affordance, exact badge strings, Export menu shape, accessibility, and
  responsive refinements.
- Ops/test helper: export safety, preset helper/guard, read-model rendering,
  mesh manifest containment, browser acceptance gaps, forbidden-copy target
  scoping, and validation matrix.

Local parallel reads were also used for the workflow packet, RFCs, review
artifacts, prior workflow artifacts, and context docs. No Striatum
publish/complete/verdict commands were run, no commits or pushes were made,
`.striatum` was not edited, product code was not changed, and root
`OPERATOR_REPORT.md` was not altered.
