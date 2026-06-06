# Sources — workflow 0062 (test-protection P0 gate recovery)

Provenance for this workflow's scope. Read in this order:

1. `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md` — the audit
   that produced the findings. Ledger rows closed by this workflow:
   - **R0** (SERIOUS, code half): `kayakgen/services/evaluation.py:33`
     imports `kayakgen.ui.hydrostatics_metadata`;
     `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
     red on `main` since commit `313dfdd` (2026-05-25). Workflow 0061 carried
     it as "known pre-existing NB-2 failure (out of scope)".
   - **R3** (SERIOUS): sweep/search runner tests write the operator's real
     `~/.local/share/kayakgen/index.sqlite` (at audit time 129/129 runs rows
     were pytest tmp-path phantoms; operator purged them 2026-06-06 — the
     conftest isolation prevents recurrence).
   - **R4** (SERIOUS, gate half): RELEASE_DISCIPLINE's "green or skipped"
     wording + importorskip lattice lets minimal envs skip the desktop
     forbidden-copy gate invisibly; pin expected skips = 4.
2. `KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md`
   §3 — the three P0 items this workflow implements, with acceptance
   criteria (P0-BOUNDARY-FIX, P0-INDEX-ISOLATION, P0-GATE-ENFORCE) and §8
   answered questions (Q3 = "fast": fast-subset pre-push hook; full suite at
   slice gates).
3. `docs/RELEASE_DISCIPLINE.md` — the gate this workflow repairs and
   re-documents.
4. `docs/bug-hunt/LEDGER.md` — adjacent open findings deliberately NOT in
   scope here (BUG-001/D049 and BUG-026/D048 are workflow C; the durable-
   state batch is workflow B; see the plan's §6 routing).

Out of scope for 0062: any change to claim surfaces, the stability registry,
artifact-store write paths (P1-STORE-ATOMIC), sqlite schema versioning
(P1-SQLITE-VERSION), and the D048/D049 implementations.
