Read `docs/workflows/0022-generalized-trim-gz-stability/SOURCES.md`,
especially RFC 0011, RFC 0014, `kayakgen/eval/contract.py`,
`kayakgen/eval/stability.py`, `kayakgen/cli/main.py`, and tests.

Produce `striatum/0022-generalized-trim-gz-stability/traceability/REVIEW_TRACEABILITY.md`
with:

- author line: `author: operator [self-declared: operator-traceability-review]`
- verdict intent
- findings `T-001`, `T-002`, ...
- required action for each finding

Focus on:

- RFC 0011 deferrals and RFC 0014 acceptance criteria;
- whether RFC 0014 should be accepted, amended, or partially landed;
- compatibility for existing compact `LoadCase` fields and current
  equilibrium-sinkage JSON;
- CLI and sweep/evaluation record surfaces that must carry trim fields;
- status/readme updates needed after implementation;
- which high-angle GZ criteria must remain deferred until volume semantics are
  accepted.
