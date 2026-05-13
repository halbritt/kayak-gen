author: operator [self-declared: operator-implementer]

# Patch summary - workflow 0026

## Files changed

- `README.md`: added a concise user-facing entry point.
- `docs/USER_GUIDE.md`: added install, quick-start, CLI command, desktop/web,
  mesh/CFD caveat, troubleshooting, and limitation guidance.
- `docs/PRD.md`: split delivered behavior from roadmap/deferrals and removed
  claims that watertight solids, calibrated resistance, high-angle GZ, full web
  parity, or real CFD execution are delivered today.
- `docs/rfcs/0016-closed-volume-geometry.md`: proposed closed-volume geometry
  contract.
- `docs/rfcs/0017-first-real-cfd-adapter.md`: proposed first real CFD adapter
  contract.
- `docs/rfcs/0018-web-cfd-job-routes.md`: proposed web CFD job routes.
- `docs/rfcs/0019-resistance-calibration-fixtures.md`: proposed resistance
  calibration fixture contract.
- `docs/rfcs/0020-high-angle-gz-secondary-stability.md`: proposed high-angle
  GZ and secondary stability contract.
- `docs/rfcs/README.md`: indexed RFCs 0016-0020 and linked the user guide.
- `docs/workflows/0018-deferred-backlog/QUEUE.md`: moved workflows 0019-0025
  into completed history and reordered remaining work from 0026 onward.
- `OPERATOR_REPORT.md` and
  `docs/workflows/0026-docs-roadmap-user-guide/OPERATOR_REPORT.md`: updated
  workflow state and verification notes.

## Findings addressed

- F-001: added `docs/USER_GUIDE.md`.
- F-002: corrected stale PRD delivery claims.
- F-003: reconciled root operator report state.
- F-004: replaced stale deferred queue wording.
- F-005: drafted proposed RFCs 0016-0020.
- F-006: updated RFC index/navigation and root README.
- F-007: kept resistance, CFD, mesh, and high-angle stability caveats explicit.

## Verification

- `.venv/bin/python -m pytest -q` -> 160 passed.
- `git diff --check` -> clean.
- `striatum --repo . doctor` -> clean.
- User-guide worker also smoke-tested `.venv/bin/kayakgen --help`,
  `.venv/bin/kayakgen cfd profiles`, and `init -> mesh-package -> cfd prepare`.
