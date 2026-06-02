# Role: Reviewer — Tests and operational behaviour

Verify:

- Each new empty/loading/error-state hook has a positive assertion in
  `tests/test_web_layout.py` or `tests/test_web_inline_help.py`: Generate jobs
  table (empty/running/failed/cancelled/resumable), frontier scatter
  (loading/empty/rendered), Comparison (no-report vs present), Mesh
  (`mesh-no-package-chip` vs `mesh-live-readiness-chip`), CFD (no-job vs status),
  Share-URL (`share-url-state`) + invalid-hull banners.
- The honestly-disabled control states are asserted (disabled + `aria-disabled` +
  copy) for the watertight-solid, `EXPORT_MENU_ROWS`, Cm reserved-preset, and
  `generative_submit_disabled` cases.
- The forbidden-copy / no-go scan in `tests/test_web_layout.py` was EXTENDED to
  every new rendered string and still passes (not a no-op).
- The Slice 2 region/status/collapse hooks and the 1440×900 first-viewport
  assertion still pass; the widened orphan-literal lint stays green (token-only
  styling; any new `theme.py` token additive + both-palette/contrast-covered if
  colour-bearing).
- The desktop rendered-bbox tests stay green; `theme.py` (if touched) has no
  module-level side effects.
- The full repo suite (minus env-gated smoke) is green **except** the known
  pre-existing NB-2 `tests/test_services_boundaries.py` services→ui
  import-boundary failure (out of scope); `git diff --check` passes; the
  import-boundary scan otherwise passes.

Tests must not depend on wall-clock sleeps; loading-state tests must be
deterministic (no real timers). Findings cite file paths. Use
`accept_with_findings` for issues the remediation lane can fix.
