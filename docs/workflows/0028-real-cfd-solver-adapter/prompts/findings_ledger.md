Read the three review artifacts for this workflow and consolidate them into
`striatum/0028-real-cfd-solver-adapter/ledger/FINDINGS.md`.

Use this format:

- author line: `author: operator [self-declared: operator-ledger]`
- run id and job name
- gate result
- stats
- deduplicated findings `F-001`, `F-002`, ...
- implementation guidance with safe-now and do-not-implement lists

Preserve these constraints:

- require RFC 0017 to be accepted or amended before implementation;
- require workflow 0027 if the selected solver requires watertight solid input;
- name exactly one first real adapter profile for the implementation slice;
- preserve existing RFC 0015 job/run/profile contracts;
- require missing solver dependencies to produce truthful `unavailable` states;
- do not normalize raw outputs into calibrated physical claims unless a
  separate validation/calibration RFC has landed.
