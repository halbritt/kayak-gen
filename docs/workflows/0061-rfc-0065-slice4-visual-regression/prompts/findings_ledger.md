# Findings Ledger Prompt

Read all review artifacts. Produce a deduplicated findings ledger:

- must-fix findings for the remediation lane;
- non-blocking successor findings (deferred to a follow-up workflow), each with an
  explicit pointer;
- explicitly accepted review concerns that require no action.

Do not create new design scope or implement code. Cross-check every finding
against `SLICE_4_DECISIONS.md`. Flag as **must-fix** any baseline PNG committed
without an explained diff, any visual compare that is still advisory or a no-op,
any a11y check that is non-deterministic or asserts nothing, any non-additive
`CONTRAST_MANIFEST`/`theme.py` change, any retained behavioural check that
regressed, or any missing/incorrect docs update or D047 ratification. Treat the
known NB-2 `tests/test_services_boundaries.py` services→ui import-boundary failure
as a non-blocking successor (hygiene follow-up), not a Slice 4 must-fix.

Publish the ledger artifact.
