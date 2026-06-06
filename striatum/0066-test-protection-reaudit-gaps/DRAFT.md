# Draft — Workflow 0066: re-audit gap remediation (G1-G6, G8-G10)

author: author-claude-001
date: 2026-06-06
run: run_d7e3d217fe8bba2e1a77b3c32fca815d
branch: striatum/0066-test-protection-reaudit-gaps (worktree wt_8ea907882a78c4b8c97981f2dee144b2)

Nine gaps from the 2026-06-06 post-remediation re-audit, closed in
packet order, one commit per item, in three slices (gate / store /
tests), plus one forecast follow-up commit for the re-measured gate
header numbers and the CHANGELOG. G7 (CLI NaN negatives) was not
touched — deferred by workflow 0065 SUMMARY decision; G11 stays
deferred (D006/D007). The audit and report files at repo root are
untouched evidence.

The two SERIOUS rows are mechanism changes; everything else is
test-only. `kayakgen/eval/` and `kayakgen/cli/` were never edited.

## Slice A — gate

### Item 1 — G1-SKIP-PIN (`63b0fcd94cabc6209839f4fee8e1318d22afcf26`)

```
 docs/RELEASE_DISCIPLINE.md | 36 ++++++++++++++++++----------
 scripts/fast-gate.sh       | 35 +++++++++++++++++++++++++--
 scripts/full-gate.sh       | 59 ++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 116 insertions(+), 14 deletions(-)
```

The pin that commit `fbfdf9e` and the release doc claimed but never
implemented. Both gates now stream pytest through `tee` into a mktemp
file (pipefail keeps red runs failing at the pipeline) and refuse any
summary whose skip count != `EXPECTED_SKIPS=4`, including 0. New
`scripts/full-gate.sh` = ruff + full `pytest -q` + the identical pin;
`docs/RELEASE_DISCIPLINE.md` cites it as the mechanical form of the
pre-merge requirements and the striatum slice gate. Both headers
document the pin assumes the OpenFOAM knobs are UNSET.

**Demonstrated to fail on a wrong count** (role hard constraint),
end-to-end via a `KAYAKGEN_PY` stub interpreter: green pytest emitting
"8 skipped" → exit 1; "no skipped token" (0) → exit 1; "4 skipped" →
exit 0. Same checks repeated against `fast-gate.sh` (3→1, 4→0).

### Item 2 — G4-GATE-SELFCHECK (`e6d714ffebbbc534cf6957d7af65ea065f181691`)

```
 tests/test_fast_gate_manifest.py | 84 ++++++++++++++++++++++++++++++++++++++++
 1 file changed, 84 insertions(+)
```

Three pins: every `--ignore` path in `fast-gate.sh` exists in the repo;
every `--deselect` nodeid still collects (`pytest --collect-only` exit
0 + nodeid in output); both gate scripts contain `EXPECTED_SKIPS=4`
AND the `-ne "$EXPECTED_SKIPS"` comparison — so G1's enforcement cannot
regress to claimed-but-absent. The header-numbers refresh was
deliberately deferred to the follow-up commit (`b0cc086`) so the
recorded numbers are re-measured after this workflow's own 23 tests
landed, not projected.

## Slice B — store

### Item 3 — G2-READ-VERIFY (`3bf00607c64ad82579454d0bffa4ae99d927380f`)

```
 docs/DECISION_LOG.md                |   1 +
 kayakgen/services/artifact_store.py |  97 ++++++++++++++++++++++++++++----
 tests/test_artifact_store.py        | 108 ++++++++++++++++++++++++++++++++++++
 3 files changed, 196 insertions(+), 10 deletions(-)
```

**Contract decision (recorded as DECISION_LOG row `D050`):**
SERVE-ONLY-VERIFIED. Every read path (`get_json`/`get_file` via
`_resolve_artifact`) rehashes before serving. On mismatch: repair from
the canonical path only when its bytes rehash to `ref.artifact_hash`
(atomic replace, mirroring the write-side repair; note a hard-linked
canonical shares the corrupt inode, so the rescue fires only for
independent copies); otherwise raise structured
`ArtifactIntegrityError` (carries `path`, `expected_hash`,
`actual_hash`). The re-derive branch's warn-and-serve on mismatch is
escalated to the same raise; the missing-store warning stays for the
intact case. Perf: occasional-read JSON/CSV/STL — rehash-on-read is
acceptable; D050 records the revisit condition (read volume growth).

Closing tests mirror the R5 house style: corrupt store → raises (no
canonical) / repairs (independent intact canonical); both copies
corrupt → raises; **equal-length bit-rot** (one bit flipped, same byte
count — the §6 sibling the write-side length screen misses) → caught
by read rehash, pinned through `get_file`.

### Item 4 — G6-STORE-ERROR-BRANCHES (`d407aa6231656526a5015b2569f5e80a5122578c`)

```
 tests/test_artifact_store.py | 91 ++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 91 insertions(+)
```

Stat-failure fallback (:719): OSError forces rehash-to-confirm; intact
occupant left alone, zero warnings. Read-failure fallback (:726-727):
unconfirmable occupant → warn + atomic repair. Both use monkeypatched
`Path.stat`/`Path.read_bytes` scoped to the target path (not
chmod 000) — deterministic and root-safe, per the packet. Plus the
re-derive mismatch path as redefined by item 3: missing store entry +
drifted canonical → raise, and **no mirror re-created under either
hash** (the old code wrote the mirror under the drifted hash).

### Item 5 — G8-NEWER-STAMP (`156df831aae8ef876751c02834a579cc7488c7b4`)

```
 tests/test_artifact_store.py | 35 +++++++++++++++++++++++++++++++++
 1 file changed, 35 insertions(+)
```

`PRAGMA user_version = SCHEMA_VERSION + 1` on a DB with rows, reopened
by a fresh `SqliteIndex`: rows survive, no rebuild warning
(`simplefilter("error")`), stamp not downgraded.

### Item 6 — G9-TOCTOU-PIN (`5430a6c19a38f68be0864100386395153da8dd17`)

```
 tests/test_artifact_store.py | 58 ++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 58 insertions(+)
```

A competing intact write of the same content is injected exactly in
the window (patched `exists()` plants the competitor's file and still
reports False); the address ends intact with the correct hash, no torn
temps, clean verified read. The test docstring states what it does NOT
prove: true parallel interleaving of partial writes — it pins the worst
ordering the window permits.

## Slice C — tests (test-only; kayakgen/eval and kayakgen/cli untouched)

### Item 7 — G3-CLI-EXPLORATORY (`85dbb0365d19a74f64118f6a9085e1cb1cc7ed3a`)

```
 tests/test_cli.py | 75 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 75 insertions(+)
```

CliRunner pair for `kayakgen compare`, staging mirrored from the
function-level fixture in `tests/test_compare.py`: `Rt_N_last:min`
without `--explicit-exploratory` → exit 1 +
`RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY` in stderr + no report
written; with the flag → exit 0 + `report_kind ==
"exploratory_frontier"` in the written report.

### Item 8 — G5-FIT-THRESHOLD-PIN (`c9e1a2cd6e55acc4751ec0549e9eb87e33890e06`)

```
 tests/test_calibration_campaigns.py | 56 +++++++++++++++++++++++++++++++++++
 1 file changed, 56 insertions(+)
```

Both directions of MAPE and R2 pinned via the structured reason tokens
`fit_above_mape_threshold` / `fit_below_r2_threshold`. **G5 pin
rationale (decision made, recorded):** the fail-closed default is
INTENDED — the D006 promotion gate defaults `acceptance_threshold_pct`
to 5.0 and forwards it regardless of `fit_metric`, so an R2 record can
never pass under the default (R2 ≤ 1.0 < 5.0), even a perfect fit.
Claims discipline holds; promoting an R2 fit requires an explicit
per-fixture `acceptance_threshold_pct`. Pinned exactly as that quirk
(`test_r2_record_under_default_threshold_refuses_every_fit`), with the
audit-G5 citation in the test docstring. `campaigns.py` unchanged.

**Open question (operator decision, future):** should
`evaluate_fit_against_threshold` / the promotion gate grow a
per-metric default (e.g. R2 minimum 0.9) instead of one shared
`threshold_pct`? The first real R2 fit will be rejected confusingly
until either a per-fixture threshold is set or this is decided.

### Item 9 — G10-CSV-REFUSALS (`8922a4e3116d8366e39440135d6eee458025f20e`)

```
 tests/test_calibration_campaigns.py | 83 +++++++++++++++++++++++++++++++++++++
 1 file changed, 83 insertions(+)
```

Missing required column (`sink_mm`) → ValueError naming it;
unrecognised extra column (`wave_height_m`) → ValueError naming it;
`_coerce_bool` garbage (`"maybe"`) → cannot-coerce ValueError; and the
`IncliningTestCampaign._rows_share_source_id` mismatch validator,
mirroring the tested tank-side twin.

## Follow-up commit — measured numbers + CHANGELOG (`b0cc08636239661655e2ddbaa95221a34d6729dc`)

```
 CHANGELOG.md               | 23 +++++++++++++++++++++++
 docs/RELEASE_DISCIPLINE.md |  5 +++--
 scripts/fast-gate.sh       | 13 ++++++++-----
 3 files changed, 34 insertions(+), 7 deletions(-)
```

Refreshed gate-header numbers (audit G4 called the old ones stale —
said 1309 full / 1052 fast; pre-workflow reality was already 1324):

- **full suite: 1347 passed + 4 skipped in 10:49** (649.29s)
- **fast subset: 1087 passed / 4 skipped / 2 deselected, pytest
  220.6s, 3m42s wall**

Both re-measured 2026-06-06 in this striatum per-job worktree with
`KAYAKGEN_PY` → the primary venv, after this workflow's 23 new tests.

## Slice gate (after item 9, via the new scripts/full-gate.sh — own dogfood)

```
[full-gate] ruff check kayakgen tests
[full-gate] pytest full suite (this is the release gate)
...
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1347 passed, 4 skipped, 1 warning in 649.29s (0:10:49)
[full-gate] OK (4 skipped == expected 4)
full-gate exit=0
```

- 0 failed; exactly the 4 documented OpenFOAM opt-in skips (2×
  `test_cfd_run_stages`, 2× `test_openfoam_v2512_smoke`), enforced by
  the new pin, which passed on its own first production run.
- ruff clean (`ruff check kayakgen tests` inside the gate; also run
  per-commit).
- The 1 warning is the PRE-EXISTING write-side repair warning
  (`repairing with intact payload`) surfacing from
  `test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`
  — not introduced here (this workflow's read-side warning says
  "repairing from canonical").
- User-level `~/.local/share/kayakgen/index.sqlite` byte-identical
  before/after the suite: `e0e9a367228389d4bc83ab2abaa39124` both
  sides.

## Cumulative diffstat (10 commits on top of `341d126`)

```
 CHANGELOG.md                        |  23 +++
 docs/DECISION_LOG.md                |   1 +
 docs/RELEASE_DISCIPLINE.md          |  37 +++--
 kayakgen/services/artifact_store.py |  97 ++++++++++--
 scripts/fast-gate.sh                |  48 +++++-
 scripts/full-gate.sh                |  59 ++++++++
 tests/test_artifact_store.py        | 292 ++++++++++++++++++++++++++++++++++++
 tests/test_calibration_campaigns.py | 139 +++++++++++++++++
 tests/test_cli.py                   |  75 +++++++++
 tests/test_fast_gate_manifest.py    |  84 +++++++++++
 10 files changed, 826 insertions(+), 29 deletions(-)
```

| item | commit | subject |
|---|---|---|
| 1 | `63b0fcd` | G1-SKIP-PIN: enforce the skip-count pin in both gates (audit G1, SERIOUS) |
| 2 | `e6d714f` | G4-GATE-SELFCHECK: pin the fast-gate manifest against rot (audit G4) |
| 3 | `3bf0060` | G2-READ-VERIFY: serve-only-verified artifact reads (audit G2, SERIOUS; D050) |
| 4 | `d407aa6` | G6-STORE-ERROR-BRANCHES: pin the store-file error fallbacks (audit G6) |
| 5 | `156df83` | G8-NEWER-STAMP: pin the leave-alone direction of _ensure_schema (audit G8) |
| 6 | `5430a6c` | G9-TOCTOU-PIN: prove the put-path concurrent-writer benignity (audit G9) |
| 7 | `85dbb03` | G3-CLI-EXPLORATORY: pin the compare CLI's RFC 0044 wiring (audit G3) |
| 8 | `c9e1a2c` | G5-FIT-THRESHOLD-PIN: pin the MAPE and R2 threshold branches (audit G5) |
| 9 | `8922a4e` | G10-CSV-REFUSALS: pin the CSV-ingest refusal paths (audit G10) |
| +1 | `b0cc086` | Refresh measured gate numbers (G4 follow-up) + CHANGELOG for workflow 0066 |

## Successor findings

No new test exposed a product bug — Slice C produced **zero successor
bug findings**. Two non-bug items for the queue:

1. **Fast-gate budget overage (process, not product):** the fast
   subset now measures 3m42s wall against its "<= ~3 minutes" budget
   (the subset grew from 1052 to 1087 tests since the last
   measurement). The header states the overage honestly; revisiting
   the deselect list (next runtime-dominant candidates) is a future
   process item, not done here.
2. **G5 open question** (recorded above): per-metric threshold default
   for R2 — operator decision; until then the first real R2 fit will
   refuse under the shared 5.0 default unless the fixture sets
   `acceptance_threshold_pct`.

## Notes for the reviewer

- Write scope respected: the two gate scripts, the release doc, the
  decision log, `artifact_store.py`, four test files, `CHANGELOG.md`,
  and this artifact directory. The forbidden paths (audit/report
  evidence files, `kayakgen/eval/`, `kayakgen/cli/`, boundary tests)
  are untouched — the cumulative diffstat above is exhaustive.
- One commit per item plus one forecast follow-up commit (`b0cc086`):
  the item-2 commit message announced the deferred header refresh so
  the measured numbers would post-date the workflow's own tests.
- The enforcement-honesty constraint was treated as the point of the
  run: the skip pin was shown to fail end-to-end on wrong counts via a
  stub interpreter before commit, and the read path's refusal is
  pinned by four tests including the equal-length sibling.
- `ArtifactIntegrityError` is exported only from
  `kayakgen.services.artifact_store` (the services `__init__` is
  outside this packet's write scope); callers that want to catch it
  import from the module, same as `ArtifactRef` in the existing tests.
