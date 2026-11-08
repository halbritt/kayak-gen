from pathlib import Path
import os
import json, time, math
import numpy as np
from kayakgen.model.hull import Hull
from kayakgen.eval.resistance import (
    _half_breadth_grid,
    wetted_surface,
    viscous_resistance,
    KNOTS_TO_MS,
)
from quadrature_experiment import grid_wave, wigley_reference

R = Path(os.environ["KAYAKGEN_NUMERICAL_STUDY_OUT"])
R.mkdir(parents=True, exist_ok=True)
S = Path(__file__).resolve().parents[2] / "tests/fixtures/numerical"
controls = []
for fn in [0.25, 0.275, 0.3, 0.35, 0.4, 0.45, 0.5]:
    xs = np.linspace(-0.5, 0.5, 1600)
    zs = np.linspace(0, 0.0625, 100)
    f = 0.05 * (1 - (2 * xs[:, None]) ** 2) * (1 - (zs[None, :] / 0.0625) ** 2)
    ref, tail = wigley_reference(fn)
    ref2, _ = wigley_reference(fn, 100001)
    actual = grid_wave(xs, zs, f, fn * math.sqrt(9.80665), 640, "depth", "trap")
    allowance = (abs(actual - ref) + tail + abs(ref - ref2)) / ref
    controls.append(
        dict(
            fn=fn,
            reference=ref,
            reference_tail_bound=tail,
            reference_outer_grid_change=abs(ref - ref2),
            depth_exact=actual,
            relative_allowance=allowance,
        )
    )
REFERENCE_ALLOWANCE = max(c["relative_allowance"] for c in controls)
(R / "policy-controls.json").write_text(
    json.dumps(dict(controls=controls, relative_allowance=REFERENCE_ALLOWANCE), indent=2)
)
print("reference allowance", REFERENCE_ALLOWANCE, flush=True)
resolutions = [
    (400, 25, 40),
    (400, 100, 640),
    (800, 100, 640),
    (1600, 100, 640),
    (1600, 25, 640),
    (1600, 50, 640),
    (1600, 100, 40),
    (1600, 100, 160),
]
subjects = {
    f"candidate-{n:02d}": Hull.model_validate_json((S / f"fast-tourer-{n:02d}.json").read_text())
    for n in [6, 8, 18]
}
base = subjects["candidate-06"]
for family in ["shallow_arch", "shallow_v", "deep_v", "hard_chine", "multi_chine"]:
    data = base.model_dump(mode="json")
    data["distribution_v2"]["cross_section_family"] = family
    subjects["family-" + family] = Hull.model_validate(data)
rows = []
for name, hull in subjects.items():
    speeds = np.array([4, 4.5, 5, 5.5, 6])
    surface_observations = []
    for stations in (60, 120, 240):
        started = time.perf_counter()
        sw = wetted_surface(hull, stations)
        rv_at_resolution = np.array(
            [viscous_resistance(hull, v * KNOTS_TO_MS, Sw=sw) for v in speeds]
        )
        surface_observations.append(
            dict(
                stations=stations,
                area_m2=sw,
                rv=rv_at_resolution.tolist(),
                seconds=time.perf_counter() - started,
            )
        )
    rv = np.asarray(surface_observations[0]["rv"])
    fine_rv = np.asarray(surface_observations[2]["rv"])
    viscous_uncertainty = abs(rv - fine_rv) + abs(
        np.asarray(surface_observations[1]["rv"]) - fine_rv
    )
    obs = []
    cache = {}
    for res in resolutions:
        start = time.perf_counter()
        key = res[:2]
        if key not in cache:
            cache[key] = _half_breadth_grid(hull, *key)
        grid_seconds = time.perf_counter() - start
        xs, zs, f = cache[key]
        start = time.perf_counter()
        rw = np.array(
            [grid_wave(xs, zs, f, v * KNOTS_TO_MS, res[2], "depth", "trap") for v in speeds]
        )
        kernel = time.perf_counter() - start
        obs.append(
            dict(
                resolution=res,
                rt=(rv + rw).tolist(),
                grid_seconds=grid_seconds,
                kernel_seconds=kernel,
            )
        )
    values = [np.array(o["rt"]) for o in obs]
    ref = values[3]
    residual = np.abs(ref - values[2]) + np.abs(ref - values[5]) + np.abs(ref - values[7])
    uncertainty = (
        np.abs(values[0] - ref) + residual + np.abs(ref) * REFERENCE_ALLOWANCE + viscous_uncertainty
    )
    row = dict(
        subject=name,
        speeds=speeds.tolist(),
        observations=obs,
        surface_observations=surface_observations,
        viscous_uncertainty_N=viscous_uncertainty.tolist(),
        absolute_uncertainty=uncertainty.tolist(),
        relative_uncertainty=(uncertainty / np.maximum(abs(values[0]), 1e-20)).tolist(),
        intervals=np.column_stack([values[0] - uncertainty, values[0] + uncertainty]).tolist(),
        seconds=sum(o["grid_seconds"] + o["kernel_seconds"] for o in obs)
        + sum(o["seconds"] for o in surface_observations),
    )
    rows.append(row)
    (R / "total-policy-results.json").write_text(json.dumps(rows, indent=2))
    print(name, "uncertainty", row["relative_uncertainty"], "seconds", row["seconds"], flush=True)
