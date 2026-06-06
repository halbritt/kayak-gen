# Role: Author (Test-protection P1 — durable-state hardening)

Implement P1-STORE-ATOMIC, P1-SQLITE-VERSION, and P1-SHA-PIN from the
2026-06-06 remediation plan, in that order, one commit per slice, strictly
inside the declared write scope.

Hard constraints:

- **Byte-stability**: the JSON payload bytes written by put_json /
  save_hull / save_evaluation must remain byte-identical
  (`model_dump_json(indent=2)`); only write mechanics (temp + os.replace,
  explicit utf-8) change. Existing design-hash and round-trip tests pass
  unchanged.
- **Repair, don't trust**: the store's exists()-dedupe branch must detect a
  corrupt file at the hash path (length check, rehash on mismatch) and
  repair it rather than hard-linking corrupt bytes into canonical paths.
- **Rebuild, don't migrate**: SqliteIndex uses PRAGMA user_version; on
  mismatch drop + recreate with a UserWarning. A current-version DB must
  NOT be dropped on reopen.
- **The SHA pin is test-only**: `kayakgen/eval/stability/registry.py` is a
  forbidden path. The pin's comment must say a failure is an
  evaluator-version event (re-sign packets), never a hash to update.
- Final gate: `.venv/bin/python -m pytest -q` → 0 failed, exactly the 4
  documented OpenFOAM skips; ruff clean. Heartbeat around the ~9-minute
  run. Commit messages follow repo convention with the co-author line.
