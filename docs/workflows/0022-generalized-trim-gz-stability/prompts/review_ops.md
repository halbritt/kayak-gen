Read `docs/workflows/0022-generalized-trim-gz-stability/SOURCES.md`,
especially `kayakgen/eval/contract.py`, `kayakgen/eval/stability.py`,
`kayakgen/cli/main.py`, `kayakgen/search/sweep.py`, and stability/CLI/sweep
tests.

Produce `striatum/0022-generalized-trim-gz-stability/ops/REVIEW_OPS.md`
with:

- author line: `author: operator [self-declared: operator-ops-review]`
- verdict intent
- findings `O-001`, `O-002`, ...
- required action for each finding

Focus on:

- pydantic model compatibility and `extra="forbid"` migration risk;
- deterministic tests for forward/aft trim and non-convergence;
- CLI JSON compatibility and snapshot-stable field names;
- sweep record compatibility and summaries;
- avoiding hidden performance costs or brittle solvers.
