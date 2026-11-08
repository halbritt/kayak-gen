"""Reproduce RFC0077 baseline, candidate methods and independent references.

Output directory must be explicit; archived observations are never overwritten
by default. The legacy kernel is retained from de8783ed for reproducibility.
"""

from pathlib import Path
import os
import hashlib, json, math, time, sys
import numpy as np
from kayakgen.model.hull import Hull
from kayakgen.eval.resistance import _half_breadth_grid, KNOTS_TO_MS

RHO = 1025.0
G = 9.80665
ROOT = Path(os.environ["KAYAKGEN_NUMERICAL_STUDY_OUT"])
ROOT.mkdir(parents=True, exist_ok=True)


def wave_resistance_michell(
    hull: Hull,
    V_ms: float,
    n_stations: int = 800,
    n_depths: int = 30,
    n_theta: int = 50,
    rho: float = RHO,
    g: float = G,
) -> float:
    """Wave-making resistance via the polar Michell integral, Newtons."""
    if V_ms <= 0:
        return 0.0
    k0 = g / (V_ms * V_ms)

    xs, zs, f = _half_breadth_grid(hull, n_stations, n_depths)
    df_dx = np.gradient(f, xs, axis=0)

    # Truncate the theta integration just shy of pi/2 (sec(theta) singular).
    thetas = np.linspace(0.0, np.pi / 2 - 1e-3, n_theta)
    cos_t = np.cos(thetas)
    sec_t = 1.0 / cos_t
    sec2_t = sec_t * sec_t
    sec3_t = sec_t * sec2_t

    pq2 = np.zeros_like(thetas)
    for k, theta in enumerate(thetas):
        cos_kx = np.cos(k0 * xs * sec_t[k])  # (N,)
        sin_kx = np.sin(k0 * xs * sec_t[k])
        exp_kz = np.exp(-k0 * zs * sec2_t[k])  # (M,)
        kernel_P = cos_kx[:, None] * exp_kz[None, :]
        kernel_Q = sin_kx[:, None] * exp_kz[None, :]
        P = np.trapezoid(np.trapezoid(df_dx * kernel_P, zs, axis=1), xs)
        Q = np.trapezoid(np.trapezoid(df_dx * kernel_Q, zs, axis=1), xs)
        pq2[k] = P * P + Q * Q

    # Factor 16 (= 4 × 4): the 4 from the standard Michell prefactor times
    # a 4 from the (port + starboard) × (fore + aft) symmetry of integrating
    # ∂f/∂x once over the half-hull. Verified against the Wigley parabolic
    # hull (L=1, B=0.1, T=0.0625): with this factor, computed Cw at Fn=0.30
    # matches the published 1.3e-3 ± 5%, and at Fn=0.50 the published 2.6e-3.
    R_w = (16.0 * rho * g * g / (math.pi * V_ms * V_ms)) * np.trapezoid(pq2 * sec3_t, thetas)
    return float(R_w)


def depth_integral(zs, f, beta):
    h = np.diff(zs)
    q = beta * h
    a = -np.expm1(-q) / beta
    b = np.empty_like(q)
    small = q < 1e-3
    b[small] = h[small] * (
        0.5 - q[small] / 3 + q[small] ** 2 / 8 - q[small] ** 3 / 30 + q[small] ** 4 / 144
    )
    b[~small] = (1 - (1 + q[~small]) * np.exp(-q[~small])) / (beta * beta * h[~small])
    decay = np.exp(-beta * zs[:-1])
    return f[:, :-1] @ ((a - b) * decay) + f[:, 1:] @ (b * decay)


def grid_wave(xs, zs, f, v, nt, method="bilinear", angle="trap"):
    k0 = G / v**2
    if angle == "trap":
        theta = np.linspace(0, np.pi / 2 - 1e-3, nt)
        weights = None
    else:
        roots, weights = np.polynomial.legendre.leggauss(nt)
        theta = (roots + 1) * np.pi / 4
        weights = weights * np.pi / 4
    integrand = []
    dfdx = np.gradient(f, xs, axis=0) if method != "bilinear" else None
    dx = np.diff(xs)
    mid = (xs[1:] + xs[:-1]) / 2
    for t in theta:
        sec = 1 / np.cos(t)
        alpha = k0 * sec
        beta = k0 * sec**2
        d = depth_integral(zs, f, beta)
        if method == "bilinear":
            amplitude = np.sum(
                np.diff(d) * np.sinc(alpha * dx / (2 * np.pi)) * np.exp(1j * alpha * mid)
            )
        else:
            d = depth_integral(zs, dfdx, beta)
            amplitude = np.trapezoid(d * np.exp(1j * alpha * xs), xs)
        integrand.append(abs(amplitude) ** 2 * sec**3)
    integral = np.trapezoid(integrand, theta) if weights is None else np.dot(weights, integrand)
    return float(16 * RHO * G**2 / (np.pi * v * v) * integral)


def wigley_reference(fn, theta_count=200001, lam=64):
    length = 1.0
    beam = 0.1
    draft = 0.0625
    v = fn * math.sqrt(G * length)
    k0 = G / v**2
    theta = np.linspace(0, np.arccos(1 / lam), theta_count)
    sec = 1 / np.cos(theta)
    alpha = k0 * sec
    beta = k0 * sec**2
    q = beta * draft
    z = (
        1 / beta
        - 2 / (beta**3 * draft**2)
        + np.exp(-q) * (2 / (beta**2 * draft) + 2 / (beta**3 * draft**2))
    )
    a = length / 2
    x = 8 * beam / length**2 * (a * np.cos(alpha * a) / alpha - np.sin(alpha * a) / alpha**2)
    prefactor = 16 * RHO * G**2 / (np.pi * v * v)
    rw = float(prefactor * np.trapezoid((x * z) ** 2 * sec**3, theta))
    c = 4 * beam / length**2 * (length / k0**2 + 2 / (k0**3 * lam))
    tail = float(prefactor * c * c / (4 * np.sqrt(1 - 1 / lam**2) * lam**4))
    return rw, tail


def main():
    rows = []
    for fn in [0.3, 0.4, 0.5]:
        v = fn * math.sqrt(G)
        reference, tail = wigley_reference(fn)
        check, _ = wigley_reference(fn, 100001)
        for nx, nz, nt in [(100, 10, 20), (200, 20, 40), (400, 40, 80), (800, 80, 160)]:
            xs = np.linspace(-0.5, 0.5, nx)
            zs = np.linspace(0, 0.0625, nz)
            f = 0.05 * (1 - (2 * xs[:, None]) ** 2) * (1 - (zs[None, :] / 0.0625) ** 2)
            for method, angle in [("depth", "trap"), ("bilinear", "trap"), ("bilinear", "gauss")]:
                start = time.perf_counter()
                rw = grid_wave(xs, zs, f, v, nt, method, angle)
                rows.append(
                    dict(
                        subject="wigley",
                        fn=fn,
                        resolution=[nx, nz, nt],
                        method=method,
                        angle=angle,
                        rw=rw,
                        reference=reference,
                        reference_trap_change=abs(reference - check),
                        reference_tail_bound=tail,
                        relative_error=abs(rw - reference) / reference,
                        seconds=time.perf_counter() - start,
                    )
                )
    (ROOT / "wigley-first.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(rows[-12:], indent=2))
    source = Path(__file__).resolve().parents[2] / "tests/fixtures/numerical"
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
    for number in [6, 8, 18]:
        path = source / f"fast-tourer-{number:02d}.json"
        h = Hull.model_validate_json(path.read_text())
        for resolution in resolutions:
            xs, zs, f = _half_breadth_grid(h, *resolution[:2])
            for speed in [4, 4.5, 5, 5.5, 6]:
                v = speed * KNOTS_TO_MS
                start = time.perf_counter()
                legacy = wave_resistance_michell(h, v, *resolution)
                rows.append(
                    dict(
                        subject=f"candidate-{number:02d}",
                        hull_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        speed=speed,
                        resolution=resolution,
                        method="legacy",
                        angle="trap",
                        rw=legacy,
                        seconds=time.perf_counter() - start,
                    )
                )
                for method, angle in [
                    ("depth", "trap"),
                    ("bilinear", "trap"),
                    ("bilinear", "gauss"),
                ]:
                    start = time.perf_counter()
                    rw = grid_wave(xs, zs, f, v, resolution[2], method, angle)
                    rows.append(
                        dict(
                            subject=f"candidate-{number:02d}",
                            speed=speed,
                            resolution=resolution,
                            method=method,
                            angle=angle,
                            rw=rw,
                            seconds=time.perf_counter() - start,
                        )
                    )
        (ROOT / "first-results.json").write_text(json.dumps(rows, indent=2))
        print("finished", number, flush=True)
    print("All baseline/corrected candidate axis experiments retained", len(rows))


if __name__ == "__main__":
    main()
