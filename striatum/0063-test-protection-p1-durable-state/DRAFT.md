# Draft — Workflow 0063: test-protection P1 durable-state hardening

author: author-claude-001
date: 2026-06-06
run: run_2198d739c43270edeb3ee93f93160b97
branch: striatum/0063-test-protection-p1-durable-state (worktree wt_d06f9e6140f38d4bf5bb69f7899dde9b)

Three P1 durable-state slices from
`KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md` §4
(audit rows R5, R6, R9 + §6), landed in order, one commit per slice.

## Slice 1 — P1-STORE-ATOMIC (`347f7064da8ca856f6dc09a27c658b61a0f32bca`)

```
 kayakgen/io/json.py                 | 26 +++++++++++++--
 kayakgen/services/artifact_store.py | 64 +++++++++++++++++++++++++++++++++---
 tests/test_artifact_store.py        | 65 +++++++++++++++++++++++++++++++++++++
 tests/test_hull_roundtrip.py        | 24 ++++++++++++++
 4 files changed, 172 insertions(+), 7 deletions(-)
```

- `_put_bytes` writes store bytes via `_atomic_write_bytes` (temp sibling +
  `os.replace`). The temp name is **dot-prefixed**
  (`.<hash>.<ext>.tmp-<pid>`), a deliberate deviation from the plan's
  literal `store_path.with_suffix(".tmp-<pid>")`: a `with_suffix` temp
  (`<hash>.tmp-<pid>`) still matches the `_store/<hash>.*` glob that
  `_resolve_artifact` serves reads from, so a crash between write and
  rename could surface a torn file under its content address — exactly the
  bug class being closed. The dot prefix keeps half-written bytes out of
  the glob namespace entirely.
- The `exists()` dedupe branch calls `_verify_or_repair_store_file`: byte
  length is the cheap screen; on mismatch the occupant is rehashed to
  confirm corruption before being atomically replaced (`UserWarning`
  "repairing with intact payload"). Intact occupants are untouched —
  normal dedupe stays cheap (one `stat`).
- The `_resolve_artifact` redrive write (same torn-write hazard, same
  module) uses the same helper. Mentioned for the reviewer: the objective
  named only `_put_bytes`; this is a one-line consistency application
  within the declared write scope.
- `kayakgen/io/json.py`: `save_hull`/`save_evaluation` write through
  `_atomic_write_text` (temp sibling + `os.replace`, explicit
  `encoding="utf-8"`); `load_hull` reads explicit utf-8 so the non-ASCII
  round-trip is locale-independent. Helpers are module-private duplicates
  by design — sharing one would couple `io` and `services` across the
  boundary the import tests patrol.
- **Byte-stability invariant held**: payload bytes remain
  `model_dump_json(indent=2)`; only write mechanics changed. The new
  round-trip test asserts disk bytes are byte-identical to the pydantic
  dump; all existing design-hash and round-trip tests pass unchanged.

**Corruption-repair evidence** (truncated bytes pre-staged at the exact
hash path; next put of the same content):

```
tests/test_artifact_store.py::test_corrupt_store_file_repaired_on_next_put PASSED
tests/test_artifact_store.py::test_intact_store_file_left_alone_on_dedupe PASSED
tests/test_hull_roundtrip.py::test_save_hull_round_trips_non_ascii_utf8 PASSED
```

The repair test asserts: the content address holds intact bytes again, the
canonical path received the intact bytes (hard-link inode equality on
non-Windows), and no temp sibling remains. The dedupe test asserts an
intact occupant is reused (same inode) with warnings escalated to errors.

Unplanned confirmation from the full gate: the repair path fired inside the
pre-existing `tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`,
which stages stale bytes at a hash path (occupant size 3262 != 913, hash
mismatch confirmed by rehash) — previously those stale bytes would have
been silently hard-linked; now they are repaired, and the test's
assertions still hold (it *wants* the rerun to ignore stale data).

## Slice 2 — P1-SQLITE-VERSION (`83ad15bc92e15473f5b8d5eb9b07778cdd514538`)

```
 kayakgen/services/artifact_store.py | 49 +++++++++++++++++++++++++-
 tests/test_artifact_store.py        | 70 +++++++++++++++++++++++++++++++++++++
 2 files changed, 118 insertions(+), 1 deletion(-)
```

- `SqliteIndex.SCHEMA_VERSION = 1`; `_conn` now goes through
  `_ensure_schema`, which reads `PRAGMA user_version` once per instance.
- Stamp lower than current **and tables present** → `UserWarning` naming
  the rebuild and the dropped tables, drop every non-`sqlite_%` table
  (enumerated from `sqlite_master`, which also catches renamed/legacy
  tables and skips the undroppable `sqlite_sequence`), recreate, stamp.
  Fresh empty DBs are stamped silently — no spurious warning on first use.
- Stamp current or future → idempotent `CREATE IF NOT EXISTS` only; never
  dropped, never downgraded (a future-version DB keeps its stamp).
- Rebuild-not-migrate per the plan: the index is a rebuildable read-model
  over run directories (`index_run_directory`); migration machinery is
  explicitly out of scope.

**Rebuild-vs-preserve evidence:**

```
tests/test_artifact_store.py::test_stale_schema_version_db_rebuilt_not_crashed PASSED
tests/test_artifact_store.py::test_current_schema_version_db_preserved_on_reopen PASSED
```

The rebuild test stages a `user_version=0` DB whose `runs` table is
missing the `out_dir` column (the pre-RFC-0049-growth shape), then
upserts: no `OperationalError`, rebuild warning emitted, stale phantom row
dropped, stamp now `SCHEMA_VERSION`, and `kayakgen runs list` exits 0
against the rebuilt DB. The preserve test reopens a current-version DB
with warnings escalated to errors and finds its rows intact — normal
reuse never loses data.

## Slice 3 — P1-SHA-PIN (`77be4e53e71941bb31773a35b910ada9c8bda089`)

```
 CHANGELOG.md                         | 18 ++++++++++++++++++
 tests/test_stability_fit_registry.py | 28 ++++++++++++++++++++++++++++
 2 files changed, 46 insertions(+)
```

Test-only, as required — `kayakgen/eval/stability/registry.py` (forbidden
path) untouched. The pinned digest:

```
fixture_canonical_sha256(make_stability_acceptance_triple().fixture)
  == fca3840a7fa539ad849df5fb897b5d0bf45ecdee024899059959d685b04700e3
```

(verified stable across separate interpreter invocations). The test
docstring spells out the failure semantics: a mismatch means a pydantic
serialization change just invalidated every signed promotion packet's
`fixture_sha256` binding and must be handled as an evaluator-version event
(bump, re-review, re-sign, record the decision) — never by updating the
pinned digest.

```
tests/test_stability_fit_registry.py::test_fixture_canonical_sha256_pinned_to_literal_digest PASSED
```

The CHANGELOG entry covering all three P1 slices rides in this commit
(0062 convention: last slice carries it).

## Gate

`.venv/bin/python -m pytest -q -ra` in the worktree (heartbeats before,
during, and after the 8m41s run):

```
1315 passed, 4 skipped, 1 warning in 521.57s (0:08:41)

SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips (two in
`test_cfd_run_stages.py`, two in `test_openfoam_v2512_smoke.py`). The one
warning is the slice-1 repair path firing on the staged-stale CFD test
described above.

`.venv/bin/python -m ruff check kayakgen tests` → `All checks passed!`

## Notes for review

- Known residual (out of scope, flagging for completeness): repairing a
  corrupt store file via `os.replace` gives the content address a fresh
  inode; canonical paths hard-linked to the corrupt occupant by *earlier*
  puts keep the old inode until their own next put re-links them. The
  audit acceptance (current put's canonical path receives intact bytes)
  is met; a sweep-wide relink pass would be new scope.
- Same-length corruption (bit flip) passes the cheap length screen by
  design — the plan chose `stat` over rehash-every-dedupe; the rehash
  confirm only runs on length mismatch.
