Read the three review artifacts for this workflow and consolidate them into
`striatum/0019-legacy-rfc-partial-closure/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- do not relabel open display/STL surfaces as watertight CFD-ready solids;
- do not introduce asymmetric bow/stern rake unless the reviews prove it is a
  necessary safe-now fix;
- do not change geometry goldens unless a concrete RFC 0004/0006 regression
  requires it;
- do not add new dependencies;
- update RFC/readme/operator report artifacts to match what actually lands.
