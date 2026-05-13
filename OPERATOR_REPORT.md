# Operator Report

Updated: 2026-05-13

## Current State

- `main` is clean and tracking `origin/main`.
- Workflows 0021 and 0022 have landed and were pushed to `origin/main`.
- Next queued workflow is 0023, resistance calibration dataset vetting.
- Root report was created after compaction because only per-workflow reports
  were present in `docs/workflows/*/OPERATOR_REPORT.md`.

## Completed Since Backlog Queue

- 0021 web plots and comparison UI: landed compact web analysis/comparison
  views, tests, and RFC/status updates.
- 0022 generalized trim and GZ stability: landed explicit longitudinal load
  components, fixed-body upright trim equilibrium, CLI/sweep summaries, tests,
  and truthful high-angle GZ deferral.

## Active Workflow

- 0023 resistance calibration dataset vetting has been scaffolded and validated.
- Gate rule: implement calibration fixtures only if a licensed, measured,
  kayak/canoe-relevant dataset is accepted by the review lanes. Otherwise,
  record blockers and leave resistance explicitly uncalibrated.
- New candidate under review: University of Edinburgh DataShare,
  "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
  DOI `10.7488/ds/3785`, CC BY 4.0.

## Verification Baseline

- Latest full suite after workflow 0022: `.venv/bin/python -m pytest -q` ->
  147 passed.
- `striatum --repo . workflow validate
  docs/workflows/0023-resistance-calibration-dataset-vetting/workflow.json` ->
  valid.
- `git diff --check` -> clean.
- `striatum --repo . doctor` was clean after the skill refresh in workflow
  0022.
- Ruff is not installed in the current virtualenv, so ruff checks are
  unavailable unless dependencies are added.
