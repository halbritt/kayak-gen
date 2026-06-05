# Adjudicate The Plan Gate

Read only the dialogue trajectory for this run: the refactoring plan and
the falsifier challenges. Publish the collaboration ledger verdict.

For each falsifier objection, rule it:

- `binding` — load-bearing and unrebutted; it becomes a binding constraint
  the committed plan must discharge (amend a slice, add a frozen surface,
  add a characterization-test slice, tighten a cap, or add a stop
  condition).
- `rebutted` — the plan or the falsifier's own rebuttal answers it.
- `out_of_scope` — it asks the campaign to do something other than the
  named goal.

Then render the gate verdict:

- Clear the gate when every binding constraint is dischargeable by
  amending the plan without changing the goal.
- Render `needs_revision` when the dialogue lacks substance — falsifier
  objections are not load-bearing or rebuttals were never engaged — so
  the challenge round repeats once.
- Refuse the gate (do not clear; recommend the operator stop the
  campaign) when a binding constraint cannot be discharged without
  behavior change, an undischargeable frozen-surface conflict, or a goal
  change. Plan rework beyond one fresh stage-1 run is a campaign stop,
  not a third revision.

Follow the `collaboration_ledger` V1 front-matter schema; the publisher
refuses invalid front matter. Include the exact lowercase `author:` byline
near the top of the artifact.
