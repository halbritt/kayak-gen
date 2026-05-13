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
- Scaffold committed as `761195b` and pushed to `origin/main`.
- Striatum run `run_6ca2095f019345e199943d5f46f0676f` is running on branch
  `striatum/0023-resistance-calibration-dataset-vetting`.
- `source_inventory` is claimed as
  `sess_bfdb0b392b014aada3aa86da2dcf69b0` and the inventory artifact has been
  written, published as `art_ae8bbaf9890e461794d4aafc26c46d3e`, and
  completed.
- Gate rule: implement calibration fixtures only if a licensed, measured,
  kayak/canoe-relevant dataset is accepted by the review lanes. Otherwise,
  record blockers and leave resistance explicitly uncalibrated.
- New candidate under review: University of Edinburgh DataShare,
  "Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
  DOI `10.7488/ds/3785`, CC BY 4.0.
- Initial source-inventory recommendation: treat the Edinburgh dataset as a
  validation candidate, not direct `calibrated_kayak_v1` input.
- Three review lanes completed with `accept_with_findings`:
  provenance `art_6af485db5a5749fb8988b3f6864cbf61`;
  domain `art_f31b4377809d4c189618e8acfd063edd`;
  implementation `art_6e725c668de446758c6a2fb6a438045f`.
- Consensus so far: add Edinburgh as validation source metadata only; do not
  calibrate resistance curves or ingest numeric fixtures in this workflow.
- `findings_ledger` is claimed as
  `sess_74e0e572486b4644a7bcda251b0f088a` and the ledger artifact has been
  written, published as `art_bf2f9713854e4fef85e728e912bbf58d`, and
  completed.
- Ledger gate result: no calibration fixture accepted; Edinburgh should be
  added as a `validation_candidate` registry source only.
- `implement_findings` is claimed as
  `sess_d9f725f7a030423facaa31427704bf0b`.
- Implementation has added the Edinburgh validation-only source registry record,
  focused tests, and RFC status wording. Focused resistance tests pass.
- Full verification after implementation:
  `.venv/bin/python -m pytest -q` -> 147 passed;
  `striatum --repo . doctor` -> clean;
  `git diff --check` -> clean.
- Implementation patch summary published as
  `art_dca1faa393a54915bae85c1b4445bcb5` and `implement_findings` completed.
- `final_review` is claimed as
  `sess_c7f91d66bf5e4b6aad87e0da294389fa` and final review artifact has been
  written with verdict `accept`.
- Final review published as `art_27099783c2ef4921a049deaa1c4302f6`; Striatum
  run `run_6ca2095f019345e199943d5f46f0676f` is complete.

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
