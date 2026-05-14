# RFC 0036: Trame Seed Listener Proof

Status: proposed
Date: 2026-05-14
Context: successor to RFC 0035 and workflow 0047 final review FR1. This RFC
narrows one retained web preset-listener branch left after the RFC 0035 cleanup
slice. It does not reopen class preset behavior, backend capability, or broader
browser acceptance.

## Problem

Workflow 0047 accepted the RFC 0035 UI cleanup with one residual proof gap:
`_state_matches_preset_seed` was retained because Trame can reportedly fire
same-seed hull events after preset application. The landed regression test
pins the helper's steady-state behavior by calling the listener directly after
artificially widening bounds, but it does not drive the cited Trame event
sequence through the browser.

The failure mode is small but concrete. If the branch guards a real Trame event
path, future cleanup might remove it and reintroduce a preset-to-custom flip. If
the event path is not observable, the code remains a maintenance branch with no
runtime proof.

## Goals

- Decide whether `_state_matches_preset_seed` is a real browser-observable
  guard or removable dead code.
- If retained, prove the same-seed path through Trame/browser automation rather
  than only through a direct helper call.
- If removed, preserve the accepted RFC 0034/RFC 0035 preset semantics and
  regression coverage.
- Keep the decision limited to the preset listener branch and focused tests.

## Non-Goals

- No new preset UX, selector layout, rail grouping, tooltips, or visual markers.
- No changes to class preset IDs, class definitions, or the five-field preset
  reseed/narrow contract.
- No desktop UI changes.
- No export-menu, snapshot-schema, backend, CFD, mesh, resistance, stability, or
  hosted behavior changes.
- No broad browser-acceptance expansion beyond the same-seed event proof.

## Proposal

Implement one of two acceptable outcomes:

1. Retain `_state_matches_preset_seed` only if a browser-acceptance test drives
   the same-value preset event sequence end-to-end through Trame and documents
   the reachable sequence in the test name or test comments.
2. Remove `_state_matches_preset_seed` as dead code if the same-value sequence
   cannot be reproduced, while keeping focused tests for preset reseed/narrow
   behavior and no unintended custom flip.

The preferred browser proof is narrow: select a class preset, drive a hull
slider away from and then back to within the implementation tolerance of the
preset seed, and assert that the preset remains non-custom only for the
same-seed path. The implementation may use another driver if it proves the same
event sequence without direct private-helper invocation.

Existing accepted behavior remains authoritative:

- class presets seed and narrow only `length_m`, `beam_oa_m`, `beam_wl_m`,
  `draft_m`, and `Cp`;
- manual edits to hull-shaping fields switch `class_preset` to `custom`;
- `target_speed_kt` is view state and does not switch the preset.

## Acceptance Criteria

- Selecting a web class preset still reseeds and narrows only the canonical five
  hull sliders.
- Manual hull-shaping edits still switch the selected preset to `custom`.
- `target_speed_kt` edits still leave the selected preset unchanged.
- If `_state_matches_preset_seed` remains, a browser test drives the same-seed
  event path through Trame without direct private-helper invocation and asserts
  the preset remains non-custom.
- If `_state_matches_preset_seed` is removed, existing preset/browser coverage
  remains green and browser acceptance still exercises the same preset
  slider-away-and-back, or equivalent same-seed, gesture and proves preset
  reseed/bounds behavior does not create an unintended custom flip.
- The implementation patch summary or final-review artifact records the chosen
  retain/remove outcome, including the browser test path and documented event
  sequence if retained, or the deleted helper range and replacement regression
  coverage if removed.
- The RFC 0033/RFC 0034 forbidden-copy and no-claims boundaries remain
  unchanged.

## Open Questions

- Is the same-seed Trame event sequence reliably reproducible in browser
  automation, or was the retained branch guarding an inferred behavior?
- Should the test prescribe the ArrowRight/ArrowLeft nudge path, or should it
  accept any browser-driven event sequence that reaches the same state?

## Implementation Path

1. Add a first-pass browser proof attempt for the same-seed sequence while
   keeping existing preset tests unchanged.
2. If the proof is reliable, keep `_state_matches_preset_seed` and document the
   event sequence in the focused browser test.
3. If the proof is not reliable, remove the branch and keep direct regression
   coverage for reseed/bounds behavior plus the same user-observable browser
   gesture used by the proof attempt.
4. Run focused web layout/read-model/browser tests and forbidden-copy checks.
5. Record the retained or removed outcome in the workflow patch summary or
   final-review artifact so later cleanup can audit the decision.

## Domain Modeling

Boundary clarification. This RFC changes no domain model. It decides whether a
presentation-layer Trame listener branch is runtime evidence or removable UI
maintenance code.
