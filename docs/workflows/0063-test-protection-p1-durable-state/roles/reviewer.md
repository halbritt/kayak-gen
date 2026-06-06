# Role: Reviewer (Test-protection P1 — durable-state hardening)

Review the slice stack against plan items P1-STORE-ATOMIC,
P1-SQLITE-VERSION, P1-SHA-PIN and audit rows R5/R6/R9.

Non-negotiable checks:

- `git diff main...HEAD` touches no forbidden path — in particular
  `kayakgen/eval/stability/registry.py` must be untouched (the SHA pin is
  test-only).
- Atomicity is real: temp file + os.replace on the same filesystem; the
  corruption test stages corrupt bytes at the hash path and proves the next
  put repairs them. Probe the edge: corrupt content with the CORRECT byte
  length — caught, or explicitly documented as out of scope?
- JSON payload bytes unchanged: design-hash + round-trip tests untouched
  and green.
- SqliteIndex: rebuild fires ONLY on user_version mismatch; a
  current-version DB reopened is not dropped; the warning names the
  rebuild; `kayakgen runs list` works against a rebuilt DB.
- Run the FULL gate yourself (0 failed / 4 documented skips; ruff clean).
  Write the findings file BEFORE the long run; heartbeat around it.

Verdict semantics: `accept` / `accept_with_findings` for anything the apply
job can fix; `needs_revision` for scope violations or a red gate; NEVER a
terminal `reject` (it wedges the run).
