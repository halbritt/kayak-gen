---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: reviewer-ops-tests-codex-gpt-5.5-001
schema_version: striatum.finding.v1
kind: finding
logical_name: review
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_56ed3ffa1327464aacb50db0628df476
job: job_run_c6989300a86c4c6cb66e44555bb19067_review_ops_tests
lease: lease_931a6f18908e43a0b78420e27346db9d
date: 2026-05-14

# Ops And Tests Review - Workflow 0051 Stage 1

## Verdict

`accept_with_findings`

The combined workflow 0051 patch set is broadly testable and deterministic:
the full suite passes, compileall is clean, and whitespace checks are clean.
The implementation lanes also exercised focused suites for web UI, CFD jobs,
solver readiness, comparison metadata, calibration packets, and stability.

I found one concrete OpenFOAM repeat-run failure mode that should be remediated
before final acceptance. I also agree with the contract compatibility gap
around `GeneratedBodyGZCurve` serialization because it affects API stability,
although the current CLI and sweep paths do not expose that payload yet.

## Validation Run

- `python -m pytest -q` - 382 passed in 114.89s.
- `git diff --check` - passed.
- `python -m compileall -q kayakgen tests` - passed.
- `ruff` was not available in this environment; multiple implementation
  summaries also recorded that `ruff` / `python -m ruff` could not run.

## Findings

### F1 - OpenFOAM reruns can parse stale `force.dat` from a previous run

**Severity:** high

**Where:** `kayakgen/eval/cfd/jobs.py:932-1005`, `kayakgen/eval/cfd/jobs.py:1095-1147`.

`OpenFoamLocalAdapter.prepare()` rewrites the deterministic case inputs but
does not remove prior solver outputs under `case/openfoam/postProcessing/` or
the prior `openfoam-raw-result.json`. `OpenFoamLocalAdapter.run()` then treats
any existing `case/openfoam/postProcessing/forces/0/force.dat` as the current
run's output after a zero-exit command.

I reproduced this by running one fake OpenFOAM command that writes a valid
`force.dat`, then editing the same prepared job's `profile.json` to a zero-exit
command that writes no force output, then running the same job again. The
second run still returned `error_kind="solver_success_blocked"`,
`output_manifest="openfoam-raw-result.json"`, and the old `drag_force_n=3.5`
instead of `missing_output`.

This is still a failed run, so it does not create a real `succeeded` path, but
it does persist stale raw drag data and an incorrect failure mode. That weakens
the new adapter's failure-state determinism and will become more dangerous
when a real OpenFOAM success path is eventually enabled.

**Suggested remediation:** before invoking the OpenFOAM command, remove or
quarantine expected output artifacts for this run (`postProcessing/forces/**`
and `openfoam-raw-result.json`), or record an execution token and require the
parsed artifact to be created after the current command starts. Add a rerun
test that first creates parser-readable output, then reruns with a clean
zero-exit/no-output command and expects `missing_output`.

### F2 - Generated-body GZ metadata is not compatible with the canonical `GZCurve`

**Severity:** medium

**Where:** `kayakgen/eval/stability.py:112-137`, `kayakgen/eval/contract.py:109-137`,
`tests/test_stability.py:331-348`.

`evaluate_gz_curve()` can now return a `GeneratedBodyGZCurve` with
`method="fixed_trim_generated_body_v1"` plus `heel_point_metadata`,
`summary_semantics`, and `result_semantics`. The canonical `GZCurve` model
still allows only `method="generated_body_handoff" | "fixture_only_math"` and
forbids extra fields. The new test explicitly asserts that
`GZCurve.model_validate(result.model_dump())` raises `ValidationError`.

That means the new direct evaluator surface is not round-trippable through the
public stability contract. Current CLI and sweep paths still serialize
`gz_curve=None`, so this is not breaking a user-facing command today, but it is
an API compatibility problem for the v1 high-angle evaluator.

**Suggested remediation:** move the additive metadata fields and method value
into `kayakgen/eval/contract.py::GZCurve` or widen the canonical stability
result type so the generated-body payload can round-trip without dropping or
rejecting the per-heel metadata.

### F3 - Web CFD status copy is now stale for non-fixture profiles

**Severity:** low

**Where:** `kayakgen/ui/web/controllers.py:928-935`,
`kayakgen/eval/cfd/jobs.py:486-514`.

`cfd_status_lines_from_payload()` always includes
`fixture-local-command is a deterministic checked-in test adapter, not real CFD.`
The same workflow now exposes `openfoam-v2512-interfoam-local` through the
built-in profile list. For OpenFOAM jobs, the web status panel still displays a
fixture-local-command line, which is misleading operationally even though the
raw/unvalidated warnings remain correct.

**Suggested remediation:** make that line conditional on the selected solver
profile, or replace it with profile-neutral local-dispatch copy and add a web
read-model test for an OpenFOAM payload.

## Coverage Notes

- CFD job tests cover profile registration, readiness rejection, dependency
  unavailable, version mismatch, command failure, timeout, missing output,
  malformed output, parser-readable fake output blocked from `succeeded`, raw
  parser fixtures, and claim-promotion rejection.
- Solver-readiness tests cover open-surface packages, generated-body evidence
  without volume mesh, fixture handoff with boundary metadata, and synthetic
  evidence rejection.
- Comparison tests cover conservative default objectives, explicit raw
  resistance warnings, accepted-use gates, design-fitness rejection, and
  unsupported objective metadata.
- Web tests cover schema aliases, export-row consolidation, the disabled mesh
  package label, and browser same-seed preset behavior.
- Stability tests cover gate failures, fixture-only math, strict heel-grid
  validation, generated-body computed results, and per-heel metadata on the
  direct evaluator surface.

## Non-Findings

- No required test was skipped without justification in the implementation
  summaries I reviewed. The only repeatedly skipped tool was `ruff`, and every
  relevant summary records it as unavailable.
- `git diff --check` and `compileall` pass on the combined worktree.
- The OpenFOAM skeleton does not enable a real `succeeded` path; parser-readable
  fake output is persisted as `failed` with `solver_success_blocked`.
- Default comparison objectives remain conservative and exclude raw resistance.
- Runtime `SourceUse` values still exclude `rejected`; rejected source reviews
  remain review-only.
