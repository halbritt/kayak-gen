author: findings-ledger-codex-gpt-5.5-001

# Findings Ledger — Workflow 0057 / RFC 0065 Slice 1

Source reviews:

- `striatum/0057-rfc-0065-slice1-theme-tokens/reviews/traceability/REVIEW.md`
- `striatum/0057-rfc-0065-slice1-theme-tokens/reviews/ops_tests/REVIEW.md`
- `striatum/0057-rfc-0065-slice1-theme-tokens/reviews/claims/REVIEW.md`

Slice yardstick:

- `docs/workflows/0057-rfc-0065-slice1-theme-tokens/SLICE_1_DECISIONS.md`

## Must-Fix Remediation Items

### MF-1 — Restore browser-acceptance class-preset selector expectations

Finding source: `ops_tests/REVIEW.md` finding 4; corroborated by
`implementation/PATCH_SUMMARY.md`.

Deduped finding: `tests/test_web_browser.py::test_kayakgen_serve_browser_acceptance`
still expects the removed `.kg-class-preset-radio input[type='radio']` controls,
while the web shell now exposes class selection through the toolbar `VSelect`.
The implementation summary reports the Slice 1 VTK sizing regression as fixed;
the focused browser test now advances to this stale selector expectation.

Decision cross-check:

- D7 forbids Slice 1 from renaming or moving `data-testid` / `kg-*` hooks and
  from changing layout, behaviour, or claim copy. The remediation should update
  the stale browser-acceptance selector to the already-landed toolbar class
  control, or restore an equivalent stable test hook if one already exists,
  without changing UI behaviour or reopening layout scope.
- D8 forbids Slice 1 documentation footprint beyond `CHANGELOG.md` and the
  workflow report, so this fix should be test-only unless a minimal hook is
  required in the existing web file.

Remediation instruction: fix the acceptance test/hook drift narrowly. Do not
change class-selection behaviour, layout, claim copy, or RFC 0065 Slice 2
information hierarchy.

## Non-Blocking Successor Items

### NB-1 — Revisit component-specific dimension token homing during Slice 2

Finding source: `traceability/REVIEW.md` F1.

Deduped finding: `DENSITY` currently contains single-use component dimensions
(`viewport-height`, `viewport-min-height`, `frontier-max-width`,
`frontier-scatter-height`, `screen-reader-size`), and `SPACING` contains
`screen-reader-offset`. These tokens were introduced to satisfy the widened
literal lint while preserving existing rendered values.

Decision cross-check:

- D2 requires new token families and does not forbid additional tokens.
- D6 requires migrating existing inline literals under `kayakgen/ui/` into
  tokens and making the repo clean against the widened lint.
- D7 requires token values to equal the replaced literals, with no layout or
  behaviour change.

Disposition: non-blocking. Re-homing or renaming these component-specific
dimensions would reopen the D6/D7 literal-preserving Slice 1 decision. If the
Slice 2 shell re-flow creates a cleaner scale or component-token convention,
handle it there; no Slice 1 remediation is required.

Pointer: RFC 0065 Slice 2 (shell layout and information hierarchy).

### NB-2 — Track the pre-existing service/UI import-boundary failure outside RFC 0065

Finding source: `ops_tests/REVIEW.md` finding 4.

Deduped finding: `tests/test_services_boundaries.py` fails because
`kayakgen/services/evaluation.py` imports
`kayakgen.ui.hydrostatics_metadata`. The review identifies this as pre-existing
on `main` and not introduced by the Slice 1 changes.

Decision cross-check:

- D7 says Slice 1 is presentation-only and changes no behaviour, REST route,
  claim literal, or readiness literal.
- RFC 0065 touches `kayakgen/ui/theme.py`, web layout/partials, and
  `tests/test_web_*` only; it explicitly does not change `kayakgen/model`,
  `kayakgen/eval`, or `kayakgen/search`. A service-boundary refactor is outside
  this workflow's theme-token foundation.

Disposition: non-blocking for this workflow. Record as a separate architecture
or boundary-cleanup follow-up; do not fold it into RFC 0065 Slice 1 remediation.

Pointer: follow-up workflow outside RFC 0065 Slice 1, likely service-boundary or
metadata-ownership cleanup.

## Accepted Concerns Requiring No Action

### A-1 — Claim truthfulness and boundary review passes

Finding source: `claims/REVIEW.md`.

Disposition: accepted, no action. The review found no chip-label, palette,
persistent-caption, REST-route, claim-state, readiness, accepted-use, or
forbidden-copy regression. This matches D7's hard invariant that Slice 1 changes
no claim copy or semantics.

### A-2 — Slice 1 traceability gates pass apart from NB-1

Finding source: `traceability/REVIEW.md`.

Disposition: accepted, no action. D1-D8 traceability passes: token extension is
additive, new token families resolve in both palettes, helpers emit/map the new
tokens, contrast pairs are covered, the widened lint has a negative case and a
clean-tree case, protected docs are untouched, and no Slice 2/3/4 scope creep is
present.

### A-3 — Test and ops checks pass for the Slice 1 surface apart from MF-1/NB-2

Finding source: `ops_tests/REVIEW.md`.

Disposition: accepted with the two deduped findings above. The widened
orphan-literal lint, contrast checks, helper checks, import-boundary check for
the touched surface, `git diff --check`, and theme import side-effect check are
accepted as sufficient Slice 1 evidence once MF-1 is resolved or explicitly
waived by the operator.
