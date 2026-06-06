# Role: Reviewer (Test-protection P2 — protection top-ups)

Review the five P2 items for assertion honesty above all: these are tests
about tests — a dishonest anchor or a vacuous derivation is worse than no
change.

Non-negotiable checks:

- Scope: git diff main...HEAD touches ONLY the three test files +
  pyproject.toml + CHANGELOG.md + the workflow artifact dir. Any kayakgen/
  or scripts/ edit → needs_revision.
- Recompute the hydrostatics analytic derivation yourself; confirm the test
  fails under a deliberate tolerance-exceeding perturbation (reason about
  it; do not edit product code to prove it).
- The deterministic cancel test runs unconditionally (no skip path); the
  racy variant is clearly labeled smoke.
- The three registry tests pin ANY-pass / hysteresis-branch / touching-range
  exactly; the 0063 digest pin is byte-identical.
- The reason-enum test would fail if a new REASON_X constant shipped without
  remediation copy.
- mypy removed from extras only; CHANGELOG notes it.
- Run the FULL gate yourself (0 failed / 4 documented skips; ruff clean);
  findings file BEFORE the long run; heartbeat around it.

Verdicts: accept / accept_with_findings for apply-fixable issues;
needs_revision for scope violations or a red gate; NEVER terminal reject.
