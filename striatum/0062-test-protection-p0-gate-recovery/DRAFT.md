# Draft — Workflow 0062: test-protection P0 gate recovery

author: author-claude-001
date: 2026-06-06
run: run_00abc6ed7fb8b35ed5860d7d4286643a
branch: striatum/0062-test-protection-p0-gate-recovery (worktree wt_f801f9f8e0702c832e3ca52b4d6a397e)

Three P0 slices from
`KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md` §3,
landed in order, one commit per slice.

## Slice 1 — P0-BOUNDARY-FIX (`f8555c3244bad32f897cef35f3e924d0ac322b9c`)

```
 docs/ARCHITECTURE_MAP.md               |   4 ++
 kayakgen/metadata/__init__.py          |   9 +++
 kayakgen/metadata/hydrostatics_rows.py | 122 +++++++++++++++++++++++++++++++++
 kayakgen/services/evaluation.py        |   2 +-
 kayakgen/ui/hydrostatics_metadata.py   | 120 ++++----------------------------
 5 files changed, 149 insertions(+), 108 deletions(-)
```

Registry relocated verbatim to the new `kayakgen/metadata/` package
(`hydrostatics_rows.py`); `kayakgen/ui/hydrostatics_metadata.py` is now a
re-export shim (generator.py pattern); `services/evaluation.py:33` imports
the new home. The forbidden-path tests were not touched.

**Boundary-test evidence** (after slice 1):

```
$ pytest tests/test_services_boundaries.py tests/test_import_boundaries.py \
    tests/test_hydrostatics_row_metadata.py tests/test_hydro_tab_descriptions.py -q
114 passed in 2.56s
```

`test_services_does_not_import_ui_or_cli[path2]` — red on `main` since
`313dfdd` (2026-05-25) — is green; row-metadata byte-stability and
hydro-tab description tests pass unchanged through the shim.

## Slice 2 — P0-INDEX-ISOLATION (`63ee198a34b4464b4c978a165ed3707a9d0de201`)

```
 tests/conftest.py            | 56 ++++++++++++++++++++++++++++++++++++++++++++
 tests/test_artifact_store.py | 48 +++++++++++++++++++++++++++++++++++++
 2 files changed, 104 insertions(+)
```

Two-layer isolation, both citing audit R3 in comments:

- **Per-test autouse fixture** (`_isolate_kayakgen_index_db`): monkeypatches
  `KAYAKGEN_INDEX_DB` to a fresh `tmp_path_factory.mktemp("index")` path.
- **Session-scoped floor** (`_isolate_kayakgen_index_db_session`): pins the
  value that monkeypatch undo restores to a session tmp path.

The floor is not defensive decoration — verification caught a real leak the
per-test fixture alone misses: `test_fork_route_returns_201_with_new_job`
forks a search job on a non-daemon background thread and never joins it; the
job finished *after* test teardown, read the by-then-restored (unset) env
var, and wrote one phantom row to the operator's real DB. With the floor, the
restored value is still a tmp path. The leaked row (run_id
`search-0a6a35fedd14cab0-output`, out_dir under `/tmp/pytest-of-*`) plus its
8 candidate / 32 metric / 28 artifact rows were deleted, returning the
operator DB to its post-purge state (0 rows in all tables).

Regression test `test_index_db_isolated_from_user_level_path` pins: fixture
active without being requested; `_default_index_path()` resolves inside
pytest's tmp tree, never `~/.local/share/kayakgen/index.sqlite`;
default-constructed `SqliteIndex()` lands on the isolated path; session
floor also inside the tmp tree.

**Isolation evidence — user DB untouched across the final full-suite run:**

```
user DB pre-gate:  mtime=1780730948 size=90112
user DB post-gate: mtime=1780730948 size=90112   (runs rows: 0)
```

## Slice 3 — P0-GATE-ENFORCE (`fbfdf9e5926556b487d9e28ec154a734875902b2`)

```
 CHANGELOG.md               | 21 +++++++++++++
 docs/RELEASE_DISCIPLINE.md | 49 +++++++++++++++++++++++++++---
 scripts/fast-gate.sh       | 76 ++++++++++++++++++++++++++++++++++++++++++++++
 scripts/install-hooks.sh   | 28 +++++++++++++++++
 4 files changed, 169 insertions(+), 5 deletions(-)
```

**Measured fast-gate runtime: 2m57s wall** (pytest 175.4s — 1052 passed /
4 skipped / 2 deselected — plus ruff + startup). Budget ≤ ~3 min: met.

**Deselect list (evidence-driven).** The three named sets cut only ~51s of a
516s suite, nowhere near the budget, so a junitxml profiling pass
(per-file totals, 2026-06-06) extended the list with the measured runtime
dominators. File-level `--ignore`:

| set | file | measured |
|---|---|---|
| named: browser/visual | `tests/test_web_browser.py` | 34.3s |
| named: subprocess lifecycle | `tests/test_generative_jobs_subprocess.py` | 10.9s |
| named: CFD fixture-command (whole integration file) | `tests/test_cfd_jobs.py` | 29.7s |
| dominator | `tests/test_generated_closed_body_hardening.py` | 58.8s |
| dominator | `tests/test_design_report.py` | 36.4s |
| dominator | `tests/test_generated_closed_body.py` | 34.8s |
| dominator | `tests/test_sweep.py` | 32.6s |
| dominator | `tests/test_active_search_nested_keys.py` | 29.4s |
| dominator | `tests/test_web_layout.py` | 22.8s |
| dominator | `tests/test_generative_jobs_manager.py` | 19.4s |
| dominator | `tests/test_compare.py` | 18.6s |

plus node-level `--deselect` for the two fixture-command tests outside
`test_cfd_jobs.py`:
`tests/test_cli.py::test_cfd_fixture_run_and_status_keep_raw_warning_visible` (1.1s),
`tests/test_web.py::test_cfd_routes_fixture_command_success_remains_raw_unvalidated` (0.7s).

Kept on purpose (cheap, protection-critical): boundary tests, forbidden-copy
regressions (`test_web_read_models.py`, `test_desktop_layout.py`), claims
promotion chain, artifact-store + index-isolation regression.

`scripts/install-hooks.sh` installs the gate as `.git/hooks/pre-push`
(verified in a scratch repo: hook lands executable; refuses with exit 1 on
interpreter-missing and on failing check). The script honors `KAYAKGEN_PY`
for environments where the venv is not at repo root (e.g. striatum
worktrees). Installing into the operator clone is one command:
`scripts/install-hooks.sh`.

`docs/RELEASE_DISCIPLINE.md`: gate 1 now reads "green, with only the
documented OpenFOAM opt-in skips (expected: 4)" with the four named (2 ×
`test_openfoam_v2512_smoke.py`, 2 × `test_cfd_run_stages.py`), closing the
audit R4 skip-as-pass hole; new "Local enforcement" section documents the
hook and records that striatum review/apply jobs run the FULL suite as
their slice-completion gate.

## Final slice gate (after slice 3)

`.venv/bin/python -m pytest -q` → exit 0; `.venv/bin/python -m ruff check
kayakgen tests` → "All checks passed!" (pre-existing invalid-`# noqa`
warnings on `kayakgen/ui/web/generate_frontier_view.py`, untouched by this
work). Output tail:

```
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1309 passed, 4 skipped in 509.55s (0:08:29)
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips. (Audit baseline
was 1307 passed + 1 failed; +1 from the fixed boundary test now passing,
+1 from the new isolation regression test.)

## Notes for review

- The session-floor leak (slice 2) is a finding the remediation plan did not
  anticipate; the unjoined forked job in `test_generative_jobs_fork.py` is
  the only observed offender. A joined/cancelled-job audit of the generative
  manager tests would belong to the durable-state batch (workflow B), not
  here.
- Striatum workflow-template enforcement (plan P0-GATE-ENFORCE item b) is
  recorded in RELEASE_DISCIPLINE as the full-suite slice gate; the template
  files themselves are outside this packet's write scope.
