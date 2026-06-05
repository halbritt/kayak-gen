# Author The Refactoring Plan

Read the stage-0 goal decision artifact
(`striatum/refactoring/kayakgen-smoke-1/00-goal/GOAL_DECISION.md`).
Execute the preflight below against the current tree, then publish the
refactoring plan as the claim the falsifiers will challenge. Do not edit
any source file in this job.

## Preflight, in order

1. Run `git status --short`. If dirty paths overlap the goal's blast
   radius, record the overlap as a stop condition in the plan instead of
   planning around it.
2. Discover and run the verification commands named in the goal decision.
   Record the baseline result. If the baseline is red, name each
   pre-existing failure; the per-slice bar becomes "no new failures". If a
   command appears flaky, rerun it once and name the flake.
3. Read the blast radius: target files, call sites, tests, generated
   sources, docs, config, and public entrypoints.
4. Build the frozen-surface inventory for this goal: exported signatures,
   CLI commands, env vars, RPC methods, HTTP routes, migrations,
   serialized payloads, generated files, event order, file formats, and
   user-facing docs the campaign must not change.
5. Detect generated files in the blast radius. Plan to change the
   generator, never the generated output.
6. Decide whether existing tests are sufficient. If coverage is missing
   but behavior is testable, the plan's first slices add characterization
   tests at the nearest stable seam, labeled as preserving current
   behavior rather than proving ideal behavior. If neither tests nor
   mechanical verification are possible, the plan must say so and stop
   the campaign at this gate.

## Plan contents

- Files read; current behavior; invariants; frozen surfaces;
  baseline result; verification commands; stop conditions.
- A step table: `id | change | files | preservation claim | verification |
  rollback unit | estimated size | max net-diff cap`. Move-only slices and
  edit slices are separate rows so reviewers can inspect behavioral risk
  without rename noise.
- Stop conditions, including at minimum: the refactor requires behavior
  change; a frozen surface blocks progress; a slice exceeds its declared
  cap; the chosen goal turns out to be wrong; the work crosses into
  features, bug fixes, schema changes, or dependency upgrades.

Follow the `work_plan` V1 front-matter schema (`scope_kind: initiative`);
the publisher refuses invalid front matter. Include the exact lowercase
`author:` byline near the top of the artifact. Do not treat falsifier
challenge completion as acceptance; the adjudicator ledger decides whether
the gate clears.
