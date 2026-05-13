Read the three review artifacts for this workflow and consolidate them into
`striatum/0021-web-plots-comparison-ui/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- do not claim Playwright or Lighthouse ran unless they actually did;
- do not replace Trame or redesign the UI;
- implement only the smallest coherent plot/comparison slice that the reviews
  mark safe now;
- keep raw uncalibrated resistance warnings visible and do not turn them into
  default design recommendations;
- unsupported comparison actions must be explicit in the UI/docs;
- update RFC/readme/operator report artifacts to match what actually lands.
