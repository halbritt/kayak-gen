"""Hydrostatics from the integrated mesh — agree with the geometry the STL writer sees."""

from __future__ import annotations

import numpy as np

from kayakgen.eval.hydrostatics import SEAWATER_DENSITY_KG_M3, evaluate
from kayakgen.model.distribution_v2 import (
    DistributionV2Spec,
    PolynomialDistribution,
    UniformDistribution,
)
from kayakgen.model.hull import Hull


def test_default_hydrostatics_match_golden_volume() -> None:
    h = evaluate(Hull())
    np.testing.assert_allclose(h.displaced_volume_m3, 0.11436507419829935, rtol=1e-9)
    np.testing.assert_allclose(
        h.displaced_mass_kg, 0.11436507419829935 * SEAWATER_DENSITY_KG_M3, rtol=1e-9
    )


def test_default_hydrostatics_match_golden_wetted() -> None:
    h = evaluate(Hull())
    np.testing.assert_allclose(h.wetted_surface_m2, 1.962403180945398, rtol=1e-9)


def test_lcb_at_default_is_midship() -> None:
    h = evaluate(Hull())
    assert abs(h.LCB_frac - 0.5) < 1e-6


def test_doubling_length_doubles_volume_for_geometric_scale() -> None:
    base = evaluate(Hull(length_m=4.5, beam_oa_m=0.55, draft_m=0.12))
    longer = evaluate(Hull(length_m=9.0, beam_oa_m=0.55, draft_m=0.12))
    np.testing.assert_allclose(longer.displaced_volume_m3, 2.0 * base.displaced_volume_m3, rtol=1e-3)


def test_cp_actual_in_reasonable_range() -> None:
    h = evaluate(Hull())
    assert 0.4 < h.Cp_actual < 0.7
    assert 0.6 < h.Cm_actual < 0.95


def test_cm_actual_uses_waterline_beam_when_present() -> None:
    hull = Hull(beam_oa_m=0.60, beam_wl_m=0.50)
    h = evaluate(hull)
    midship_area = hull.to_geometry().section_area(0.0)
    np.testing.assert_allclose(h.Cm_actual, midship_area / (0.50 * hull.draft_m))


def test_gm0_is_populated_and_grows_with_waterline_beam() -> None:
    narrow = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.45))
    wide = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.60))
    assert narrow.GM0_m is not None
    assert wide.GM0_m is not None
    assert wide.GM0_m > narrow.GM0_m


def test_analytic_anchor_parabolic_body_volume_and_lcb() -> None:
    """External closed-form anchor for displaced volume and LCB (audit R7).

    Every other pin in this file is self-generated; this test compares the
    mesh integration against a value derived independently by calculus.

    GEOMETRIC IDEALIZATION — why not the wall-sided prism the audit
    sketched: the parametrization cannot represent one honestly.

    * The mesh volume integrator (``_signed_volume``) is a
      divergence-theorem tetrahedron sum over the open hull shell. It is
      exact only when every boundary ring of the shell lies in a plane
      through the origin: the waterline ring (z=0 plane) qualifies, but a
      prism's full-area end rings at x = ±L/2 do not — uniform
      distributions would leave the shell open there and the sum off by
      exactly ``A·L/3`` (a 33% error, verified analytically). The body
      must taper to ~zero at both ends.
    * No section family produces a wall-sided rectangle: ``hard_chine``
      floors deadrise at 8°, and the others are curved by construction.

    Instead we anchor on a closed-form body the V2 loft CAN reach exactly:

    * Section (``round`` family, deadrise 0): ``y = b·t^(1/2)``,
      ``z = -T + T·t``  ⇒  ``z(y) = -T·(1 - (y/b)²)`` — a parabola with
      section area ``A = (4/3)·b·T``.
    * Plan (polynomial half-breadth): ``b(ξ) = b0·(1-ξ²)·(1+cξ)``,
      ``ξ = 2x/L`` — parabolic taper to zero at both ends with a linear
      fore-aft asymmetry ``c`` so LCB is a NON-trivial closed form.

    Closed forms (draft uniform ``T``; odd terms vanish over [-1, 1]):

      V   = ∫ A(x) dx = (4/3)·T·(L/2)·b0·∫(1-ξ²)(1+cξ) dξ = (8/9)·b0·T·L
      x̄   = (L/2)·[∫ξ(1-ξ²)(1+cξ)dξ / ∫(1-ξ²)(1+cξ)dξ] = (L/2)·(c/5)
      LCB = (x̄ + L/2)/L = 1/2 + c/10

    TOLERANCE: rtol=1e-2 per the remediation plan ("coarse"). Observed
    discretization error at the default 150×40 mesh is ~1.5e-3 on volume
    (piecewise-linear loft under a curved analytic surface) and ~1e-6 on
    LCB, so the anchor has >6× margin while still catching any
    integrator-level error (e.g. the A·L/3 open-boundary class above).
    """

    length_m, b0, draft_m, c = 4.0, 0.25, 0.12, -0.3
    spec = DistributionV2Spec(
        # b(xi) = b0*(1-xi^2)*(1+c*xi) = b0 + b0*c*xi - b0*xi^2 - b0*c*xi^3
        waterline_half_breadth=PolynomialDistribution(
            coefficients=[b0, b0 * c, -b0, -b0 * c]
        ),
        draft_profile=UniformDistribution(value=draft_m),
        section_area_curve=UniformDistribution(value=1.0),
        deck_freeboard=UniformDistribution(value=0.10),
        rocker=UniformDistribution(value=0.0),
        cross_section_family="round",
        deadrise_deg=0.0,
    )
    hull = Hull(
        length_m=length_m,
        beam_oa_m=0.52,
        draft_m=draft_m,
        geometry_kind="distribution_v2",
        distribution_v2=spec,
    )

    h = evaluate(hull)

    volume_analytic = (8.0 / 9.0) * b0 * draft_m * length_m
    lcb_analytic = 0.5 + c / 10.0
    np.testing.assert_allclose(h.displaced_volume_m3, volume_analytic, rtol=1e-2)
    np.testing.assert_allclose(h.LCB_frac, lcb_analytic, rtol=1e-2)
