# Role: Author (workflow 0067)

Close the highest-value 0066 pre-merge successor findings without widening
the audit scope.

Hard constraints:

- Do not re-derive the 0066 ranked review table; use
  `docs/workflows/0066-test-protection-reaudit-gaps/OPERATOR_REPORT.md`.
- Slice A's pytest hook must be explicit-env only:
  `KAYAKGEN_ENFORCE_SKIP_PIN=1`. Partial pytest invocations must remain
  legitimate.
- Slice A's expected skip count must derive from the OpenFOAM opt-in knobs.
  Default gates expect the documented OpenFOAM opt-ins to skip; opt-in smoke
  runs expect them to pass.
- Slice B's read verification must not claim more than it can enforce. Move
  production readers to verified refs where hash-bearing records are present;
  record any remaining path-only legacy surface honestly.
- Store hardening must fail closed on corrupt bytes and remain repairable only
  from canonical bytes that rehash to the expected address.
- Audit/report files at repo root are evidence; never edit them.
- Gate with focused tests, ruff, and `scripts/full-gate.sh`. Verify the
  user-level kayakgen index DB remains empty/unchanged.
