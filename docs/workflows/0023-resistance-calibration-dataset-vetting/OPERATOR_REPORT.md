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
- Scaffold committed as `761195b` and pushed to `origin/main`.
- Prepared Striatum run `run_6ca2095f019345e199943d5f46f0676f`.
- Confirmed branch `striatum/0023-resistance-calibration-dataset-vetting` and
  started the run.
- Claimed and acked `source_inventory` as
  `sess_bfdb0b392b014aada3aa86da2dcf69b0`.
- Wrote source inventory at
  `striatum/0023-resistance-calibration-dataset-vetting/research/SOURCE_INVENTORY.md`.
- Source inventory recommendation: Edinburgh DataShare Pacific-canoe dataset
  should proceed as a validation-candidate review, not as direct
  `calibrated_kayak_v1` calibration.
- Published source inventory as `art_ae8bbaf9890e461794d4aafc26c46d3e` and
  completed `source_inventory`.
- Registered, claimed, and acked review sessions:
  - `review_provenance` as `sess_6a4f82c2ae42437eac741c823efec901`.
  - `review_domain` as `sess_12a50500686741e9a93eeeb62469f8c5`.
  - `review_implementation` as `sess_095b670e857044e69fabf070faf12b01`.
- Submitted three `accept_with_findings` review artifacts:
  - provenance `art_6af485db5a5749fb8988b3f6864cbf61`;
  - domain `art_f31b4377809d4c189618e8acfd063edd`;
  - implementation `art_6e725c668de446758c6a2fb6a438045f`.
- Review consensus: Edinburgh can be recorded as a validation candidate with
  CC BY 4.0 provenance, but no reviewed source should become a calibration
  fixture in this workflow.
- Claimed and acked `findings_ledger` as
  `sess_74e0e572486b4644a7bcda251b0f088a`.
- Wrote findings ledger at
  `striatum/0023-resistance-calibration-dataset-vetting/ledger/FINDINGS.md`.
- Ledger gate result: no calibration fixture accepted; Edinburgh accepted only
  as a `validation_candidate` registry source.
- Published ledger as `art_bf2f9713854e4fef85e728e912bbf58d` and completed
  `findings_ledger`.
- Claimed and acked `implement_findings` as
  `sess_d9f725f7a030423facaa31427704bf0b`.
- Implementation completed:
  - added Edinburgh DataShare as a validation-only source registry record;
  - added focused registry assertions in `tests/test_resistance.py`;
  - updated RFC 0012 and the RFC index without changing raw resistance status.
- Verification so far:
  - `.venv/bin/python -m pytest tests/test_resistance.py -q` -> 12 passed.
  - `.venv/bin/python -m pytest -q` -> 147 passed.
  - `striatum --repo . doctor` -> clean.
  - `git diff --check` -> clean.
- Wrote patch summary at
  `striatum/0023-resistance-calibration-dataset-vetting/implementation/PATCH_SUMMARY.md`.
- Published implementation patch summary
  `art_dca1faa393a54915bae85c1b4445bcb5` and completed
  `implement_findings`.
- Claimed and acked `final_review` as
  `sess_c7f91d66bf5e4b6aad87e0da294389fa`.
- Wrote final review at
  `striatum/0023-resistance-calibration-dataset-vetting/final/FINAL_REVIEW.md`
  with verdict `accept`.
- Published final review as `art_27099783c2ef4921a049deaa1c4302f6` with
  verdict `accept`.
- Striatum run `run_6ca2095f019345e199943d5f46f0676f` is complete.

## Queue

1. 0023 resistance calibration dataset vetting.
2. 0024 watertight solid mesh profile.
3. 0025 CFD solver dispatch and jobs.

## Findings recorded

- None yet for this workflow.

## Next action

- Commit, push, and fast-forward `main`.
