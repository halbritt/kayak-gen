Read `docs/workflows/0029-web-cfd-job-routes/SOURCES.md`, especially the web
modules, CFD job code, and tests.

Produce `striatum/0029-web-cfd-job-routes/ops/REVIEW_OPS.md` with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- route error handling for bad payloads, missing job IDs, missing artifacts, and
  mesh readiness rejection;
- local filesystem job-store access and path traversal boundaries for logs and
  raw artifacts;
- deterministic API payloads over `CfdJobSpec`, `CfdRunRecord`, and solver
  profiles;
- headless web tests and optional browser smoke coverage;
- failure/unavailable fixtures that do not require external solver binaries.
