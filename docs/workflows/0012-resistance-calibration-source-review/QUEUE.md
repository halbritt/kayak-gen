# Pipeline backlog queue

This queue is ordered by dependency leverage, not by RFC number. Do not advance
to a later workflow if the prior final gate rejects or leaves unresolved
blockers.

## 1. Resistance calibration source review

Workflow: `0012-resistance-calibration-source-review`

Gate: accept a concrete published kayak/canoe resistance source, or record that
no current source is suitable and keep analytical resistance uncalibrated.

## 2. Resistance closure

Workflow to scaffold after gate success: `0013-resistance-closure`

Scope: create the calibration data schema/fixtures if the source gate accepts,
wire calibrated metadata, and either satisfy or revise the RFC 0005 low-Froude
and 200 ms xfailed acceptance tests.

## 3. Comparison reports

Workflow to scaffold after resistance closure: `0014-comparison-reports`

Scope: implement `kayakgen compare`, comparison report models, default
objectives that exclude uncalibrated resistance, and tests over deterministic
sweep fixtures.

## 4. Mesh package and solver profile

Workflow to scaffold after comparison reports: `0015-mesh-package-profile`

Scope: implement `kayakgen mesh-package`, manifest writing, the first open
wetted-surface solver profile, and explicit future checks for watertight solid
profiles.

## 5. Equilibrium stability

Workflow to scaffold after mesh profile work: `0016-equilibrium-stability`

Scope: add sinkage/trim equilibrium mode for load cases with convergence
tolerances, while keeping design-waterline diagnostics available.

## 6. Web verification

Workflow to scaffold after the CLI/report surfaces stabilize:
`0017-web-verification`

Scope: browser visual verification, performance/Lighthouse checks where
practical, and demo/deployment documentation.
