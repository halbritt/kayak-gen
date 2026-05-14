Read `docs/workflows/0047-ui-follow-up-cleanup/SOURCES.md`, drafted RFC 0035,
the four review artifacts, and the findings ledger.

Implement only the ledger-approved UI cleanup slice. Do not implement deferred
backend, solver, calibration, high-angle stability, watertight-readiness, or
desktop parity work.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent UI, accessibility, tests, docs/changelog, and
cleanup tasks, but keep one agent responsible for final integration.

Constraints:

- Do not mutate Striatum state, prepare runs, claim jobs, commit, push, or
  edit `.striatum/`.
- Do not add `author:`, `byline:`, `Co-Authored-By:`, or other attribution
  metadata unless Striatum supplies an exact expected author line in the
  packet.
- Keep `CHANGELOG.md` and user-facing docs factual and narrow.
- Add focused tests for every behavior change or cleanup that could regress.

Publish
`striatum/0047-ui-follow-up-cleanup/implementation/PATCH_SUMMARY.md` with
changed files, tests run, sub-agent usage, and any deferred findings.
