# Operator Report — Workflow 0062: test-protection P0 gate recovery

date: 2026-06-06
run: run_00abc6ed7fb8b35ed5860d7d4286643a
branch: `striatum/0062-test-protection-p0-gate-recovery`
review verdict: **accept, no findings** (`striatum/0062-test-protection-p0-gate-recovery/review/REVIEW.md`)

## What landed (slice stack, one commit per slice)

| slice | commit | summary |
|---|---|---|
| P0-BOUNDARY-FIX | `f8555c3244bad32f897cef35f3e924d0ac322b9c` | Hydrostatics row registry relocated verbatim to the new `kayakgen/metadata/` package (`hydrostatics_rows.py`); `kayakgen/ui/hydrostatics_metadata.py` is now a re-export shim; `kayakgen/services/evaluation.py` imports the new home. `test_services_does_not_import_ui_or_cli[path2]` (red on `main` since `313dfdd`, 2026-05-25) is green; the boundary and row-metadata byte-stability tests were not touched. |
| P0-INDEX-ISOLATION | `63ee198a34b4464b4c978a165ed3707a9d0de201` | Two-layer autouse conftest isolation (per-test tmp path + session-scoped floor) pins `KAYAKGEN_INDEX_DB` inside pytest's tmp tree; regression test `tests/test_artifact_store.py::test_index_db_isolated_from_user_level_path` pins the property. The session floor catches the real leak from an unjoined forked-search job thread that outlives its test. |
| P0-GATE-ENFORCE | `fbfdf9e5926556b487d9e28ec154a734875902b2` | `scripts/fast-gate.sh` (ruff + measured fast pytest subset) + `scripts/install-hooks.sh` (installs it as `.git/hooks/pre-push`); `docs/RELEASE_DISCIPLINE.md` gate 1 pins "expected: 4" documented OpenFOAM opt-in skips and records the striatum full-suite slice gate. |
| draft artifact | `5b4672a1c82933a56a6dcb0b137edd92a359b0e8` | Published `striatum/0062-test-protection-p0-gate-recovery/DRAFT.md`. |

The apply job changed no production code: the review accepted with zero
must-fix findings, so `CHANGELOG.md` needed no further update (the
workflow 0062 entry landed with slice 3) and the apply commit adds only
this report, the published summary artifact, and the reviewer's
`REVIEW.md` (committed for provenance, matching prior workflow
directories).

## Fast gate — measured runtime + deselect list

Measured on the operator workstation, 2026-06-06: **2m57s wall**
(pytest 175.4s — 1052 passed / 4 skipped / 2 deselected — plus ruff and
interpreter startup). Budget ≤ ~3 minutes: met. The reviewer
independently measured `time -p scripts/fast-gate.sh` at 181.63s real
(1052 passed / 4 skipped / 2 deselected).

Canonical deselect list (lives in the `scripts/fast-gate.sh` header;
file-level `--ignore` unless noted):

| set | target | measured |
|---|---|---|
| named: browser/visual | `tests/test_web_browser.py` | 34.3s |
| named: subprocess lifecycle | `tests/test_generative_jobs_subprocess.py` | 10.9s |
| named: CFD fixture-command (whole integration file) | `tests/test_cfd_jobs.py` | 29.7s |
| named: CFD fixture-command (node `--deselect`) | `tests/test_cli.py::test_cfd_fixture_run_and_status_keep_raw_warning_visible` | 1.1s |
| named: CFD fixture-command (node `--deselect`) | `tests/test_web.py::test_cfd_routes_fixture_command_success_remains_raw_unvalidated` | 0.7s |
| dominator | `tests/test_generated_closed_body_hardening.py` | 58.8s |
| dominator | `tests/test_design_report.py` | 36.4s |
| dominator | `tests/test_generated_closed_body.py` | 34.8s |
| dominator | `tests/test_sweep.py` | 32.6s |
| dominator | `tests/test_active_search_nested_keys.py` | 29.4s |
| dominator | `tests/test_web_layout.py` | 22.8s |
| dominator | `tests/test_generative_jobs_manager.py` | 19.4s |
| dominator | `tests/test_compare.py` | 18.6s |

Kept on purpose (protection-critical, cheap): import/services boundary
tests, forbidden-copy regressions (`test_web_read_models.py`,
`test_desktop_layout.py`), claims promotion chain, artifact-store +
index-isolation regression, registry/metadata pins.

The fast gate is a pre-push convenience net, NOT the release gate; the
full suite remains the slice-completion / pre-merge gate
(`docs/RELEASE_DISCIPLINE.md`).

## Final full gate (apply job, run-branch worktree, 2026-06-06)

`.venv/bin/python -m pytest -q` → exit 0:

```text
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1309 passed, 4 skipped in 517.49s (0:08:37)
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1.

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (the invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65` are pre-existing and
untouched by this workflow).

R3 evidence: the operator's `~/.local/share/kayakgen/index.sqlite` was
byte-identical across this full-suite run
(`mtime_ns=1780730948 size=90112` before and after).

## Audit ledger rows closed

From `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md`:

- **R0 (code half)** — `kayakgen.services.evaluation` no longer imports
  `kayakgen.ui.*`; the services→ui boundary test is green again.
  (The process half — red gate invisible for 12 days — is addressed by
  the R4 wording fix plus the pre-push hook below.)
- **R3** — no test can write the operator's
  `~/.local/share/kayakgen/index.sqlite`; verified unchanged across the
  full-suite runs (operator purged the 129 phantom rows 2026-06-06; the
  conftest isolation prevents recurrence).
- **R4** — `docs/RELEASE_DISCIPLINE.md` gate 1 now requires "green,
  with only the documented OpenFOAM opt-in skips (expected: 4)"; any
  other skip count does not count as a gate.

## Remaining operator actions

1. **Install the pre-push hook** (once per clone — not done by the
   workflow; `.git/hooks/` is per-clone state):

   ```bash
   scripts/install-hooks.sh
   ```

2. **Merge the run branch to `main`**: the slice stack is left on
   `striatum/0062-test-protection-p0-gate-recovery` per the apply
   packet; merging is the operator's step after the run completes.

Out of scope here (routed per the remediation plan §6): P1-STORE-ATOMIC,
P1-SQLITE-VERSION, the durable-state batch (workflow B), and the
D048/D049 implementations (workflow C).
