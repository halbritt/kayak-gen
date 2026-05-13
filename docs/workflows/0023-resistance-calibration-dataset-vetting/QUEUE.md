# Pipeline backlog queue

This queue is ordered by dependency leverage, not by RFC number. Do not advance
to a later workflow if the prior final gate rejects or leaves unresolved
blockers.

## 1. Resistance calibration dataset vetting

Workflow: `0023-resistance-calibration-dataset-vetting`

Gate: accept a concrete published kayak/canoe resistance source for calibration,
classify it as validation-only/citation-only, or record that no current source
is suitable and keep analytical resistance uncalibrated.

Primary candidate for this pass: University of Edinburgh DataShare,
"Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
DOI `10.7488/ds/3785`.

## 2. Watertight solid mesh profile

Workflow to scaffold after this gate: `0024-watertight-solid-mesh-profile`

Scope: implement only explicit watertight-solid readiness behavior from RFCs
0010 and 0015. Do not relabel open wetted surfaces as watertight.

## 3. CFD solver dispatch and jobs

Workflow to scaffold after watertight profile: `0025-cfd-solver-dispatch-and-jobs`

Scope: introduce local job specs, unavailable/mock adapter behavior, run
records, and status surfaces without claiming real solver success.
