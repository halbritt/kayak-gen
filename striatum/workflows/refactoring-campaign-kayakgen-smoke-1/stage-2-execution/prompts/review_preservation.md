# Review Preservation Evidence

You are a fresh reviewer auditing a behavior-preserving refactoring
execution. Read the committed plan, the step ledger, and the executed
slices' commits. Do not trust the ledger's claims; replay them.

Check, with commands run against the executed tree:

- The full verification suite: no new failures beyond the baseline's
  named pre-existing failures.
- A sample of per-slice preservation claims, including every slice whose
  ledger evidence looks weakest: rerun the named verification and compare
  with the recorded result.
- Frozen surfaces from the committed plan: untouched. Check exported
  signatures, CLI output, serialized formats, and generated files the
  plan names.
- Commit discipline: one verified slice per commit, move-only and edit
  slices in separate commits, no slice over its declared net-diff cap,
  no commits touching paths outside the plan's blast radius.
- No behavior change hidden under "refactor": no new public surface, no
  bug fixes, no dependency changes, no unrelated formatting churn.

Render a single verdict: `accept`, `accept_with_findings`, or
`needs_revision` naming the specific slices to rework. An honest ledger
that stopped at a stop condition is not a defect; judge it on whether the
stop was correct and the evidence truthful. Include the exact lowercase
`author:` byline near the top of the artifact.
