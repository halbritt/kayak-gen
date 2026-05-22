# Remediation Plan — 2026-05-22 code+doc audit

Date: 2026-05-22
Workflow shape: `code_doc_audit` (proposed in RFC 0059)
Audit run: `docs/audits/2026-05-22-code-doc-audit/`

## Plan shape

Findings grouped into nine remediation batches (R1-R9). Each batch names the
owner surface, the touched files, the gating tests / discipline checks, and
the follow-up classification from `RFC 0059 §4`.

The high-severity batches R1 and R3 are driven by this audit run. R2, R4-R9
become individual TODO entries or scoped follow-up workflows.

## R1 — Discipline-checklist catch-up for RFC 0057 stage 4 + RFC 0058 stages 2-3

Severity: high
Findings: AUD-D-001, AUD-D-002, AUD-O-001, AUD-O-002, AUD-O-007 (the
related docs-only slice)
Owner surface: documentation only
Touched files:
- `docs/ARCHITECTURE_MAP.md` — bump date, add `runs jobs`, add the four
  `stability` subcommands.
- `docs/USER_GUIDE.md` — add `#### Stability fixtures (RFC 0058)`
  subsection; add `#### mesh-evidence (RFC 0045)` subsection; document the
  RFC 0046 three-mechanism opt-in under `### cfd prepare` and in the
  env-var section; add one sentence about D040's legacy routing shim.
- `docs/rfcs/README.md` — add RFC 0059 row (this audit's source RFC).
- `CHANGELOG.md` — `### Changed` and `### Added` entries naming the audit
  run and the doc surfaces touched.
Gating: none — docs only. Re-verify the changed sections render cleanly in
the local markdown preview (`grep "^##" docs/USER_GUIDE.md`).
Follow-up classification: docs-only correction.
Status: **landed in the same change as this remediation plan** (audit run
+ Step-2 workflow scaffold + Step-4 dogfood close together per RFC 0059
Implementation Path).

## R2 — Glossary + vocab-coverage regression net for RFC 0057/0058 aggregates

Severity: medium-high (combines AUD-D-003 + AUD-P-003 + AUD-P-004)
Findings: AUD-D-003, AUD-P-003, AUD-P-004
Owner surface: docs + tests
Touched files:
- `docs/UBIQUITOUS_LANGUAGE.md` — add entries for `GenerativeJob`,
  `StabilityFitRecord`, `StabilityFixturePromotionPacket`,
  `MeasuredStabilityFixture`, `cfd_in_loop_evaluator_status`,
  `AnalyticalClaimLabel`.
- `tests/test_vocabulary_coverage.py` — extend `_DECISION_TOKENS` (or add a
  new parametric list) with the same terms; add a small test for the
  documented `kayakgen runs jobs --state` vocabulary.
Gating: `pytest tests/test_vocabulary_coverage.py -q`.
Follow-up classification: needs source/test work + docs-only correction
in the same slice.
Status: **landed in the docs slice for the new glossary rows**; the
test-extension slice is a follow-up workflow.

## R3 — `GZCurve.result_semantics` Literal widening + round-trip test

Severity: high
Finding: AUD-P-001
Owner surface: source (Pydantic schema) + tests
Touched files:
- `kayakgen/eval/contract.py:175` — widen `result_semantics` to the
  `AnalyticalClaimLabel` union (or its inlined two-element Literal to
  avoid a circular import; see Open Question in the RFC).
- `tests/test_stability.py` (new test case) — round-trip a
  `GeneratedBodyGZCurve(result_semantics="validated_hydrostatic_comparison")`
  through `StabilityResult.model_validate_json(s.model_dump_json())`.
Gating: `pytest tests/test_stability.py tests/test_high_angle_stability_evaluator.py -q`.
Follow-up classification: needs source/test work.
Status: **deferred to a follow-up striatum workflow** — code change
requires the standard workflow per project memory rule
`feedback_striatum_required`. Recorded as a TODO entry in the same R1
batch (CHANGELOG `### Pending`).

## R4 — `kayakgen runs list / jobs` headers + filter-key documentation

Severity: medium
Finding: AUD-O-004
Owner surface: CLI source + docs
Touched files:
- `kayakgen/cli/runs_cli.py:59-62,144-149` — add optional `--header` flag
  (default false for back-compat); add `--filter` key list to help text.
- `docs/USER_GUIDE.md:469-495` — document the new flag and enumerate
  valid filter keys.
Gating: `pytest tests/test_runs_cli.py -q` if such a file exists; otherwise
add a small smoke test.
Follow-up classification: needs source/test work.
Status: **deferred to a follow-up striatum workflow**.

## R5 — CFD CLI polish: `mesh-evidence` error message + `cfd prepare` next-step

Severity: medium-low
Findings: AUD-O-005, AUD-O-006
Owner surface: CLI source
Touched files:
- `kayakgen/cli/main.py:273-291` — append one line naming RFC 0046 + the
  three mechanisms.
- `kayakgen/cli/main.py:438-441` — append one line naming
  `kayakgen cfd run <dir>` as the next step.
Gating: existing `tests/test_cfd_jobs*.py`.
Follow-up classification: needs source/test work.
Status: **deferred to a follow-up striatum workflow** (bundle with R4).

## R6 — Generate-panel form-builder labels and tooltips

Severity: medium
Finding: AUD-O-003
Owner surface: web UI (`kayakgen/ui/web/generate_spec_form.py`)
Touched files: new label/description map module; spec-form rendering.
Follow-up classification: needs a new RFC. The desktop-vs-web UX gap is
broader than a quick fix; warrants an RFC that decides whether to share a
single label table between desktop sliders and web form (and that
introduces a small Pydantic schema for field metadata).
Status: **TODO entry created**; deferred to a successor RFC.

## R7 — `fit_registry` shared empty-tuple constant

Severity: low
Finding: AUD-P-002
Owner surface: source (clarity, no behavior change)
Touched files: `kayakgen/eval/stability/accepted_fit.py` (add constant);
three call sites (`evaluator.py:385`, `generate_frontier_view.py:558`,
`generate_spec_form.py:832`).
Follow-up classification: source clarity. Bundle with R3 (same module
neighborhood) or defer.
Status: **bundle with R3** in the follow-up workflow.

## R8 — `GenerativeJob` state-vocabulary regression test

Severity: low
Finding: AUD-P-004
Owner surface: tests
Touched files: `tests/test_vocabulary_coverage.py`.
Follow-up classification: test coverage. Bundle with R2.
Status: **bundle with R2**.

## R9 — PRD high-angle GZ sentence naming RFC 0058's upgrade contract

Severity: low
Finding: AUD-D-004
Owner surface: docs only
Touched files: `docs/PRD.md:75-76`.
Follow-up classification: docs-only correction.
Status: **landed in the R1 batch**.

## Follow-up workflow needs

R3 + R7 → single striatum workflow ("0030-stability-claim-gate-literal" or
similar) under `docs/workflows/`. Use the `code_doc_audit` workflow's
remediation-plan job as a model: drive from this REMEDIATION_PLAN.md, land
the schema widening + tests, update the audit FINDINGS status fields, and
record a `CHANGELOG.md ### Fixed` entry citing AUD-P-001.

R2 (test slice) + R8 → single striatum workflow ("0031-vocab-coverage-rfc-0057-0058").

R4 + R5 → single striatum workflow ("0032-cli-ergonomics-runs-cfd").

R6 → new RFC (number TBD; the next free is 0060 because RFC 0059 is this
audit's source RFC).

## Status closure rule

A finding's `status:` flips from `open` to `closed` when:

1. The named files are landed; AND
2. The gating tests pass (where applicable); AND
3. A `CHANGELOG.md` line references the finding ID; AND
4. A reviewer (operator or follow-up audit) confirms the close.

The status fields in the per-lane FINDINGS.md files remain `open` until
all four conditions are met. A separate `CLOSURE_NOTES.md` (optional, not
created by this run) can record close metadata if the operator chooses.
