author: reviewer-ops-codex-gpt-5.5-001
schema_version: striatum.finding.v1
kind: finding
logical_name: review
run: run_c1de081e76f14cd1a81194e306338ac2
session: sess_2273cdd11ef544b5a6fec1b4b5b42522
job: job_run_c1de081e76f14cd1a81194e306338ac2_review_ops
lease: lease_008722452fb1412f823ac5d7531a0a1c
date: 2026-05-14
verdict_intent: accept_with_findings

# Review Ops - Workflow 0048 Successor RFC Backlog

## Verdict

`accept_with_findings`

RFCs 0036-0043 are reviewable as proposed successor RFCs. They keep tests
practical, preserve package/CLI/web/desktop boundaries, and do not hide a
requirement for unavailable hosted services, solver binaries, Docker,
calibration data, or real secondary-stability infrastructure. The findings
below are sequencing and indexing constraints for integration and future
workflow planning, not blockers on accepting this RFC packet.

## Findings

### O1 - Index the solver-readiness work as gated scope, not as one ready-to-code feature

Severity: Medium

RFC 0040 is correctly framed as a roadmap over the closed-volume and
solver-readiness evidence ladder. Its implementation path is intentionally
larger than one safe coding slice: readiness read model, generated-body
hardening fixtures, volume-mesh diagnostic contract, mesh-package handoff, and
dispatch preparation are separate gates.

Integration should index RFC 0040 as proposed roadmap/scope until those later
implementation workflows land. Do not schedule it as a single "make generated
packages cfd_ready" packet. The practical test boundary is good: negative
cases cover open surface as closed body, synthetic body as generated kayak,
generated closed body as volume mesh, fixture handoff as production meshing,
and raw solver output as validated prediction.

### O2 - RFC 0041 requires a solver-selection decision before implementation

Severity: Medium

RFC 0041 has the right external-adapter boundaries: no hosted workers, no new
route shape, no container requirement, no installed solver required for normal
CI, and all outputs remain `raw_unvalidated`. The important sequencing guard is
that the RFC itself does not choose a solver. The first implementation workflow
must begin with the named solver decision record, including executable/version
checks, supported platform notes, mesh profile, case-template version, expected
raw outputs, timeout/log policy, and limitations.

If that decision chooses `watertight_solid_resistance_v1`, RFC 0041 should
wait behind RFC 0040's verified profile gate. If it chooses an open-surface
mode, the decision must explain why that mode is physically and operationally
coherent without implying watertight readiness. Required tests can stay
fixture/fake-command based; optional installed-solver smoke tests should remain
environment-gated.

### O3 - RFCs 0042 and 0043 are evidence/design gates, not runtime implementation packets

Severity: Low

RFC 0042 properly narrows resistance work to source review, provenance, and
fixture promotion. It should not be treated as approval to check in measured
rows, fit a model, or remove uncalibrated warnings. A later implementation
needs manifest/source-use mapping tests and negative promotion tests before any
validation fixture is loaded.

RFC 0043 properly keeps high-angle `GZ` unavailable until the heeled
integration model is accepted. It should be indexed as a successor design gate,
not as authority to emit `GZ`, `GZ_max`, range-of-positive-stability, or
capsize-range metrics. The next runtime workflow needs a separate design
decision for body profile, trim policy, CG convention, waterline clipping,
residuals, tolerances, and warning behavior before user-facing CLI/sweep/web or
desktop surfaces change.

### O4 - The UI successor split is acceptable, with one ordering note

Severity: Low

RFCs 0036-0039 are small but not incoherent. RFC 0036 is a narrow browser proof
or dead-code removal decision. RFC 0039 is a state-schema consolidation. RFCs
0037 and 0038 both touch the export menu, but keeping them separate is
reasonable because one collapses schema ownership while preserving shipped
copy, and the other changes one disabled-row label.

Implementation should run RFC 0037 before RFC 0038, or bundle them in one
workflow with separate acceptance gates. Otherwise 0037 will pin
`Mesh package...` as current visible copy and 0038 will immediately revise it.
The test strategy remains practical: static row-schema drift tests, browser
acceptance for enabled/unavailable rows, route-shape preservation for snapshot
schema work, and forbidden-copy/no-claims checks.

## Per-RFC Test And Boundary Check

- RFC 0036: practical browser acceptance or removal path; no desktop/backend
  scope.
- RFC 0037: practical static/rendered row-schema drift tests; no export
  behavior or route changes.
- RFC 0038: practical visible-copy/browser tests; row remains disabled and
  CLI-only.
- RFC 0039: practical snapshot/alias compatibility tests; no REST payload
  redesign.
- RFC 0040: practical negative evidence and fixture tests, but should be split
  into later implementation workflows.
- RFC 0041: practical fake-command/parser/unavailable tests; real solver smoke
  must be optional.
- RFC 0042: practical source-review and manifest validation tests; no data
  promotion by RFC text alone.
- RFC 0043: practical fixture-only math and unavailable-result tests; no
  user-facing metrics until generated-body evidence and the heeled model land.

## Validation Performed

- Ran `striatum byline --session-id sess_2273cdd11ef544b5a6fec1b4b5b42522 --job-id job_run_c1de081e76f14cd1a81194e306338ac2_review_ops --json` and used the returned author line.
- Read the required context, workflow sources, RFCs 0036-0043, the three RFC
  scoping artifacts, and predecessor RFCs covering closed volume, real CFD,
  resistance calibration, and high-angle `GZ`.
- `git diff --check -- docs/rfcs/0036-trame-seed-listener-proof.md docs/rfcs/0037-export-row-schema-consolidation.md docs/rfcs/0038-export-menu-disabled-copy-polish.md docs/rfcs/0039-web-snapshot-schema-unification.md docs/rfcs/0040-closed-volume-solver-readiness-roadmap.md docs/rfcs/0041-real-cfd-adapter-successor.md docs/rfcs/0042-resistance-calibration-fixture-successor.md docs/rfcs/0043-high-angle-gz-successor.md striatum/0048-successor-rfc-backlog/rfc_ui/RFC_SCOPE_UI.md striatum/0048-successor-rfc-backlog/rfc_geometry_solver/RFC_SCOPE_GEOMETRY_SOLVER.md striatum/0048-successor-rfc-backlog/rfc_calibration_stability/RFC_SCOPE_CALIBRATION_STABILITY.md` produced no output.
- `rg -n "[[:blank:]]$" ...` over the same RFC/scope files found no trailing
  whitespace.

No runtime tests were run because this is a docs/RFC review packet and no
runtime code was changed.
