---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---
# Domain Review for Workflow 0035: High-angle GZ generated-body handoff

This review focuses on the domain aspects of workflow `0035-high-angle-gz-generated-body-handoff`, analyzing the provided Python evaluation scripts and associated documentation for gaps and readiness for implementation.

## Findings

### 1. Generated-body `body_ref` Semantics

*   **Observation**: The term `body_ref` is not directly present in the analyzed code. However, the concept of a 'generated body' is represented by `ClosedVolumeBody` with `body_type='generated_hull_plus_deck_closed_body'` in `kayakgen/eval/closed_volume.py`.
*   **Gap**: The integration of this generated body type for high-angle GZ calculations is pending. A specific `GZNotImplementedError` in `kayakgen/eval/stability.py` states, "high-angle GZ is reserved until closed_volume_body_not_defined is resolved," indicating that the mechanism for referencing or passing such a generated body to stability functions is not yet established.
*   **Implication**: The intended semantics for using generated bodies in high-angle GZ are not fully defined in the current implementation.

### 2. Heel Grid

*   **Observation**: No explicit 'heel grid' is defined or utilized in the provided stability calculation files (`kayakgen/eval/stability.py`, `kayakgen/eval/hydrostatics.py`).
*   **Gap**: The function `evaluate_gz_curve`, which would naturally involve iterating through heel angles (forming a heel grid), is explicitly marked as not implemented. Current stability calculations focus on upright or trimmed equilibrium conditions.
*   **Implication**: The absence of a heel grid and the unimplemented high-angle GZ function means there is no systematic evaluation of stability across a range of heel angles.

### 3. CG and Trim Assumptions

*   **Observation**: Center of Gravity (CG) is managed via `LoadCase` parameters (`kg_above_keel_m`) and associated methods. Trim is handled for initial stability (assumed zero) and equilibrium stability (zero for legacy, or calculated via a 'fixed-body station area trim model' for longitudinal components).
*   **Gap**: Specific assumptions for the interaction of trim and heel at high angles are undefined due to the lack of high-angle GZ implementation.
*   **Implication**: While current assumptions are suitable for upright/trimmed equilibrium, they do not extend to the high-angle GZ regime, which is the focus of this workflow.

### 4. Warnings

*   **Observation**: Warning messages are implemented as clear, descriptive strings within the `StabilityResult` object.
*   **Strength**: The warnings effectively communicate the status and limitations of the analysis, including a direct `high_angle_gz_not_implemented` warning.
*   **Implication**: The warning system is robust for indicating current implementation boundaries.

### 5. Fixture-only Math vs. Derived Calculations

*   **Observation**: The core hydrostatic and stability calculations in `kayakgen/eval/hydrostatics.py` and `kayakgen/eval/stability.py` are predominantly derived from geometric properties and numerical methods.
*   **Strength**: There is no evidence of reliance on fixture-only mathematical models; calculations are based on hull geometry, mesh data, and numerical integration.
*   **Implication**: This indicates a sound, physics-based approach for the implemented functionalities.

### 6. Summary Metrics (Relevant to High-angle GZ)

*   **Observation**: Several summary metrics for initial and equilibrium stability are defined (e.g., `initial_GM0_m`, displacement, wetted surface area, equilibrium draft/trim).
*   **Critical Gap**: **No summary metrics relevant to high-angle GZ are calculated or reported.** The `evaluate_gz_curve` function is explicitly unimplemented, meaning metrics like the GZ lever, the range of positive GZ, or the area under the GZ curve are absent.
*   **Implication**: The absence of high-angle GZ specific metrics is a significant gap for a workflow focused on this domain.

## Verdict

The workflow scaffold is not contradictory and utilizes sound, derived calculation methods for existing stability features. However, critical components for the high-angle GZ domain, including the definition and use of generated bodies for this purpose, the implementation of a heel grid, specific high-angle trim/heel assumptions, and most importantly, the definition and calculation of high-angle GZ summary metrics, are either pending or entirely absent. These represent significant evidence gaps and "not implemented yet" findings.

Therefore, the verdict is `accept_with_findings`, indicating that the current state is implementable with the identified gaps needing further development.
