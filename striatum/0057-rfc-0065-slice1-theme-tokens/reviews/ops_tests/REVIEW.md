# Review: Tests, Determinism, and Operational Behaviour (Workflow 0057)

author: reviewer-ops-tests-gemini-pro-3.1-001
date: 2026-06-02
verdict: accept_with_findings

## Summary

The theme-token foundation (RFC 0065 Slice 1) is technically sound, deterministic, and correctly verified by the extended test suite. The widened orphan-literal lint successfully identifies raw dimension, radius, shadow, and focus literals outside `theme.py`, and the core visual-system maps (`SPACING`, `DENSITY`, `RADII`, `ELEVATION`, `BORDERS`) are correctly emitted and resolved in both palettes.

While the branch identifies pre-existing regressions in the repository (`main` is currently broken in `test_services_boundaries.py` and `test_web_browser.py`), these are not regressions introduced by the workflow 0057 changes. The specific objectives for this workflow have been met.

## Findings

### 1. Widened Orphan-Literal Lint
- **Status:** PASS
- **Verification:** `tests/test_ui_theme.py::test_no_orphan_visual_literals_under_kayakgen_ui` passes on the current tree.
- **Negative Case:** Manually verified that planting `border-radius: 4px` or `12px` in `kayakgen/ui/` triggers a deterministic failure. The test `test_visual_literal_lint_fails_on_planted_literal` also covers this.

### 2. Contrast and Resolution
- **Status:** PASS
- **Contrast:** `CONTRAST_MANIFEST` now covers `focus.ring.panel`, `focus.ring.viewport`, `state.hover`, `state.active`, and `state.disabled`. All pairs clear their `min_ratio` (>= 3.0 or 4.5 as appropriate) in both `COLORS_LIGHT` and `COLORS_DARK`.
- **Resolution:** Every new colour-bearing token resolves in both palettes. Dimensionless tokens are correctly shared.

### 3. CSS/Vuetify/Matplotlib Helpers
- **Status:** PASS
- **CSS:** `css_root_block(dark=True)` correctly emits the new variables.
- **Vuetify:** `vuetify_theme_config()` maps the state and focus-ring tokens onto the Vuetify 3 theme registry.
- **Matplotlib/VTK:** Helpers maintain existing inheritance; `tests/test_desktop_layout.py` (bbox tests) stay green.

### 4. Codebase Hygiene and Boundaries
- **Status:** ACCEPT WITH FINDINGS
- **Git Diff:** `git diff --check` is clean.
- **Import Boundaries:** `tests/test_import_boundaries.py` passes.
- **Service Boundary Violation (Pre-existing):** `tests/test_services_boundaries.py` fails because `kayakgen/services/evaluation.py` imports from `kayakgen.ui.hydrostatics_metadata`. This is a pre-existing violation on `main` and not a regression of this workflow.
- **Browser Acceptance (Pre-existing):** `tests/test_web_browser.py` fails due to a layout change (VRadioGroup replaced by VSelect) that was landed in a previous wave but never reflected in the acceptance tests. This is a pre-existing regression on `main`.

### 5. Side Effects
- **Status:** PASS
- **Verification:** `import kayakgen.ui.theme` has no module-level side effects (no printing, no global mutations beyond Final declarations).

## Verdict

The implementation of RFC 0065 Slice 1 is correct and unregressed. The findings regarding `test_services_boundaries.py` and `test_web_browser.py` are noted as blocking for the project's overall health but non-blocking for this specific theme-token foundation.

**Recommendation:** Accept with findings. The remediation lane should prioritize the `test_web_browser.py` fix to restore the browser-acceptance gate.
