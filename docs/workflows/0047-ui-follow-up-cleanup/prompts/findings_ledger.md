Read all four first-pass review artifacts for workflow 0047 and consolidate
them into `striatum/0047-ui-follow-up-cleanup/ledger/FINDINGS.md`.

Do not implement runtime behavior. Do not modify product code.

Use the maximal number of useful sub-agents or parallel helpers to extract
traceability, no-claims, ergonomics/design, and ops findings independently,
then merge them into one ledger.

The ledger must:

- list implementation-required findings with severity and source review;
- distinguish safe-now cleanup from deferred broad UI redesign or backend
  capability work;
- keep no-overclaim boundaries explicit;
- specify required tests and docs/changelog updates;
- state whether implementation may proceed.

Use valid `findings_ledger` artifact front matter. Do not add bylines or
co-author trailers unless Striatum supplies an exact expected author line in
the packet.
