# Operator report - workflow 0023

Updated: 2026-05-13

## Current state

- Starting from clean `main` after workflows 0021 and 0022 were landed.
- Primary gate: revisit RFC 0012 only if a currently licensed and relevant
  source dataset can be identified.
- New candidate found by web research: University of Edinburgh DataShare,
  "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
  DOI `10.7488/ds/3785`, with measured towing-tank forces and CAD files under
  CC BY 4.0.
- Initial operator assessment: the Edinburgh dataset is legally stronger than
  the prior reviewed candidates and contains measured slender-hull resistance
  data, but it is Pacific-canoe-like rather than sea-kayak-specific. The
  workflow must decide whether it is a calibration fixture, validation fixture,
  citation-only source, or no-go.
- Workflow scaffold validated:
  `striatum --repo . workflow validate
  docs/workflows/0023-resistance-calibration-dataset-vetting/workflow.json`
  -> valid.
- `git diff --check` -> clean.

## Queue

1. 0023 resistance calibration dataset vetting.
2. 0024 watertight solid mesh profile.
3. 0025 CFD solver dispatch and jobs.

## Findings recorded

- None yet for this workflow.

## Next action

- Commit the workflow scaffold, then prepare the Striatum run.
