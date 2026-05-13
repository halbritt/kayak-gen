author: operator [self-declared: operator-domain-review]

# Domain review - workflow 0025

Verdict intent: accept_with_findings

## Findings

### D-001 - Raw CFD artifacts are not resistance calibration

RFC 0012 keeps measured-source calibration separate from unvalidated solver
output. An unavailable/mock dispatch workflow can prove record semantics, but
it cannot support any physical resistance claim.

Required action: include `raw_results_validated: false` or equivalent warning
metadata in job/run records and status text. Do not produce calibrated drag,
resistance, or comparison-score fields from mock/unavailable runs.

### D-002 - Solver profiles need explicit fluid and speed inputs

RFC 0015 names `speed_mps`, seawater density, and kinematic viscosity as job
inputs. These are required for reproducibility even before a real solver
exists.

Required action: persist speed, seawater density, and kinematic viscosity in
`job.json`; validate positive numeric values; keep defaults explicit and
documented by tests.

### D-003 - Profile readiness must encode mesh assumptions, not solver success

The open wetted-surface mesh profile is acceptable only as a surface candidate.
The watertight-solid profile should reject current packages. Neither state
means the hydrodynamics are validated.

Required action: model CFD solver profiles with a required mesh profile and
required mesh readiness. Provide one unavailable open-surface profile that can
exercise queue states and one watertight profile that currently rejects
packages below `cfd_ready`.

### D-004 - Provenance needs enough artifact references to reproduce a run

A future solver run must be reproducible from the mesh manifest, solver
profile, and job/run records. The first implementation should not copy large
surfaces unnecessarily, but it must keep a stable reference to the mesh package
manifest that was used.

Required action: store a manifest path/reference in `job.json` and `run.json`,
keep deterministic job IDs from the mesh package/profile/fluid inputs, and
write records with stable schema versions.

### D-005 - Result normalization should wait for real solver output

No real residual or force files exist in this workflow. Normalizing drag
coefficients, residual histories, or force summaries now would create schema
confidence without source data.

Required action: limit the landed result surface to raw artifact references and
state/error metadata. Defer normalized result records until a real solver
adapter supplies concrete output files and validation criteria.
