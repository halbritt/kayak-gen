---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: operator [self-declared: operator-0052-panel-wave1-gemini-1]
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_58291c85c93d427f954272141ee09501
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_panel_sweep_next_delta_gemini
lease: lease_fbac96a4c89244a3bea9b99695f7f192

# Vote - Sweep Next Delta (Gemini)

## Vote

**Vote: Option A - Schedule `pending` candidate state next.**

## Decision Sentence

Schedule the `pending` record state as the next sweep/search workflow delta, establishing a robust candidate lifecycle that preserves all existing no-claims boundaries and explicitly blocks active optimizer behavior or sweep-side STL generation.

## Evidence And Citations

### External Research
- **Optuna's TrialState documentation** (https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.TrialState.html) highlights the importance of distinguishing waiting/unfinished runs (`WAITING`) from `COMPLETE` or `FAIL`. This supports the explicit introduction of a `pending` state for not-yet-run or queued candidates over overloading complete/failed/skipped states.
- **SciPy and pymoo documentation** (https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html, https://pymoo.org/problems/definition.html) both indicate that solvers and evolutionary algorithms expect well-defined constraints, bounds, and state definitions. This demonstrates that a predictable lifecycle with resumption is required before introducing active optimizer logic.
- **W3C PROV** (https://www.w3.org/TR/prov-overview/) outlines best practices for provenance, supporting explicit state transitions (like `pending`) and reproducible runs before advancing to higher-order search automation.

### Project Context
- **Decision D010** from the project's internal `DECISION_LOG.md` mandates that RFC 0009's status must be reconciled before any optimizer/search work begins. Implementing the `pending` state fulfills this by safely completing the run-record lifecycle gap.

## Why Rejected Alternatives Lose

### Option B (Sweep-Side STLs)
While visible, mass-generating STLs risks large disk budgets and incomplete data. As the Library of Congress notes (https://www.loc.gov/preservation/digital/formats/fdd/fdd000504.shtml), STLs lack rich self-describing metadata. Given the risk of interruptions on large sweeps, the fundamental lifecycle feature (`pending`) is more critical and safer to schedule first.

### Option C (Metadata Hardening)
Workflow 0051 successfully landed the highest-risk objective metadata. Scheduling further metadata improvements in isolation without advancing runtime capabilities could degenerate into abstract schema churn. The necessary parts of this option should be deferred to when an optimizer requires them.

### Option D (Optimizer/Search)
Introducing active optimization without first defining how to handle unfinished or interrupted candidates is premature. Current tools (like SciPy and Optuna) require explicit budget and iteration states. Doing this without a `pending` candidate lifecycle violates D010 and creates a risk of exposing uncalibrated physics as definitive fitness measurements.

## Implementation Gates

- **Lifecycle Correctness:** `pending` records must not contain a `hull_hash` or other evaluation artifacts before the execution has actively produced them.
- **Resume Behavior:** `resume` behavior must correctly handle `pending` records. Prior `complete` records should be skipped, while `pending` runs should be evaluated or requeued safely.
- **Block Optimizer/Search:** Any optimizer loops, parallel execution, or new evaluation artifact types are strictly forbidden in this delta unless they are isolated fixtures for testing pending-state compatibility.

## No-Claims Language

The pending workflow must preserve the existing product boundaries. All existing no-claims gates (e.g., raw resistance remaining `uncalibrated_comparative`, unvalidated raw CFD, unsupported high-angle `GZ`, and no definition of `design_fitness`) remain fully in effect. `pending` candidates carry no fitness or success implication.

## Confidence

**High.**
