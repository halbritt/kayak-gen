Read `docs/workflows/0019-legacy-rfc-partial-closure/SOURCES.md`, especially RFC
0004, RFC 0006, `docs/design/kayak_hull_design_constraints.md`,
`kayakgen/model/geometry.py`, `kayakgen/model/classes.py`, and the UI code.

Produce `striatum/0019-legacy-rfc-partial-closure/domain/REVIEW_DOMAIN.md` with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- stern-positive coordinate conventions and bow-on-left display expectations;
- whether current `bow_rake` behavior satisfies "plumb enough" without claiming
  exact watertight end caps;
- whether class presets and ranges match the design constraints document;
- whether advisory warnings use defensible design-space boundaries;
- whether any domain gaps should stay deferred to future RFCs.
