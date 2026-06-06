# Role: Reviewer (Test-protection P1 — contract decisions D048/D049)

Review the two slices against DECISION_LOG D048/D049, audit rows R2/R1, and
the claims discipline.

Non-negotiable checks:

- Forbidden paths untouched (git diff main...HEAD --stat): especially
  kayakgen/search/pareto.py (the gate is called, not changed) and
  tests/test_stability_fit_registry.py (the 0063 digest pin).
- D048: refusal fires without opt-in (token pinned in a test); ALL prior
  exploratory labeling/warning assertions preserved behind the opt-in;
  default-objective compare unchanged; --explicit-exploratory documented.
- D049: kind is additive with default; graduation tests use REAL records
  (conftest factory) and cover the five cases (analytical-only, both-kinds
  covering, non-covering, rejected, opt-out); BUG-001/BUG-026 ledger rows
  closed with citations.
- No new claim/readiness/accepted_uses literal beyond the kind discriminator;
  no forbidden-claim copy introduced anywhere.
- Run the FULL gate yourself (0 failed / exactly 4 documented skips; ruff
  clean); findings file written BEFORE the long run; heartbeat around it.

Verdicts: accept / accept_with_findings for apply-fixable issues;
needs_revision for scope violations or a red gate; NEVER terminal reject
(it wedges the run).
