# Role: Reviewer — Tests and operational behaviour

Verify:

- `tests/test_web_layout.py` reflects EVERY renamed/moved/removed `data-testid` /
  `kg-*` hook: no assertion is left pointing at a hook that no longer exists, and
  each new hook name has a positive assertion. The region (`region-params` /
  `-geometry` / `-review`) test-ids and the four status segments
  (`status-package` / `-readiness` / `-resistance` / `-cfd` + `workspace-status-bar`)
  still assert.
- The 1440×900 first-viewport assertion and the ≤960 px collapse hooks
  (`kg-collapse-under-960`, `kg-geometry-accordion-under-960`,
  `kg-review-body-under-960`, `kg-status-wrap-under-960`) are still asserted.
- `tests/test_web_inline_help.py` reflects any moved inline-help hook.
- The widened orphan-literal lint (`tests/test_ui_theme.py`) still passes —
  styling stayed token-only; any new `theme.py` token is additive and, if
  colour-bearing, resolves in both palettes and clears its `CONTRAST_MANIFEST`
  ratio.
- The desktop rendered-bbox tests stay green; `theme.py` (if touched) has no
  module-level side effects.
- The full repo suite (minus env-gated smoke) is green; `git diff --check`
  passes; the forbidden-copy and import-boundary scans still pass.

Tests must not depend on wall-clock sleeps. Findings cite file paths. Use
`accept_with_findings` for issues the remediation lane can fix.
