# Role: Reviewer — Tests and operational behaviour

Verify:

- The widened orphan-literal lint actually fails on a planted dimension / radius
  / shadow / focus literal outside `theme.py` and passes on the clean tree — it
  must not be a no-op assertion.
- `CONTRAST_MANIFEST` covers the focus-ring and state tokens and every pair
  clears its `min_ratio` in BOTH palettes
  (`test_contrast_manifest_clears_thresholds` parametrised light + dark).
- Every new colour-bearing token resolves in both `COLORS_LIGHT` and
  `COLORS_DARK`; dimensionless tokens are single maps. `css_root_block(dark=…)`
  emits each new CSS variable; `vuetify_theme_config()` maps the state/focus
  tokens onto the registry.
- The desktop rendered-bbox tests stay green (token inheritance via the unchanged
  matplotlib/vtk helpers), and `theme.py` has no module-level side effects.
- The full repo suite (minus env-gated smoke) is green; `git diff --check`
  passes; the forbidden-copy and import-boundary scans still pass.

Tests must not depend on wall-clock sleeps. Findings cite file paths. Use
`accept_with_findings` for issues the remediation lane can fix.
