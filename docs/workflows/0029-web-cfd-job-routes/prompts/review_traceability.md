Read `docs/workflows/0029-web-cfd-job-routes/SOURCES.md`, especially RFC 0008,
RFC 0015, RFC 0018, and the workflow 0029 queue entry.

Produce `striatum/0029-web-cfd-job-routes/traceability/REVIEW_TRACEABILITY.md`
with:

- author line: `author: operator [self-declared: operator-traceability-review]`
- verdict intent
- findings `T-001`, `T-002`, ...
- required action for each finding

Focus on:

- RFC 0008 job-stub expectations and how RFC 0018 narrows them into concrete
  routes;
- RFC 0015 local dispatch behavior that web routes must reuse rather than
  re-model;
- route and UI states required for profiles, job creation, status, run, logs,
  and raw-result inspection;
- test and documentation updates required by the accepted route slice;
- deferrals that must remain explicit, including hosted workers, real solver
  adapters, auth, cancellation guarantees, and validated CFD claims.
