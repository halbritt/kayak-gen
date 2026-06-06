# Draft Prompt — P1 durable-state slices

Read the packet objective, your role file, audit rows R5/R6/R9 + §6 in
`KAYAKGEN_TEST_COVERAGE_AUDIT_..._2026-06-06.md`, plan items
P1-STORE-ATOMIC / P1-SQLITE-VERSION / P1-SHA-PIN in the remediation plan,
and `SOURCES.md`. Implement in order, one commit per slice:

1. **P1-STORE-ATOMIC** — `kayakgen/services/artifact_store.py`
   `_put_bytes`: temp sibling + `os.replace`; dedupe branch verifies length
   and rehashes on mismatch, repairing corrupt store files.
   `kayakgen/io/json.py`: explicit `encoding="utf-8"` + the same atomic
   pattern. Payload bytes byte-identical. New tests: pre-staged truncated
   file at the hash path is repaired by the next put (canonical path gets
   intact bytes); save_hull/load_hull round-trips non-ASCII metadata.
2. **P1-SQLITE-VERSION** — `SqliteIndex`: PRAGMA user_version constant;
   mismatch → drop tables + recreate + UserWarning; tests for (a)
   version-0 DB with missing column → rebuild, not OperationalError, (b)
   current-version DB reopened → data preserved.
3. **P1-SHA-PIN** — one test in `tests/test_stability_fit_registry.py`
   pinning `fixture_canonical_sha256(make_stability_acceptance_triple().fixture)`
   to its literal hex digest with the evaluator-version-event comment.
   `kayakgen/eval/stability/registry.py` is forbidden — test-only.

**Slice gate:** `.venv/bin/python -m pytest -q` → 0 failed, 4 documented
skips; ruff clean. Heartbeat before/after the full run.

Publish `striatum/0063-test-protection-p1-durable-state/DRAFT.md`: slice
shas + diffstat, corruption-repair evidence, rebuild-vs-preserve evidence,
the pinned digest, the full-gate tail. Use the packet's byline.
