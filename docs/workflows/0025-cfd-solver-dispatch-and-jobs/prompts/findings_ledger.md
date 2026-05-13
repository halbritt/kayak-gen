Read the three review artifacts for this workflow and consolidate them into
`striatum/0025-cfd-solver-dispatch-and-jobs/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- implement local dispatch contracts and unavailable/mock behavior first;
- do not integrate a real solver;
- do not claim solver results are calibrated or validated;
- reject mesh packages below the selected solver profile's required readiness;
- update RFC/readme/operator report artifacts to match what actually lands.
