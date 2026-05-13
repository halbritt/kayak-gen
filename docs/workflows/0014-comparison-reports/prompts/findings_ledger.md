Read the three review artifacts for this workflow and consolidate them into
`striatum/0014-comparison-reports/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats by source count, deduplicated count, severity, and actionable-now count
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with explicit safe-now and do-not-implement lists

The implementation guidance must preserve these constraints:

- no default Pareto objective may use uncalibrated resistance;
- missing metrics become warnings, not crashes;
- no web UI implementation in this workflow;
- no new runtime dependency should be added without a finding that justifies it.
