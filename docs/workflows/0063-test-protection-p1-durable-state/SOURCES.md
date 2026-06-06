# Sources — workflow 0063 (test-protection P1 durable-state hardening)

1. `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md` — ledger rows
   closed here:
   - **R5** (SERIOUS): `FilesystemArtifactStore._put_bytes` non-atomic write +
     exists()-dedupe permanently poisons a content address after a crash
     mid-write (BUG-041 family).
   - **R6** (SERIOUS): `SqliteIndex` has no schema versioning; the next column
     addition crashes every existing operator DB at upsert (recoverable —
     rebuildable read-model — hence rebuild-not-migrate).
   - **R9** (MINOR): `io/json.py` save_hull/save_evaluation lack explicit
     utf-8 + atomic writes.
   - **§6**: `fixture_canonical_sha256` IS the tamper-evidence boundary of the
     claims chain; a pydantic serialization change would silently invalidate
     every signed packet — one literal-digest pin catches it.
2. `KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md`
   §4 — items P1-STORE-ATOMIC, P1-SQLITE-VERSION, P1-SHA-PIN (acceptance
   criteria per item).
3. Workflow 0062 (landed 2026-06-06) — the P0 predecessor; its conftest
   isolation means these new tests cannot touch the user-level index DB.

Out of scope: D048/D049 implementations (workflow C), compare.py, stability
registry code changes (the SHA pin is test-only), P2 items (workflow D).
