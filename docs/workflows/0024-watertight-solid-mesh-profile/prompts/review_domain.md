Read `docs/workflows/0024-watertight-solid-mesh-profile/SOURCES.md`,
especially RFC 0004, RFC 0010, `kayakgen/model/geometry.py`,
`kayakgen/eval/mesh_diagnostics.py`, and `kayakgen/eval/mesh_package.py`.

Produce `striatum/0024-watertight-solid-mesh-profile/domain/REVIEW_DOMAIN.md`
with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- whether current hull/deck surfaces define a closed volume;
- end-cap and plumb-stem ambiguity from RFC 0004;
- deck/hull body semantics and whether a deck is required for a solid;
- normal orientation, waterline boundary policy, and manifold checks;
- whether any watertight geometry generation is safe now or must remain a
  blocked profile with explicit diagnostics.
