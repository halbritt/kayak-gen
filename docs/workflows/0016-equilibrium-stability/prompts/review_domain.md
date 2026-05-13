Read `docs/workflows/0016-equilibrium-stability/SOURCES.md`, especially RFC
0011, `docs/design/kayak_hull_design_constraints.md`,
`kayakgen/eval/hydrostatics.py`, and `kayakgen/eval/stability.py`.

Produce `striatum/0016-equilibrium-stability/domain/REVIEW_DOMAIN.md` with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- safe equilibrium solving with the current hull/load-case model;
- whether trim is fully specified or needs explicit warnings/deferral;
- convergence tolerance semantics and failure reporting;
- KG reference normalization under changed draft;
- how the Nick Schade stability explainer should remain non-normative context.
