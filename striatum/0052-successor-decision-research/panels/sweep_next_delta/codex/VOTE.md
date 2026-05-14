---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-001
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_33593cdf172f4cae9ba83f59e1ff5585
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_sweep_next_delta_codex
lease: lease_74d9e36b42de46029dd397161a6b59e6

# Vote - Sweep Next Delta

Vote: Option A - Pending Candidate State Next.

## Decision Sentence

Schedule the `pending` sweep candidate lifecycle state as the next RFC 0009
delta: add pending candidate records and counts with explicit transition and
resume semantics, keep pending candidates visible but frontier-ineligible, and
defer sweep-side STL artifacts, optimizer/search loops, and broad metadata
hardening except for the small provenance fields needed to make `pending`
records safe and auditable.

## Evidence

The research packet frames the decision correctly: workflow 0052 is design-only,
RFC 0009 is now a partial landed sweep-run-record slice, and the explicit
remaining deltas are `pending`, sweep-side `stl`, and search/metadata follow-up
(`striatum/0052-successor-decision-research/research/sweep_next_delta/RESEARCH.md:24-45`).
The same packet identifies `pending` as the smallest next delta because it
improves provenance and interruption auditability without adding physics,
geometry artifacts, solver readiness, optimizer behavior, or product claims
(`striatum/0052-successor-decision-research/research/sweep_next_delta/RESEARCH.md:100-134`).

RFC 0009 supports the same ordering. It says the landed sweep command writes
run/spec/summary/failure files and per-candidate artifacts, while `pending` is
not serialized, `stl` remains reserved, and raw resistance is not an optimizer
or design-fitness claim (`docs/rfcs/0009-sweep-run-records.md:8-19`). It also
states that `pending`, `complete`, `failed`, and `skipped` were the proposed
statuses, but only `complete`, `failed`, and `skipped` are currently emitted
(`docs/rfcs/0009-sweep-run-records.md:119-122`), and lists `pending` and
sweep-side `stl` as intentionally narrow remaining deltas
(`docs/rfcs/0009-sweep-run-records.md:146-162`).

The current code confirms the gap and the modest blast radius. `CandidateStatus`
is still `Literal["complete", "failed", "skipped"]`, `EvaluatorOptions.stl`
exists but is only a flag, and `SweepRunRecord` counts only completed, failed,
and skipped candidates (`kayakgen/search/sweep.py:24-70`,
`kayakgen/search/sweep.py:125-137`). Resume currently skips only prior
`complete` records and leaves all non-complete records to run again or fail
again (`kayakgen/search/sweep.py:165-220`). Comparison already filters Pareto
points to `status == "complete"` and adds a warning for every non-complete
candidate (`kayakgen/search/compare.py:133-160`), with tests proving failed and
skipped candidates remain visible but are not frontier members
(`tests/test_compare.py:228-257`). Adding `pending` should reuse that policy.

Workflow 0051 reduced the need for Option C as a standalone successor. The
current objective registry already defines conservative defaults
(`GM0_m`, `displacement_error_kg`, `mesh_problem_count`), explicit exploratory
resistance metadata for `Rt_N_last`, and a claim-gated reserved
`design_fitness` metric (`kayakgen/search/objectives.py:17-118`). That does not
make optimizer/search ready, but it means the next best delta should be a
concrete lifecycle contract rather than another abstract metadata pass.

The roadmap no-claims rules are decisive. Resistance is
`uncalibrated_comparative`, raw CFD is unvalidated or unavailable, open STLs are
inspection/open-surface artifacts, high-angle real kayak `GZ` is unavailable,
validity/advisory badges are not safety or design fitness, and the web frontend
is not hosted CFD or production parity (`docs/ROADMAP.md:33-59`). The sweep
track keeps defaults to conservative metrics, makes raw resistance explicit
exploratory comparison only, and blocks optimizer work behind remaining RFC 0009
deltas plus objective metadata (`docs/ROADMAP.md:92-95`,
`docs/ROADMAP.md:277-296`).

My independent external check supports `pending` before search. Optuna's
current `TrialState` model separates waiting/running unfinished states from
complete/fail states, which supports an explicit pending lifecycle instead of
overloading `failed` or `skipped` for not-yet-run work:
https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.TrialState.html
(accessed 2026-05-14). Optuna's multi-objective guide requires an optimization
direction per objective, and SciPy's `differential_evolution` requires bounded
variables, minimizes an objective, is stochastic, and can require many
evaluations; both argue that active search needs lifecycle, budget, bounds,
objective, seed, and resume contracts first:
https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/002_multi_objective.html
and
https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
(accessed 2026-05-14). W3C PROV ties provenance to assessing quality,
reliability, and trustworthiness, including reproducibility, versioning,
procedures, and derivation, which fits pending transition records before richer
automation: https://www.w3.org/TR/prov-overview/ (accessed 2026-05-14).
The Library of Congress STL note describes STL as a surface mesh format with
limited self-description, which supports deferring sweep-side STL until
manifest/checksum/no-claim sidecars are designed:
https://www.loc.gov/preservation/digital/formats/fdd/fdd000504.shtml
(accessed 2026-05-14).

## Why Rejected Alternatives Lose

- Option B, sweep-side STL artifacts, is useful but should follow `pending`.
  Large binary outputs make interruption, partial runs, resume behavior, and
  artifact provenance more important. STLs also need checksums, source hull
  hashes, part/profile labels, disk-budget warnings, and explicit open
  inspection-surface wording before they can be safe in sweep records.
- Option C, additional metadata/claim hardening, should be folded into Option A
  acceptance criteria. Workflow 0051 already landed the high-risk objective
  registry and comparison gates; a standalone metadata workflow now risks schema
  churn without closing a recorded RFC 0009 lifecycle or artifact delta.
- Option D, optimizer/search, loses now. Search would amplify ambiguous metrics
  and failed lifecycle semantics. It still needs pending/unfinished state,
  search spec/versioning, random seed or sampler provenance, evaluation budget,
  design-space bounds, dependent constraints such as `beam_wl_m <= beam_oa_m`,
  invalid-candidate policy, and claim-gated objective selection.
- Treating raw resistance, raw CFD, advisory validity, unavailable high-angle
  stability, or `design_fitness` as search pressure loses because every current
  project source keeps those outputs either exploratory, raw/unvalidated,
  unavailable, advisory-only, or claim-gated reserved.

## Implementation Gates

- Add `pending` as an additive `CandidateStatus` value and add an additive
  `pending_count` to `SweepRunRecord` without breaking existing run records.
- Pending records must include candidate index, key, attempted parameters,
  evaluator settings, and schema/provenance fields, but must not carry
  `hull_hash`, evaluation summaries, or artifact paths before validation or
  evaluation actually produces them.
- Define transitions explicitly: pending can become `complete` or `failed`;
  resume should skip only prior `complete` records, requeue or re-evaluate
  prior `pending` records, and leave prior `failed` records visible unless a
  separate rerun policy is accepted.
- Preserve pending rows in `run.json`, `summary.csv`, and comparison reports,
  but do not count them as completed and do not make them Pareto eligible.
- Add tests for deterministic pending record creation, pending-to-complete and
  pending-to-failed transitions, resume over pending records, backward
  compatibility for older run records, and comparison warnings for pending.
- Do not bundle optimizer/search, parallel worker queues, sweep-side STL
  generation, calibrated resistance, real CFD success, high-angle stability
  surfacing, or new design-fitness semantics into the pending workflow.

## No-Claims Language

The pending workflow must preserve the existing product boundaries. Raw
analytical resistance remains `uncalibrated_comparative`, not calibrated
performance or a default optimization objective. CFD output remains
raw/unvalidated, fixture-only, unavailable, or failed; no real solver success is
created. Open hull/deck STLs remain inspection/open-surface artifacts and are
not `cfd_ready`. High-angle real kayak `GZ` and secondary-stability metrics
remain unavailable unless the generated-body and heeled-integration gates land.
Class validity and advisory warnings are not seaworthiness, safety, solver
readiness, or final design fitness. No current metric is an automatic best
kayak or final design-fitness score.

Confidence: high.
