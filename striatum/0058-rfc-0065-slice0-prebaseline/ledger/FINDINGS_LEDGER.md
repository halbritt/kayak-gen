author: findings-ledger-codex-gpt-5.5-001

# Findings Ledger — RFC 0065 Slice 0 Prebaseline

## Sources Read

- `docs/workflows/0058-rfc-0065-slice0-prebaseline/SLICE_0_DECISIONS.md`
- `striatum/0058-rfc-0065-slice0-prebaseline/implementation/PATCH_SUMMARY.md`
- `striatum/0058-rfc-0065-slice0-prebaseline/reviews/ops_tests/REVIEW.md`
- `striatum/0058-rfc-0065-slice0-prebaseline/reviews/traceability/REVIEW.md`
- Required context files named in the work packet.

## Must-Fix Remediation Items

### M1 — Make the narrow visual baselines reflect their configured viewport widths

Finding(s): traceability F1.

Decision cross-check: S0-D1 requires capture at representative viewports,
including a <=960 px collapsed width. S0-D3 requires committed baselines of
today's shell. The review found the 1024x768 and 960x720 PNGs decode to the same
effective render, and both are wider than their nominal viewport. That satisfies
the literal "three captures exist" requirement but weakens the Slice 0 baseline
as evidence for the narrow bucket.

Remediation target: adjust the capture/comparison scaffold so each committed
baseline is governed by the configured viewport width, then regenerate the three
Slice 0 PNGs. A viewport-clipped screenshot, a width assertion, or equivalent
test-side capture constraint is acceptable. Do not add responsive CSS, rename UI
hooks, change `kayakgen/ui/`, or introduce a hard-failure gate.

Why this is current-slice scope: it is capture-scaffold correctness under
S0-D1/S0-D3, not Slice 2 responsive layout work.

## Non-Blocking Successor Items

### S1 — Re-baseline and harden the narrow buckets after the Slice 2 responsive collapse lands

Finding(s): traceability F1.

Decision cross-check: S0-D5 explicitly forbids appearance/layout changes in
Slice 0, and the <=960 px responsive-collapse implementation is named as later
scope. The fact that today's 960 and 1024 views do not show a distinct collapsed
layout must not pull Slice 2 work into Slice 0.

Pointer: RFC 0065 Slice 2 should regenerate/review the narrow visual diffs once
the collapse rules exist. Slice 4 may add a pairwise-distinctness or viewport
efficacy assertion if that becomes part of the hard visual-regression gate.

### S2 — Ratify tolerance, canonical render environment, and hard-failure behavior in Slice 4

Finding(s): ops-tests successor note; traceability F1.

Decision cross-check: S0-D3 says the exact per-viewport tolerance and canonical
environment hardening are provisional in Slice 0 and refined in Slice 4. S0-D4
says compare mismatch is advisory in Slice 0 and the hard-failure gate lands in
Slice 4.

Pointer: RFC 0065 Slice 4 owns the exact tolerance, canonical environment
hardening, hard failure on mismatch in the browser-acceptance profile, and the
`docs/WEB_VERIFICATION.md` baseline-update procedure.

### S3 — Revisit mask placement when Slice 2/3 reflow can move the VTK region

Finding(s): traceability F3.

Decision cross-check: S0-D2 requires masking the `VtkRemoteView` region and
asserting 3D liveness separately. The committed Slice 0 PNGs show the current
mask is effective. The future risk appears only if later layout reflow pushes
the VTK viewport below the fold while capture mechanics still assume a
viewport-fixed overlay.

Pointer: RFC 0065 Slice 2/3 reviewers should re-check the mask against the new
layout. Slice 4 may harden it as part of the visual-regression gate if needed.

### S4 — Keep a11y, focus-order, hit-target, contrast, Lighthouse, and WEB_VERIFICATION docs in Slice 4

Finding(s): no current review found a Slice 0 a11y defect; this is a scope
guardrail from the prompt and S0 decisions.

Decision cross-check: S0-D6 forbids `docs/WEB_VERIFICATION.md` edits in Slice 0.
The Slice 0 out-of-scope list assigns focus-order, visible-ring, hit-target,
contrast a11y checks, Lighthouse, and `WEB_VERIFICATION.md` procedure updates
to Slice 4.

Pointer: RFC 0065 Slice 4 only. Do not add these as Slice 0 remediation items.

## Accepted Concerns

### A1 — Additive test-only `kg-visual-mask` / `visual-vtk-mask` literals are acceptable

Finding(s): traceability F2.

Decision cross-check: S0-D5 forbids `data-testid` / `kg-*` hook renames in the
application. The review found only a runtime test overlay inserted by
`_mask_vtk_viewport`; it is not persisted under `kayakgen/ui/`, does not rename
an application hook, and traces directly to S0-D2's masking requirement.

Disposition: accepted, no action.

### A2 — Advisory compare behavior is accepted for Slice 0

Finding(s): ops-tests PASS; traceability S0-D4 PASS.

Decision cross-check: S0-D4 explicitly makes mismatch advisory in Slice 0 and
defers the hard gate to Slice 4. Missing Playwright/Chromium/Pillow skip
behavior is compatible with the Slice 0 scaffold.

Disposition: accepted, no action before Slice 4.
