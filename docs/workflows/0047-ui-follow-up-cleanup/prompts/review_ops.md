Read `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md`, drafted RFC 0035,
and the current tests.

Review ops, tests, and maintainability. Do not modify repo files outside the
required review artifact.

Check:

- whether the suspected dead preset branch is actually dead and safe to remove
  or whether tests should lock it down;
- whether export row data or state snapshot keys can be centralized without
  changing behavior;
- whether `PARAMETER_RAIL_CSS` duplicates global token CSS and how to test any
  cleanup safely;
- which focused static, browser, desktop, or accessibility tests should gate
  implementation;
- whether docs/changelog updates are in scope.

Use parallel helper/sub-agent analysis if available and useful. Write
`striatum/0047-ui-follow-up-cleanup/ops/REVIEW_OPS.md` as a `finding`
artifact with verdict intent:
`accept`, `accept_with_findings`, `needs_revision`, or `reject`.
