author: findings-ledger-codex-gpt-5.5-001

# Workflow 0061 Findings Ledger

date: 2026-06-02
scope: RFC 0065 Slice 4 visual-regression hard gate, a11y checks, Lighthouse record, and docs/D047 ratification.

## Source Reviews

- `striatum/0061-rfc-0065-slice4-visual-regression/reviews/claims/REVIEW.md`
- `striatum/0061-rfc-0065-slice4-visual-regression/reviews/ops_tests/REVIEW.md`
- `striatum/0061-rfc-0065-slice4-visual-regression/reviews/traceability/REVIEW.md`
- `striatum/0061-rfc-0065-slice4-visual-regression/implementation/PATCH_SUMMARY.md`
- `docs/workflows/0061-rfc-0065-slice4-visual-regression/SLICE_4_DECISIONS.md`

## Must-Fix Remediation

### MF-1 — Commit a no-browser self-test for the visual diff comparator

Source finding: traceability F1.

Decision cross-check: `SLICE_4_DECISIONS.md` D3 requires the hard compare to demonstrably fail on an over-tolerance diff and not be a no-op. The current implementation has manual injected-diff evidence in `PATCH_SUMMARY.md`, but no committed regression test pins that failure mode.

Remediation: add focused unit coverage for `_compare_visual_png` using synthetic PNGs. The test should assert an over-tolerance change returns `VisualCompareResult.passed is False` and writes diff evidence, and an under-tolerance change returns `passed is True`. This is test-only remediation; it must not change the tolerance constants, viewport list, masking policy, or browser acceptance scope.

Blocking reason: without a committed self-test, a future refactor could neuter the comparator while the live baseline path continues to pass against unchanged images.

## Non-Blocking Successor

### NB-1 — Track the known services-import-boundary failure as hygiene follow-up

Source finding: ops_tests Objective 9 and `PATCH_SUMMARY.md` verification.

Decision cross-check: `SLICE_4_DECISIONS.md` explicitly names the pre-existing NB-2 `tests/test_services_boundaries.py` services-to-UI import-boundary failure as out of scope and says it is a separate hygiene follow-up, not a Slice 4 must-fix.

Pointer: open or continue a follow-up hygiene workflow for NB-2 services boundary cleanup, specifically `kayakgen/services/evaluation.py` importing `kayakgen.ui.hydrostatics_metadata`. Do not remediate it in the Slice 4 lane.

## Accepted / No Action

### A-1 — Baseline PNG changes have the required explained diff

Source finding: traceability D1 note and `PATCH_SUMMARY.md` Baseline Diff Review.

Decision cross-check: D1 requires regenerated committed PNGs to be reviewed and explained. The patch summary records the visible reason for the diff: the previously inert token CSS is now rendered in Chromium, so the committed PNGs reflect the post-Slice-2/3 tokenized shell; it also records per-file byte-size deltas and states that chip copy/classes are unchanged and the VTK region remains masked.

Disposition: accepted, no must-fix. There is no committed baseline PNG with unexplained binary churn in the reviewed artifacts.

### A-2 — CSS-injection rewrite is traceable Slice 4 implementation detail

Source finding: traceability F2.

Decision cross-check: D1/D2 require baselines and the hard gate to capture the actual post-polish Chromium render. The `workspace_style_html` rewrite makes the existing token CSS active in the Trame content; the CSS strings are not new design scope.

Disposition: accepted, no action. Reviewer awareness note only.

### A-3 — Rendered chip-colour confirmation is covered by claims review

Source finding: traceability F3 and claims review.

Decision cross-check: D7 requires claim line and chip semantics to remain intact. Claims review records `CHIP_SPECS`, `CHIP_LABELS`, and `CHIP_CLASSES` byte-identical to `HEAD`, persistent captions byte-identical, no chip recolouring, no new claim/readiness/accepted-use literals, and no REST-route expansion.

Disposition: accepted, no action.

### A-4 — Lighthouse remains recorded, not mandatory pytest

Source finding: ops_tests Objective 8 and docs review.

Decision cross-check: D5 says Lighthouse Best Practices >= 90 is recorded and optional/tool-dependent, not a mandatory pytest gate. `docs/WEB_VERIFICATION.md` records Best Practices `1.0` (100) on 2026-06-02 and keeps Lighthouse out of the mandatory pytest gate table.

Disposition: accepted, no action.

## Ledger Verdict

Remediation lane has one Slice 4 must-fix: `MF-1`.

Known `NB-2` services-import-boundary failure is deferred to hygiene successor `NB-1`.

No baseline PNG is flagged as must-fix for unexplained churn.
