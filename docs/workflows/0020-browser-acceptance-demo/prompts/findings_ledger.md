Read the three review artifacts for this workflow and consolidate them into
`striatum/0020-browser-acceptance-demo/ledger/FINDINGS.md`.

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
- web comparison UI remains deferred unless the ledger proves a small safe slice;
- demo/deployment docs must be truthful about local Docker vs hosted demo state;
- update RFC/readme/operator report artifacts to match what actually lands.
