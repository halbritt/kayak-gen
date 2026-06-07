# Sources - workflow 0067

1. `/tmp/HANDOFF_kayak-gen_0067-gate-altitude-verified-reads_2026-06-07.md`
   - operator handoff for this run. It identifies Slice A (in-suite skip pin)
   and Slice B (verified production artifact reads) as the top successor work.
2. `docs/workflows/0066-test-protection-reaudit-gaps/OPERATOR_REPORT.md`
   - authoritative ranked findings table. Use the pre-merge `/code-review`
   section; do not re-derive it.
3. `striatum/0066-test-protection-reaudit-gaps/review/REVIEW.md` - D050
   review context and the enforcement-honesty lens.
4. `docs/DECISION_LOG.md` row D050 - current SERVE-ONLY-VERIFIED read
   contract.
5. `docs/RELEASE_DISCIPLINE.md`, `scripts/fast-gate.sh`,
   `scripts/full-gate.sh`, `tests/conftest.py` - gate altitude and skip-pin
   implementation surface.
6. `kayakgen/services/artifact_store.py`, `kayakgen/search/compare.py`,
   `kayakgen/cli/runs_cli.py`, `kayakgen/eval/cfd/job_store.py` - artifact
   read and store hardening surface.

Deferred, do not touch: G7 (CLI NaN negatives) and G11 (external fixtures).
Audit/report files at repo root are evidence and remain read-only.
