# Operator report - workflow 0013

Updated: 2026-05-13

## Current state

- User asked to proceed through the queued backlog after workflow 0012.
- Workflow 0012 accepted, but its gate rejected all reviewed sources as
  canonical calibration fixtures.
- This workflow therefore targets RFC 0005/0012 resistance acceptance revision,
  not numeric calibration.
- Starting from clean `main` at `76a080e`.
- Workflow scaffold committed on `main` as `6590032`.
- Prepared Striatum run `run_09d8fab3d88e4a6588b8838ff9f34e61`.
- Confirmed branch `striatum/0013-resistance-acceptance-revision` and started
  the run.
- Registered, claimed, and acked review sessions:
  - `review_traceability` as `sess_1f270ae08a234e4dac8d0c363bf3a4da`.
  - `review_domain` as `sess_cc00a9ffcecb405ca793c506504eddce`.
  - `review_ops` as `sess_73802a8d9cff40dea02627e67d69a00c`.
- Wrote three review artifacts with `accept_with_findings` intent. The shared
  recommendation is to retire the two stale RFC 0005 xfails from the current
  test contract and document the landed tier as raw comparative filtering.
- Submitted review artifacts:
  - traceability `art_d24cc675f6174c4fb794235ba25728a5`;
  - domain `art_b503d5d6f30c48eba34e47f8f99d26a5`;
  - ops `art_4faeabb43132410eaa1b6aa39df7a960`.
- Claimed and acked `findings_ledger` as
  `sess_c7d17b700bbf4804b99e89f75dc1e701`.
- Wrote findings ledger at
  `striatum/0013-resistance-acceptance-revision/ledger/FINDINGS.md`.
- Ledger artifact was accepted as
  `art_cc4466130ca3452ab85695202bfeea0b`.
- Claimed and acked `implement_findings` as
  `sess_1220d62d197d4596a72bfa1c34931f56`.
- Implementation revised RFC 0005/RFC index wording and removed the two stale
  expected-failure tests from `tests/test_resistance.py`.
- Final review found and fixed one stale RFC 0012 cross-reference describing
  RFC 0005 as partial and the old xfails as preserved.
- Wrote implementation artifact at
  `striatum/0013-resistance-acceptance-revision/implementation/PATCH_SUMMARY.md`.
- Verification passed:
  - `.venv/bin/python -m pytest tests/test_resistance.py -q` -> 12 passed.
  - `.venv/bin/python -m pytest -q` -> 100 passed.
  - `git diff --check` -> clean.
- Final review accepted the workflow:
  - artifact `art_450f788bcd8641309d16cf25242295ae`;
  - verdict `verdict_a3a320bf5de34c11b89d87d3b98e8d11`;
  - run state `completed`.

## Findings recorded

- F-001: RFC 0005 acceptance criteria need a landed raw-filter tier and a
  deferred calibrated/optimized tier.
- F-002: two xfailed tests encode retired claims.
- F-003: RFC index needs the new status.
- F-004: anti-overclaiming guardrails must remain.
- F-005: runtime budget must match the raw evaluator tier.

## Next action

- Commit workflow 0013, push the branch, fast-forward `main`, and continue to
  the next queued workflow.
