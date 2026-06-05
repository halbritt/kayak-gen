# Survey Candidate Refactoring Goals

Read the target repository and publish the problem brief at the expected
artifact path. You are scoping a behavior-preserving refactoring campaign:
a refactor changes code shape — boundaries, ownership, names, duplication,
dependency direction, test seams, or module layout — and does not change
observable behavior.

Include in the brief:

- A survey of candidate refactoring goals, each one concrete and bounded:
  splitting one oversized module, collapsing one unnecessary abstraction,
  extracting one test seam, moving one responsibility to a clearer owner,
  renaming one concept across a bounded surface, or deduplicating one
  cluster toward an existing abstraction. One sentence of rationale per
  candidate. Reject "refactor this repo" as too broad; do not list it.
- The repository's verification commands, inferred from Makefiles, package
  manifests, CI config, and test directories.
- A first-pass frozen-surface inventory: public APIs, CLI commands, wire
  formats, database schema, migrations, file formats, event ordering,
  generated files, and compatibility aliases that no candidate may change.
- The fixed scorecard dimensions every goal will be scored on:
  preservation_verifiability, blast_radius, payoff, reversibility,
  frozen_surface_risk, sliceability.

Out of scope for every candidate: features, bug fixes, schema changes,
dependency upgrades, broad rewrites, speculative abstractions, and cleanup
findings small enough for a hygiene pass.

Keep the brief factual. Do not rank or choose a goal here. Include the
exact lowercase `author:` byline near the top of the artifact.
