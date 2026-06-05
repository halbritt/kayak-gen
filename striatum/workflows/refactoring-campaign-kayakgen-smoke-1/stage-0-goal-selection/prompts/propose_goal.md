# Champion One Refactoring Goal

Read the problem brief and champion exactly one candidate goal as the
proposal artifact assigned to your job. Re-verify the brief's claims about
your candidate against the current tree; do not propagate stale evidence.

Include:

- The goal, stated as one named, behavior-preserving structural change.
- Files and modules in the blast radius: targets, call sites, tests,
  generated sources, docs, and public entrypoints.
- Which frozen surfaces from the brief the goal comes near, and why it
  does not cross them.
- How the work decomposes into bounded slices, each with a preservation
  claim and a verification command.
- Existing test coverage near the blast radius, and whether
  characterization tests would be needed before semantic movement.
- Expected payoff: what becomes easier to understand, test, review, or
  change.
- Known risks and what evidence would reduce them.

Do not read sibling proposal artifacts. This job is an independent
proposal lane by design. Include the exact lowercase `author:` byline near
the top of the artifact.
