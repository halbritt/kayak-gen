# RFC 0035: UI Follow-Up Cleanup

Status: landed safe-slice
Date: 2026-05-14
Context: successor to RFC 0034, workflow 0045 final review, and workflow
0046 final review. This RFC is limited to reviewable UI cleanup and
maintenance findings already recorded by those workflows.

## Problem

Workflows 0045 and 0046 landed their accepted safe slices with
non-blocking follow-up findings. The current UI avoids false capability
claims and keeps the accepted RFC 0033/RFC 0034 behavior, but several
small pieces of semantics and maintenance debt remain:

- the web validity badge is keyed to the selected preset rather than to
  all class envelopes, unlike the desktop classifier;
- the parameter rail narrows only the canonical five hull fields while
  edits to other hull fields still switch the preset to `custom`;
- web preset handling contains an effectively unreachable branch;
- the export menu duplicates labels and disabled-state data already
  declared in `EXPORT_MENU_ROWS`;
- the web state snapshot hand-rolls a growing list of ad-hoc keys;
- the slider-label fix introduced a wrapper accessibility structure and
  duplicated root-token CSS that deserve a focused review pass;
- the desktop slider-label fallback should remain bounded until the
  Matplotlib version floor can use `label_location` directly.

The common risk is maintenance drift, not missing physics or backend
capability. A narrow cleanup RFC can make these details explicit without
reopening the broader desktop rewrite, CFD, stability, mesh, or
calibration roadmap.

## Goals

- Align or explicitly codify web validity-badge semantics for `custom`
  hulls that satisfy a known class envelope.
- Clarify the preset interaction model: presets seed and narrow the five
  canonical hull fields; edits to hull-shaping fields return the preset
  selector to `custom`; view-only fields such as target speed do not.
- Remove or test any dead preset listener branch that is not reachable
  through normal slider interaction.
- Make `EXPORT_MENU_ROWS` the single source for export-menu labels,
  availability, disabled states, and guidance copy.
- Replace ad-hoc web state snapshot key copying with a small declared
  snapshot schema, without changing public REST payload shapes.
- Consolidate parameter-rail slider-label CSS so it references existing
  theme tokens without re-emitting an unnecessary `:root` block.
- Review and test the slider wrapper's accessibility semantics so the
  canonical visible label and accessible name stay in sync.
- Keep desktop slider labels legible while isolating the Matplotlib
  fallback and documenting the removal condition for the shim.
- Add focused tests and docs/changelog updates for the cleanup only.

## Non-Goals

- No desktop parity rewrite, Qt-native slider rewrite, `QMainWindow`
  migration, or broader desktop layout redesign.
- No new backend capability, REST route shape, hosted service, hosted
  CFD, worker queue, or cloud storage.
- No OpenFOAM/SU2 integration or other real solver adapter.
- No calibrated drag, accepted final prediction, final design fitness,
  or new resistance validity envelope.
- No real high-angle `GZ`, `GZ_max`, `heel_angle_max_deg`, or capsize
  range stability claim.
- No web-side mesh-package authoring beyond the existing safe export
  entries and local/CLI guidance.
- No watertight-solid promotion and no bare `cfd_ready` promotion.
- No new class definitions, hull geometry parameters, mesh profiles, or
  solver readiness states.

## Proposal

Implement a conservative cleanup pass over the review findings:

1. **Preset and validity semantics.** Move the web validity badge toward
   the desktop class-detection model by classifying the current hull
   against all canonical class envelopes before falling back to the RFC
   0033 custom strings. Keep the selected preset as UI control state,
   not as the only source of validity truth. Preserve the accepted badge
   vocabulary: `In <class> envelope`, `Custom — sub-touring`,
   `Custom — beyond elite`, and `Custom (L/B_wl=X.X)`.
2. **Preset edit model.** Keep the RFC 0034 behavior where presets seed
   and narrow only the canonical five hull fields. Add tests and user
   guide wording for the current rule that editing hull-shaping fields
   switches the selector to `custom`, while target speed remains a view
   control and does not change the selected preset.
3. **Dead branch cleanup.** Remove the unreachable
   `_state_matches_preset_seed` listener branch if review confirms no
   observable interaction depends on it. If a reachable path exists,
   cover it with a focused test and document the event sequence.
4. **Export menu single source.** Render the export menu from
   `EXPORT_MENU_ROWS` so the visible menu and test/data contract cannot
   drift. Keep enabled rows limited to existing safe local actions and
   keep unavailable rows honest.
5. **State snapshot hygiene.** Replace the hand-written snapshot list
   with a named schema used by the web app/controller boundary. Preserve
   existing keys and route payload compatibility; this is only a
   maintenance cleanup.
6. **Slider-label CSS and accessibility.** Remove duplicate `:root`
   token emission from `PARAMETER_RAIL_CSS` if the existing theme path
   already provides the variables. Confirm the wrapper `role="group"`
   and `aria-label` structure produces one clear accessible name per
   slider row and still preserves the canonical visible label.
7. **Desktop fallback maintenance.** Keep the current compatibility shim
   only while the installed Matplotlib lacks `label_location` support.
   Isolate the fallback path, keep rendered bounding-box proof, and make
   the removal condition clear for the future version-floor bump.

## Acceptance Criteria

- A custom web hull that satisfies a canonical class envelope gets the
  same class-envelope badge outcome as the desktop classifier, using only
  the accepted badge strings.
- Selecting a class preset still reseeds and narrows the five canonical
  hull sliders; manual hull-shaping edits still switch to `custom`;
  target-speed edits still do not.
- Any retained preset seed short-circuit has a focused test proving its
  reachable event sequence; otherwise the dead branch is removed.
- The export menu is rendered from `EXPORT_MENU_ROWS`, and tests fail if
  row labels, disabled states, or guidance copy are duplicated out of
  sync.
- The state snapshot keys are declared in one small schema and existing
  controller/read-model behavior remains compatible.
- Parameter-rail slider-label CSS uses existing theme tokens without an
  extra root-token block unless a review records why the duplicate block
  is still required.
- Browser/static tests prove visible slider labels, canonical
  `aria-label` text, and wrapper accessibility semantics remain intact.
- Desktop rendered bounding-box tests continue to prove label and value
  text legibility at the existing viewport anchors.
- Docs and changelog describe only UI cleanup; forbidden-copy tests still
  prevent new backend, solver, calibration, stability, hosted, or
  watertight-readiness claims.

## Implementation Path

1. Run workflow 0047's traceability, no-claims, ergonomics/design, and
   ops/test reviews over this RFC and the workflow 0045/0046 findings.
2. Consolidate review findings into a ledger that separates safe-now
   cleanup from any larger parity, backend, or capability work.
3. Implement only ledger-accepted cleanup items, using disjoint write
   scopes for web semantics, UI rendering/accessibility, tests, and docs
   if parallel work is useful.
4. Run focused web layout/read-model/browser checks, desktop layout
   checks if desktop code changes, forbidden-copy checks, `git diff
   --check`, and final review before landing.

## Domain Modeling

Boundary clarification. This RFC does not add domain concepts. It makes
the UI boundary around existing class envelopes, advisory state,
export-readiness copy, theme tokens, and desktop/web label presentation
more explicit while preserving the current physics, mesh, CFD,
calibration, and stability boundaries.
