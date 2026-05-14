# RFC 0009: Sweep and Candidate Run Records

Status: partial landed sweep-run-record slice
Date: 2026-05-13
Context: builds on RFC 0007 package/CLI extraction, RFC 0005 resistance
filtering, RFC 0006 class constraints, and the `kayakgen.search` namespace.

Status note (2026-05-14): The deterministic JSON sweep runner and candidate
run-record slice has landed. Current `kayakgen sweep` writes `spec.json`,
`run.json`, `summary.csv`, `failures.jsonl`, and per-candidate
record/hull/evaluation artifacts; supports `--resume` by marking existing
completed candidates as `skipped`; records invalid candidate attempts as
`failed`; and can add optional resistance, stability summaries, and mesh
diagnostics to candidate records. This is not full RFC 0009 closure: the
planned `pending` record state is not serialized by the current runner, the
sweep `stl` evaluator flag is reserved rather than a landed sweep-side STL
artifact path, and objective metadata/search remains future work. Raw
resistance stays an uncalibrated comparative filter, and sweep/comparison
records are not optimizer or design-fitness claims.

## Problem

`kayakgen evaluate` can score one hull, but the generative pipeline described
in RFC 0007 needs reproducible candidate sets. At proposal time there was no
sweep spec, no stable run directory layout, no candidate manifest, and no
record tying a generated hull to evaluation settings, failures, timings, and
output files.

Without those records, a future optimizer or CFD worker cannot resume work,
compare runs, audit why a candidate was rejected, or reproduce a promising hull.

## Goals

- Add a deterministic sweep runner for bounded parameter exploration.
- Define persistent candidate run records that can be resumed, audited, ranked,
  and diffed.
- Keep v1 focused on grid and explicit-value sweeps, not optimization.
- Make candidate hull artifacts content-addressed by `Hull.hash()`.
- Emit machine-readable summaries suitable for notebooks, CI, and later Pareto
  filtering.
- Preserve the current truthfulness around RFC 0005: analytical resistance is a
  comparative filter, not final performance prediction.

## Non-Goals

- Bayesian optimization, CMA-ES, genetic search, gradient methods, or active
  learning.
- Distributed execution, queue workers, cloud storage, or databases.
- Selecting a best kayak automatically.
- Treating current Michell resistance as accepted final physics.
- Generating CFD volume meshes.

## Proposal

Introduce `kayakgen.search.sweep` with Pydantic models:

- `SweepSpec`: schema version, name, base hull, variable definitions,
  evaluator options, and limits.
- `ParameterSweep`: one parameter's `values` or `linspace` definition.
- `CandidateRecord`: one deterministic candidate key, optional hull hash,
  varied parameters, status, artifact paths, evaluator provenance, warnings,
  optional error text, and summary metrics.
- `SweepRunRecord`: run metadata, input spec hash, candidate records, counts,
  and completion status.

The v1 spec is JSON-compatible. YAML can be accepted later if the project adds a
dependency or a small loader.

Example:

```json
{
  "schema_version": "1",
  "name": "touring-beam-cp-sweep",
  "base_hull": {
    "length_m": 5.0,
    "beam_oa_m": 0.58,
    "beam_wl_m": 0.53,
    "draft_m": 0.12,
    "Cp": 0.54
  },
  "variables": {
    "beam_wl_m": {"kind": "linspace", "min": 0.48, "max": 0.56, "count": 5},
    "Cp": {"kind": "values", "values": [0.52, 0.54, 0.56, 0.58]}
  },
  "evaluators": {
    "hydrostatics": true,
    "resistance": false,
    "mesh_diagnostics": false,
    "stl": false
  },
  "limits": {
    "max_candidates": 1000
  }
}
```

Output directory:

```text
run.json
spec.json
summary.csv
failures.jsonl
candidates/
  <candidate_key>.hull.json
  <candidate_key>.eval.json
  <candidate_key>.record.json
  <candidate_key>.mesh.json
```

CLI:

```text
kayakgen sweep sweep.json --out runs/touring-001
kayakgen sweep sweep.json --out runs/touring-001 --resume
```

Candidate statuses were proposed as `pending`, `complete`, `failed`, and
`skipped`. The landed partial slice serializes `complete`, `failed`, and
`skipped`; `pending` remains a planned state for a future queued or optimizer
workflow, not current output.

## Acceptance Criteria

- `kayakgen sweep <spec> --out <dir>` writes `run.json`, `spec.json`,
  candidate hull JSON, candidate record JSON, and `summary.csv`.
- Re-running with `--resume` skips completed candidate hashes and records the
  skip count.
- A fixed sweep spec produces the same ordered candidate hashes on repeated
  runs.
- Invalid candidates rejected by `Hull` validation are recorded as failed, not
  lost. Failed records include `candidate_index`, `candidate_key`, attempted
  parameters, and validation error text. `hull_hash` is optional and present
  only after `Hull` validation succeeds.
- `summary.csv` includes at least candidate key, hull hash when available,
  varied parameters, displacement mass, wetted surface, `GM0_m`, `Cp_actual`,
  and resistance summary when resistance is enabled.
- Resistance can be disabled for large sweeps.
- Mesh diagnostics are optional and require the RFC 0010 diagnostics layer.
- Candidate records include evaluator settings, evaluator versions, and
  warnings sufficient to reproduce the read models used.
- Tests cover deterministic expansion, resume behavior, failure records, and
  CLI output.

## Landed Slice And Remaining Deltas

The landed slice covers deterministic `values` and `linspace` expansion,
`kayakgen sweep`, run/spec/summary/failure files, per-candidate
record/hull/evaluation artifacts, invalid-candidate failure records,
resume-skip behavior, optional resistance and stability summary fields, and
optional mesh-diagnostic artifacts.

Remaining RFC 0009 deltas are intentionally narrow:

- `pending` is still a planned record state rather than a serialized candidate
  status.
- The sweep-side `stl` evaluator flag is reserved and does not currently
  produce per-candidate STL artifacts.
- Objective metadata and any optimizer/search loop remain future work.
- Raw resistance remains an explicit exploratory comparison input, not a
  default objective, calibrated prediction, or design-fitness metric.

## Open Questions

- Should v1 add random or Latin-hypercube sampling, or stay grid-only until
  optimizer requirements are clearer?
- Which objective metadata fields and non-default objective roles become
  canonical before optimizer/search work?
- Should YAML support be added now, or should JSON remain the only v1 format?

## Implementation Path

- Step 1 - Add `kayakgen/search/sweep.py` models and deterministic expansion.
- Step 2 - Add run-record JSON and CSV writing.
- Step 3 - Replace the `kayakgen sweep` stub with a working runner.
- Step 4 - Add resume-by-candidate-key behavior.
- Step 5 - Add focused tests using tiny two-variable sweeps.
- Step 6 - Add optional mesh-diagnostics artifacts after RFC 0010 diagnostics
  exist.

## Domain Modeling

`SweepSpec` and `SweepRunRecord` are application-layer value objects and run
records around the `Hull` aggregate root. They do not add new hull-domain
semantics.
