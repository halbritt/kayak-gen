author: final-reviewer-claude-opus-4.7-001
schema_version: striatum.finding.v1
kind: finding
logical_name: final_review
workflow_id: 0056-rfc-0058-stage2-3-burndown
role: final_reviewer
verdict: accept_with_findings

# Workflow 0056 Final Review — RFC 0058 stage 2 + 3 + workflow 0054 NB-1

Reviewer: Claude Opus 4.7 (final-reviewer-claude-opus-4.7-001)
Date: 2026-05-21
Branch: `striatum/0056-rfc-0058-stage2-3-burndown`
Verdict: **accept_with_findings**

## Scope

Final review of workflow 0056 for accepted scope, decision fidelity,
no-claims boundary preservation, and validation evidence. Cross-checks
required by the work packet:

- RFC 0058 status flipped to `landed` while preserving the Stage-4
  caveat (first promotion gated on D007/D014 physical rig data).
- The empty-registry default still yields the
  `unvalidated_hydrostatic_comparison` analytical-claim label and the
  `opt_in_only` evaluator status.

Inputs reviewed: `STAGE_2_3_DECISIONS.md` (D-1..D-21), RFC 0058,
`reviews/{claims,traceability,ops_tests}/REVIEW.md`,
`ledger/FINDINGS_LEDGER.md`, `remediation/PATCH_SUMMARY.md`, the
landed source / test diff, and the focused + boundary-gate test runs.

## Accepted scope

Stages 2 and 3 of RFC 0058 plus the workflow 0054 NB-1 stepped-clock
seam are within scope, per the workflow operator report and the
decisions doc. The accepted scope is:

- The two contract functions `resolve_analytical_claim_label` and
  `cfd_in_loop_evaluator_status` (D-1..D-8).
- A schema-only `kayakgen stability` sub-app with four named
  subcommands (D-9..D-12).
- Generate-panel frontier-view colour wiring (D-13) and form-builder
  evaluators-block visibility wiring (D-14..D-15).
- The NB-1 stepped-clock seam in `install_generate_state_listener`
  with stepped-clock test variants (D-16..D-17).
- Docs sync flipping RFC 0058 to `landed` with explicit Stage-4
  caveat, decision-log row D039, ROADMAP track flip, RFC index
  status update, and CHANGELOG entries (D-18..D-19).
- No-claims boundary preservation and explicit out-of-scope
  deferrals (D-20, D-21).

No fixture is promoted by this workflow; no real fit is computed; no
new claim-state literal beyond the two named in RFC 0058 is
introduced.

## Decision fidelity

Each of the 21 decision rows has direct code or documentation
evidence on disk. Spot-checks performed:

- **D-1** — `resolve_analytical_claim_label(hull, fit_registry)` is
  defined in `kayakgen/eval/stability/high_angle_contracts.py:60-79`
  and re-exported from `kayakgen/eval/stability/__init__.py:50,110`.
- **D-2** — `AnalyticalClaimLabel` literal carries both labels and is
  the type of `GeneratedBodyGZCurve.result_semantics`; default stays
  `unvalidated_hydrostatic_comparison` (`high_angle_contracts.py:24-49`).
- **D-3** — Acceptance gate is the three-part conjunction
  (accepted ∧ hull_class match ∧ design_hash in envelope) at
  `high_angle_contracts.py:71-78`.
- **D-4** — The wired call site passes the empty tuple
  (`kayakgen/eval/stability/evaluator.py:_generated_body_gz_curve`,
  per traceability review). No disk loading in the resolver module.
- **D-5..D-8** — `cfd_in_loop_evaluator_status(*, registry,
  hull_scope, persistent_opt_in=None)` is defined in
  `kayakgen/services/generative_jobs.py:61-94`. Default is
  `opt_in_only`; promotion to `first_class` requires both an
  accepted `analytical` and an accepted `cfd_in_loop` record covering
  the scope; persistent opt-out short-circuits to `opt_in_only` at
  `:75-76`, ahead of the graduation check; structural `.kind`
  discriminator is read via `getattr` (D-7).
- **D-9..D-12** — `kayakgen/cli/stability_cli.py` exists; the
  sub-app is wired through `app.add_typer(stability_app,
  name="stability")` at `kayakgen/cli/main.py:54`. All four
  schema-only subcommands (`ingest-rig-run`, `promote-fixture`,
  `accept-fit`, `residual-plot`) refuse overwrites and exit non-zero
  on validation failure. Tests use `tmp_path`; the production
  directory constants `data/stability/{fixtures,fits}` are
  created-on-demand and gitignored.
- **D-13** — `kayakgen/ui/web/generate_frontier_view.py` imports
  `resolve_analytical_claim_label`, computes
  `claim_label_color_token` for each hull-bearing scatter point and
  table row, and reuses the existing `state-success` / `state-raw`
  theme tokens via `kg-state-validated` / `kg-state-raw` CSS classes.
  No new theme token introduced.
- **D-14..D-15** — `refresh_cfd_in_loop_status` invokes the helper
  with `registry=()` and no `persistent_opt_in`, so RFC 0046's
  persistent-setting API is untouched. The acknowledgement
  `VCheckbox` carries `v_show=("generative_cfd_in_loop_status ===
  'opt_in_only'",)`. The evaluator toggle row still renders in both
  branches.
- **D-16..D-17** — `install_generate_state_listener` gains
  `time_provider` and `clock_step` parameters; when `clock_step` is
  set, no thread starts. `tick_generate_state_listener` is the
  test-side synchronous driver. Stepped-clock variants land for
  cadence (running + idle), terminal-detail one-shot, coalesce, and
  reinstall; the existing wall-clock tests are preserved per D-17.
- **D-18** — RFC 0058 header reads `Status: landed`. Stage-4 caveat
  is preserved verbatim in the body
  (`docs/rfcs/0058-stability-calibration-acceptance.md:14-16`). The
  Open Questions section is rewritten; Q3 and Q5 are marked
  `resolved`, Q1/Q2/Q4 are marked `deferred to successor RFC`.
- **D-19** — `docs/DECISION_LOG.md` adds row D039 (persistent
  opt-out wins; `fit_kind` deferral). `docs/ROADMAP.md` flips the
  Stability calibration acceptance track to `landed`.
  `docs/rfcs/README.md:75` carries the `landed` row with the
  Stage-4 caveat.
- **D-20** — No new safety / seaworthiness / final-prediction /
  design-fitness wording introduced. The
  `forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
  test still passes; the `ui-theme-orphan-scan`,
  `import-boundary-scan`, and `services-boundary-scan` gates all pass.
- **D-21** — No EvaluatorVersion struct, no `expires_at`, no
  `fit_kind` field on `StabilityFitRecord`, no real fit ingest, no
  frontier-view per-point hover, no RFC 0046 API change. Confirmed
  via diff scan.

## No-claims boundaries

Preserved. Spot-checks:

- The two analytical claim labels in scope are exactly the RFC 0058
  pair (`unvalidated_hydrostatic_comparison`,
  `validated_hydrostatic_comparison`). No third literal anywhere.
- `opt_in_only` / `first_class` are evaluator-availability states,
  not candidate claim states; they do not leak into any candidate
  `claim_state` projection.
- `kayakgen stability residual-plot` writes an explicit placeholder
  SVG (title text "Stability residual placeholder for <fit_id>",
  body label "validation_candidate vs reference") with only
  fit-metric metadata — no measured-vs-analytical curve, no fixture
  promoted.
- `CFD_IN_LOOP_ACK_LABEL` byte-stable ("I accept evaluation may take
  orders of magnitude longer"); the pre-vetted forbidden-claim
  scrub test is unchanged and passes.
- The four ignore/scan boundary gates were re-run and pass:
  `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`,
  `tests/test_ui_theme.py::test_no_orphan_color_literals_under_kayakgen_ui`,
  `tests/test_import_boundaries.py`, `tests/test_services_boundaries.py`
  — 100 passed locally.

## Empty-registry default cross-check

Independently exercised at the boundary:

```
resolve_analytical_claim_label(<hull>, ()) -> unvalidated_hydrostatic_comparison
cfd_in_loop_evaluator_status(registry=(), hull_scope=<scope>) -> opt_in_only
```

Both match the workflow operator report's byte-stability claim and
the RFC 0058 acceptance criteria for stage 2 default behaviour.

## RFC 0058 status cross-check

- `docs/rfcs/0058-stability-calibration-acceptance.md:3` reads
  `Status: landed`.
- The Stage-4 caveat is intact at lines 14-16: "no measured fixture
  or fit is promoted by this RFC landing. The first concrete
  promotion remains a successor workflow gated on D007/D014 physical
  rig data and operator review."
- `docs/rfcs/README.md:75` shows the index row as `landed` with the
  Stage-4 first-promotion gate annotated in the topic cell.

## MF-1 remediation

The ops/tests review flagged MF-1 (first-class branch hid the
acknowledgement control but the form serializer still required it).
The remediation lands inside D-14:

- `kayakgen/ui/web/generate_spec_form.py:634-643` now reads
  `generative_cfd_in_loop_status` and treats the acknowledgement as
  implicit when the helper returns `"first_class"`.
- Default `opt_in_only` behaviour is preserved (unacknowledged
  CFD-in-loop requests still raise `cfd_in_loop_ack_required`).
- A regression test at
  `tests/test_generate_spec_form.py:test_cfd_in_loop_first_class_does_not_require_acknowledgement`
  pins the first-class branch.
- CHANGELOG and OPERATOR_REPORT both record the remediation.

No new evaluator status, claim-state literal, RFC 0046 API change,
or real CFD-in-loop graduation evidence was introduced by the patch.

## Validation evidence

Re-run locally as part of this final review:

- Focused suite (RFC 0058 + Generate):
  `tests/test_stability_accepted_fit.py
   tests/test_resolve_analytical_claim_label.py
   tests/test_cfd_in_loop_evaluator_status.py
   tests/test_cli_stability.py
   tests/test_generate_frontier_view.py
   tests/test_generate_spec_form.py
   tests/test_generate_state_listener.py
   tests/test_high_angle_stability_evaluator.py`
  → **84 passed** (one over the ops/tests review's 83 because the
  MF-1 regression test landed in the remediation pass).
- Boundary gates: forbidden-claim scrub + ui-theme orphan + import
  boundary + services boundary → **100 passed**.
- Pre-existing source reviews:
  - `reviews/claims/REVIEW.md` → `accept`
  - `reviews/traceability/REVIEW.md` → `accept_with_findings`
    (F-1, F-2, F-3 minor docs/scope-record items)
  - `reviews/ops_tests/REVIEW.md` → `needs_revision` (MF-1; now
    remediated; remediator's focused suite re-run is recorded in
    `remediation/PATCH_SUMMARY.md`)
- Full-suite evidence from the ops/tests review:
  **1091 passed, 4 skipped** (skips are opt-in OpenFOAM-v2512
  smoke/stage tests requiring env knobs).

## Findings carried forward

These are the documented non-blocking successor items from the
findings ledger; this final review accepts them as carry-overs and
does not require remediation in this workflow:

- **NB-1** (FINDINGS_LEDGER) — record the hidden
  `kayakgen stability legacy` compatibility shim in a future docs
  sync (extend D-9 or add a D-row). The shim preserves backwards
  compatibility for `kayakgen stability <hull>`.
- **NB-2** — tighten `.gitignore` to the two named subdirectories
  `data/stability/fixtures/` and `data/stability/fits/`, or extend
  D-12 to authorise the broader parent ignore.
- **NB-3** — if future docs describe the listener seam in detail,
  name `tick_generate_state_listener` as the stepped-clock driver
  and the `GENERATIVE_REFRESH_COALESCE_SECONDS` re-export as the
  coalesce-window symbol available to tests.

These are documentation / scope-record polish items and do not
change runtime behaviour, schema behaviour, validation behaviour,
public claims, or default outputs.

## Out-of-scope (carried forward to successor RFC)

D-21 deferrals confirmed absent:

- Structured `EvaluatorVersion(record_hash, evaluator_id)` (Q2).
- `StabilityFitRecord.expires_at` (Q4).
- Real fit ingestion / residual plotting.
- The `fit_kind` discriminator field on `StabilityFitRecord` (Q5).
- Frontier-view per-point hover with metric values.
- Any change to RFC 0046's persistent-setting API (D-15 / Q3).

Stage 4 (first concrete promotion of a measured-stability fixture
and accepted CFD-in-loop fit) remains gated on D007 / D014 physical
rig data and operator review.

## Verdict rationale

`accept_with_findings`. All 21 decision rows trace to landed code or
documentation, the two cross-checks required by the work packet
hold, the MF-1 remediation is in place with a regression test, the
no-claims boundary is preserved, and the focused + boundary-gate
test suites pass locally. The three non-blocking successor items
(NB-1 through NB-3) are documentation/scope-record follow-ups
acknowledged in the findings ledger; they do not block the landing
and are appropriate to roll into the next workflow that touches the
stability CLI or docs.
