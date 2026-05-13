Read `docs/workflows/0027-closed-volume-geometry-contract/SOURCES.md`,
especially proposed RFC 0016, RFC 0004, RFC 0010, and the current geometry and
mesh-package code.

Produce `striatum/0027-closed-volume-geometry-contract/domain_geometry/REVIEW_DOMAIN_GEOMETRY.md`
with:

- author line: `author: operator [self-declared: operator-domain-geometry-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- closure policy for bow, stern, deck join, sheerline, and plumb-stem end caps;
- whether the first body is hull-plus-deck, hull-only capped at sheerline, or
  another explicit accepted shape;
- normal orientation, signed volume, manifold edge counts, and tolerance
  handling;
- waterline semantics as metadata versus a cut boundary;
- why closed-volume candidates must stay separate from display STL surfaces and
  future solver-specific case directories.
