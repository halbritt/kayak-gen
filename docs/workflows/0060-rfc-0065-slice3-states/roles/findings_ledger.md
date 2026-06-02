# Role: Findings Ledger

Deduplicate review findings into:

- **Must-fix** — items the remediation lane will fix before final review.
- **Non-blocking successor** — items deferred to a later RFC 0065 slice or a
  follow-up workflow, each with a one-line pointer (e.g. "Slice 4", "hygiene
  follow-up").
- **Accepted** — items raised that require no action (either because they reopen
  a settled decision in `SLICE_3_DECISIONS.md`, or because they fall outside
  Slice 3 scope).

Do not implement code. Do not create new design scope. Cross-check every finding
against `SLICE_3_DECISIONS.md`: a finding that would reopen a settled decision —
or that demands visual-regression/a11y/Lighthouse/docs work (Slice 4) — belongs in
the non-blocking successor bucket with an explicit pointer. The known NB-2
`tests/test_services_boundaries.py` services→ui import-boundary failure is a
non-blocking successor (hygiene follow-up), not a Slice 3 must-fix. The ledger is
the operator's source of truth for remaining work.
