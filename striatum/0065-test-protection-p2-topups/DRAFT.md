# Draft — Workflow 0065: test-protection P2 top-ups

author: author-claude-001
date: 2026-06-06
run: run_e06f2ba0dacd3251d26bdd7365a1575e
branch: striatum/0065-test-protection-p2-topups (worktree wt_ceade0656ef655fff1c9481f260291cf)

The five P2 items from the 2026-06-06 remediation plan §5, landed in
packet order, one commit per item. The batch is TEST-ONLY plus the
pyproject mypy removal: nothing under `kayakgen/` or `scripts/` was
touched, and the workflow-0063 canonical-digest pin test is
byte-identical (verified: the item-3 commit is additions-only — zero
deleted lines). No new test exposed a product bug, so there are **no
successor findings** to record from this batch.

## Item 1 — P2-HYDRO-ANCHOR (`5268757862c534711c757d1903c91699dd4747ac`)

```
 tests/test_hydrostatics.py | 76 ++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 76 insertions(+)
```

New test: `test_analytic_anchor_parabolic_body_volume_and_lcb`.

**Path taken:** closed-form external anchor (the item's primary path),
with the analytic body adjusted from the audit's wall-sided prism to a
body the parametrization can represent exactly — NOT the documented
fallback (tighter property pins), which was not needed.

**Why the wall-sided prism is not honestly reachable:**

1. The volume integrator (`_signed_volume` in
   `kayakgen/eval/hydrostatics.py`) is a divergence-theorem tetrahedron
   sum over the open hull shell. It is exact only when every boundary
   ring of the shell lies in a plane through the origin. The waterline
   ring (z = 0 plane) qualifies; a prism's full-area end rings at
   x = ±L/2 do not. With uniform distributions the shell stays open at
   the ends and the sum is off by exactly `A·L/3` — for a prism that is
   a 33% systematic error, so "as close to a prism as the loft allows"
   degenerates into measuring mesh-closure error, not hydrostatics.
   The body must taper to ~zero half-breadth at both ends.
2. No cross-section family is wall-sided: `hard_chine` floors deadrise
   at 8° (`max(deadrise_rad, radians(8.0))`), `shallow_v`/`deep_v`
   floor it at 5°/15°, and `round`/`shallow_arch` are curved by
   construction.

**The analytic body and derivation** (also in the test comment):

- Section (`round` family, deadrise 0): the sampler emits
  `y = b·t^(1/2)`, `z = -T + T·t` for `t ∈ [0,1]`, i.e. the parabola
  `z(y) = -T·(1 - (y/b)²)` with closed-form section area
  `A = ∫ T(1-(y/b)²) dy |_{-b}^{b} = (4/3)·b·T`.
- Plan (polynomial half-breadth): `b(ξ) = b0·(1-ξ²)·(1+cξ)`, `ξ = 2x/L`
  — parabolic taper to zero at both ends (closing the shell honestly)
  with linear fore-aft asymmetry `c` so LCB is a non-trivial closed form.
- With draft uniform `T`, odd powers of ξ vanish over [-1, 1]:

  ```
  V   = ∫ A(x) dx = (4/3)·T·(L/2)·b0·∫(1-ξ²)(1+cξ) dξ = (8/9)·b0·T·L
  x̄   = (L/2)·[∫ξ(1-ξ²)(1+cξ)dξ / ∫(1-ξ²)(1+cξ)dξ]
      = (L/2)·[(4c/15)/(4/3)] = (L/2)·(c/5)
  LCB = (x̄ + L/2)/L = 1/2 + c/10
  ```

- Parameters: L = 4.0 m, b0 = 0.25 m, T = 0.12 m, c = -0.3
  → V = 0.106667 m³, LCB = 0.47.

**Tolerance honesty:** rtol = 1e-2 per the plan ("coarse"). Measured
discretization error at the default 150×40 mesh: volume 1.48e-3
(mesh 0.1065088 vs analytic 0.1066667 — piecewise-linear loft under a
curved surface), LCB 1.0e-6 (mesh 0.4699995 vs 0.47). >6× margin on the
binding metric while still catching integrator-level errors (e.g. the
`A·L/3` open-boundary class above). This is the file's first pin whose
expected value was derived independently of the code under test.

## Item 2 — P2-CANCEL-DETERMINISTIC (`891c3c8314eabd4475dbce8f5f0e3f817bec887f`)

```
 tests/test_generative_jobs_subprocess.py | 83 ++++++++++++++++++++++++++++----
 1 file changed, 74 insertions(+), 9 deletions(-)
```

New test:
`test_subprocess_manager_cancel_deterministic_with_controlled_runner` —
now the owner of the manager cancel contract, running unconditionally in
the default suite.

**Mechanism (deterministic-cancel evidence):** a monkeypatch cannot
cross a real process boundary, so the test reroutes the manager's
`_spawn` to invoke the real runner entry-point
(`generative_jobs_runner._run`) in-process, with
`kayakgen.search.sweep.run_sweep` replaced by the existing
`_controlled_cancel_runner`. `manager.cancel` touches the flag **before**
the runner body executes, so `_controlled_cancel_runner`'s
`assert progress_sink.should_cancel() is True` proves the cancel was
observed mid-flight — no poll loop, no sleep, no race. Asserted
unconditionally: terminal `state == "resumable"`,
`error.kind == "cancelled_by_operator"`,
`cancellation_requested_at is not None`,
`resumable_from_checkpoint is True`,
`progress.realized_evaluations == 1`, and the cancel flag cleaned up on
terminal write. What this intentionally bypasses — the real `Popen`
spawn — remains covered by the smoke and crash-survival tests.

**Demotions:** `test_subprocess_manager_cancel_via_flag` keeps its
disjunctive final assertion but is now docstring-labeled integration
SMOKE with a do-not-tighten note pointing at the deterministic owner.
`test_subprocess_manager_resume_after_cancel` no longer has its
mid-race `pytest.skip`: it now branches on the race outcome and asserts
both sides (cancel won → resume must complete; sweep won →
`state == "succeeded"`), so it always reaches a real assertion. The two
`pytest.skip`s in `test_subprocess_manager_crash_survival` concern
SIGKILL timing, not the cancel contract, and were left as-is.

## Item 3 — P2-REGISTRY-MICROGAPS (`7ad325635f681ddc2d553e22888fc1a41399f055`)

```
 tests/test_stability_fit_registry.py | 79 ++++++++++++++++++++++++++++++++++++
 1 file changed, 79 insertions(+)
```

Exactly three tests (the micro-gap test names):

1. `test_multi_fixture_fit_loads_when_only_second_fixture_clears_chain`
   — 2-fixture fit; first cited fixture fails gate 4 (manifest staged,
   promotion packet missing), second clears the full chain; the fit
   loads with no diagnostics. Pins the ANY-pass loop of
   `_evaluate_fit_gates`.
2. `test_gate_loose_hysteresis_bound` — `bound_fraction=0.031`
   (schema-valid: observed max 0.018 stays below it) exceeds
   `OPERATOR_MAX_HYSTERESIS_BOUND_FRACTION` (0.03) →
   `REASON_FIXTURE_BOUNDS_TOO_LOOSE`, with the diagnostic detail
   asserted to contain "hysteresis" so the test pins the second branch
   of gate 3a specifically (not the drift branch).
3. `test_gate_touching_heel_range_is_intended_pass` — fit `(30, 60)` vs
   fixture `(0, 30)` touch at exactly 30°; pins the `<=` overlap
   boundary of gate 9 as intended-pass (tightening to strict `<` must
   fail this test and go through review).

The commit is additions-only (0 deletions);
`test_fixture_canonical_sha256_pinned_to_literal_digest` (workflow
0063) is byte-identical.

## Item 4 — P2-REASON-ENUM (`5069c2673a0a1cf07f02c5c3fcf1662a086edf62`)

```
 tests/test_stability_fit_registry.py | 38 +++++++++++++++++++-----------------
 1 file changed, 20 insertions(+), 18 deletions(-)
```

**Derivation:** `test_every_reason_has_a_next_action` now computes

```python
emitted = {
    value
    for name, value in vars(reg).items()
    if name.startswith("REASON_") and name != "REASON_NEXT_ACTION"
}
```

and asserts `emitted - set(reg.REASON_NEXT_ACTION)` is empty, naming any
missing codes. A floor assertion (`len(emitted) >= 16`, today's count)
prevents the derivation from silently asserting over an empty set after
a refactor. Side benefit: the derived set covers
`REASON_FIT_RECORD_UNREADABLE`, which the old hand-enumerated list
omitted. Acceptance verified live: injecting a dummy
`REASON_DUMMY_NEW_GATE = "dummy_new_gate"` into the module namespace
fails the test with
`REASON_* constants without REASON_NEXT_ACTION remediation copy: ['dummy_new_gate']`.

## Item 5 — P2-MYPY-DECIDE (`6095b4863fcf23090f9f6a522daa7011cf21d055`)

```
 CHANGELOG.md   | 18 ++++++++++++++++++
 pyproject.toml |  1 -
 2 files changed, 18 insertions(+), 1 deletion(-)
```

Took the plan's recommended branch: removed `mypy>=1.10` from the
`[dev]` optional-dependency extras; **no** `[tool.mypy]` config added.
Rationale (recorded in CHANGELOG): never configured, never part of the
documented gate stack (`pytest -q` + `ruff check`), never run in any
recorded gate — the extras line implied a type gate that does not
exist. `grep -rn mypy pyproject.toml requirements-dev.txt` is now
empty. The CHANGELOG entry also records the workflow-0065 disposition,
including the explicit deferral of P2-CLI-NEGATIVES to the bug-hunt
NaN-validator family (plan §5/§6 — deliberately not in this workflow).

## Slice gate (after item 5)

`/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q` from the
worktree root (the venv resolves `kayakgen` and `tests` from the
worktree cwd), exit code 0, tail:

```
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; ...
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; ...
1324 passed, 4 skipped, 1 warning in 524.61s (0:08:44)
pytest exit: 0
```

0 failed; exactly the 4 documented OpenFOAM env-gate skips
(`test_cfd_run_stages.py` ×2, `test_openfoam_v2512_smoke.py` ×2).
Collection verified against the branch base: 61a88b1 collects 1323
tests, this HEAD collects 1328 — exactly the 5 added by this batch
(1328 = 1324 passed + 4 skipped). The single warning is the
workflow-0063 store-repair
`UserWarning` deliberately exercised by
`test_openfoam_rerun_ignores_stale_force_dat_and_raw_result` —
pre-existing, not introduced here.

`ruff check kayakgen tests` → `All checks passed!`, exit 0. (Six
pre-existing invalid-`# noqa` *warnings* in
`kayakgen/ui/web/generate_frontier_view.py` are outside this batch's
write scope and do not affect the exit code; noted for a possible
successor cleanup.)

## Cumulative diffstat (5 commits on top of `61a88b1`)

```
 CHANGELOG.md                             |  18 +++++
 pyproject.toml                           |   1 -
 tests/test_generative_jobs_subprocess.py |  83 +++++++++++++++++++---
 tests/test_hydrostatics.py               |  76 ++++++++++++++++++++
 tests/test_stability_fit_registry.py     | 117 ++++++++++++++++++++++++++-----
 5 files changed, 267 insertions(+), 28 deletions(-)
```

Commits, in packet order:

| item | commit | subject |
|---|---|---|
| 1 | `5268757` | P2-HYDRO-ANCHOR: analytic closed-form anchor for volume and LCB (audit R7) |
| 2 | `891c3c8` | P2-CANCEL-DETERMINISTIC: manager-level cancel runs unconditionally (audit R8) |
| 3 | `7ad3256` | P2-REGISTRY-MICROGAPS: pin the three unpinned gate branches (audit R10) |
| 4 | `5069c26` | P2-REASON-ENUM: derive the reason-code set from the module namespace |
| 5 | `6095b48` | P2-MYPY-DECIDE: remove vestigial mypy from [dev] extras (audit §3 note) |

## Notes for the reviewer

- Write scope respected: only the three named test files,
  `pyproject.toml`, `CHANGELOG.md`, and this artifact directory were
  touched. `kayakgen/`, `scripts/`, and the boundary tests are
  untouched (cumulative diffstat above is exhaustive).
- The deterministic cancel test monkeypatches a private manager method
  (`_spawn`) on the instance. This follows the file's existing pattern
  of reaching into `manager._processes` for crash simulation; the
  alternative (a public injection seam on the manager) would be product
  code, which is out of scope for this batch.
- Item 1 asserts two metrics (volume, LCB) in one test rather than the
  one-assertion-per-test house preference, mirroring the audit row
  ("volume/LCB ... vs closed-form") — both bind to the same analytic
  body and fail independently under `assert_allclose`.
