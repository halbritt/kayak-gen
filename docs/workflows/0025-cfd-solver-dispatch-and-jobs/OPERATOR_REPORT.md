# Operator report - workflow 0025

Updated: 2026-05-13

## Current state

- Workflow 0024 accepted and was fast-forwarded to `main` at `91de322`.
- Queue item 0025 is `0025-cfd-solver-dispatch-and-jobs`: introduce local CFD
  job specs, run records, solver profiles, unavailable/mock adapter behavior,
  and CLI status surfaces before any real solver integration.
- Current `main` is clean and `striatum --repo . doctor` is clean.
- Workflow scaffold validated:
  `striatum --repo . workflow validate
  docs/workflows/0025-cfd-solver-dispatch-and-jobs/workflow.json` -> valid.
- `git diff --check` -> clean.
- Scaffold committed as `7039878` and pushed to `origin/main`.
- Prepared Striatum run `run_ac6771c05d58422da72797fa47edf967`.
- Confirmed branch `striatum/0025-cfd-solver-dispatch-and-jobs` and started
  the run.
- Registered, claimed, and acked review sessions:
  - `review_traceability` as `sess_aca015c75c0449d589065cd9e70ee60c`;
  - `review_domain` as `sess_125abf9811c249b4892d19fb36ea1c75`;
  - `review_ops` as `sess_eac7f8cdc9d24f8fb72c3af8373e50db`.
- Submitted three `accept_with_findings` review artifacts:
  - traceability `art_40461f93bb8a4cf3a04fe94471a048b4`;
  - domain `art_ee4f71da2bb24dd0931e76dd6f5dc2a5`;
  - ops `art_1a7f17bbb7824ff9a94602e094732fee`.
- Review consensus: implement deterministic local job/run records, mesh
  readiness gating, CLI prepare/status/run, unavailable solver state, and a
  failing mock local-command state. Do not integrate a real solver, emit fake
  success, or make calibrated CFD claims.
- Claimed and acked `findings_ledger` as
  `sess_310961c0c9c142e3ab3bc1b27205cece`.
- Wrote findings ledger at
  `striatum/0025-cfd-solver-dispatch-and-jobs/ledger/FINDINGS.md`.
- Ledger gate result: proceed with local dispatch contracts, profile/readiness
  gating, raw/unvalidated status text, unavailable state, and mock failed
  command handling. Real solver adapters, normalized physical outputs, web job
  routes, and watertight geometry remain deferred.
- Published ledger as `art_6f5c7d26bf5e4df98996d7bb37936282` and completed
  `findings_ledger`.
- Claimed and acked `implement_findings` as
  `sess_253976cf21164e3fbd921063575922cf`.
- Implementation-doc status update drafted for RFC 0015 and the RFC index:
  the workflow is recorded as partial local-dispatch only, with real solver
  adapters, normalized outputs, web job routes, watertight geometry, and
  calibrated/validated CFD claims deferred. The RFC text includes the local CLI
  prepare/status/run/profiles surfaces.
- Implementation completed:
  - converted the reserved `kayakgen.eval.cfd` module into a package while
    preserving `evaluate_cfd` and `CfdNotImplementedError`;
  - added local CFD job/run/profile models and deterministic local job
    directories;
  - added mesh manifest profile/readiness gating during `cfd prepare`;
  - added unavailable solver state and mock failed-command state;
  - added `kayakgen cfd prepare/status/run/profiles`;
  - added focused core and CLI tests.
- Refreshed Striatum Claude/Codex skill bundles and Codex plugin bundle after
  `striatum --repo . doctor` reported bundle drift from runtime `1.33.0`.
- Verification so far:
  - `.venv/bin/python -m pytest tests/test_cfd_jobs.py tests/test_cli.py -q`
    -> 21 passed.
  - `.venv/bin/python -m pytest -q` -> 160 passed.
  - `git diff --check` -> clean.
  - `striatum --repo . doctor` -> clean.
  - `.venv/bin/ruff --version` -> unavailable; `.venv/bin/ruff` is missing.
- Wrote patch summary at
  `striatum/0025-cfd-solver-dispatch-and-jobs/implementation/PATCH_SUMMARY.md`.
- Published implementation patch summary
  `art_1cb4d53b1459438a92e77be868636e93` and completed
  `implement_findings`.
- Claimed and acked `final_review` as
  `sess_2c61851082064b52b08f2c111d8cb464`.
- Wrote final review at
  `striatum/0025-cfd-solver-dispatch-and-jobs/final/FINAL_REVIEW.md` with
  verdict `accept`.
- Published final review as `art_1090063be141486aa89dca66630b1424` with
  verdict `accept`.
- Striatum run `run_ac6771c05d58422da72797fa47edf967` is complete.

## Findings recorded

- Review findings are recorded in:
  - `striatum/0025-cfd-solver-dispatch-and-jobs/traceability/REVIEW_TRACEABILITY.md`;
  - `striatum/0025-cfd-solver-dispatch-and-jobs/domain/REVIEW_DOMAIN.md`;
  - `striatum/0025-cfd-solver-dispatch-and-jobs/ops/REVIEW_OPS.md`.
- Deduplicated implementation findings are recorded in
  `striatum/0025-cfd-solver-dispatch-and-jobs/ledger/FINDINGS.md`.

## Next action

- Commit, push, and fast-forward `main`.
