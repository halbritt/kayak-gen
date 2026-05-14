Read `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md`, drafted RFC 0035,
and the current desktop/web UI files.

Review ergonomics and design. Do not modify repo files outside the required
review artifact.

Evaluate:

- slider-label legibility, CSS scoping, and interaction behavior after
  workflow 0046;
- web parameter row accessibility naming and whether wrapper semantics are
  appropriate;
- preset selector, custom-state, and validity-badge behavior from the user's
  point of view;
- export menu clarity and disabled/unavailable row wording;
- whether any proposed cleanup would make the UI less compact or less
  predictable.

Keep recommendations scoped to this cleanup workflow, not a desktop parity
rewrite or a broader redesign.

Write
`striatum/0047-ui-follow-up-cleanup/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`
as a `finding` artifact with verdict intent:
`accept`, `accept_with_findings`, `needs_revision`, or `reject`.
