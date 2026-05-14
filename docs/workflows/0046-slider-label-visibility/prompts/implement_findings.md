# Implementation Prompt

Implement only the accepted findings in
`striatum/0046-slider-label-visibility/ledger/FINDINGS.md`.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent desktop UI, web UI, tests, docs, and local
review tasks, but keep one agent responsible for final integration.

Constraints:

- Do not mutate Striatum state, commit, push, or edit `.striatum/`.
- Do not add `author:`, `byline:`, or `Co-Authored-By` metadata.
- Keep the fix narrow to slider/parameter-label visibility and focused tests.
- Do not introduce new backend capability, CFD, stability, or calibration
  claims.
- Update `CHANGELOG.md` if user-visible behavior changes.

Write `striatum/0046-slider-label-visibility/implementation/PATCH_SUMMARY.md`
with changed files, findings addressed, validation commands and results,
deferrals, and any exact operator follow-up wording.
