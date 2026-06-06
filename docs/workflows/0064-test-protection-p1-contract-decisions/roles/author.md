# Role: Author (Test-protection P1 — contract decisions D048/D049)

Implement DECISION_LOG rows D048 and D049 exactly as decided, one commit per
decision, strictly inside the declared write scope.

Hard constraints:

- **D048 is refusal, not removal**: the exploratory_frontier labeling,
  warnings, and provenance annotations that tests/test_compare.py pins today
  must survive behind --explicit-exploratory with their assertions intact.
  Without the flag, inadmissible objectives REFUSE with the existing
  RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY token. The gate function in
  kayakgen/search/pareto.py is forbidden — call it, never modify it.
- **Default compare behavior unchanged**: admissible/default objectives need
  no flag and produce byte-identical reports.
- **D049 is additive**: kind defaults to "analytical"; existing fit JSONs
  parse unchanged; tests/test_stability_fit_registry.py (incl. the 0063
  digest pin) is forbidden and must stay green untouched.
- **Real records over fakes**: the graduation tests must construct
  StabilityFitRecord via the conftest factory; at most one clearly-labeled
  SimpleNamespace shape-tolerance test may remain.
- Public-schema-change checklist applies (USER_GUIDE / ARCHITECTURE_MAP /
  CHANGELOG); close BUG-001 and BUG-026 in docs/bug-hunt/LEDGER.md citing
  D049/D048.
- Final gate: .venv/bin/python -m pytest -q → 0 failed, exactly the 4
  documented OpenFOAM skips; ruff clean. Heartbeat around the ~9-minute run.
