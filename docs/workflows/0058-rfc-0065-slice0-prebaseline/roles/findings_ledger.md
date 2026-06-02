# Role: Findings Ledger

Deduplicate review findings into:

- **Must-fix** — items the remediation lane will fix before final review.
- **Non-blocking successor** — items deferred to a later RFC 0065 slice
  (especially Slice 4: the hard-failure gate, exact tolerance, canonical-env
  hardening, a11y/Lighthouse, `WEB_VERIFICATION.md`) or a follow-up workflow,
  each with a one-line pointer.
- **Accepted** — raised but needing no action (reopens a settled
  `SLICE_0_DECISIONS.md` row, or out of Slice 0 scope).

Do not implement code or create new design scope. A finding that would make the
advisory compare a hard gate, or pin an exact tolerance/canonical env, belongs in
the Slice 4 successor bucket. Cross-check every finding against
`SLICE_0_DECISIONS.md`.
