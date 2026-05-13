# Kayakgen User Guide

Kayakgen is a parametric kayak hull generator with scriptable evaluation
tools. Current output is useful for geometry iteration, hydrostatic checks,
exploratory sweeps, mesh diagnostics, and local CFD job-record plumbing. It is
not yet a validated performance-prediction or production CFD system.

## Install From This Repo

Use Python 3.11 or newer.

```bash
cd /home/halbritt/git/kayak-gen
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

Optional extras:

```bash
python -m pip install -e '.[desktop]'  # PyQt/PyVista desktop GUI
python -m pip install -e '.[web]'      # Trame web frontend
python -m pip install -e '.[dev]'      # tests, linting, type checking
```

After install, `kayakgen --help` should show the command list.

## Quick Start

Create a default hull, generate STL surfaces, evaluate hydrostatics plus raw
analytical resistance, and inspect mesh quality:

```bash
kayakgen init hull.json
kayakgen generate hull.json --stl-out build/default
kayakgen evaluate hull.json --out build/default.eval.json
kayakgen stability hull.json --out build/default.stability.json
kayakgen mesh-check hull.json --out build/default.mesh.json
```

The generated STL command writes `build/default_hull.stl` and
`build/default_deck.stl`. JSON inputs and outputs use SI units; hull parameters
use names such as `length_m`, `beam_oa_m`, `beam_wl_m`, and `draft_m`.

## Editing Hull Inputs

`kayakgen init` writes a Pydantic `Hull` JSON record. Edit that file directly
for repeatable command-line work. Important fields include:

- `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`
- `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`
- `bow_rake` and `stern_rake`, where `0.0` is exact plumb and `1.0` is the
  legacy raked taper
- `rocker_bow_m` and `rocker_stern_m`

Coordinate convention: X increases from bow to stern. The bow endpoint is
`x = -length_m / 2`; the stern endpoint is `x = +length_m / 2`. Z increases
upward from the design waterline, and Y spans half-beam in generated sections
before being mirrored port/starboard.

`bow_rake` is retained as the legacy compatibility field. Older hull JSON that
only supplies `bow_rake` uses that value symmetrically for bow and stern,
matching historical behavior. New hull JSON may supply `stern_rake` to make the
stern independent. Rake fields are dimensionless fullness controls, not angles;
reverse rake and values outside `[0, 1]` are invalid.

The current loft honors only the implemented parameter set. Some fields exist
for RFC compatibility and are not complete shape controls yet; for example,
`LCB_frac` is reserved and not yet honored by the loft.

## CLI Commands

### `init`

Write a default hull JSON:

```bash
kayakgen init hull.json
```

### `generate`

Write open hull and deck STL inspection surfaces from a hull JSON:

```bash
kayakgen generate hull.json --stl-out build/example
```

Without `--stl-out`, the prefix is the hull path without `.json`.

### `evaluate`

Write hydrostatics and, by default, a raw ITTC plus Michell resistance curve:

```bash
kayakgen evaluate hull.json --out build/eval.json
kayakgen evaluate hull.json --skip-resistance --out build/hydro-only.json
```

Resistance output is an analytical screening estimate. It is explicitly
uncalibrated, has no accepted final-prediction validity envelope, and is meant
for comparative filtering across nearby candidates.

The evaluation JSON also includes additive `design_validity` metadata for
valid hulls. These records separate non-blocking design advisories, such as
`L/B_wl`, `Cp`, and displacement guidance, from unsupported reserved controls
such as non-neutral `LCB_frac`, `rocker_bow_m`, or `rocker_stern_m`. Advisory
and unsupported records do not make the hull invalid, do not change sweep or
comparison ranking, and are not proof of seaworthiness or final design fitness.

### `stability`

Write initial-stability results for a load case:

```bash
kayakgen stability hull.json --out build/stability.json
```

Use `--load-case` to pass a JSON load case. A compact example:

```json
{
  "name": "day-trip",
  "paddler_mass_kg": 85,
  "hull_mass_kg": 18,
  "cargo_mass_kg": 8,
  "kg_above_keel_m": 0.28
}
```

Use `--equilibrium` to solve upright sinkage, and for explicit longitudinal
components the command attempts the current bounded fixed-body trim slice:

```bash
kayakgen stability hull.json --load-case load.json --equilibrium --out build/equilibrium.json
```

High-angle `GZ` curves and secondary-stability peak metrics are unavailable.
They require a closed-volume heeled integration contract that has not landed.

### `sweep`

Run a deterministic JSON sweep and write candidate records:

```bash
kayakgen sweep sweep.json --out runs/demo
kayakgen sweep sweep.json --out runs/demo --resume
```

Minimal sweep spec:

```json
{
  "schema_version": "1",
  "name": "beam-scan",
  "base_hull": {"length_m": 5.2, "beam_oa_m": 0.55, "draft_m": 0.12},
  "variables": {
    "beam_wl_m": {"kind": "values", "values": [0.45, 0.50, 0.55]},
    "Cp": {"kind": "linspace", "min": 0.50, "max": 0.58, "count": 3}
  },
  "evaluators": {
    "hydrostatics": true,
    "resistance": true,
    "stability": true,
    "mesh_diagnostics": true,
    "stl": false
  },
  "limits": {"max_candidates": 100}
}
```

The run directory contains `run.json`, `summary.csv`, `failures.jsonl`, the
copied `spec.json`, and per-candidate artifacts under `candidates/`.

### `compare`

Build a Pareto-style comparison report from a sweep run:

```bash
kayakgen compare runs/demo --out runs/demo/compare.json
kayakgen compare runs/demo --out runs/demo/compare.json \
  -o GM0_m:max -o displacement_error_kg:min -o mesh_problem_count:min
```

Resistance metrics can be named as objectives, but reports that include them
remain exploratory because resistance is a raw comparative filter.

### `mesh-check`

Diagnose the generated surface mesh for one part:

```bash
kayakgen mesh-check hull.json --part hull --out build/hull.mesh.json
kayakgen mesh-check hull.json --part deck --out build/deck.mesh.json
```

Diagnostics report boundary edges, non-manifold edges, degenerate faces,
readiness level, and warnings. This command does not promote a mesh to CFD
readiness.

### `mesh-package`

Write a deterministic mesh package with manifest, hull JSON, quality reports,
and STL surfaces:

```bash
kayakgen mesh-package hull.json --out build/mesh-package
kayakgen mesh-package hull.json --out build/watertight-package --solver-profile watertight-solid
```

The default `open-wetted-surface` profile currently produces an open-surface
candidate with readiness `cfd_surface_candidate`, not `cfd_ready`. The
`watertight-solid` profile is a future boundary and current generated packages
remain below that readiness because the writer emits separate open surfaces,
not a closed hull/deck solid.

Changing `bow_rake` or `stern_rake` to `0.0` does not by itself make those
inspection STLs watertight; closed-body readiness must come from the explicit
generated closed-body path and diagnostics.

## Synthetic Closed-Volume Diagnostics

Workflow 0027 introduced a narrow diagnostic contract for explicit synthetic
triangle meshes. Workflow 0032 adds self-intersection evidence for the
RFC 0021 synthetic profile. These diagnostics are serializable and can
distinguish valid closed synthetic bodies from open, nonmanifold, or
self-intersecting synthetic fixtures.

The contract requires zero body-level boundary edges, zero body-level
nonmanifold edges, and positive signed volume with outward normals before a
synthetic body can report `closed_volume`. The compatibility profile
`explicit_synthetic_closed_volume_v1` records
`self_intersection_status: not_checked`; the RFC 0021 profile
`explicit_synthetic_closed_volume_self_intersection_v1` requires
`self_intersection_status: passed`.

Self-intersection diagnostics are body-level checks on the assembled explicit
body, not per-part readiness claims. The serialized result records
`self_intersection_status`, `self_intersection_algorithm`,
`self_intersection_tolerance_m`, `self_intersection_pair_count`, and up to
eight example triangle pairs. Status values are `not_checked`, `passed`,
`failed`, and `inconclusive`. Both `failed` and `inconclusive` block the
RFC 0021 closed-volume diagnostic profile.

The first algorithm,
`assembled_welded_aabb_triangle_pairs_v1`, uses deterministic expanded
axis-aligned bounding boxes as a broad phase, then checks non-adjacent triangle
pairs. Adjacency is derived from the assembled body after the vertex-weld
tolerance is applied: shared-edge neighbors are skipped, and vertex-only pairs
are skipped only when the welded topology proves they belong to the same local
vertex fan. Coplanar overlap, coplanar touch, edge/point touch, and crossing
between non-adjacent triangles are `failed`; non-adjacent pairs closer than
`self_intersection_tolerance_m` without a detected crossing are
`inconclusive`.

The diagnostic artifact always keeps `cfd_ready` false. Synthetic diagnostics
do not repair geometry, create a volume mesh, or make a watertight solver
handoff. Generated closed-body construction is a separate evaluation-side path;
it must still pass closed-volume diagnostics before it can be treated as a
closed body, and it still does not make a CFD-ready solver handoff.

Generated mesh packages remain open-surface artifacts. Treat their hull and
deck STLs as inspection and packaging surfaces, not as a closed volume for
high-angle stability or watertight CFD.

### `cfd profiles`

List built-in local dispatch profiles:

```bash
kayakgen cfd profiles
```

Current profiles are placeholders for deterministic job-state behavior:
`unavailable-open-wetted-surface`, `unavailable-watertight-solid`, and
`mock-failing-local-command`. The `fixture-local-command` profile is also
available as a checked-in deterministic test adapter; it writes a
`raw-result.json` fixture artifact for route and CLI plumbing tests, but it is
not a real CFD solver and does not produce validated or calibrated output.

### `cfd prepare`

Prepare a local CFD job record from a mesh package:

```bash
kayakgen cfd prepare \
  --mesh-package build/mesh-package \
  --out runs/cfd \
  --solver-profile unavailable-open-wetted-surface \
  --speed-mps 2.5
```

This writes a job directory containing `profile.json`, `job.json`, and
`run.json`. Mesh profile and readiness are checked before the job is written.

### `cfd status`

Show current state for a prepared local job:

```bash
kayakgen cfd status runs/cfd/cfd-xxxxxxxxxxxxxxxx
```

### `cfd run`

Run the selected local adapter state:

```bash
kayakgen cfd run runs/cfd/cfd-xxxxxxxxxxxxxxxx
```

No real OpenFOAM, SU2, hosted worker, Docker solver, or calibrated CFD result
is available in the current CLI. The unavailable profiles report
`solver_unavailable`; the mock local-command profile deliberately fails for
dispatch testing. The fixture local-command profile can produce a deterministic
successful raw fixture record for tests. All CFD run records are raw and
unvalidated.

### `view`

Open the desktop GUI:

```bash
kayakgen view
kayakgen view hull.json
```

Install `kayakgen[desktop]` first. The legacy `python gui.py` entry point is
still present, but `kayakgen view` is the package CLI path.

The desktop GUI exposes sliders for the implemented hull fields, including
`Cp`, `Cm`, beam-at-waterline, deck flatness, parallel mid-body, bow rake, and
stern rake. The target-speed slider only changes the live resistance readout;
it is not written into the `Hull` JSON model.

Use **Export STLs** to write the current open inspection surfaces. The button
label changed from the older "Generate STLs" wording, but the filenames are
unchanged: choosing a stem such as `kayak` writes `kayak_hull.stl` and
`kayak_deck.stl`.

The desktop review text now keeps the same four status categories used by the
workspace RFC: package, readiness, resistance, and CFD. In the current desktop
slice these are status labels only; the GUI does not prepare mesh packages,
start CFD jobs, or promote raw resistance output to a final prediction. The
3D preview still opens as a separate PyVista window.

### `serve`

Run the local Trame web frontend:

```bash
kayakgen serve
kayakgen serve hull.json --host 127.0.0.1 --port 8080
```

Install `kayakgen[web]` first, then open the printed local URL. The web shell
supports interactive hull inspection, compact analysis views, comparison report
loading, and a local CFD job panel. Required local browser acceptance and
hosted-demo documentation are covered by the web verification runbook; public
hosting, full dashboard parity, hosted CFD workers, cancellation guarantees,
authentication, and real solver adapters are not complete.

The web CFD panel and `/api/cfd/*` routes use the same local filesystem job
records as `kayakgen cfd`. They accept an explicit server-local
`mesh_package_ref`, prepare jobs under the web server's local CFD jobs root,
run the current local adapter synchronously, and expose status, logs, and raw
artifacts when present. All CFD route and panel output is raw and unvalidated;
unavailable and failed states are terminal problem states, not completed solver
work.

Current local routes:

```text
GET  /api/cfd/profiles
POST /api/cfd/jobs
GET  /api/cfd/jobs/{job_id}
POST /api/cfd/jobs/{job_id}/run
GET  /api/cfd/jobs/{job_id}/logs
GET  /api/cfd/jobs/{job_id}/raw-result
```

Set `KAYAKGEN_WEB_CFD_JOBS_ROOT` before `kayakgen serve` to choose the local
job-artifact root. Web-side mesh-package creation remains a separate follow-up
work item; create a mesh package with `kayakgen mesh-package` first.

## Mesh And CFD Readiness Caveats

Generated hull and deck meshes are useful STL surfaces for inspection and
packaging. They are not currently a closed watertight solid suitable for a
watertight CFD solver. Treat `cfd_surface_candidate` as a diagnostic staging
state, not proof that a solver can produce meaningful drag numbers.

The current local CFD layer is job plumbing: deterministic profile selection,
mesh-package gating, local job directories, status records, and adapter error
capture. It does not run a real solver unless a future adapter is added, and it
does not normalize, validate, or calibrate external solver output.

## Troubleshooting

- `kayakgen: command not found`: activate the virtual environment and reinstall
  with `python -m pip install -e .`.
- `desktop GUI extras not installed`: install `python -m pip install -e '.[desktop]'`.
- `web extras not installed`: install `python -m pip install -e '.[web]'`.
- `mesh-package solver profile mismatch`: prepare CFD jobs with a solver
  profile that matches the package profile. The default package matches
  `unavailable-open-wetted-surface`.
- `mesh package readiness below solver requirement`: the selected solver
  requires a higher readiness level than the package provides. Current
  generated packages do not satisfy watertight-solid readiness.
- `unknown solver profile`: run `kayakgen cfd profiles` and use one of the
  listed names.
- `candidate failed` in a sweep: inspect `failures.jsonl` and the candidate
  record under `candidates/`; invalid parameter combinations are recorded
  rather than stopping the whole sweep.
- Resistance or CFD values look surprising: check metadata and warnings in the
  output JSON. Resistance is raw analytical screening output; CFD dispatch
  records are raw and unvalidated.

## Current Limits

- Analytical resistance is uncalibrated and accepted only as a comparative
  filter.
- CFD dispatch is local job-state plumbing with unavailable or test adapters,
  not real solver execution.
- Mesh packages are open-surface candidates by default and are not watertight
  closed solids.
- High-angle `GZ`, secondary-stability peak, and full capsize-range stability
  are unavailable.
- Some class/shape parameters are reserved or partially surfaced in frontends
  while the RFC backlog lands.
