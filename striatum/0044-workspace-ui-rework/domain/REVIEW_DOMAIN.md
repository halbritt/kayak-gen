Verdict intent: accept

## Reviewed Scope

This domain review focused on RFC 0033: Workspace UI Rework, evaluating its alignment with the kayak design domain, current product pivot, hull/stability vocabulary, and existing constraints. Key documents reviewed include:
- AGENTS.md
- docs/PRD.md
- docs/design/kayak_hull_design_constraints.md
- docs/rfcs/0007-architectural-revisit.md
- docs/rfcs/0008-web-frontend.md
- kayakgen/eval/claims.py
- kayakgen/eval/mesh_diagnostics.py
- kayakgen/eval/cfd/jobs.py
- kayakgen/model/advisory.py
- kayakgen/model/classes.py
- kayakgen/model/hull.py

The review specifically scrutinized every chip text, persistent banner, and status-bar segment proposed in the rework against the established literals (`ClaimState`, `ReadinessLevel`, `CfdRunStatus`), the forbidden-claim list, class-preset wording, and the handling of unsupported reserved fields.

## Sub-agent/parallel assistance used

No sub-agents or parallel workers were explicitly invoked for this review. The analysis was performed by directly reading and cross-referencing the specified source documents and code files.

## Findings

No blocking findings were identified. The RFC demonstrates a robust understanding and meticulous application of the domain model and safety considerations.

*   **Clear Claim and Readiness Messaging**: The RFC consistently mandates the use of exact literals from `kayakgen/eval/claims.py` (`ClaimState`, `uncalibrated_comparative`, associated warnings) and `kayakgen/eval/mesh_diagnostics.py` (`ReadinessLevel`). This directly addresses the problem of users misinterpreting raw data as final predictions, as highlighted in `docs/PRD.md` and RFC 0033's problem statement.
*   **Strict Adherence to Forbidden Language**: The RFC explicitly lists and prohibits the use of terms like `calibrated`, `validated`, `final prediction`, `design fitness`, `hosted`, `cloud`, `worker queue`, `OpenFOAM`, `SU2` (outside specific contexts), and numeric `GZ_max`/`heel_angle_max_deg` where inappropriate. This is a critical safety measure to prevent misleading users about the current capabilities of the CFD pipeline, aligning with `docs/PRD.md` and the `reviewer_domain.md` role.
*   **Correct Handling of Unsupported Parameters**: The decision to keep `LCB_frac`, `rocker_bow_m`, and `rocker_stern_m` hidden and surface them only via RFC 0031's `unsupported` channel correctly reflects their current unimplemented status in `kayakgen/model/hull.py` and RFC 0007. This prevents users from interacting with parameters that do not yet influence the geometry as expected.
*   **Consistent Vocabulary for Class Presets**: The proposed class presets (`touring`, `performance`, `surfski_int`, `surfski_elite`) and their behavior (reseeding sliders, narrowing ranges within a class envelope) are fully consistent with the `KayakClass` definitions in `kayakgen/model/classes.py` and the design principles outlined in `docs/design/kayak_hull_design_constraints.md`.
*   **Accurate Hydrostatic and Mesh Diagnostics Representation**: The UI explicitly states that hydrostatics are "Computed from integrated geometry" and clearly distinguishes between `stl_surface` and `cfd_ready` mesh packages, reflecting the single source of truth for hydrostatics (RFC 0007) and the current state of mesh generation (`docs/PRD.md`, `kayakgen/eval/mesh_diagnostics.py`).
*   **Strong Traceability and Safety Mechanisms**: The inclusion of a "Forbidden-claim guard" in the acceptance criteria, to be enforced by new regression tests, establishes a robust mechanism for maintaining domain accuracy and preventing the reintroduction of misleading claims in future copy edits. The explicit deferral notices for "High-angle GZ unavailable" are also excellent for managing user expectations and ensuring traceability to relevant RFCs.

## Required Actions

No specific blocking actions are required from a domain perspective. The RFC is well-aligned with the domain.

## Residual Risk

No residual domain risks are identified, assuming the implementation strictly adheres to the acceptance criteria, especially regarding the exact string matching for claims and warnings. The built-in guard tests should mitigate future drift.
