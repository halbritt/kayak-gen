# Role: Findings Ledger

Deduplicate review findings into:

- **Must-fix** — items the remediation lane will fix before final review.
- **Non-blocking successor** — items deferred to a follow-up workflow, each with a
  one-line pointer.
- **Accepted** — items raised that require no action (reopen a settled
  `SLICE_4_DECISIONS.md` decision, or fall outside Slice 4 scope).

Do not implement code. Do not create new design scope. Cross-check every finding
against `SLICE_4_DECISIONS.md`. Treat as **must-fix**: a baseline PNG committed
without an explained diff; a visual compare still advisory or a no-op; a
non-deterministic or vacuous a11y check; a non-additive `CONTRAST_MANIFEST`/
`theme.py` change; a regressed behavioural check; or a missing/incorrect docs
update or D047 ratification. The known NB-2 services→ui import-boundary failure is
a non-blocking successor (hygiene follow-up), not a Slice 4 must-fix. The ledger
is the operator's source of truth for remaining work.
