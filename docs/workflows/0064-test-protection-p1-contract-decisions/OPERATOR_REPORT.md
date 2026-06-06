# Operator Report — Workflow 0064: test-protection P1 contract decisions

date: 2026-06-06
run: run_f090c84339d75237140b6b6f9a681260
branch: `striatum/0064-test-protection-p1-contract-decisions`
review verdict: **accept, no findings** (`striatum/0064-test-protection-p1-contract-decisions/review/REVIEW.md`)

## What landed (slice stack, one commit per decision)

| slice | commit | summary |
|---|---|---|
| D048 / P1-COMPARE-GATE | `565a8cb494d352ed375f096dd23eb039d9f54b02` | `build_comparison_report` now calls `ensure_objectives_claim_admissible_for_search` (the frozen gate in `kayakgen/search/pareto.py` is called, never modified) after the existing RFC 0043 high-angle refusal. Claim-inadmissible objectives (`raw_unvalidated` / `uncalibrated_comparative`, e.g. `Rt_N_last:min`, `design_fitness:max`) refuse with the `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY` token unless the new keyword-only `explicit_exploratory=True` / CLI `--explicit-exploratory` opt-in is passed. **Refusal is not removal**: every prior auto-downgrade assertion (exploratory_frontier kind, accepted-use provenance, warnings, objective metadata) survives behind the opt-in in `tests/test_compare.py`; default conservative objectives (`GM0_m`, `displacement_error_kg`, `mesh_problem_count`) are byte-identical with no flag. Docs: USER_GUIDE compare section, ARCHITECTURE_MAP CLI-table row, LEDGER BUG-026 → fixed. |
| D049 / P1-FIT-KIND | `5a2278851705aeede21ffddf1e4bdcf49c287537` | `StabilityFitRecord` gains `kind: Literal["analytical", "cfd_in_loop"] = "analytical"` — additive with default, so existing fit JSONs parse unchanged (pinned by `test_kind_is_additive_legacy_fit_json_parses_as_analytical`) and the workflow-0063 fixture-digest pin is untouched (forbidden path, no branch diff). `tests/test_cfd_in_loop_evaluator_status.py` rewritten around real records from the `make_stability_acceptance_triple` conftest factory; `test_both_accepted_covering_fits_promote_to_first_class` is the BUG-001 kill shot — `first_class` graduation is now reachable with production records. Exactly one labeled SimpleNamespace shape-tolerance test remains. `kayakgen/services/generative_jobs.py` change is docstring-only. Docs: USER_GUIDE stage-4 fit bullet, LEDGER BUG-001 → fixed, CHANGELOG entry covering both slices. |
| draft artifact | `7795ac466cc61d3ec0fc0c10ceaa601e0b6b2324` | Published `striatum/0064-test-protection-p1-contract-decisions/DRAFT.md`. |

(Workflow scaffold: `ed651a82e241ad1841f5a91896182f7e8a6450fd`.)

The apply job changed no production code and no test code: the review
(reviewer-codex-001) accepted with zero must-fix findings, so
`CHANGELOG.md` needed no further update (the workflow 0064 entry landed
with slice 2) and the apply commit adds only this report, the published
summary artifact, and the reviewer's `REVIEW.md` (committed for
provenance, matching prior workflow directories).

## Decisions implemented

- **D048** (`docs/DECISION_LOG.md`, accepted 2026-06-06): compare takes
  the REFUSAL branch — the auto-downgrade to `exploratory_frontier`
  without opt-in was decided to be a contract violation of the
  RELEASE_DISCIPLINE no-claim invariant, not an intended exception.
  Implemented exactly as decided; the labeled-exploratory behavior
  survives behind `--explicit-exploratory`.
- **D049** (`docs/DECISION_LOG.md`, accepted 2026-06-06): the `kind`
  discriminator lands now (default `"analytical"`) rather than deferring
  to the RFC 0058 successor, making CFD-in-loop graduation reachable
  with real records.

## Final full gate (apply job, run-branch worktree, 2026-06-06)

`.venv/bin/python -m pytest -q` → exit 0:

```text
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1319 passed, 4 skipped, 1 warning in 517.97s (0:08:37)
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1. The single warning
is the pre-existing corrupt-store-repair `UserWarning` exercised by
`tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`
(workflow-0063 P1-STORE-ATOMIC repair path firing inside its own test).

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (the invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65` are pre-existing and
untouched by this workflow).

## Audit ledger rows closed

From `KAYAKGEN_TEST_COVERAGE_AUDIT_CLAUDE_OPUS_4_8_2026-06-06.md`:

- **R1 (SERIOUS)** — the one real mock-erasure: all eight graduation
  tests fed `SimpleNamespace(kind=...)` fakes while `StabilityFitRecord`
  had no `kind` field, leaving the `first_class` branch unreachable with
  production records and the green suite asserting the fake. Closed by
  D049: real factory-built records now drive the graduation suite and
  the audit's recommended counter-test (real record → intended
  graduation outcome) passes.
- **R2 (SERIOUS)** — the rarer inversion: a well-asserted suite that
  *counter-tested* the RELEASE_DISCIPLINE refusal invariant by pinning
  the opt-in-free downgrade as correct at the `build_comparison_report`
  entry point (while `active/runner.py` called the gate). Closed by
  D048: the audit's recommended probe (`build_comparison_report` with a
  raw metric and no opt-in → RFC 0044 refusal token) is now the pinned
  regression.

## Bug-ledger rows closed

- **BUG-001 (critical, 2026-05-29)** → fixed, citing D049 / this
  workflow.
- **BUG-026 (high, 2026-05-29)** → fixed, citing D048 / this workflow.

## What remains (routed per the remediation plan §6)

- **Workflow D — protection top-ups**: P2 test-only items
  (P2-HYDRO-ANCHOR, P2-CANCEL-DETERMINISTIC, P2-REGISTRY-MICROGAPS,
  P2-CLI-NEGATIVES, P2-MYPY-DECIDE, P2-REASON-ENUM), whenever idle;
  P2-CLI-NEGATIVES waits on the bug-hunt NaN family. With workflow 0064
  landed, the P0 and P1 tiers of the remediation plan are complete.

## Remaining operator action

**Merge the run branch to `main`**: the slice stack is left on
`striatum/0064-test-protection-p1-contract-decisions` per the apply
packet; merging is the operator's step after the run completes.
