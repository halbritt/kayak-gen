# Execute The Plan Slices

Read the committed plan
(`striatum/refactoring/kayakgen-smoke-1/01-plan/COMMITTED_PLAN.md`).
You are executing one behavior-preserving refactoring campaign in an
isolated worktree. The plan is the contract: do not add slices, widen
scope, or "improve" code the step table does not name.

Before the first slice, reproduce the plan's recorded baseline with its
verification commands. If the baseline does not reproduce, stop and record
the discrepancy in the step ledger instead of proceeding.

Then execute one bounded slice at a time:

1. Apply the smallest change that satisfies the slice.
2. Run the slice's named verification for its preservation claim.
3. Record the slice's evidence in the step ledger: slice id, what changed,
   verification command, observed result, and the rollback unit.
4. Continue only if the preservation claim is supported. A red result that
   is not a named pre-existing failure stops the loop; record it and
   complete the job with the ledger honest about where it stopped.
5. Commit the verified slice before starting the next one. Move-only
   slices and edit slices are separate commits with subjects naming the
   structural change.

A slice that wants to exceed its declared net-diff cap is a stop
condition, not a stretch: record it and stop. Behavior change discovered
mid-slice is a stop condition. Never use destructive git operations as
rollback; revert only the failed slice commit.

After the last slice, run the repository's full verification suite and
record the result in the ledger.

The step ledger follows the `support_ledger` V1 front-matter schema
(`audited_artifact` names the committed plan); the publisher refuses
invalid front matter. Include the exact lowercase `author:` byline near
the top. One preservation claim per slice, each with its observed
evidence — the reviewer replays these.
