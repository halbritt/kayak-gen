Read the three review artifacts for this workflow and consolidate them into
`striatum/0029-web-cfd-job-routes/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- implement only accepted web CFD job routes and UI states over the existing
  local dispatch contract;
- reuse `CfdJobSpec`, `CfdRunRecord`, solver profiles, mesh readiness gates, and
  local job artifacts;
- keep unavailable, failed, and raw/unvalidated states visible;
- do not add hosted workers, authentication, billing, quotas, real solver
  adapters, or cancellation guarantees unless the accepted RFC explicitly
  requires them;
- do not claim CFD outputs are calibrated, validated, or final design fitness
  signals.
