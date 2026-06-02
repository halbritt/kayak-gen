# Operator Report — Workflow 0061 (RFC 0065 Slice 4: visual-regression hard gate + a11y + Lighthouse)

**Status:** remediation complete; final review pending.

## Scope

Slice 4 of RFC 0065 (the final core slice): regenerate the committed PNG baselines
on the canonical env to capture the post-Slice-2/3 appearance, flip the Slice 0
advisory screenshot compare to a HARD FAILURE with a documented per-viewport
tolerance (VTK region masked), add acceptance-profile a11y checks (focus order,
visible focus ring from the Slice 1 token, hit-target minimum, `CONTRAST_MANIFEST`
contrast), record Lighthouse Best-Practices ≥ 90, retain all existing behavioural
checks, update `docs/WEB_VERIFICATION.md` + `docs/USER_GUIDE.md`, and ratify
DECISION_LOG **D047** (`proposed` → `accepted`). This is the **only** slice that
touches `docs/USER_GUIDE.md`, `docs/WEB_VERIFICATION.md`, and
`docs/DECISION_LOG.md`. See `SLICE_4_DECISIONS.md` (D1–D8).

## Lanes

- Implement / ledger / remediate: `codex` (write lane; self-heartbeats through the
  long browser-acceptance / baseline-regeneration runs).
- Reviews (traceability, claims, ops-tests) and final review: `claude` / `gemini`.
  Reviews off the codex lane. Gemini reviews dispatched one at a time; long
  reviews/synthesis operator-heartbeated with a liveness-aware watch and, if a
  lease expires mid-run or an agent helper dies, operator-finalized from the
  on-disk artifact or re-dispatched (`recovery requeue-stale --force` + fresh
  session) per the operator-hazards playbook.

## Outcome

Remediation addressed the single must-fix in the findings ledger, MF-1, by
adding committed no-browser regression coverage for
`tests/test_web_browser.py::_compare_visual_png`. The synthetic PNG tests prove
both hard-gate edges: an over-tolerance diff fails and writes actual/diff
evidence, while a below-ratio diff passes without writing a diff artifact.

No comparator constants, viewport list, VTK masking policy, browser-acceptance
scope, claim/readiness/status chip contract, RFC 0032 boundary text, baseline
PNGs, D047 ratification, `WEB_VERIFICATION.md`, or `USER_GUIDE.md` claim
wording changed in remediation. The known NB-2 services import-boundary failure
remains out of scope.

Verification re-run by the remediation lane:

- Focused comparator self-test:
  `.venv/bin/python -m pytest tests/test_web_browser.py::test_compare_visual_png_fails_over_tolerance_and_writes_diff tests/test_web_browser.py::test_compare_visual_png_passes_under_mismatch_ratio_without_diff -q`
  - `2 passed in 0.07s`
- `CONTRAST_MANIFEST` gate + desktop rendered-bbox tests:
  `.venv/bin/python -m pytest tests/test_ui_theme.py::test_contrast_manifest_clears_thresholds tests/test_desktop_layout.py -q`
  - `6 passed in 4.04s`
- Visual-baseline compare on the canonical env:
  `.venv/bin/python -m pytest tests/test_web_browser.py::test_web_workspace_visual_baseline -q`
  - `3 passed in 19.97s`
- Browser-acceptance profile:
  `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q`
  - `4 passed, 2 deselected in 34.88s`
- Full repo suite, excluding only env-gated smoke by default:
  `.venv/bin/python -m pytest -q`
  - `1 failed, 1307 passed, 4 skipped in 471.93s`
  - Failure is the known out-of-scope NB-2 services boundary:
    `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
    reports `kayakgen/services/evaluation.py` importing
    `kayakgen.ui.hydrostatics_metadata`.
- `.venv/bin/python -m ruff check tests/test_web_browser.py`
  - `All checks passed!`
- `git diff --check`
  - clean

On acceptance, RFC 0065 core (Slices 1-4) is complete; Slice 5 (desktop polish)
remains deferred / operator-gated per D009 / D021.
