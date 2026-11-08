"""Fixed-body immersion tests with independent rectangular-body references."""

from __future__ import annotations

import math

import numpy as np
import pytest

from kayakgen.eval.closed_volume import explicit_synthetic_body
from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.hull import Hull
from kayakgen.model.operating_state import OperatingPose


def _box_body():
    # A 2 x 1 x 1 m rectangular closed body, keel Z=-0.5, deck Z=+0.5.
    vertices = [[x, y, z] for x in (-1., 1.) for y in (-.5, .5) for z in (-.5, .5)]
    faces = [[0, 2, 3], [0, 3, 1], [4, 5, 7], [4, 7, 6], [0, 1, 5], [0, 5, 4],
             [2, 6, 7], [2, 7, 3], [0, 4, 6], [0, 6, 2], [1, 3, 7], [1, 7, 5]]
    return explicit_synthetic_body(vertices, faces, body_id="analytic-box")


@pytest.fixture
def box_hull(monkeypatch: pytest.MonkeyPatch):
    import kayakgen.eval.immersed_geometry as operating

    operating._canonical_arrays.cache_clear()
    monkeypatch.setattr(operating, "generated_hull_plus_deck_body", lambda *a, **kw: _box_body())
    yield Hull(length_m=2.0, beam_oa_m=1.0, draft_m=.5)
    operating._canonical_arrays.cache_clear()


@pytest.mark.parametrize("sinkage,expected_volume", [(-.2, .6), (0., 1.), (.2, 1.4)])
def test_pose_integrates_independent_box_displacement(box_hull: Hull, sinkage: float, expected_volume: float) -> None:
    hydro = evaluate(box_hull, pose=OperatingPose(sinkage_m=sinkage))
    assert hydro.displaced_volume_m3 == pytest.approx(expected_volume, abs=1e-12)
    assert hydro.waterplane_area_m2 == pytest.approx(2.0, abs=1e-12)
    depth = .5 + sinkage
    assert hydro.GM0_m == pytest.approx((1.0 / 6.0) / expected_volume + depth / 2.0 - .25, abs=1e-12)
    # Bottom plus four wetted vertical sides: 2 + 6 * submerged depth.
    assert hydro.wetted_surface_m2 == pytest.approx(2.0 + 6.0 * (.5 + sinkage), abs=1e-12)


def test_trimmed_pose_uses_rigid_world_coordinates(box_hull: Hull) -> None:
    hydro = evaluate(box_hull, pose=OperatingPose(trim_angle_deg=10.0))
    # Symmetry leaves half the box submerged; oblique waterplane stretches by sec(theta).
    assert hydro.displaced_volume_m3 == pytest.approx(1.0, abs=1e-12)
    assert hydro.waterplane_area_m2 == pytest.approx(2.0 / math.cos(math.radians(10.)), abs=1e-12)
    angle = math.radians(10.)
    assert hydro.GM0_m == pytest.approx((1.0 / 6.0 - math.sin(angle)**2 / 3.0) / math.cos(angle), abs=1e-12)


def _v2_hull() -> Hull:
    from kayakgen.model.distribution_v2 import DistributionV2Spec, PolynomialDistribution, UniformDistribution

    return Hull(draft_m=.05, geometry_kind="distribution_v2", distribution_v2=DistributionV2Spec(
        waterline_half_breadth=PolynomialDistribution(coefficients=[.25, 0., -.25]),
        draft_profile=UniformDistribution(value=.12), section_area_curve=UniformDistribution(value=.04),
        deck_freeboard=UniformDistribution(value=.15), rocker=UniformDistribution(value=0.),
        cross_section_family="round",
    ))


@pytest.mark.parametrize("mass", [108., 180.])
def test_v2_equilibrium_moves_waterplane_and_preserves_hull_shape(mass: float) -> None:
    from kayakgen.eval.contract import LoadCase
    from kayakgen.eval.stability import evaluate_equilibrium_stability

    hull = _v2_hull()
    record = hull.model_dump_json()
    result = evaluate_equilibrium_stability(hull, LoadCase(paddler_mass_kg=mass, hull_mass_kg=0.))
    assert result.status == "converged", result
    assert abs(result.displaced_mass_kg - mass) < .01
    assert result.equilibrium_draft_m == pytest.approx(.12 + result.sinkage_m, abs=1e-8)
    hydro = evaluate(hull, pose=OperatingPose(sinkage_m=result.sinkage_m))
    assert hydro.displaced_mass_kg == pytest.approx(mass, abs=.01)
    assert hull.model_dump_json() == record


def test_v2_trim_equilibrium_uses_the_same_fixed_body_pose() -> None:
    from kayakgen.eval.contract import LoadCase, LongitudinalLoadComponent
    from kayakgen.eval.stability import evaluate_equilibrium_stability

    hull = _v2_hull()
    load = LoadCase(components=[LongitudinalLoadComponent(name="paddler", mass_kg=108., x_m=.15, kg_above_keel_m=.25)])
    result = evaluate_equilibrium_stability(hull, load)
    assert result.status == "converged", result
    assert result.trim_angle_deg > 0
    hydro = evaluate(hull, pose=OperatingPose(result.sinkage_m, result.trim_angle_deg))
    assert hydro.displaced_mass_kg == pytest.approx(108., abs=.01)
    assert abs(result.moment_error_kg_m) <= result.moment_tolerance_kg_m


def test_v2_infeasible_load_does_not_claim_equilibrium() -> None:
    from kayakgen.eval.contract import LoadCase
    from kayakgen.eval.stability import evaluate_equilibrium_stability

    result = evaluate_equilibrium_stability(_v2_hull(), LoadCase(paddler_mass_kg=10000., hull_mass_kg=0.))
    assert result.status == "not_converged"
    assert "equilibrium_mass_out_of_bracket" in result.warnings
    assert result.equilibrium_draft_m is None
    assert result.sinkage_m is None


def test_resistance_wetted_sampling_uses_the_operating_pose(box_hull: Hull) -> None:
    from kayakgen.eval.resistance import viscous_resistance, wetted_surface

    pose = OperatingPose(sinkage_m=.2)
    area = 2.0 + 6.0 * .7
    assert wetted_surface(box_hull, pose=pose) == pytest.approx(area, abs=1e-12)
    speed = 2.0
    friction = .075 / (math.log10(speed * 2.0 / 1.19e-6) - 2.0)**2
    assert viscous_resistance(box_hull, speed, pose=pose) == pytest.approx(.5 * 1025 * speed**2 * area * friction)


def test_trimmed_resistance_grid_uses_inverse_rigid_transform(box_hull: Hull) -> None:
    from kayakgen.eval.immersed_geometry import immersed_geometry

    pose = OperatingPose(sinkage_m=.1, trim_angle_deg=10.)
    geometry = immersed_geometry(box_hull, pose)
    vertices, _faces = geometry.mesh()
    assert (vertices[:, 2] <= 1e-12).all()
    xs, depths, half_breadths = geometry.half_breadth_grid(31, 21)
    angle = math.radians(10.)
    for i, x in enumerate(xs):
        for j, depth in enumerate(depths):
            body_x = x * math.cos(angle) + depth * math.sin(angle)
            body_z = .1 + x * math.sin(angle) - depth * math.cos(angle)
            inside = -1. < body_x < 1. and -.5 < body_z < .5
            if inside:
                assert half_breadths[i, j] == pytest.approx(.5)
            elif abs(abs(body_x) - 1) > 1e-10 and abs(abs(body_z) - .5) > 1e-10:
                assert half_breadths[i, j] == 0.


def test_pose_bounds_identify_dry_and_fully_submerged_bodies(box_hull: Hull) -> None:
    dry = evaluate(box_hull, pose=OperatingPose(sinkage_m=-1.))
    full = evaluate(box_hull, pose=OperatingPose(sinkage_m=1.))
    assert dry.displaced_volume_m3 == 0.
    assert dry.GM0_m is None
    assert "operating_pose_dry" in dry.notes
    assert full.displaced_volume_m3 == pytest.approx(2.0)
    assert full.waterplane_area_m2 == 0.
    assert full.GM0_m is None
    assert "operating_pose_fully_submerged" in full.notes


@pytest.mark.parametrize("sinkage,trim", [(float("nan"), 0.), (0., float("inf")), (0., 90.), (0., -90.)])
def test_invalid_pose_fails_explicitly(sinkage: float, trim: float) -> None:
    with pytest.raises(ValueError):
        OperatingPose(sinkage, trim)


@pytest.mark.parametrize("pose", [OperatingPose(-.02), OperatingPose(.02), OperatingPose(.02, 3.)])
def test_resistance_grid_and_hydrostatics_integrate_the_same_immersed_body(pose: OperatingPose) -> None:
    from kayakgen.eval.immersed_geometry import immersed_geometry

    hull = _v2_hull()
    hydro = evaluate(hull, pose=pose)
    xs, depths, breadths = immersed_geometry(hull, pose).half_breadth_grid(320, 161)
    grid_volume = np.trapezoid(np.trapezoid(2 * breadths, depths, axis=1), xs)
    assert grid_volume == pytest.approx(hydro.displaced_volume_m3, rel=.01)


def test_fluid_properties_reach_actual_posed_hydro_and_resistance() -> None:
    from kayakgen.eval.resistance import resistance_curve

    hull = _v2_hull()
    pose = OperatingPose(.02, 2.)
    dense = evaluate(hull, pose=pose, density_kg_m3=1025.)
    fresh = evaluate(hull, pose=pose, density_kg_m3=997.)
    assert fresh.displaced_volume_m3 == dense.displaced_volume_m3
    assert fresh.displaced_mass_kg / dense.displaced_mass_kg == pytest.approx(997. / 1025.)
    settings = dict(V_knots=np.array([3.]), n_stations=60, n_depths=10, n_theta=10, pose=pose)
    first = resistance_curve(hull, rho=1025., **settings)
    second = resistance_curve(hull, rho=997., **settings)
    assert second.metadata.constants["seawater_density_kg_m3"] == 997.
    assert second.Rt_N[0] / first.Rt_N[0] == pytest.approx(997. / 1025.)
    changed = resistance_curve(hull, rho=997., nu=1.5e-6, **settings)
    assert changed.metadata.constants["seawater_kinematic_viscosity_m2_s"] == 1.5e-6
    assert changed.Rv_N[0] != second.Rv_N[0]
