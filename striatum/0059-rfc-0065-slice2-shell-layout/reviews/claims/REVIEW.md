author: operator [self-declared: 0059-claims-fin]

# Review: Claims and User-Facing Boundaries (RFC 0065 Slice 2)

**Verdict:** `accept_with_findings`

The workflow 0059 (RFC 0065 Slice 2) changes have been reviewed for claim truthfulness and adherence to user-facing boundary constraints. The reflow of the workspace shell onto Slice 1 theme tokens maintains the established "claim line" without regression.

## Findings

### 1. Chip Specs and Semantic Classes (Byte-stability)
- **Status:** Verified.
- **Detail:** `CHIP_SPECS`, `CHIP_LABELS`, and `CHIP_CLASSES` in `kayakgen/ui/theme.py` are untouched by this slice and remain byte-identical to their pre-slice state.
- **Traceability:** RFC 0065 Slice 2 D6.

### 2. Chip Coloring
- **Status:** Verified.
- **Detail:** No raw or advisory chips have been recoloured into the `success` palette. The new `WORKSPACE_SHELL_CSS` in `kayakgen/ui/web/app.py` applies the `type-caption` role to chips consistently without introducing new color-mapping logic that would promote a "raw" result.

### 3. Persistent Captions
- **Status:** Verified.
- **Detail:** All required persistent captions remain byte-identical after the reflow:
    - **Resistance:** `"Raw comparative filter; not final prediction."` and the `RESISTANCE_DETAIL_COPY` uncalibrated warning in `app.py`.
    - **High-angle GZ:** `"Unvalidated hydrostatic comparison; not safety, seaworthiness, calibrated, validated, or final-prediction claim"` in `read_models.py` (referenced by `app.py`).
    - **CFD:** `CFD_LOCAL_FILESYSTEM_NOTICE` and `CFD_ARTIFACT_STRAPLINE` in `controllers.py` and `app.py`.
    - **Mesh:** `"Open wetted-surface profile; not watertight cfd_ready."` in `app.py`.
- **Traceability:** RFC 0065 Slice 2 D6.

### 4. Claim Literals and REST Boundaries
- **Status:** Verified.
- **Detail:** No new `claim_state`, `Readiness`, or `accepted_uses` literals were introduced. `kayakgen/ui/web/controllers.py` is unchanged in this slice, ensuring the RFC 0032 REST boundary remains intact.

### 5. RFC 0033 Section 8 No-Go List
- **Status:** Verified.
- **Detail:** Forbidden tokens (`hosted`, `cloud`, `worker queue`, `OpenFOAM`, `SU2`) remain absent from `kayakgen/ui/web/app.py` except where explicitly permitted in established safety notices.

### 6. Information Hierarchy and Positioning
- **Status:** Verified.
- **Detail:** The reflow (D1-D4) wraps existing generated sections in layout-only `Div` containers (`kg-generate-build`, `kg-generate-watch`, etc.) using the `TYPOGRAPHY` roles. Unvalidated/raw results have not been moved into positions that would imply calibration or validation.

### 7. ARIA Labels and Tooltips
- **Status:** Verified.
- **Detail:** New or moved ARIA labels (e.g., `aria-label="{region} region"`) carry structural/navigation semantics only and do not introduce new claim-bearing language.

## Conclusion

The "claim line" is preserved. The UI reflow correctly applies the new visual language without compromising the project's commitment to technical integrity and the clear separation of unvalidated results from calibrated claims.
