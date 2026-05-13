Read the three review artifacts for this workflow and consolidate them into
`striatum/0024-watertight-solid-mesh-profile/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- do not relabel current open hull/deck surfaces as watertight or `cfd_ready`;
- implement watertight geometry only if the ledger accepts an explicit closure
  contract with tests;
- prefer a named watertight-required profile plus blocked/readiness diagnostics
  if closure semantics are still open;
- keep current open wetted-surface package behavior compatible;
- update RFC/readme/operator-report artifacts to match what actually lands.
