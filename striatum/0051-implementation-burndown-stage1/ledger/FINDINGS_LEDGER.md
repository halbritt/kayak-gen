---
schema_version: "striatum.findings_ledger.v1"
artifact_kind: "findings_ledger"
summary_count: 4
---

author: findings-ledger-codex-gpt-5.5-001
schema_version: striatum.findings_ledger.v1
kind: findings_ledger
logical_name: findings_ledger
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_983b7767d6464e1890ec4834ced04a5f
job: job_run_c6989300a86c4c6cb66e44555bb19067_findings_ledger
lease: lease_f3824937dde14f9bad33f7afcec9cfbe
date: 2026-05-14

# Findings Ledger - Workflow 0051 Stage 1

## Ledger Verdict

`accept_with_must_fix_findings`

The three review artifacts support two must-fix remediation items before final
acceptance, two non-blocking successor/bookkeeping findings, and several
accepted concerns that require no action in this workflow. This ledger does
not add new design scope; every item below is grounded in the review artifacts.

## Must-Fix Remediation Items

### MF1 - OpenFOAM reruns can parse stale raw output from a previous run

**Source finding:** Ops/tests review F1
(`striatum/0051-implementation-burndown-stage1/reviews/ops_tests/REVIEW.md:43-72`).

**Severity:** high.

**Affected paths:** `kayakgen/eval/cfd/jobs.py`,
`tests/test_cfd_jobs.py`.

**Deduplicated issue:** `OpenFoamLocalAdapter.prepare()` rewrites deterministic
case inputs but leaves previous `case/openfoam/postProcessing/forces/**` output
and `openfoam-raw-result.json` in place. A subsequent zero-exit fake command
that writes no new `force.dat` can still parse the prior run's force file and
persist stale raw drag data with the wrong failure mode.

**Required remediation:** Before each OpenFOAM command run, clear or quarantine
expected per-run OpenFOAM raw outputs, including `postProcessing/forces/**` and
`openfoam-raw-result.json`, or add equivalent freshness evidence that rejects
pre-existing artifacts. Add a regression test that first creates parser-readable
OpenFOAM output, then reruns the same prepared job with a zero-exit/no-output
command and expects `missing_output`, not `solver_success_blocked` with stale
drag data.

**Boundary to preserve:** Do not enable a real OpenFOAM `succeeded` path. The
fake parser-readable path must remain failed/raw-unvalidated unless a later
accepted workflow supplies the required mesh and solver evidence.

### MF2 - Generated-body GZ metadata does not round-trip through the canonical contract

**Source findings:** Ops/tests review F2
(`striatum/0051-implementation-burndown-stage1/reviews/ops_tests/REVIEW.md:74-96`)
and traceability review F1
(`striatum/0051-implementation-burndown-stage1/reviews/traceability/REVIEW.md:71-81`).

**Severity:** medium, but must-fix for this workflow because both reviews
identify the same contract-boundary gap and the remediation lane has
`kayakgen/eval/` plus `tests/` write scope.

**Affected paths:** `kayakgen/eval/contract.py`,
`kayakgen/eval/stability.py`, `tests/test_stability.py`.

**Deduplicated issue:** `evaluate_gz_curve()` can return a
`GeneratedBodyGZCurve` containing `method="fixed_trim_generated_body_v1"`,
`heel_point_metadata`, `summary_semantics`, and `result_semantics`, but the
canonical `GZCurve` in `kayakgen/eval/contract.py` still forbids those fields
and method value. The current test pins that
`GZCurve.model_validate(result.model_dump())` raises `ValidationError`, so the
new RFC 0043/D007 per-heel metadata is available only to direct evaluator
callers and cannot flow through `StabilityResult.gz_curve`.

**Required remediation:** Make the canonical stability contract accept the
generated-body v1 payload without accepting arbitrary unknown keys. Acceptable
fixes include lifting the additive fields and method value into
`kayakgen/eval/contract.py::GZCurve`, or widening the canonical
`StabilityResult.gz_curve` type to accept the generated-body subtype. Replace
the current rejection-pinning test with a round-trip compatibility test that
proves the generated-body metadata survives canonical model validation.

**Boundary to preserve:** Keep RFC 0024 generated-body evidence gates,
fixture-only labeling, and no-safety/no-seaworthiness/no-capsize/no-design-
fitness warnings intact. This is a serialization/contract fix, not permission
to surface unsupported high-angle values where gates fail.

## Non-Blocking Successor Or Bookkeeping Items

### NB1 - Web CFD status copy is stale for non-fixture solver profiles

**Source finding:** Ops/tests review F3
(`striatum/0051-implementation-burndown-stage1/reviews/ops_tests/REVIEW.md:98-114`).

**Severity:** low.

**Affected paths:** `kayakgen/ui/web/controllers.py`,
`kayakgen/eval/cfd/jobs.py`, web read-model tests.

**Disposition:** Non-blocking successor cleanup. The raw/unvalidated warnings
remain correct, and the claims review found no overclaiming, but the status
panel currently emits fixture-local-command-specific copy even for the new
`openfoam-v2512-interfoam-local` profile. A later cleanup should make the line
profile-conditional or profile-neutral and add a web read-model test for an
OpenFOAM payload.

### NB2 - Decision log does not explicitly record the RFC 0009 status reconciliation event

**Source finding:** Traceability review F2
(`striatum/0051-implementation-burndown-stage1/reviews/traceability/REVIEW.md:83-91`).

**Severity:** low.

**Affected paths:** `docs/DECISION_LOG.md` for a future durable entry;
`OPERATOR_REPORT.md` or
`docs/workflows/0051-implementation-burndown-stage1/OPERATOR_REPORT.md` for
run-local bookkeeping if desired.

**Disposition:** Non-blocking bookkeeping item. The RFC index, RFC 0009 body,
roadmap, and user guide already carry the reconciled status, and D010 records
the underlying sweep/search admissibility decision. The remediation lane cannot
edit `docs/DECISION_LOG.md`; it may optionally note the D010/RFC 0009
reconciliation in an operator report while updating workflow status. A future
docs workflow can add a durable decision-log row or note if the project wants a
separate receipt.

## Accepted Concerns Requiring No Action

- **Claims review:** Accepted with no blocking findings. The review explicitly
  found that all seven implementation patches preserved no-claims boundaries
  for resistance, CFD output, solver readiness, high-angle stability,
  safety/seaworthiness, hosting, and design fitness
  (`striatum/0051-implementation-burndown-stage1/reviews/claims/REVIEW.md:20-32`).
- **Traceability review non-findings:** No forbidden capability wording was
  introduced; `solver_success_blocked` preserves the no-real-succeeded boundary;
  `SourceUse` still excludes `rejected`; default objectives still exclude raw
  resistance and `design_fitness`; web schema work preserves `/api/*` payload
  shapes; and RFC 0036's same-seed path was pinned by browser coverage
  (`striatum/0051-implementation-burndown-stage1/reviews/traceability/REVIEW.md:93-100`).
- **Ops/tests review validation and non-findings:** The full suite passed
  during review, `git diff --check` and `compileall` were clean, and `ruff`
  absence was recorded as an environment limitation rather than a product
  finding (`striatum/0051-implementation-burndown-stage1/reviews/ops_tests/REVIEW.md:33-39`,
  `striatum/0051-implementation-burndown-stage1/reviews/ops_tests/REVIEW.md:134-144`).

## Deduplication Notes

- Ops/tests F2 and traceability F1 are the same contract issue and should be
  remediated once as MF2.
- Claims-review observations are acceptance evidence, not separate findings.
- NB1 and NB2 remain visible, but neither should expand the remediation lane
  into new solver capability, public hosting, calibrated output, stability
  validation, desktop parity, or optimizer/search scope.
