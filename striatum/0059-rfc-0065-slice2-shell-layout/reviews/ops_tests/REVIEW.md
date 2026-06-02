author: operator [self-declared: 0059-ops-fin]

# Review: Tests and Operational Behaviour (Workflow 0059)

verdict: accept_with_findings (gemini author: reviewer-ops-tests-gemini-pro-3.1-001; operator-finalized after lease expired during the full suite)

## Summary

The Slice 2 implementation correctly applies the new theme tokens and typographic hierarchy across the web shell. Core UI tests, theme-token linting, and desktop layout verification tests all pass. However, two operational defects were identified: one related to test coverage of the status-bar contract, and another regarding an import boundary violation in the services layer.

## Findings

### F1: Status-bar `data-testid` hooks are not asserted (Severity: Low/Medium)
The workflow objective and D3/D5 require that the four status segments (`status-package`, `status-readiness`, `status-resistance`, `status-cfd`) and the `workspace-status-bar` test-ids "still assert" in `tests/test_web_layout.py`. 
- **Observation:** While these hooks are correctly present in `kayakgen/ui/web/app.py` (lines 2297-2314), there are no positive assertions for these specific `data-testid` strings in `tests/test_web_layout.py`.
- **Requirement:** `tests/test_web_layout.py` should be updated to include positive assertions for these hooks to preserve the workspace contract.

### F2: Import boundary violation in `evaluation.py` (Severity: Medium)
The repo-wide hygiene mandate requires that `kayakgen/services` does not import from `kayakgen.ui`.
- **Observation:** `kayakgen/services/evaluation.py` imports `HYDROSTATICS_ROW_METADATA` from `kayakgen.ui.hydrostatics_metadata`. 
- **Impact:** This causes a failure in `tests/test_services_boundaries.py` (`test_services_does_not_import_ui_or_cli[path2]`).
- **Recommendation:** Move the metadata registry to a lower-level shared package (e.g., `kayakgen.model` or a dedicated `kayakgen.registry`) that both `services` and `ui` can import from.

### F3: Determinism and Repo Hygiene
- **Positive:** No `time.sleep` calls were found in the core UI test files (`tests/test_web_layout.py`, `tests/test_web_inline_help.py`, `tests/test_ui_theme.py`).
- **Positive:** `git diff --check` passed with no whitespace or conflict marker issues.
- **Positive:** The widened orphan-literal lint in `tests/test_ui_theme.py` correctly identified no new visual literals in `kayakgen/ui`.

## Verdict Details

| Requirement | Status | Note |
| :--- | :--- | :--- |
| `test_web_layout.py` reflects renamed/moved hooks | ✓ | No hooks were renamed/removed; re-indentation of `generative-jobs-table` is correct. |
| Status-bar test-ids still assert | ✗ | **Defect F1**: Missing positive assertions for status-bar `data-testid` hooks. |
| Region test-ids still assert | ✓ | `region-params/-geometry/-review` asserted via `LAYOUT_TEST_IDS`. |
| First-viewport & collapse hooks asserted | ✓ | `kg-collapse-under-960`, etc. asserted via `RESPONSIVE_CLASS_HOOKS`. |
| `test_web_inline_help.py` reflects moved hooks | ✓ | `comparison-source-help` remains correctly asserted. |
| Token-only styling (no new literals) | ✓ | `test_ui_theme.py` passes with widened lint. |
| Desktop rendered-bbox tests green | ✓ | `tests/test_desktop_layout.py` and related pass. |
| Full repo suite green (minus smoke) | ✗ | **Defect F2**: Boundary test failure in `test_services_boundaries.py`. |
| No wall-clock sleeps in new/modified tests | ✓ | Verified in core UI files. |
| `git diff --check` passes | ✓ | Verified. |
| Forbidden-copy scan passes | ✓ | Verified via `test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`. |
