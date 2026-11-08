from pathlib import Path
import os
import json, time, hashlib
import numpy as np
from kayakgen.model.hull import Hull
from kayakgen.eval.resistance import (
    _half_breadth_grid,
    wave_resistance_michell,
    wetted_surface,
    viscous_resistance,
    KNOTS_TO_MS,
)
from quadrature_experiment import grid_wave, wigley_reference

R = Path(os.environ["KAYAKGEN_NUMERICAL_STUDY_OUT"])
R.mkdir(parents=True, exist_ok=True)
S = Path(__file__).resolve().parents[2] / "tests/fixtures/numerical"
rows = []
resolutions = [
    (400, 25, 40),
    (800, 25, 40),
    (1600, 25, 40),
    (400, 50, 40),
    (400, 100, 40),
    (400, 25, 80),
    (400, 25, 160),
    (800, 50, 80),
    (1600, 100, 160),
]
base = Hull.model_validate_json((S / "fast-tourer-06.json").read_text())
for family in ["round", "shallow_arch", "shallow_v", "deep_v", "hard_chine", "multi_chine"]:
    dump = base.model_dump(mode="json")
    dump["distribution_v2"]["cross_section_family"] = family
    hull = Hull.model_validate(dump)
    sw = wetted_surface(hull)
    for resolution in resolutions:
        start = time.perf_counter()
        xs, zs, f = _half_breadth_grid(hull, *resolution[:2])
        sample = time.perf_counter() - start
        for speed in [4, 4.5, 5, 5.5, 6]:
            v = speed * KNOTS_TO_MS
            rv = viscous_resistance(hull, v, Sw=sw)
            for method in ["depth", "bilinear"]:
                start = time.perf_counter()
                rw = grid_wave(xs, zs, f, v, resolution[2], method, "trap")
                seconds = time.perf_counter() - start
                rows.append(
                    dict(
                        subject="family-" + family,
                        speed=speed,
                        resolution=resolution,
                        method=method,
                        rw=rw,
                        rv=rv,
                        rt=rv + rw,
                        grid_seconds=sample,
                        kernel_seconds=seconds,
                        total_seconds=sample + seconds,
                    )
                )
    (R / "family-results.json").write_text(json.dumps(rows, indent=2))
    print("family", family, flush=True)
angles = []
for candidate in [6, 8, 18]:
    path = S / f"fast-tourer-{candidate:02d}.json"
    hull = Hull.model_validate_json(path.read_text())
    sw = wetted_surface(hull)
    for nx, nz in [(800, 50), (1600, 100), (3200, 200)]:
        start = time.perf_counter()
        xs, zs, f = _half_breadth_grid(hull, nx, nz)
        sample = time.perf_counter() - start
        for speed in [4, 4.5, 5, 5.5, 6]:
            v = speed * KNOTS_TO_MS
            rv = viscous_resistance(hull, v, Sw=sw)
            for theta in [80, 160, 320, 640]:
                start = time.perf_counter()
                rw = grid_wave(xs, zs, f, v, theta, "depth", "trap")
                sec = time.perf_counter() - start
                angles.append(
                    dict(
                        subject=f"candidate-{candidate:02d}",
                        speed=speed,
                        resolution=[nx, nz, theta],
                        method="depth",
                        rw=rw,
                        rv=rv,
                        rt=rv + rw,
                        grid_seconds=sample,
                        kernel_seconds=sec,
                        total_seconds=sample + sec,
                    )
                )
    (R / "angular-results.json").write_text(json.dumps(angles, indent=2))
    print("angles", candidate, flush=True)
print("retained", len(rows), "family and", len(angles), "angular observations", flush=True)
