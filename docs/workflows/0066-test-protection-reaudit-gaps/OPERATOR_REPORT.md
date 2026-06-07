# Operator Report — workflow 0066 (re-audit gap remediation)

Run `run_d7e3d217fe8bba2e1a77b3c32fca815d`, branch
`striatum/0066-test-protection-reaudit-gaps`, 2026-06-06 → 2026-06-07.
Work order: `KAYAKGEN_TEST_COVERAGE_AUDIT_WHOLE_REPO_CLAUDE_OPUS_4_8_2026-06-06.md`
§4 (gap ledger G1–G11). Review verdict: accept_with_findings
(`striatum/0066-test-protection-reaudit-gaps/review/REVIEW.md`).

## Items landed (draft, one commit per item)

| item | sha | slice |
|---|---|---|
| G1-SKIP-PIN | 63b0fcd | gate |
| G4-GATE-SELFCHECK | e6d714f | gate |
| G2-READ-VERIFY (D050) | 3bf0060 | store |
| G6-STORE-ERROR-BRANCHES | d407aa6 | store |
| G8-NEWER-STAMP | 156df83 | store |
| G9-TOCTOU-PIN | 5430a6c | store |
| G3-CLI-EXPLORATORY | 85dbb03 | tests |
| G5-FIT-THRESHOLD-PIN | c9e1a2c | tests |
| G10-CSV-REFUSALS | 8922a4e | tests |
| measured-numbers refresh + CHANGELOG | b0cc086 | gate follow-up |
| review MF-1 fix (apply job) | (this commit) | store |

## Gap rows closed — one-line evidence each

- **G1 (SERIOUS)**: pin proven to FIRE — sabotaged `EXPECTED_SKIPS=5` run
  of the real fast subset exited 1 with `FAIL: 4 skipped, expected
  exactly 5`; green path proven by `full-gate.sh` exit 0
  (`OK (4 skipped == expected 4)`). Both gates carry the identical pin;
  RELEASE_DISCIPLINE.md cites `scripts/full-gate.sh` as the mechanical
  form.
- **G2 (SERIOUS)**: SERVE-ONLY-VERIFIED (DECISION_LOG row **D050**) —
  every `_resolve_artifact` return is rehash-verified or raises
  `ArtifactIntegrityError`; warn-and-serve re-derive escalated to raise;
  four corruption shapes pinned incl. the equal-length bit-rot sibling.
  Review MF-1 (the one escape: `get_json`'s second read) fixed in apply:
  verified bytes are returned and decoded, deny-`read_text` regression
  test added.
- **G3**: CliRunner pair pins exit 1 + RFC 0044 token + no report
  without the flag; exit 0 + `exploratory_frontier` with it.
- **G4**: manifest tests fail on renamed `--ignore` paths /
  non-collecting `--deselect` nodeids; stale header counts re-measured
  (1347 full / 1087 fast).
- **G5**: `fit_above_mape_threshold` and `fit_below_r2_threshold` reason
  tokens pinned; the fail-closed R2-under-default-threshold quirk pinned
  as intended behavior.
- **G6**: stat-failure / read-failure OSError fallbacks pinned via
  monkeypatch (deterministic, root-safe).
- **G8**: future-stamp DB left alone — rows survive, stamp not
  downgraded.
- **G9**: injected-race test proves the TOCTOU window is benign for
  identical content (last-writer-wins, no torn temp); scope honestly
  limited to ordering, not torn-write atomicity (review SF-2: documented
  non-goal).
- **G10**: CSV-ingest refusals (missing column, extra column,
  `_coerce_bool` garbage) + inclining `source_id` mismatch validator
  pinned, mirroring the tank twin.

## Decisions recorded

- **D050** (DECISION_LOG): SERVE-ONLY-VERIFIED read contract; rehash on
  every read; repair only from canonical bytes that rehash to the
  expected address; perf accepted at current read volumes.
- **G5 open question** (recorded, no product change): the default
  `threshold_pct=5.0` refuses every R2 fit (R2 ≤ 1.0 < 5.0). Pinned as
  fail-closed-intended; a per-metric default is a future operator
  decision — revisit when the first real R2 calibration record arrives.

## Standing deferrals (visible, not debt)

| gap | status | unblocks when |
|---|---|---|
| G7 — CLI NaN/inf negatives | deferred (workflow 0065 SUMMARY) | bug-hunt NaN-validator sweep green-light |
| G11 — absolute-path evidence refs | deferred (morning audit R11) | externally-authored fixtures arrive (D006/D007) |

## Review findings disposition

| id | disposition |
|---|---|
| MF-1 `get_json` second read | **fixed in apply** + regression test; full gate re-run green |
| SF-1 textual pin-presence test | accepted as tripwire; parser-level script test left as future hardening (would need a bash test harness this repo does not have) |
| SF-2 G9 atomicity scope | documented non-goal; no action |

## Process notes (striatum readout)

- Supervised lane spawn broke mid-run: the host adopted the #87
  lane-sandbox posture (`STRIATUM_LANE_OS_USER=striatum-lane`) between
  the draft spawn (16:45Z, ran as operator) and the review spawn
  (17:29Z+); `striatum-lane` cannot traverse `/home/halbritt`, so all
  three codex spawns died "child exited before attach". Review and apply
  were driven through the operator MCP/CLI claim loop; the independent
  review pass ran via local `codex exec` (sandbox bypassed to match the
  lane's own `--yolo` config). Cross-model review preserved;
  supervised-lane provenance was not possible.
- The draft job's per-job worktree was released after completion leaving
  its 11 commits dangling (striatum #186); recovered by fast-forwarding
  the run branch to the verified tip `6abee0a` (striatum #184 precedent).
- Codex's MF-1 repro ran outside pytest and upserted one row into the
  user-level `index.sqlite`; detected, deleted, all tables re-verified
  0 rows (see REVIEW.md).

## Gates

- Draft (its worktree): full suite 1347 passed + 4 skips (10:49);
  fast subset 1087/4/2 (3m42s).
- Review (this checkout, via `scripts/full-gate.sh`): exit 0,
  **1347 passed, 4 skipped** in 9:21, `OK (4 skipped == expected 4)`;
  ruff clean; break-the-pin sabotage run exit 1.
- Apply (after MF-1 fix): full gate re-run — see SUMMARY.md for the tail.
- User-level `~/.local/share/kayakgen/index.sqlite`: 0 rows in all six
  tables at apply close.
