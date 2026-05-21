# Docs Sync Prompt — workflow 0056

You run in parallel with the implementer tracks. Read
`STAGE_2_3_DECISIONS.md`, RFC 0058, and the current state of
`CHANGELOG.md`, `docs/ROADMAP.md`, `docs/DECISION_LOG.md`,
`docs/rfcs/README.md`, and the existing OPERATOR_REPORT.md before
editing.

Synchronize docs for stages 2 + 3 + NB-1:

- `CHANGELOG.md` Unreleased — add an entry covering:
  - `resolve_analytical_claim_label` contract (RFC 0058 stage 2);
  - `cfd_in_loop_evaluator_status` contract (RFC 0058 stage 2);
  - `kayakgen stability` CLI sub-app (RFC 0058 stage 3);
  - Generate panel frontier-view colour wiring and form-builder
    acknowledgement-hide wiring (RFC 0058 stage 3);
  - NB-1 stepped-clock seam for the auto-poll listener (workflow
    0054 successor).
- `docs/DECISION_LOG.md` — add row `D039` recording (a) the
  persistent-opt-out-wins rule for `cfd_in_loop_evaluator_status`
  and (b) the deferral of the `fit_kind` discriminator field on
  `StabilityFitRecord` to a successor RFC.
- `docs/ROADMAP.md` — flip "Stability calibration acceptance" from
  `landed (schemas only)` to `landed` (schemas + contracts + CLI +
  read-model wiring). Stage-4 first-promotion gate stays explicit:
  `gated on D007/D014 physical rig data`.
- `docs/rfcs/0058-stability-calibration-acceptance.md` — flip the
  status header to `landed` (with a Stage-4 caveat line) and update
  the "Open Questions" section: Q1 (thresholds) `deferred to first
  concrete fit record`, Q2 (EvaluatorVersion shape) `deferred to
  successor RFC`, Q3 (persistent setting precedence) `resolved:
  persistent opt-out wins over graduation (D-8)`, Q4 (`expires_at`)
  `deferred to successor RFC`, Q5 (separate CfdInLoopFitRecord)
  `resolved: identified by a structural .kind discriminator;
  formal field deferred (D-7)`.
- `docs/rfcs/README.md` — update RFC 0058's row to reflect the
  status flip.
- `docs/workflows/0056-rfc-0058-stage2-3-burndown/OPERATOR_REPORT.md`
  — add a 2026-05-21 docs-sync log line summarizing the above.

Strictly forbidden:

- Do not edit any code file. Docs only.
- Do not introduce new claim-state literals or change forbidden-
  claim scrub-list copy.

Write scope:
- `CHANGELOG.md`
- `docs/DECISION_LOG.md`
- `docs/ROADMAP.md`
- `docs/rfcs/0058-stability-calibration-acceptance.md`
- `docs/rfcs/README.md`
- `docs/workflows/0056-rfc-0058-stage2-3-burndown/OPERATOR_REPORT.md`
- `striatum/0056-.../implementation/docs_sync/PATCH_SUMMARY.md`

Publish the required patch summary artifact.
