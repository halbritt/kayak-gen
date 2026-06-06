# KAYAKGEN Test-Protection Remediation Plan — Claude Opus 4.8 — 2026-06-06

Tiered, executable plan derived from
`KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md` (same day, same
model, same repo state: `main` @ `df66178`). Constraints treated as
load-bearing: single operator, homelab runtime, no CI service planned, all
code changes route through striatum workflows (docs/RFCs exempt per standing
operator rule). Plan only — no source edited by this document.

## 0. Source audit

- **Input**: `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md`,
  verdict `MIXED` / confidence `medium`, 0 BLOCKER / 7 SERIOUS / 5 MINOR /
  2 NOTE. Zero staleness: produced this session against the current tree;
  every cited file/line was re-verified live during the audit (BUG-001,
  BUG-026, BUG-041 sites, the red boundary test, the polluted index DB).
- **Cross-references**: `docs/bug-hunt/LEDGER.md` (2026-05-29, all 85
  findings open) where audit rows coincide with ledger rows; RFC 0044,
  RFC 0058, `docs/RELEASE_DISCIPLINE.md` no-claim invariants.

## 1. Executive summary

- **Two of the three P0s are about the gate, not the code.** Fix the
  layering import to turn the trunk green again (red since 2026-05-25),
  then add the cheapest enforcement that makes red *visible*, because a
  red trunk that nobody sees will recur. The third P0 stops the suite from
  writing into the operator's production index DB on every run.
- **Decision-first items are separated from mechanical items.** R1
  (fit-record `kind`) and R2 (compare refusal vs auto-downgrade) each need
  a one-paragraph maintainer decision before any code lands; everything
  else in P1 is mechanical and can proceed in parallel.
- **Durable-state hardening is one batch**: atomic store writes, sqlite
  schema versioning, canonical-hash byte pin, IO encoding — one striatum
  workflow, four small slices.
- **P2 is test additions only** — no production code except optional CLI
  validators. Be unsentimental about deferring it; nothing there blocks.
- **Total estimated effort**: P0 ≈ half a day; P1 ≈ 2–3 days including the
  two decisions; P2 ≈ 1–2 days, deferrable.
- **Routing**: four striatum workflows (A: gate recovery; B: durable
  state; C: contract decisions, RFC-first; D: protection top-ups).
  RELEASE_DISCIPLINE wording changes are docs-only and exempt.

## 2. Re-tiering notes vs. the audit

The audit ranked by *test-protection severity*; this plan ranks by *what to
do first*. Differences, with reasoning:

- **R0 splits into two items** (fix the import; add enforcement). The audit
  treated it as one gate-posture row. The import fix is trivial; the
  enforcement question is the part worth a decision.
- **R4 (skip-as-pass) drops from SERIOUS to P1-late.** *Audit said*: a
  minimal env silently skips the desktop forbidden-copy gate. *Actual*: the
  only machine that runs the gate today provably has all extras installed,
  and the web-side gates always run. *Mine*: real, but the cheapest fix is
  a five-line skip-count pin, so it lands in P1 as a tail item rather than
  driving urgency.
- **R6 (sqlite schema versioning) stays P1 despite being recoverable.** The
  schema already grew once (`generative_jobs` table happened to be additive
  via `CREATE TABLE IF NOT EXISTS`; a column addition will not be), and the
  fix is ~20 lines.
- **R12 (CLI NaN/inf negatives) stays P2.** It coincides with the open
  bug-hunt NaN-validator family (11+ instances); piecemeal CLI-only fixes
  would fragment that remediation. Do it as one validator sweep when the
  bug-hunt family is addressed, not as audit fallout.

## 3. P0 — blocking

### P0-BOUNDARY-FIX
- **source**: audit R0 (red trunk); `test_services_does_not_import_ui_or_cli[path2]`
- **what**: relocate `kayakgen/ui/hydrostatics_metadata.py` to a new
  `kayakgen/metadata/hydrostatics_rows.py` (it is a pure-data pydantic
  registry with no UI imports), leave
  `kayakgen/ui/hydrostatics_metadata.py` as a one-line re-export shim
  (repo's established shim pattern), and point
  `kayakgen/services/evaluation.py:33` at the new location.
- **why**: the documented mandatory gate has been red on `main` since
  `313dfdd` (2026-05-25); every landing since has had no working safety
  signal.
- **touches**: `kayakgen/metadata/` (new), `kayakgen/ui/hydrostatics_metadata.py`
  (becomes shim), `kayakgen/services/evaluation.py`,
  `docs/ARCHITECTURE_MAP.md` (package layout row).
- **effort**: 1–2 hours.
- **depends on**: none.
- **acceptance**: `pytest -q` fully green (0 failed; 4 documented OpenFOAM
  skips only); `tests/test_hydrostatics_row_metadata.py` byte-stability
  tests unchanged and green; `test_services_boundaries.py` green.
- **note (alternative rejected)**: moving row-labeling out of services into
  ui is architecturally purer but churns the byte-pinned wire-payload
  builder; smallest viable change wins at this maturity.

### P0-INDEX-ISOLATION
- **source**: audit R3 (129/129 phantom rows in
  `~/.local/share/kayakgen/index.sqlite`)
- **what**: add an autouse fixture in `tests/conftest.py` that sets
  `KAYAKGEN_INDEX_DB` to `tmp_path_factory.mktemp("index") / "index.sqlite"`
  for every test, plus one regression test asserting the default user path
  is untouched after a sweep-runner test executes. Separately (operator
  action, not code): clean the polluted DB once —
  `sqlite3 ~/.local/share/kayakgen/index.sqlite "DELETE FROM runs WHERE out_dir LIKE '/tmp/%';"`
  (or simply delete the file; it is a rebuildable read-model).
- **why**: the mandated pre-merge gate corrupts the operator's production
  `kayakgen runs` read-model on every run; each day it runs, the cleanup
  story gets murkier.
- **touches**: `tests/conftest.py`, new test in `tests/test_artifact_store.py`.
- **effort**: 1–2 hours.
- **depends on**: P0-BOUNDARY-FIX (land on a green trunk).
- **acceptance**: run `pytest -q` twice; `~/.local/share/kayakgen/index.sqlite`
  mtime and row counts unchanged across both runs.

### P0-GATE-ENFORCE
- **source**: audit R0 (enforcement half)
- **what**: make red visible without inventing CI: (a) a repo-local
  `.git/hooks/pre-push`-installable script (`scripts/install-hooks.sh`)
  that runs `ruff check kayakgen tests` and `pytest -q` and refuses the
  push on failure, and (b) add the same commands as a required
  prepare/verify step in the striatum workflow templates used for this
  repo, so lane agents cannot complete a slice on a red suite.
- **why**: the boundary test *worked* and was ignored for 12 days; without
  enforcement, P0-BOUNDARY-FIX just resets the clock on the next
  violation.
- **touches**: `scripts/` (new hook installer), striatum workflow template
  for kayak-gen, `docs/RELEASE_DISCIPLINE.md` (document the hook).
- **effort**: 2–4 hours. Per Q3 ("fast", 2026-06-06): the hook runs the
  fast subset (deselect browser/subprocess/CFD-fixture tests, ~2 min);
  the full 9-minute suite is the striatum slice-completion gate.
- **depends on**: P0-BOUNDARY-FIX (a hook installed against a red trunk
  blocks all pushes immediately).
- **acceptance**: a push with an intentionally broken test is refused
  locally; a striatum slice on a red suite cannot reach completion.

## 4. P1 — serious

### P1-FIT-KIND-DECISION — decision made (D049); implementation only
- **source**: audit R1; BUG-001 (critical, open); D049
- **what**: per D049 (operator decision 2026-06-06): add
  `kind: Literal["analytical","cfd_in_loop"]` to `StabilityFitRecord`
  with `"analytical"` default (option 1 of the three the bug ledger
  enumerated). Additive-with-default: existing staged fit JSONs parse
  unchanged; `fixture_canonical_sha256` unaffected (hashes the fixture
  manifest, not the fit record).
- **why**: graduation is dead-on-arrival with real records while eight
  green tests assert otherwise; the first real fit promotion will silently
  fail to graduate.
- **touches**: `kayakgen/eval/stability/accepted_fit.py` or
  `kayakgen/services/generative_jobs.py` (per decision),
  `tests/test_cfd_in_loop_evaluator_status.py`, `docs/DECISION_LOG.md`,
  RFC 0058 successor stub if option 2.
- **effort**: decision 1 hour; implementation 2–4 hours.
- **depends on**: P0-BOUNDARY-FIX.
- **acceptance**: at least one test feeds a **real**
  `make_stability_acceptance_triple().fit` through
  `cfd_in_loop_evaluator_status` and asserts the decided behavior; the
  `SimpleNamespace` fakes are removed or demoted to shape-only tests;
  BUG-001 closed in the ledger.

### P1-COMPARE-GATE — decision made (D048); refusal branch only
- **source**: audit R2; BUG-026 (high, open); D048
- **what**: per D048 (operator decision 2026-06-06): call
  `ensure_objectives_claim_admissible_for_search` in
  `build_comparison_report`, add an `--explicit-exploratory` CLI flag to
  the compare command, and pin the refusal token in a test. The
  downgrade-pinning tests in `test_compare.py` move to the opt-in path
  (same assertions, explicit flag set).
- **why**: the canonical invariant says "refused unless explicit opt-in";
  one entry point silently opts in on the operator's behalf, and the suite
  pins the weaker behavior — spec and tests currently certify different
  contracts.
- **touches**: `kayakgen/search/compare.py`, `kayakgen/cli/main.py`
  (compare command), `tests/test_compare.py`,
  `docs/RELEASE_DISCIPLINE.md` + `docs/DECISION_LOG.md` (either branch).
- **effort**: decision 1 hour; implementation 2–4 hours (refusal branch) or
  1 hour (docs branch).
- **depends on**: P0-BOUNDARY-FIX.
- **acceptance**: refusal branch — `build_comparison_report` with a
  `raw_unvalidated` objective and no opt-in raises the RFC 0044 token
  (test exists and is green); docs branch — invariant text names the
  exception and BUG-026 is closed `wontfix-by-decision`.

### P1-STORE-ATOMIC
- **source**: audit R5 + R9 (collapsed); BUG-041, BUG-022/-078
- **what**: in `FilesystemArtifactStore._put_bytes`, write to
  `store_path.with_suffix(".tmp-<pid>")` then `os.replace`; on the
  `store_path.exists()` dedupe branch, verify length (cheap) and rehash on
  mismatch, repairing corrupt bytes instead of linking them. Same
  temp+replace pattern and explicit `encoding="utf-8"` in
  `kayakgen/io/json.py` `save_hull`/`save_evaluation`.
- **why**: a crash mid-write permanently poisons a content address — every
  future put of the same content silently links truncated bytes into
  canonical run layouts; this is the provenance substrate for every
  sweep/search run.
- **touches**: `kayakgen/services/artifact_store.py`,
  `kayakgen/io/json.py`, `tests/test_artifact_store.py`.
- **effort**: 3–5 hours.
- **depends on**: P0-INDEX-ISOLATION (its tests exercise the store; land
  isolation first so new tests don't pollute).
- **acceptance**: new test writes truncated bytes at a hash path, calls
  `put_json` with the full payload, asserts canonical path receives intact
  bytes; existing round-trip/redrive tests unchanged.

### P1-SQLITE-VERSION
- **source**: audit R6
- **what**: set `PRAGMA user_version = 1` at schema creation; on open, if
  `user_version` < current, drop all tables and recreate (it is a
  rebuildable read-model — migration machinery is overkill for a solo
  operator), emitting a `UserWarning` naming the rebuild. Add a test that
  opens a DB missing one column at version 0 and asserts rebuild instead
  of `OperationalError`.
- **why**: the next additive schema change crashes every existing operator
  DB at upsert time, in the middle of a sweep.
- **touches**: `kayakgen/services/artifact_store.py` (`SqliteIndex._conn`/
  `_create_schema`), `tests/test_artifact_store.py`.
- **effort**: 2–3 hours.
- **depends on**: P1-STORE-ATOMIC (same module; one workflow slice apart).
- **acceptance**: the old-DB test passes; `kayakgen runs list` works after
  a simulated schema bump against a stale DB.

### P1-SHA-PIN
- **source**: audit §6 (canonical-hash stability)
- **what**: one regression test pinning
  `fixture_canonical_sha256(make_stability_acceptance_triple().fixture)`
  to its literal hex digest, with a comment explaining that a failure
  means a pydantic serialization change just invalidated every signed
  promotion packet and must be handled as an evaluator-version event, not
  a test update.
- **why**: the SHA-256 over `model_dump_json()` *is* the tamper-evidence
  boundary of the claims chain; a silent pydantic format change would
  strand all signed packets with no test noticing until promotion fails in
  the field.
- **touches**: `tests/test_stability_fit_registry.py`.
- **effort**: <1 hour.
- **depends on**: P0-BOUNDARY-FIX.
- **acceptance**: test green today; deliberately changing field order in
  the model makes it fail with the explanatory message.

### P1-SKIP-PIN
- **source**: audit R4
- **what**: extend the gate (the P0-GATE-ENFORCE script is the natural
  home) to fail when the skip count exceeds the documented OpenFOAM set —
  e.g. `pytest -q -ra | tail` parsed for `skipped`, allowed ceiling 4 with
  the allowed skip locations grep-checked — so a `[dev]`-only env cannot
  report success while the desktop/web forbidden-copy gates silently
  skipped.
- **why**: "green or skipped" semantics plus `importorskip` means the
  named no-claim invariant gates can be skipped invisibly on any machine
  other than this one.
- **touches**: `scripts/` gate script, `docs/RELEASE_DISCIPLINE.md`
  (replace "green or skipped" with "green, with only the documented
  OpenFOAM skips").
- **effort**: 1–2 hours.
- **depends on**: P0-GATE-ENFORCE.
- **acceptance**: running the gate script in a venv without PyQt6 fails
  with a message naming the missing extras; in the full venv it passes.

## 5. P2 — protection top-ups

### P2-HYDRO-ANCHOR
- **source**: audit R7
- **what**: one analytic cross-check test — evaluate a hull configured to
  approximate a wall-sided prism (or the closest the parametrization
  allows) and assert displaced volume/LCB against the closed-form value at
  coarse tolerance (rtol ~1e-2), documenting the geometric idealization in
  the test.
- **why**: every hydrostatics number is currently pinned only against
  itself; one external anchor converts the golden pins from "unchanged"
  to "unchanged and plausibly right" — these numbers become GA fitness
  inputs on the north-star path.
- **touches**: `tests/test_hydrostatics.py`.
- **effort**: 2–4 hours (most of it choosing the analytic body honestly).
- **depends on**: none. **acceptance**: test green with a tolerance
  justified in-comment.

### P2-CANCEL-DETERMINISTIC
- **source**: audit R8
- **what**: a manager-level cancel test using the existing
  controlled-runner monkeypatch pattern
  (`_controlled_cancel_runner`) so the cancel path executes
  deterministically, then delete the `pytest.skip("job completed before
  cancel landed")` raceout from the racy variant or demote that variant to
  an opt-in slow marker.
- **why**: on a fast machine the cancel integration path can stay green
  for months without ever executing.
- **touches**: `tests/test_generative_jobs_subprocess.py`.
- **effort**: 2–3 hours. **depends on**: none.
- **acceptance**: cancel-path assertions run unconditionally in the
  default suite.

### P2-REGISTRY-MICROGAPS
- **source**: audit R10
- **what**: three small tests in `test_stability_fit_registry.py`:
  a 2-fixture fit where only the second fixture clears the chain (pins
  ANY-pass semantics); a hysteresis `bound_fraction=0.031` rejection
  (gate 3a second branch); a touching heel-range load `(30,60)` vs
  `(0,30)` (pins the `<=` overlap boundary as intended behavior).
- **why**: the 13-gate surface is the project's authority boundary; these
  are its only unpinned branches.
- **touches**: `tests/test_stability_fit_registry.py`.
- **effort**: 1–2 hours. **depends on**: none.
- **acceptance**: three named tests green; multi-fixture semantics now
  documented by test.

### P2-CLI-NEGATIVES
- **source**: audit R12; BUG-073..077 family
- **what**: as part of the bug-hunt NaN-validator sweep (not before it):
  parametrized `CliRunner` tests for each float option × {`nan`, `inf`,
  negative} asserting non-zero exit and a structured message, landing
  together with the pydantic/typer validators that make them pass.
- **why**: CLI is the default operator surface; today NaN propagates into
  prepared CFD cases and stability JSON.
- **touches**: `kayakgen/cli/*.py` validators, `tests/test_cli.py`.
- **effort**: half a day (validator sweep dominates). **depends on**:
  maintainer green-lighting the bug-hunt NaN family remediation.
- **acceptance**: BUG-073..077 closed; parametrized negatives green.

### P2-MYPY-DECIDE
- **source**: audit §3 note
- **what**: remove `mypy` from `[dev]` extras (recommended — it has never
  been configured or gated and ruff is established) **or** add
  `[tool.mypy]` config and wire it into the gate script. Pick one; the
  current state implies a gate that does not exist.
- **touches**: `pyproject.toml` (± gate script).
- **effort**: minutes (removal) / half a day (adoption). **depends on**:
  none. **acceptance**: extras match the actual gate stack.

### P2-REASON-ENUM
- **source**: audit §5 note
- **what**: rewrite `test_every_reason_has_a_next_action` to derive the
  expected set from the module namespace
  (`[v for k,v in vars(reg).items() if k.startswith("REASON_") and k != "REASON_NEXT_ACTION"]`)
  instead of a hand-enumerated list.
- **why**: a future gate constant can silently ship without operator
  remediation copy.
- **touches**: `tests/test_stability_fit_registry.py`.
- **effort**: <30 min. **depends on**: none.
- **acceptance**: adding a dummy `REASON_X` constant without a
  `REASON_NEXT_ACTION` entry makes the test fail.

## 6. Dependency map

P0 is strictly ordered: **P0-BOUNDARY-FIX → P0-INDEX-ISOLATION →
P0-GATE-ENFORCE** (green trunk before isolation tests land; both before a
hook that would otherwise block all pushes). P1 fans out from
P0-BOUNDARY-FIX in parallel, except P1-SQLITE-VERSION follows
P1-STORE-ATOMIC (same module) and P1-SKIP-PIN follows P0-GATE-ENFORCE
(extends the same script). The two decision items (P1-FIT-KIND-DECISION,
P1-COMPARE-GATE) gate only their own implementations. P2 has no internal
edges; P2-CLI-NEGATIVES waits on the bug-hunt NaN family.

Edges: BOUNDARY-FIX → {INDEX-ISOLATION, GATE-ENFORCE, FIT-KIND, COMPARE-GATE,
STORE-ATOMIC, SHA-PIN}; INDEX-ISOLATION → STORE-ATOMIC;
GATE-ENFORCE → SKIP-PIN; STORE-ATOMIC → SQLITE-VERSION.

**Striatum routing** (code items must ride the runner per standing rule):

- **Workflow A — gate recovery**: P0 trio, three slices, in order.
- **Workflow B — durable state**: STORE-ATOMIC, SQLITE-VERSION, SHA-PIN.
- **Workflow C — contract decisions**: FIT-KIND, COMPARE-GATE; RFC/DECISION_LOG
  rows first (docs, exempt), then one implementation slice each.
- **Workflow D — protection top-ups**: P2 test-only items, whenever idle.
- Operator actions outside workflows: the one-time index-DB cleanup;
  installing the pre-push hook.

## 7. What I'd defer indefinitely

- **R11 (absolute-path evidence rejection in `_resolve_evidence`)**: the
  manifests are operator-authored on the operator's own machine; the
  "hostile manifest" threat is unrealistic until fixtures arrive from
  third parties. Revisit when a real external measurement campaign (D006/
  D007) produces externally-authored fixture files — at that point it
  becomes a P1.
- **Manager-level concurrency tests (audit §6)**: two simultaneous
  generative jobs against one `jobs_root` is not an operator workflow
  today; the SIGKILL/reconciliation coverage already protects the
  realistic failure (daemon restart killing a child).
- **SQLite `database is locked` race tests**: same reasoning; single
  operator, single writer in practice once tests are isolated (P0).
- **Coverage tooling adoption**: the audit found the suite's weak spots by
  reading, not by profiling; a coverage floor would add gate cost and
  percentage worship to a project whose failure modes are contract drift,
  not unexercised lines. Not worth it at this maturity.

## 8. Open questions — ANSWERED 2026-06-06

All four answered by the operator on 2026-06-06; branches resolved:

- **Q1 → "no"** (downgrade not intended). P1-COMPARE-GATE takes the
  **refusal branch**: gate call in `build_comparison_report`,
  `--explicit-exploratory` CLI flag, refusal-token test. Recorded as
  **D048** in `docs/DECISION_LOG.md`.
- **Q2 → "yes"** (graduation reachable now). P1-FIT-KIND lands
  `kind: Literal["analytical","cfd_in_loop"]` with `"analytical"` default
  on `StabilityFitRecord`. Recorded as **D049**.
- **Q3 → "fast"**. P0-GATE-ENFORCE installs the fast-subset pre-push hook
  (excludes browser/subprocess/CFD-fixture tests); the full 9-minute suite
  runs at striatum slice completion.
- **Q4 → targeted delete, executed 2026-06-06**: removed 129 phantom runs
  plus dependent rows (1,115 candidates / 5,388 metrics / 12,922
  artifacts) and vacuumed; `~/.local/share/kayakgen/index.sqlite` went
  6.5 MB → 80 KB with zero remaining rows (every row was a phantom). The
  P0-INDEX-ISOLATION operator action is done; the conftest fixture and
  regression test remain to land.

---

*Plan only. No source, test, config, or CI files were modified in
producing this document.*
