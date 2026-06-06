# Operator Report — Workflow 0063: test-protection P1 durable-state hardening

date: 2026-06-06
run: run_2198d739c43270edeb3ee93f93160b97
branch: `striatum/0063-test-protection-p1-durable-state`
review verdict: **accept, no findings** (`striatum/0063-test-protection-p1-durable-state/review/REVIEW.md`)

## What landed (slice stack, one commit per slice)

| slice | commit | summary |
|---|---|---|
| P1-STORE-ATOMIC | `347f7064da8ca856f6dc09a27c658b61a0f32bca` | `FilesystemArtifactStore._put_bytes` writes store bytes through a dot-prefixed same-directory temp sibling + `os.replace` (the dot prefix keeps half-written bytes out of the `_store/<hash>.*` read glob — a deliberate, documented deviation from the plan's `with_suffix` literal, which would still match the glob). The `exists()` dedupe branch verifies byte length (rehash to confirm on mismatch) and atomically repairs a corrupt occupant instead of hard-linking truncated bytes into canonical run layouts. `kayakgen/io/json.py` `save_hull`/`save_evaluation` use the same atomic pattern with explicit utf-8; payload bytes stay byte-identical (`model_dump_json(indent=2)`). New tests: corruption-repair at the exact hash path, intact-occupant dedupe, non-ASCII utf-8 round-trip byte identity. |
| P1-SQLITE-VERSION | `83ad15bc92e15473f5b8d5eb9b07778cdd514538` | `SqliteIndex.SCHEMA_VERSION = 1` stamped via `PRAGMA user_version`. A DB stamped lower with tables present is rebuilt (drop every non-`sqlite_%` table + recreate + stamp) with a `UserWarning` — rebuild-not-migrate; it is a rebuildable read-model over run directories. Fresh DBs are stamped silently; current- and future-version DBs are never dropped, never downgraded. Tests cover both branches: stale `user_version=0` DB with the pre-RFC-0049 `runs` shape upserts without `OperationalError`; current-version DB reopens with rows intact under warnings-as-errors. |
| P1-SHA-PIN | `77be4e53e71941bb31773a35b910ada9c8bda089` | Test-only tamper-evidence tripwire: pins `fixture_canonical_sha256(make_stability_acceptance_triple().fixture)` to its literal digest `fca3840a7fa539ad849df5fb897b5d0bf45ecdee024899059959d685b04700e3`. A mismatch means a pydantic serialization change just invalidated every signed promotion packet's `fixture_sha256` binding — handled as an evaluator-version event (bump, re-review, re-sign, record the decision), never by updating the pin. `kayakgen/eval/stability/registry.py` has no branch diff (forbidden path; verified by the reviewer). The workflow's `CHANGELOG.md` entry rides in this commit (0062 convention: last slice carries it). |
| draft artifact | `d953d1c9721eb7bf1a2c651155f8100b5b627297` | Published `striatum/0063-test-protection-p1-durable-state/DRAFT.md`. |

(Workflow scaffold: `0a8783895ac74b2031d3b072e678c6222c681f03`.)

The apply job changed no production code and no test code: the review
(reviewer-codex-001) accepted with zero must-fix findings, so
`CHANGELOG.md` needed no further update (the workflow 0063 entry landed
with slice 3) and the apply commit adds only this report, the published
summary artifact, and the reviewer's `REVIEW.md` (committed for
provenance, matching prior workflow directories).

## Final full gate (apply job, run-branch worktree, 2026-06-06)

`.venv/bin/python -m pytest -q -ra` → exit 0:

```text
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1315 passed, 4 skipped, 1 warning in 528.97s (0:08:48)
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1. The single warning
is the slice-1 repair path firing inside the pre-existing
`tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`,
which stages stale bytes at a hash path — previously silently
hard-linked, now repaired, with the test's own assertions unchanged.

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (the invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65` are pre-existing and
untouched by this workflow).

R3 isolation evidence: the operator's
`~/.local/share/kayakgen/index.sqlite` was byte-identical across the
full-suite run (`mtime_ns=1780730948 size=90112` before and after).

## Audit ledger rows closed

From `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md`:

- **R5 (SERIOUS)** — `_put_bytes` non-atomic write + exists()-dedupe can
  no longer permanently poison a content address after a crash mid-write
  (BUG-041 family): writes are atomic, and the dedupe branch repairs a
  corrupt occupant (length screen, rehash confirm) instead of trusting it.
- **R6 (SERIOUS)** — `SqliteIndex` is schema-versioned; the next column
  addition rebuilds existing operator DBs (UserWarning, rebuild-not-migrate)
  instead of crashing every upsert.
- **R9 (MINOR)** — `io/json.py` `save_hull`/`save_evaluation` write
  explicit utf-8, atomically, with payload bytes unchanged.
- **§6 sha-pin** — `fixture_canonical_sha256` is pinned to a literal
  digest as the tamper-evidence boundary of the claims chain; a silent
  pydantic serialization change now fails loudly.

Documented residuals (reviewed, accepted as out of scope):

- Same-length corruption (bit flip) passes the cheap length screen by
  design — the plan chose `stat` over rehash-every-dedupe; the rehash
  confirm only runs on length mismatch.
- Repairing a corrupt store file gives the content address a fresh inode;
  canonical paths hard-linked by *earlier* puts keep the old inode until
  their own next put. A sweep-wide relink pass would be new scope.

## What remains (routed per the remediation plan §6)

- **Workflow C — contract decisions**: P1-FIT-KIND-DECISION and
  P1-COMPARE-GATE; RFC/DECISION_LOG rows first (docs, exempt from the
  runner), then one implementation slice each.
- **Workflow D — protection top-ups**: P2 test-only items, whenever idle
  (P2-CLI-NEGATIVES waits on the bug-hunt NaN family).

## Remaining operator action

**Merge the run branch to `main`**: the slice stack is left on
`striatum/0063-test-protection-p1-durable-state` per the apply packet;
merging is the operator's step after the run completes.
