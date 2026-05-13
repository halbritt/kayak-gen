Read the three review artifacts for this workflow and consolidate them into
`striatum/0016-equilibrium-stability/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- keep design-waterline initial stability available;
- do not implement high-angle GZ curves;
- do not add CFD, dynamic stability, or new dependencies;
- do not overclaim trim if longitudinal load/geometry inputs are
  under-specified;
- update RFC/readme/operator report artifacts to match what actually lands.
