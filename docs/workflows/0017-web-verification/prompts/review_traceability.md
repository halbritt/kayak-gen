Read `docs/workflows/0017-web-verification/SOURCES.md`, especially RFC 0008,
the web app, Dockerfile, CLI serve command, and tests.

Produce `striatum/0017-web-verification/traceability/REVIEW_TRACEABILITY.md`
with:

- author line: `author: operator [self-declared: operator-traceability-review]`
- verdict intent
- findings `T-001`, `T-002`, ...
- required action for each finding

Focus on:

- which RFC 0008 acceptance criteria are already implemented;
- which are headless-tested but not browser-verified;
- whether RFC 0008 and the RFC index need status updates after this workflow;
- whether web comparison UI from RFC 0013 remains deferred;
- whether demo/deployment documentation is missing or stale.
