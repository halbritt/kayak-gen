# RFC 0007: Architectural Revisit — From Prototype Script to Generative Pipeline

Status: proposed
Date: 2026-05-09
Context: generator.py, gui.py, pyvista_view.py; informs and partially
re-frames RFCs 0002–0006. Source motivation: the parameter space and
"10 000 candidates → hydrostatic filter → CFD survivors" pipeline
described in `docs/design/kayak_hull_design_constraints.md`.

## Problem

The codebase today is a productive prototype: three flat files at the
repo root (`generator.py`, `gui.py`, `pyvista_view.py`), no package, no
tests, no dependency manifest. That was the right shape for getting a
hull on screen. It is the wrong shape for the desired outcome —
a generative CFD pipeline that produces thousands of candidates,
filters them by hydrostatics, runs resistance on the survivors, and
explores a Pareto frontier.

Five symptoms are already visible in the code as written:

1. **Geometry is a single hard-coded loft.**
   `generator.py:36` produces every section from one formula
   (`m = 2.0 + (Cm - 0.78) * 5`). RFC 0004 (plumb bow) already needs
   `_end_decay` as a workaround, and the cross-section archetypes from
   §6 of the constraints doc (deep-V, multi-chine, hard chine) cannot
   be expressed at all. Each new shape parameter requires editing this
   single function.

2. **The hull abstraction leaks.**
   `gui.py:212` reaches into `kg._get_area_fraction` and
   `kg._get_deck_height_scaling` — private methods — to render the
   sheer plan. `pyvista_view.py:58` reconstructs a generator from a
   parameter dict per redraw. Public accessors for "the hull's
   waterplane" or "the hull's keel line" do not exist; consumers each
   re-derive them from the lofting internals.

3. **Two competing displacement calculations.**
   `gui.py:176` computes `vol = Cp * Cm * L * B * T` — a formula
   envelope. The actual STL geometry from `generator.py` integrates a
   different volume because the section shape `(t_norm)**(1/m)` is not
   a perfect rectangle of midship area `Cm·B·T`. The number on screen
   can disagree with the number a CFD solver would compute from the
   exported mesh. There is no shared, geometry-truth metric.

4. **No serializable hull, no run record.**
   `_on_generate` writes STLs to a user-chosen path. Nothing records
   which parameters produced which STL, which hydrostatics fell out of
   it, or which resistance curve it scored. The pipeline cannot
   reproduce, diff, or rank candidates because there is no artifact
   to rank.

5. **No headless mode.**
   The only entry point that exercises the generator end-to-end is
   `KayakGUI.__init__`, which spins up matplotlib + PyQt6 + PyVista
   on import. Batch evaluation (cron, CI, optimizer loop, notebook)
   is impossible without first standing up a window system.

The RFCs already on the docket — class presets (0006), resistance
(0005), plumb bow (0004), GUI usability (0002) — each work around
some of these problems with local patches. None of them fix the
architectural shape. The longer we keep stacking parameters on
`KayakGenerator.__init__` and metrics on `gui._compute_metrics`,
the costlier the eventual extraction.

## Goals

- Separate four concerns that are currently tangled across two files:
  the parametric **model** (what is a hull?), the **evaluator(s)**
  (hydrostatics, resistance, future CFD), the **search/driver**
  (single-shot, sweep, optimiser), and the **UI/visualiser** (one of
  several consumers).
- Define a **serializable hull schema** (JSON / Pydantic) so a hull
  is a first-class artifact: store it, diff it, replay it, ship it
  to a remote CFD worker.
- Keep one **truth source for hydrostatics**: the integrated
  geometry, not a formula envelope. The GUI consumes it; future
  optimisers consume it; CFD runs against the same mesh.
- Make every existing capability reachable **without the GUI**:
  a `kayakgen` CLI that takes a hull JSON in and writes hull JSON
  + STL + hydrostatics JSON out.
- Reserve a clean seam for **second-tier CFD** (OpenFOAM / SU2 /
  panel method) without requiring it to land in this RFC.
- Pay the refactor cost **once, now**, before RFCs 0004–0006 land
  parameters that would have to be re-plumbed afterward.

## Non-Goals

- Switching language. Python + NumPy + (eventually) Numba/Cython is
  fine. The hot loops are vectorisable; real CFD calls compiled
  external solvers regardless of host language.
- Switching to a different desktop GUI framework. Matplotlib +
  PyQt6 + PyVista stays. The web/notebook UI is a future concern
  layered on top of the headless API.
- Adopting a CAD kernel (OpenCascade / build123d / OCP) **today**.
  This RFC introduces the abstract `HullGeometry` interface so a
  CAD-kernel implementation can land later as RFC 0008 without
  rewriting consumers.
- Rebuilding any RFC's *intent*. RFCs 0002–0006 keep their goals;
  they retarget onto the new module boundaries.
- Building the search / optimiser. RFC 0007 reserves the package and
  contract; the first sweep / Bayesian optimiser is its own RFC.
- Tooling religion (Poetry vs. uv vs. pip-tools, Ruff vs. Black,
  pytest vs. unittest). Pick defaults; keep moving.

## Proposal

### 1. Package layout

```
kayakgen/
  __init__.py
  model/
    __init__.py
    hull.py            # Hull aggregate (Pydantic), validation, hashing
    geometry.py        # HullGeometry ABC + LoftedHullGeometry (current code)
    classes.py         # KayakClass presets (RFC 0006 home)
    schema.py          # JSON schema export for the hull artifact
  eval/
    __init__.py
    hydrostatics.py    # GM0, displacement, wetted surface, GZ stub
    resistance.py      # ITTC + Michell (RFC 0005 home)
    cfd.py             # interface stub for external solvers (future)
    contract.py        # the EvaluationResult dataclass / Pydantic model
  io/
    __init__.py
    stl.py             # write_stl(hull, path)
    json.py            # load_hull, save_hull, save_evaluation
  search/
    __init__.py
    sweep.py           # grid / latin-hypercube sweep over hull params
    # optimisers land in a later RFC
  ui/
    __init__.py
    desktop.py         # current gui.py contents, refactored
    pv_window.py       # current pyvista_view.py contents, refactored
  cli/
    __init__.py
    main.py            # `kayakgen generate / evaluate / sweep / view`
tests/
  test_hydrostatics.py
  test_resistance.py
  test_hull_roundtrip.py
  test_geometry_lofted.py
pyproject.toml
```

The repo root keeps a thin `gui.py` shim that just imports
`kayakgen.ui.desktop` for backwards compatibility during the
transition.

### 2. Hull as a first-class aggregate

`kayakgen.model.hull.Hull` is a Pydantic model. It owns the design
parameters and a reference to a geometry implementation:

```python
class Hull(BaseModel):
    schema_version: Literal["1"] = "1"
    name: str = "untitled"
    # design parameters (from RFC 0006 + existing params)
    length_m: float
    beam_oa_m: float
    beam_wl_m: float | None = None
    draft_m: float
    deck_height_m: float
    Cp: float
    Cm: float = 0.85
    deck_flatness: float = 8.0
    center_box_ratio: float = 0.33
    bow_rake: float = 1.0          # RFC 0004
    LCB_frac: float = 0.50         # RFC 0006
    rocker_bow_m: float = 0.0      # reserved
    rocker_stern_m: float = 0.0    # reserved
    geometry_kind: Literal["lofted"] = "lofted"

    def to_geometry(self) -> HullGeometry: ...
    def hash(self) -> str: ...     # stable hash of design params for caching
```

Round-trip: `Hull.model_validate_json(...)` ↔
`hull.model_dump_json()`. A hull on disk is a single JSON file. The
hash is the cache key for hydrostatics and CFD results.

### 3. `HullGeometry` interface

Today's `KayakGenerator` becomes `LoftedHullGeometry`, an
implementation of:

```python
class HullGeometry(ABC):
    @abstractmethod
    def section(self, x: float, part: Literal["hull", "deck"]) -> np.ndarray: ...
    @abstractmethod
    def mesh(self, part: str, stations: int) -> tuple[np.ndarray, np.ndarray]: ...
    @abstractmethod
    def waterplane(self, n: int = 200) -> np.ndarray: ...
    @abstractmethod
    def keel_line(self, n: int = 200) -> np.ndarray: ...
    @abstractmethod
    def deck_centreline(self, n: int = 200) -> np.ndarray: ...
    @abstractmethod
    def section_area(self, x: float) -> float: ...
```

`gui.py:212` and any future viewer consume **only** these public
methods. The leaky `_get_area_fraction` / `_get_deck_height_scaling`
calls are deleted at the call sites; they remain as private helpers
inside `LoftedHullGeometry`.

A future RFC can introduce `BSplineHullGeometry` or
`OcctHullGeometry` with the same interface. Consumers do not change.

### 4. Single source of truth for hydrostatics

`kayakgen.eval.hydrostatics.evaluate(hull) -> Hydrostatics` integrates
the actual geometry — same mesh CFD will see — and returns:

```python
class Hydrostatics(BaseModel):
    displaced_volume_m3: float
    displaced_mass_kg:   float       # × ρ_seawater
    wetted_surface_m2:   float
    waterplane_area_m2:  float
    LCB_frac:            float
    Cp_actual:           float       # recomputed; flag if it disagrees with input
    Cm_actual:           float
    GM0_m:               float | None       # populated when KG is known
    gz_curve:            list[tuple[float, float]] | None   # stub for now
```

`gui.py:170` (`_compute_metrics`) is **deleted** and replaced by a
call into `hydrostatics.evaluate`. The formula-envelope number stops
existing. If the number is too slow to compute on every slider drag,
we throttle (we already throttle 3D updates via QTimer at
`gui.py:51`); we do not bring back a parallel approximation.

### 5. Evaluation contract

`kayakgen.eval.contract.EvaluationResult` is the union of all evaluator
outputs that share a single hull:

```python
class EvaluationResult(BaseModel):
    hull_hash: str
    hydrostatics: Hydrostatics
    resistance:   ResistanceCurve | None = None    # RFC 0005
    stability:    GZCurve | None = None            # future
    cfd:          CfdResult | None = None          # future
    timings_ms:   dict[str, float] = {}
```

Evaluators are pure functions `Hull -> partial EvaluationResult` and
compose by merging dicts. This is the read model RFC 0006 §5
described; this RFC actually pins the type.

### 6. CLI

```
kayakgen generate <hull.json> [--stl-out <path>]
kayakgen evaluate <hull.json> [--out <eval.json>]
kayakgen sweep    <sweep.yaml> --out <dir>          # writes hull_*.json + eval_*.json
kayakgen view     <hull.json>                        # opens the desktop GUI on this hull
```

`view` defaults to a fresh `Hull()` with the existing defaults so
running `kayakgen view` is equivalent to today's `python gui.py`.

### 7. Tests as a first commit

Even before the refactor lands, write **golden tests** against the
current code:

- Mesh vertex/face counts and bounding box for the default
  parameters.
- STL byte hash for the default hull (reject any silent geometry
  drift across the refactor).
- A handful of hydrostatic numbers at the default parameters,
  measured *from the integrated geometry* (the new truth source).

Land these on `main` first. They become the regression net the
refactor must keep green.

### 8. Tooling

Add `pyproject.toml` (PEP 621) with:
- runtime deps: `numpy`, `numpy-stl`, `pyvista`, `pyvistaqt`,
  `matplotlib`, `PyQt6`, `pydantic>=2`, `typer` (CLI), `numba`
  (optional, for the Michell hot loop).
- dev deps: `pytest`, `pytest-benchmark`, `ruff`, `mypy`.
- entry point: `kayakgen = "kayakgen.cli.main:app"`.

CI is out of scope for this RFC but the manifest enables it.

### 9. Rolling deprecations

To avoid a big-bang switch, this RFC lands in three commits per area:

1. **Add new module, keep old code.** New `kayakgen/model/hull.py`
   wraps the existing `KayakGenerator` without moving it.
2. **Switch consumers.** `gui.py` and `pyvista_view.py` import from
   `kayakgen.*`; old top-level files become re-export shims.
3. **Delete the shims.** Once tests are green and no external script
   imports the old paths, the root-level `generator.py` etc. are
   removed.

Each step is independently revertible.

## Acceptance Criteria

- `pip install -e .` from the repo root installs the `kayakgen`
  package and registers the `kayakgen` CLI.
- `kayakgen evaluate hull.json` produces an `EvaluationResult` JSON
  that, for the default parameters, matches the golden hydrostatics
  values within 1e-6.
- `python gui.py` continues to work (via shim) and is visually
  identical to the pre-refactor build.
- The GUI's displacement readout matches `evaluate()`'s
  `displaced_mass_kg` to the displayed precision (no more parallel
  formula).
- `gui.py` no longer imports anything underscore-prefixed from the
  geometry implementation. `grep -n '_get_area_fraction\|_get_deck_height_scaling'`
  in `kayakgen/ui/` returns nothing.
- The golden mesh test passes both before the refactor and after.
- A new contributor can run `kayakgen generate hull.json --stl-out
  out.stl` on a CI runner with no display.

## Open Questions

- **Pydantic vs. attrs vs. plain dataclasses.** Pydantic gives JSON
  schema, validation, and IDE support; cost is import time and a
  runtime dep. Lean: Pydantic v2 — the JSON-roundtrip story is the
  whole point.
- **CLI framework.** Typer is ergonomic; argparse is dependency-free.
  Lean: Typer if we already pull in Pydantic; the CLI surface stays
  small enough that argparse is fine if we want to minimise deps.
- **Where does the run record live?** A flat directory of
  `<hash>.hull.json` + `<hash>.eval.json` is enough for now. SQLite
  becomes appealing once we have ≥10⁴ candidates. Defer.
- **CAD kernel?** OpenCascade (via OCP / build123d) gives true
  NURBS, fairing, boolean ops, and IGES export. It also adds ~150 MB
  to the env and a build dependency. Recommendation: **don't** today;
  open RFC 0008 when the lofting approach blocks a real design need
  (probably: multi-chine V-sections + true rocker + asymmetric ends).
- **Differentiable geometry (JAX).** Tempting for gradient-based
  optimisation. Recommendation: not now. The hydrostatic+Michell
  evaluation tier is fast enough for non-gradient methods (CMA-ES,
  Bayesian optimisation via BoTorch) at the candidate volumes the
  constraints doc envisions. Revisit if/when we want to optimise
  through actual CFD.
- **Web/browser UI.** A FastAPI + React frontend over the headless
  CLI is feasible after this refactor lands. Out of scope here;
  cleanly enabled by the headless mode.
- **Order vs. RFC 0006.** This refactor and 0006 (class presets)
  touch overlapping files. Recommendation: land 0007 first, retarget
  0006's implementation onto the new package, save churn.

## Implementation Path

1. **Golden tests against current code** — STL byte hash, mesh
   counts, integrated displacement, integrated wetted surface, at
   the default parameters. Lands on `main` before any refactor.
   (~80 lines.)
2. **Add `pyproject.toml`** — install in editable mode; wire
   nothing yet. (~40 lines.)
3. **Create `kayakgen/` package** — empty modules + `Hull` Pydantic
   model + JSON round-trip test. (~120 lines.)
4. **Move `KayakGenerator` to `kayakgen/model/geometry.py` as
   `LoftedHullGeometry`** — keep top-level `generator.py` as a
   re-export shim. Tests stay green. (~30 lines moved.)
5. **Add `HullGeometry` ABC** and make `LoftedHullGeometry` declare
   conformance. Add public `waterplane`, `keel_line`,
   `deck_centreline`. (~60 lines.)
6. **Move and reshape evaluation** — `eval/hydrostatics.py` consumes
   the geometry, returns the read model. Delete the formula-envelope
   `_compute_metrics` and route the GUI through hydrostatics.
   (~120 lines net change.)
7. **Move GUI** — `kayakgen/ui/desktop.py`, `kayakgen/ui/pv_window.py`;
   replace private-method reaches with public accessors. Top-level
   `gui.py` and `pyvista_view.py` become shims. (~60 lines moved.)
8. **CLI** — `kayakgen generate / evaluate / view`. Sweep stub but
   not implemented. (~150 lines.)
9. **RFC 0006 retarget** — re-implement class presets and `beam_wl`
   inside the new package. (Orthogonal RFC, scoped there.)

Total net new code ≈ 600 lines; net moved/refactored ≈ 200 lines.

## Domain Modeling

Per `DDD.md § "Adding to the model"`:

- **`Hull` is the aggregate root** of the design bounded context.
  All design parameters are owned by it. Every other object refers to
  a hull by hash, not by holding a reference.
- **`HullGeometry` is a value object** parameterised by a hull. It is
  derivable, cacheable, and replaceable (a future
  `OcctHullGeometry` is just a different value-object family).
- **`Hydrostatics`, `ResistanceCurve`, `GZCurve` are read models**
  (per RFC 0006 §5). They are computed projections, never inputs.
  They live under `eval/` and never mutate the aggregate.
- **`EvaluationResult` is the integration object** — the join of
  read models keyed by `hull_hash`. It is what optimisers,
  dashboards, and reports consume.
- **The `search/` package introduces a domain service** in a future
  RFC: it consumes hulls, dispatches evaluations, and emits ranked
  results. Not part of this RFC's scope, but the boundary is reserved.

`UBIQUITOUS_LANGUAGE.md` should gain entries for: Hull, HullGeometry,
Hydrostatics, EvaluationResult, KayakClass.

## Notes on the Bigger Architectural Choices

The user's prompt asked whether the right early choices were made on
**architecture, codebase, language, and frameworks**. The honest
answer:

- **Language: Python — keep.** The numerical work is numpy-vectorisable;
  the slow path (CFD) calls into compiled external solvers; the
  designer-facing tools (PyVista, matplotlib, BoTorch, JAX if needed
  later) all live here. Switching to Rust / Julia / C++ would buy us
  nothing the bottleneck demands.
- **Frameworks: PyQt6 + PyVista + matplotlib — keep for the desktop
  designer tool, but stop treating it as the primary entry point.**
  The pipeline's real entry point is the headless CLI; the GUI is one
  consumer among several.
- **Codebase shape — change.** Three flat files at root with no
  package, no tests, no manifest is the leading cause of the leaky
  abstractions documented above. Move into a real package now,
  before another five RFCs of parameters arrive.
- **Architecture — change.** Today there is no separation between
  model, evaluator, search, and UI. The constraints document's
  pipeline ("10 000 candidates → hydrostatic filter → CFD survivors")
  is impossible to express in the current shape. The four-layer
  separation in §1 of this proposal is the smallest change that makes
  it expressible.
- **Geometry representation — defer the deep change.** The lofted
  parametric model is at its limit but not over it. Introduce the
  `HullGeometry` ABC now so swapping implementations is a localised
  change later. Open RFC 0008 if and when multi-chine, true rocker,
  or asymmetric end shaping become blockers.

The summary: the right early choices were *language and stack*; the
wrong early choice was *not extracting layers before adding
parameters*. This RFC fixes that one thing.
