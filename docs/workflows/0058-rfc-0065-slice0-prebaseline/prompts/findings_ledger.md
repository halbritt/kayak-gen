# Findings Ledger Prompt

Read all review artifacts. Produce a deduplicated ledger: must-fix (for
remediation), non-blocking successor (deferred to a later RFC 0065 slice —
especially Slice 4 for the hard gate / exact tolerance / canonical-env hardening
/ a11y / `WEB_VERIFICATION.md` — or a follow-up workflow, each with a pointer),
and explicitly accepted concerns.

Do not create new design scope or implement code. A finding that would make the
advisory compare a hard gate, or pin an exact tolerance/canonical env, belongs in
the Slice 4 successor bucket. Cross-check every finding against
`SLICE_0_DECISIONS.md`. Publish the ledger artifact.
