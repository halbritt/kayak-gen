# Operator report - workflow 0012

Updated: 2026-05-13

## Current state

- User asked to queue the next workflow and, if it succeeds, continue through
  the remaining pipeline backlog.
- Starting from clean `main` at `7222d5b`.
- Primary gate: resistance calibration source review for RFC 0012.
- Follow-on queue is recorded in `QUEUE.md` and should only advance after the
  active workflow's final review accepts or explicitly accepts with bounded
  findings.
- Workflow validated and was committed on `main` as `e00d9ef`.
- Prepared Striatum run `run_b8d2bd2b94f345c1a30521671cf0ba67`.
- Confirmed branch `striatum/0012-resistance-calibration-source-review` and
  started the run.
- Parallel source-review sub-agents returned a consistent early signal: useful
  published kayak references exist, but no candidate is yet safe and broad
  enough to vendor as canonical calibration data.
- Claimed and acked `source_inventory` as
  `sess_8ee73004f8a948ab9ec853e23a36a17d`.
- Wrote source inventory at
  `striatum/0012-resistance-calibration-source-review/research/SOURCE_INVENTORY.md`.
- Published source inventory as `art_891d37f958b14ebc88cc107a3e350e8b` and
  completed `source_inventory`.
- Registered, claimed, and acked review sessions:
  - `review_provenance` as `sess_3c555f55f8a94b18a9bf9f8e57cb5241`.
  - `review_domain` as `sess_16072d6f1b094e3590dc8619564d30d1`.
  - `review_implementation` as `sess_0e0228334f6d45c883471a0b0b059638`.
- Wrote review artifacts with `accept_with_findings` intent. The shared
  conclusion is no current source should be treated as canonical calibration
  data, but source/provenance metadata can be safely improved now.
- Submitted review artifacts:
  - provenance `art_604367e2a212430482c1cd90237b9b0a`;
  - domain `art_9b11474dda8247e6bc3870a474326db7`;
  - implementation `art_6b78cb7ef2d54894b7c90a2081b9ec66`.
- Claimed and acked `findings_ledger` as
  `sess_c050c8521d2b465599a5a9871e221f29`.
- Wrote the findings ledger at
  `striatum/0012-resistance-calibration-source-review/ledger/FINDINGS.md`.
- Published ledger as `art_10a18d36165c4f1490f1e90154837a9e` and completed
  `findings_ledger`.
- Claimed and acked `implement_findings` as
  `sess_839045cf53b6437e90f8898ce59e0cdb`.
- Implementation completed:
  - Added structured resistance source registry with no calibration fixtures.
  - Added optional calibration/provenance fields to `ResistanceMetadata`.
  - Centralized raw resistance warnings and changed Wigley wording from
    calibration to verification.
  - Updated RFC 0012 and the queue to reflect the no-accepted-source gate
    result.
- Verification so far:
  - `.venv/bin/python -m pytest tests/test_resistance.py -q` -> 12 passed,
    2 xfailed.
  - `.venv/bin/python -m pytest -q` -> 100 passed, 2 xfailed.
  - `git diff --check` -> clean.
- Published implementation patch summary
  `art_2485159c29a54302b80ed3b9f4d5cf94` and completed
  `implement_findings`.
- Claimed final review as `sess_95a65abcc2074a008725583adb5361b3`.
- Wrote final review at
  `striatum/0012-resistance-calibration-source-review/final/FINAL_REVIEW.md`.
- Published final review as `art_4ac4932edce2431bacd0d33cedf70e12` with
  verdict `accept`.
- Striatum run `run_b8d2bd2b94f345c1a30521671cf0ba67` is complete.

## Queue

1. Resistance calibration source review and provenance gate.
2. RFC 0005/0012 resistance closure or revision based on the gate.
3. RFC 0013 comparison report/CLI with calibrated-resistance-aware defaults.
4. RFC 0010 mesh package and first open-wetted-surface solver profile.
5. RFC 0011 sinkage/trim equilibrium stability mode.
6. RFC 0008 web verification and deployment follow-up.

## Findings recorded

- Findings ledger has 7 deduplicated findings: 4 actionable now and 3 blocking
  numeric calibration.
- Gate result: no reviewed source is accepted as canonical calibration data.
- Safe implementation landed source/provenance metadata and a reviewed source
  registry without changing raw resistance behavior.

## Next action

- Commit/merge workflow 0012, then scaffold the next queued workflow as
  resistance closure/revision, not numeric calibration.
