# Score One Goal Proposal

Read the problem brief and the goal proposal assigned to your job, then
publish a scorecard against the fixed dimensions:

- `preservation_verifiability` — can behavior preservation be demonstrated
  with existing tests, characterization tests at a stable seam, or
  mechanical checks? Score lowest when neither tests nor mechanical
  verification are possible.
- `blast_radius` — how many files, call sites, and contracts the change
  touches.
- `payoff` — how much easier the code becomes to understand, test, review,
  or change.
- `reversibility` — whether the change decomposes into slices that can be
  individually reverted without destructive git operations.
- `frozen_surface_risk` — how close the work comes to public APIs, CLI
  commands, wire formats, schema, migrations, or generated files.
- `sliceability` — whether the work decomposes into bounded slices with
  per-slice verification, including separable move-only and edit slices.

Score each dimension, justify each score in one or two sentences against
the current tree, and name the single biggest unverified assumption in the
proposal. Do not compare proposals; score only the one assigned to you.
Include the exact lowercase `author:` byline near the top of the artifact.
