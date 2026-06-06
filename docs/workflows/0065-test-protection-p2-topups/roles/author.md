# Role: Author (Test-protection P2 — protection top-ups)

Implement the five P2 items from the remediation plan §5, one commit per
item, strictly inside the declared write scope. This batch is TEST-ONLY
plus the pyproject mypy removal.

Hard constraints:

- kayakgen/, scripts/, and the boundary tests are forbidden. If a new test
  exposes a product bug, record it in the draft artifact as a successor
  finding — do not fix product code here.
- The hydrostatics anchor must be an honest EXTERNAL check with the analytic
  derivation written down; if the parametrization cannot honestly approximate
  the analytic body, take the documented fallback (tighter property pins) and
  say so explicitly in the draft artifact.
- The deterministic cancel test owns the cancel contract; the racy variant is
  demoted to labeled smoke, not deleted.
- Exactly three registry micro-gap tests; the 0063 digest pin stays
  byte-identical.
- The reason-enum test derives its expected set from the module namespace.
- mypy: remove from [dev] extras; no config; CHANGELOG rationale.
- Final gate: .venv/bin/python -m pytest -q → 0 failed, exactly the 4
  documented OpenFOAM skips; ruff clean. Heartbeat around the ~9-minute run.
