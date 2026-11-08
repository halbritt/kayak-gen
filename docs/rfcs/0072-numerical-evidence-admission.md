# RFC 0072: Numerical evidence and resistance objective admission

Status: landed conservative numerical status and admission
Date: 2026-11-07
Context: KAYGEN-7; system review kayakgen-system-20261107; D058 supersedes
D048 only for the numerical admission of resistance, preserving claim gates.

## Problem

Finite resistance is not convergence evidence. The owner v2 hull produced
228243, 34581 and 4297 N at 4.5 kn under successive quadrature refinements.
EvaluationResult nevertheless labeled every present resistance converged.
Exploratory permission could admit those values to comparison and search.

## Goals

Report unassessed numerics as unknown, retain diagnostic values, and require
method-specific numerical evidence independently of physical claim permission.
Apply the same rule to Pareto dominance/frontiers, NSGA-II and EHVI inputs.

## Non-Goals

Physical calibration, suitability or safety claims; selecting a new integrator;
claiming a tolerance is justified before the KAYGEN-15 experiment.

## Proposal

ResistanceMetadata carries additive NumericalQuality: unknown/converged/
not_converged, versioned policy, at least three distinct positive resolutions,
per-speed relative changes, declared tolerance and evidence locator. Assessed
records require this evidence; converged changes must meet the tolerance.
Missing quality on historical records is unknown. Existing explicit convergence
flags remain historical assertions and cannot override numerical admission.
Automatically populated non-iterative stages are unknown rather than converged.

The objective registry marks Rt_N_last as requiring numerical evidence. Raw
values remain in diagnostic outputs. A candidate lacking adequate quality cannot
dominate or join a resistance frontier, train EHVI, or be feasible for NSGA-II
resistance selection. Exploratory opt-in waives only the existing calibration
restriction. Default physical-claim and display-only gates stay closed.

## Acceptance Criteria

- Finite unstable and legacy stage-ran records have unknown numerical quality.
- Raw curves remain visible while exploratory comparison/search omit them from
  numerical frontiers without evidence.
- Synthetic explicit adequate evidence is admitted; insufficient, repeated or
  above-tolerance evidence is refused. Evidence covers all requested speeds.
- Conservative objectives and existing physical-claim refusals still work.
- Full pytest and Ruff gates pass.

## Open Questions

KAYGEN-15 must measure and justify a versioned method-specific policy with an
independent/reference check. No current default calculation is upgraded merely
because this schema exists.

## Implementation Path

Behavioral regression → additive evidence schema → central per-result admission
→ compatibility documentation → full release gate. New numerical policies are
separate semantic checkpoints with new evaluator provenance.

## Domain Modeling

NumericalQuality records numerical evidence. It is independent of claim_state,
accepted_uses, fit acceptance, geometry validity and execution completion.
