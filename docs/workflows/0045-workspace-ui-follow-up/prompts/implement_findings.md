# Implementation Prompt

Implement only the ledger-approved RFC 0034 safe slice.

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent UI, controller/read-model, tests, docs, and
browser-acceptance tasks, but keep one agent responsible for final integration.

Do not mutate Striatum state, commit, push, edit `.striatum/`, or falsify
bylines. Keep changes inside the declared write scope. Update `CHANGELOG.md`
for user-facing behavior, docs/status, or workflow landing changes.

Expected artifact:
`striatum/0045-workspace-ui-follow-up/implementation/PATCH_SUMMARY.md`

The patch summary must include:

- implemented scope
- findings resolved
- explicit deferrals
- validation commands and results
- sub-agent/parallel assistance used
- proposed changelog entry if applicable
