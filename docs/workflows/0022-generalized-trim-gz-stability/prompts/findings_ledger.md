Read the three review artifacts for this workflow and consolidate them into
`striatum/0022-generalized-trim-gz-stability/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- do not emit high-angle `GZCurve` values unless a named closed-volume model is
  accepted by the ledger and implementable with tests in this workflow;
- preserve compatibility for existing compact load cases and current
  equilibrium-sinkage JSON consumers where practical;
- keep `+x` stern / `-x` bow and trim sign conventions explicit;
- require residuals, convergence state, iteration count, and warnings in trim
  outputs;
- update RFC/readme/operator report artifacts to match what actually lands.
