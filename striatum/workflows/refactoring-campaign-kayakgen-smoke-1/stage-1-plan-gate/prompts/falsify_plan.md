# Falsify The Refactoring Plan

Read the published refactoring plan and write the strongest falsifying
challenge you can justify along the posture named in your job objective.
Every objection must be load-bearing: name the slice or claim it attacks
and the concrete evidence in the current tree that supports the objection.

Productive attack lines:

- A preservation claim whose named verification cannot actually
  distinguish old behavior from new (the test never exercises the moved
  code; the check is tautological).
- A baseline claim that does not reproduce: rerun the named verification
  command and compare.
- A frozen surface missing from the inventory that the step table's files
  would touch — exported signatures, CLI output, serialized payloads,
  generated files, event ordering.
- A slice whose rollback unit is not actually revertible in isolation
  (later slices depend on it in a way the plan does not declare).
- A slice that hides behavior change under "refactor": a feature, bug
  fix, schema change, or dependency upgrade.
- Move-only and edit work mixed in a single slice, defeating reviewable
  diffs.
- A net-diff cap that the named files make implausible.

Include the strongest rebuttal the plan holder could give to each
objection, and say whether it survives. An objection you can already
rebut is not load-bearing; cut it. Include the exact lowercase `author:`
byline near the top of the artifact.
