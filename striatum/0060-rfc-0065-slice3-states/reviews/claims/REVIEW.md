author: operator [self-declared: 0060-claims-fin]

# Review: Claims and User-Facing Boundaries

**Workflow:** 0060-rfc-0065-slice3-states  
**Job ID:** job_run_114c3b5975eb90f2542b264f033927fb_review_claims  
**Author:** author: reviewer-claims-gemini-pro-3.1-001  
**Date:** 2026-06-02  

## 1. Executive Summary

The review confirms that the changes in Workflow 0060 (RFC 0065 Slice 3) strictly adhere to the truthfulness mandates and preserve established user-facing boundaries. The implementation focuses on uniform control states (focus-ring, hover, disabled) and explicit empty/loading/error states across the web shell and Generate panel. No unvalidated results have been promoted to validated claims, and all persistent captions and claim-state constants remain byte-identical to the Slice 2 baseline.

## 2. Chip Integrity and Claim Line

- **CHIP_SPECS / CHIP_LABELS / CHIP_CLASSES:** Verified byte-identical in `kayakgen/ui/theme.py`. No new chips or semantic classes were introduced.
- **Recolouring Check:** No chips were recoloured into the success palette. Styling changes are limited to `border-radius`, `font`, and token-based state overlays (hover/focus).
- **Persistent Captions:** Every persistent caption (resistance comparative filter, high-angle GZ unavailable, CFD local/artifact banners, and not-watertight-cfd_ready negation) is byte-identical.

## 3. Honestly-Disabled Controls

- **Watertight-Solid:** The `WATERTIGHT_DISABLED_COPY` remains verbatim: "Current generated packages do not satisfy watertight-solid readiness."
- **Export Menu:** Disabled rows in the export menu preserve their `aria-disabled` status and explanatory copy.
- **Generative Submit:** The `generative_submit_disabled` button and its blocking-reason copy are unchanged.
- **Cm Reserved Preset:** The `custom` fallback behavior for the Cm slider when a preset is modified is preserved.

## 4. State Panel Truthfulness

The new empty/loading/error states introduced in Slice 3 are purely informational and carry no claim/validation semantics.

- **Loading/Running States:** Explicit `kg-state-panel--running` (info palette) used for jobs and frontier loading.
- **Failed/Cancelled States:** Explicit `kg-state-panel--failed` (error palette) used for job failures and invalid hull states.
- **Empty States:** Neutral messaging (e.g., "(no generative jobs yet)") used for empty collections.
- **Verification:** No empty/loading/error treatment allows a failed or unvalidated result to be read as successful or validated. The `generative_jobs_failed_kind` surfaces raw error types (e.g., from `GenerativeJobError.kind`) without interpretation.

## 5. Forbidden-Copy and Boundaries

- **Scan Coverage:** The extended forbidden-copy scan (`tests/test_web_layout.py`) covers all new rendered strings. No occurrences of "hosted", "cloud", "calibrated", or "final" were found in the new state panels.
- **REST Routes:** No new REST routes were added (verified in `kayakgen/ui/web/controllers.py`). The RFC 0032 boundary is intact.
- **No-Go List:** The RFC 0033 §8 no-go list remains absent from all rendered output.

## 6. Test Results

The following test suites were executed and passed successfully:
- `tests/test_web_layout.py`: Verified layout, chip, and forbidden-string assertions.
- `tests/test_web_inline_help.py`: Verified stable data-testid hooks for state panels.
- `tests/test_ui_theme.py`: Verified orphan-literal lint remains green.

**Verdict: PASS**
