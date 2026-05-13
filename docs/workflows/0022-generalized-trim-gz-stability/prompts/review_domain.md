Read `docs/workflows/0022-generalized-trim-gz-stability/SOURCES.md`,
especially RFC 0014, `docs/design/kayak_hull_design_constraints.md`,
`kayakgen/eval/hydrostatics.py`, `kayakgen/eval/stability.py`, and
`kayakgen/eval/contract.py`.

Produce `striatum/0022-generalized-trim-gz-stability/domain/REVIEW_DOMAIN.md`
with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- the `+x` stern / `-x` bow convention and trim sign convention;
- whether a forward LCG should produce bow-down trim and an aft LCG stern-down
  trim in the current coordinate system;
- load component mass, KG, LCG, and moment-balance semantics;
- what numerical tolerances and non-convergence warnings are domain-credible;
- whether any high-angle GZ work is safe now, or must remain unavailable with a
  named reason.
