# Findings Ledger Prompt

Read all review artifacts. Produce a deduplicated findings ledger:

- must-fix findings for the remediation lane;
- non-blocking successor findings (deferred to a later RFC 0065 slice or a
  follow-up workflow), each with an explicit pointer;
- explicitly accepted review concerns that require no action.

Do not create new design scope or implement code. Cross-check every finding
against `SLICE_3_DECISIONS.md` — a finding that would reopen a settled decision,
or that demands visual-regression/a11y/Lighthouse/docs work (Slice 4), belongs in
the non-blocking successor bucket with an explicit pointer. Treat the known NB-2
`tests/test_services_boundaries.py` services→ui import-boundary failure as a
non-blocking successor (follow-up hygiene workflow), not a Slice 3 must-fix.

Publish the ledger artifact.
