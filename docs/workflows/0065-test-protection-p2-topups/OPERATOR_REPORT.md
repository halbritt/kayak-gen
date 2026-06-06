# Operator Report — Workflow 0065: test-protection P2 top-ups

date: 2026-06-06
run: run_e06f2ba0dacd3251d26bdd7365a1575e
branch: `striatum/0065-test-protection-p2-topups`
review verdict: **accept, no findings** (`striatum/0065-test-protection-p2-topups/review/REVIEW.md`)

## What landed (slice stack, one commit per item)

| item | commit | summary |
|---|---|---|
| P2-HYDRO-ANCHOR | `5268757862c534711c757d1903c91699dd4747ac` | `test_analytic_anchor_parabolic_body_volume_and_lcb` — the file's first pin whose expected value was derived independently of the code under test. Closed-form external anchor on a `distribution_v2` `round`-family parabolic body (`A = (4/3)·b·T`; `b(ξ) = b0·(1-ξ²)·(1+cξ)` → `V = (8/9)·b0·T·L`, `LCB = 1/2 + c/10`), with the full derivation in the test comment. The audit's wall-sided prism is not honestly reachable (divergence-theorem integrator needs end rings that taper to ~zero; no section family is wall-sided — deadrise floors at 5–15°), so the analytic body was adjusted rather than taking the tighter-property-pins fallback. rtol 1e-2 with measured discretization error 1.48e-3 on the binding metric (>6× margin). |
| P2-CANCEL-DETERMINISTIC | `891c3c8314eabd4475dbce8f5f0e3f817bec887f` | `test_subprocess_manager_cancel_deterministic_with_controlled_runner` now owns the manager cancel contract, unconditionally in the default suite: reroutes `_spawn` to the real runner entry-point in-process with the existing `_controlled_cancel_runner`, creates the cancel flag before the runner body executes, and asserts the full terminal contract (`resumable`, `cancelled_by_operator`, `cancellation_requested_at`, `resumable_from_checkpoint`, flag cleanup) with no poll/sleep/race. The racy real-subprocess variants are demoted to labeled integration smoke (not deleted); the resume-after-cancel mid-race `pytest.skip` raceout is replaced by branch-on-outcome assertions on both sides. |
| P2-REGISTRY-MICROGAPS | `7ad325635f681ddc2d553e22888fc1a41399f055` | Exactly three tests pinning the last unpinned branches of the 13-gate registry surface: `test_multi_fixture_fit_loads_when_only_second_fixture_clears_chain` (ANY-pass loop of `_evaluate_fit_gates`), `test_gate_loose_hysteresis_bound` (gate 3a second branch, `bound_fraction=0.031` vs operator max 0.03, diagnostic asserted to name "hysteresis"), `test_gate_touching_heel_range_is_intended_pass` (gate 9 `<=` overlap boundary pinned as intended-pass). Additions-only commit (0 deletions); the workflow-0063 digest pin is byte-identical. |
| P2-REASON-ENUM | `5069c2673a0a1cf07f02c5c3fcf1662a086edf62` | `test_every_reason_has_a_next_action` derives its expected set from the module namespace (`vars(reg)`, names starting `REASON_` minus `REASON_NEXT_ACTION`) with a `len(emitted) >= 16` floor so a refactor cannot leave it asserting over an empty set. Side benefit: now covers `REASON_FIT_RECORD_UNREADABLE`, which the hand-enumerated list omitted. Acceptance verified live: an injected dummy `REASON_` constant fails the test by name. |
| P2-MYPY-DECIDE | `6095b4863fcf23090f9f6a522daa7011cf21d055` | Took the plan's recommended branch: `mypy>=1.10` removed from `[project.optional-dependencies].dev`; no `[tool.mypy]` config added. It was never configured, never part of the documented gate stack (`pytest -q` + `ruff check`), never run in any recorded gate — the extras line implied a type gate that does not exist. CHANGELOG records the rationale; adopting mypy later is a deliberate decision (config + gate wiring), not an extras line. |
| draft artifact | `8a949a4ea2f100c04bf70076d8c611d839967e42` | Published `striatum/0065-test-protection-p2-topups/DRAFT.md`. |

(Workflow scaffold: `61a88b1556f42ad1dce161e45e8e4ff85003ae2a`.)

The batch is TEST-ONLY plus the pyproject mypy removal: nothing under
`kayakgen/` or `scripts/` was touched, and no new test exposed a product
bug, so there are no successor findings from this workflow. The review
(reviewer-codex-001) accepted with zero must-fix findings, so the apply
job changed no test code and `CHANGELOG.md` needed no further update
(the workflow 0065 entry landed with the P2-MYPY-DECIDE slice); the
apply commit adds only this report, the published summary artifact, and
the reviewer's `REVIEW.md` (committed for provenance, matching prior
workflow directories).

## Final full gate (apply job, run-branch worktree, 2026-06-06)

`.venv/bin/python -m pytest -q` → exit 0:

```text
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1324 passed, 4 skipped, 1 warning in 520.14s (0:08:40)
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1. The single warning
is the pre-existing workflow-0063 corrupt-store-repair `UserWarning`
deliberately exercised by
`tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`.

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (the invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65` are pre-existing and
untouched by this workflow).

## Audit rows closed by this workflow

From `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md`:

- **R7 (SERIOUS)** — every hydrostatics number was pinned only against
  itself. Closed: one external closed-form anchor (volume + LCB) now
  converts the golden pins from "unchanged" to "unchanged and plausibly
  right" — these numbers are GA fitness inputs on the north-star path.
- **R8 (SERIOUS)** — on a fast machine the cancel integration path
  could stay green for months without ever executing. Closed: the
  deterministic manager-level test runs the cancel contract
  unconditionally; the racy variants are labeled smoke.
- **R10 (MINOR)** — the registry's only unpinned branches (ANY-pass,
  hysteresis bound, touching heel-range). Closed: three named tests;
  multi-fixture semantics now documented by test.
- **§5 note** — hand-enumerated reason set let a future gate constant
  ship without operator remediation copy. Closed: namespace-derived set
  with a count floor.
- **§3 note** — vestigial `mypy` in `[dev]` extras implied a type gate
  that does not exist. Closed: removed, rationale in CHANGELOG.

## REMEDIATION PLAN CLOSE-OUT

Final disposition of every item in
`KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md`.
With this workflow, every scheduled tier of the plan is closed: P0 via
workflow 0062, P1 via workflows 0063/0064 (decisions D048/D049), P2 via
this run, with one explicitly contingent deferral (P2-CLI-NEGATIVES)
and the four §7 items deliberately not scheduled.

| plan item | tier | disposition |
|---|---|---|
| P0-BOUNDARY-FIX | P0 | **Landed** — workflow 0062, `f8555c3244bad32f897cef35f3e924d0ac322b9c`. Row registry moved to `kayakgen/metadata/`; `test_services_does_not_import_ui_or_cli[path2]` green again (red since 2026-05-25). |
| P0-INDEX-ISOLATION | P0 | **Landed** — workflow 0062, `63ee198a34b4464b4c978a165ed3707a9d0de201`. Two-layer autouse conftest isolation of `KAYAKGEN_INDEX_DB`; operator purged the 129 phantom rows the same day (plan §8 Q4). |
| P0-GATE-ENFORCE | P0 | **Landed** — workflow 0062, `fbfdf9e5926556b487d9e28ec154a734875902b2`. `scripts/fast-gate.sh` + `scripts/install-hooks.sh` (fast subset per Q3); full suite is the striatum slice-completion gate; RELEASE_DISCIPLINE gate 1 updated. Hook install remains a once-per-clone operator action. |
| P1-FIT-KIND-DECISION | P1 | **Landed** — decision D049 (2026-06-06), implemented in workflow 0064, `5a2278851705aeede21ffddf1e4bdcf49c287537`. `kind` discriminator with `"analytical"` default; graduation reachable with real records; BUG-001 closed. |
| P1-COMPARE-GATE | P1 | **Landed** — decision D048 (2026-06-06), implemented in workflow 0064, `565a8cb494d352ed375f096dd23eb039d9f54b02`. Refusal branch with `--explicit-exploratory` opt-in; BUG-026 closed. |
| P1-STORE-ATOMIC | P1 | **Landed** — workflow 0063, `347f7064da8ca856f6dc09a27c658b61a0f32bca`. Temp-sibling + `os.replace` writes; corrupt-occupant repair on the dedupe branch; same pattern + utf-8 in `kayakgen/io/json.py`. |
| P1-SQLITE-VERSION | P1 | **Landed** — workflow 0063, `83ad15bc92e15473f5b8d5eb9b07778cdd514538`. `PRAGMA user_version` stamp; rebuild-not-migrate with `UserWarning` for stale DBs. |
| P1-SHA-PIN | P1 | **Landed** — workflow 0063, `77be4e53e71941bb31773a35b910ada9c8bda089`. `fixture_canonical_sha256` pinned to its literal digest; a mismatch is an evaluator-version event, never a test update. |
| P1-SKIP-PIN | P1 | **Closed via 0062's R4 wording pin** — `docs/RELEASE_DISCIPLINE.md` gate 1 now requires "green, with only the documented OpenFOAM opt-in skips (expected: 4)"; any other skip count does not count as a gate, and every workflow gate report since pins the count explicitly. The plan's separate skip-ceiling script check was not implemented as code; the audit row (R4) was recorded closed in the 0062 operator report on the wording + full-gate reporting basis. If a second gate machine ever appears, the script-level ceiling becomes worth landing. |
| P2-HYDRO-ANCHOR | P2 | **Landed** — this run, `5268757862c534711c757d1903c91699dd4747ac` (audit R7). |
| P2-CANCEL-DETERMINISTIC | P2 | **Landed** — this run, `891c3c8314eabd4475dbce8f5f0e3f817bec887f` (audit R8). |
| P2-REGISTRY-MICROGAPS | P2 | **Landed** — this run, `7ad325635f681ddc2d553e22888fc1a41399f055` (audit R10). |
| P2-REASON-ENUM | P2 | **Landed** — this run, `5069c2673a0a1cf07f02c5c3fcf1662a086edf62` (audit §5 note). |
| P2-MYPY-DECIDE | P2 | **Landed** — this run, `6095b4863fcf23090f9f6a522daa7011cf21d055` (audit §3 note; removal branch). |
| P2-CLI-NEGATIVES | P2 | **Deferred, contingent** — waits on the operator green-lighting the bug-hunt NaN-validator family remediation (BUG-073..077; plan §5/§6). Deliberately NOT done piecemeal here: the parametrized CLI negatives land together with the pydantic/typer validators that make them pass, as one sweep. |
| §7 — R11 absolute-path evidence rejection | deferred | **Unchanged, deferred indefinitely** — operator-authored manifests on the operator's machine; becomes P1 when externally-authored fixture files arrive (D006/D007 campaign). |
| §7 — manager-level concurrency tests | deferred | **Unchanged, deferred indefinitely** — two simultaneous generative jobs against one `jobs_root` is not an operator workflow today; SIGKILL/reconciliation coverage protects the realistic failure. |
| §7 — sqlite `database is locked` race tests | deferred | **Unchanged, deferred indefinitely** — single operator, single writer once tests are isolated (P0-INDEX-ISOLATION landed). |
| §7 — coverage tooling adoption | deferred | **Unchanged, deferred indefinitely** — failure modes here are contract drift, not unexercised lines; a coverage floor adds gate cost and percentage worship. |

Operator actions from the plan, for completeness: the one-time index-DB
purge was executed 2026-06-06 (plan §8 Q4; 6.5 MB → 80 KB, every row a
phantom); installing the pre-push hook is per-clone state
(`scripts/install-hooks.sh`) and not a workflow deliverable.

## Remaining operator action

**Merge the run branch to `main`**: the slice stack is left on
`striatum/0065-test-protection-p2-topups` per the apply packet; merging
is the operator's step after the run completes.
