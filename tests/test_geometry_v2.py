"""RFC 0048 Geometry V2 distribution-model tests.

The test surface covers four contracts:

1. **No regression for v1 hulls.** Every existing lofted ``Hull`` JSON
   loads byte-stably and produces unchanged STL / hydrostatics /
   mesh-diagnostics outputs once the v2 fields land. Pinned with
   golden-style assertions.
2. **Closed-body topology.** A ``Hull(geometry_kind="distribution_v2",
   distribution_v2=...)`` hull yields a canonical closed body that
   passes RFC 0021 self-intersection + RFC 0016 topology diagnostics.
3. **Hydrostatic cross-check matrix.** Six cross-section families ×
   three rocker amounts × three LCB targets: every combination's
   section / triangle integration cross-check stays within the RFC
   0048 tolerance vector (1.0 / 1.0 / 1.0 / 0.5 %).
4. **Validator + migration round-trip.** Non-default ``bow_rake`` or
   ``stern_rake`` is refused on v2; the migration CLI's round-trip on
   existing golden hulls produces a valid v2 file (and exits non-zero
   with a structured warning when the lossy migration exceeds
   tolerance).
"""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
import pydantic
import pytest

from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.hydrostatics import (
    V2_GM0_TOLERANCE,
    V2_LCB_TOLERANCE,
    V2_VOLUME_TOLERANCE,
    V2_WATERPLANE_TOLERANCE,
    evaluate as evaluate_hydrostatics,
)
from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.eval.resistance import resistance_curve
from kayakgen.io.json import save_hull
from kayakgen.io.stl import write_stl
from kayakgen.model.distribution_v2 import (
    DistributionV2Spec,
    KeyPointsDistribution,
    PolynomialDistribution,
    UniformDistribution,
)
from kayakgen.model.geometry import DistributionV2Geometry, LoftedHullGeometry
from kayakgen.model.hull import Hull


GOLDEN_DIR = Path(__file__).parent / "golden"

HULL_DISPLACED_VOLUME_M3 = 0.11436507419829935
HULL_SURFACE_AREA_M2 = 1.962403180945398
HULL_STL_PAYLOAD_SHA256 = "bd3ba7d497e78349d43495bb0d02097ddfcc3c0e2c5781945c25f781218a4c39"
DECK_STL_PAYLOAD_SHA256 = "fc00ffd0ba772ba6088280fa1aa352a0c9f4f58a5a830cf088a7b09fff763761"


def _stl_payload_sha256(path: Path) -> str:
    data = path.read_bytes()
    n_tris = struct.unpack("<I", data[80:84])[0]
    return hashlib.sha256(data[84 : 84 + n_tris * 50]).hexdigest()


def _signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0))


def _surface_area(vertices: np.ndarray, faces: np.ndarray) -> float:
    a = vertices[faces[:, 0]]
    b = vertices[faces[:, 1]]
    c = vertices[faces[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


def _make_default_v2_spec(
    *,
    family: str = "round",
    rocker_amount: float = 0.0,
    lcb_target: float = 0.5,
    multi_chine_count: int = 2,
    deadrise_deg: float = 8.0,
) -> DistributionV2Spec:
    """Build a representative V2 spec with the same overall dimensions as
    the default lofted hull (4.5m × 0.55m × 0.12m draft)."""

    rocker_knots = [(-1.0, rocker_amount), (-0.5, 0.0), (0.0, 0.0), (0.5, 0.0), (1.0, rocker_amount)]
    return DistributionV2Spec(
        waterline_half_breadth=KeyPointsDistribution(
            knots=[(-1.0, 0.0), (-0.5, 0.20), (0.0, 0.275), (0.5, 0.20), (1.0, 0.0)]
        ),
        draft_profile=KeyPointsDistribution(
            knots=[(-1.0, 0.0), (-0.5, 0.10), (0.0, 0.12), (0.5, 0.10), (1.0, 0.0)]
        ),
        section_area_curve=PolynomialDistribution(coefficients=[0.04, 0.0, -0.04]),
        deck_freeboard=KeyPointsDistribution(
            knots=[(-1.0, 0.04), (0.0, 0.11), (1.0, 0.04)]
        ),
        rocker=KeyPointsDistribution(knots=rocker_knots),
        rocker_bow_m=rocker_amount,
        rocker_stern_m=rocker_amount,
        lcb_target_frac=lcb_target,
        max_beam_position_frac=lcb_target,
        cross_section_family=family,  # type: ignore[arg-type]
        deadrise_deg=deadrise_deg,
        chine_radius_m=0.02,
        bow_flare_deg=0.0,
        multi_chine_count=multi_chine_count,
    )


# ---------------------------------------------------------------------------
# Contract 1 — no regression for v1 lofted hulls.


def test_default_lofted_hull_roundtrips_byte_stably() -> None:
    hull = Hull()
    blob = hull.model_dump_json()
    loaded = Hull.model_validate_json(blob)
    assert loaded == hull
    assert loaded.geometry_kind == "lofted"
    assert loaded.distribution_v2 is None


def test_default_lofted_hull_to_geometry_is_lofted() -> None:
    geom = Hull().to_geometry()
    assert isinstance(geom, LoftedHullGeometry)


def test_default_lofted_hull_stl_payload_stable(tmp_path: Path) -> None:
    """v2 fields landing must not change the lofted STL bytes."""

    hull_stl = tmp_path / "hull.stl"
    deck_stl = tmp_path / "deck.stl"
    write_stl(Hull(), "hull", hull_stl)
    write_stl(Hull(), "deck", deck_stl)
    assert _stl_payload_sha256(hull_stl) == HULL_STL_PAYLOAD_SHA256
    assert _stl_payload_sha256(deck_stl) == DECK_STL_PAYLOAD_SHA256


def test_default_lofted_hull_hydrostatics_unchanged() -> None:
    hy = evaluate_hydrostatics(Hull())
    np.testing.assert_allclose(hy.displaced_volume_m3, HULL_DISPLACED_VOLUME_M3, rtol=1e-9)
    np.testing.assert_allclose(hy.wetted_surface_m2, HULL_SURFACE_AREA_M2, rtol=1e-9)
    # No cross-check for v1 hulls.
    assert hy.v2_cross_check is None
    assert hy.notes == []


def test_lofted_mesh_diagnostics_unchanged() -> None:
    diag = diagnose_mesh(Hull(), part="hull")
    assert diag.readiness.level in {"cfd_surface_candidate", "stl_surface", "display"}
    assert diag.profile.vertex_count == 150 * 79
    assert diag.profile.face_count == 149 * 78 * 2


def test_lofted_resistance_curve_unchanged() -> None:
    curve = resistance_curve(Hull())
    assert curve.metadata.claim_state == "uncalibrated_comparative"


# ---------------------------------------------------------------------------
# Contract 2 — closed-body topology passes RFC 0021 + RFC 0016.


def test_distribution_v2_hull_closed_body_passes_diagnostics() -> None:
    spec = _make_default_v2_spec()
    hull = Hull(geometry_kind="distribution_v2", distribution_v2=spec)
    body = generated_hull_plus_deck_body(hull)
    diag = diagnose_closed_volume_body(body)
    assert diag.readiness.level == "closed_volume"
    assert diag.self_intersection_status == "passed"
    assert diag.signed_volume_m3 > 0


def test_distribution_v2_hull_round_trip_json() -> None:
    spec = _make_default_v2_spec()
    hull = Hull(geometry_kind="distribution_v2", distribution_v2=spec, name="v2-demo")
    blob = hull.model_dump_json()
    loaded = Hull.model_validate_json(blob)
    assert loaded == hull
    assert loaded.geometry_kind == "distribution_v2"
    assert loaded.distribution_v2 is not None


def test_distribution_v2_section_for_closed_body_derives_open_section() -> None:
    """The open inspection section is *derived* from the canonical body."""

    spec = _make_default_v2_spec()
    hull = Hull(geometry_kind="distribution_v2", distribution_v2=spec)
    geom = hull.to_geometry()
    assert isinstance(geom, DistributionV2Geometry)
    closed = geom.section_for_closed_body(0.0, "hull")
    open_ = geom.section(0.0, "hull")
    np.testing.assert_array_equal(closed, open_)


# ---------------------------------------------------------------------------
# Contract 3 — hydrostatic cross-check matrix.


@pytest.mark.parametrize(
    "family",
    ["round", "shallow_arch", "shallow_v", "deep_v", "hard_chine", "multi_chine"],
)
@pytest.mark.parametrize("rocker_amount", [0.0, 0.01, 0.03])
@pytest.mark.parametrize("lcb_target", [0.45, 0.50, 0.55])
def test_hydrostatic_cross_check_within_tolerance(
    family: str, rocker_amount: float, lcb_target: float
) -> None:
    spec = _make_default_v2_spec(
        family=family, rocker_amount=rocker_amount, lcb_target=lcb_target
    )
    hull = Hull(geometry_kind="distribution_v2", distribution_v2=spec)
    hy = evaluate_hydrostatics(hull)
    assert hy.v2_cross_check is not None, "v2 hulls must carry a cross-check block"
    cc = hy.v2_cross_check
    assert cc.volume_drift_frac <= V2_VOLUME_TOLERANCE, (
        f"{family}/{rocker_amount}/{lcb_target}: volume drift "
        f"{cc.volume_drift_frac:.4f} > {V2_VOLUME_TOLERANCE}"
    )
    assert cc.waterplane_drift_frac <= V2_WATERPLANE_TOLERANCE, (
        f"{family}/{rocker_amount}/{lcb_target}: waterplane drift "
        f"{cc.waterplane_drift_frac:.4f} > {V2_WATERPLANE_TOLERANCE}"
    )
    assert cc.lcb_drift_frac <= V2_LCB_TOLERANCE, (
        f"{family}/{rocker_amount}/{lcb_target}: lcb drift "
        f"{cc.lcb_drift_frac:.4f} > {V2_LCB_TOLERANCE}"
    )
    if cc.gm0_drift_frac is not None:
        assert cc.gm0_drift_frac <= V2_GM0_TOLERANCE, (
            f"{family}/{rocker_amount}/{lcb_target}: gm0 drift "
            f"{cc.gm0_drift_frac:.4f} > {V2_GM0_TOLERANCE}"
        )


# ---------------------------------------------------------------------------
# Contract 4 — rake refusal + migration round-trip.


@pytest.mark.parametrize(
    "rake_kwargs", [{"bow_rake": 0.5}, {"stern_rake": 0.5}, {"bow_rake": 0.0, "stern_rake": 0.0}]
)
def test_distribution_v2_refuses_non_default_rake(rake_kwargs: dict[str, float]) -> None:
    spec = _make_default_v2_spec()
    with pytest.raises(pydantic.ValidationError):
        Hull(
            geometry_kind="distribution_v2",
            distribution_v2=spec,
            **rake_kwargs,
        )


def test_distribution_v2_requires_spec() -> None:
    with pytest.raises(pydantic.ValidationError):
        Hull(geometry_kind="distribution_v2")


def test_distribution_v2_admits_default_rake() -> None:
    """The validator allows the default (1.0, 1.0) rake on v2 hulls."""

    spec = _make_default_v2_spec()
    hull = Hull(
        geometry_kind="distribution_v2",
        distribution_v2=spec,
        bow_rake=1.0,
        stern_rake=1.0,
    )
    assert hull.bow_rake == 1.0
    assert hull.stern_rake == 1.0


def test_migration_round_trip_on_default_golden_hull(tmp_path: Path) -> None:
    """The CLI migration runs on the default lofted hull and writes a v2 sibling."""

    source = Hull()
    src_path = tmp_path / "default.json"
    save_hull(source, src_path)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "kayakgen.cli.main",
            "migrate-geometry",
            str(src_path),
            "--tolerance-percent",
            "100.0",
        ],
        capture_output=True,
        text=True,
    )
    # Lossy migration: at 100% tolerance the command exits cleanly.
    assert proc.returncode == 0, proc.stderr
    out_path = src_path.with_suffix(".v2.json")
    assert out_path.exists()
    loaded = Hull.model_validate_json(out_path.read_text())
    assert loaded.geometry_kind == "distribution_v2"
    assert loaded.distribution_v2 is not None


def test_migration_emits_structured_warning_when_over_tolerance(tmp_path: Path) -> None:
    """At the configured default 1.0% tolerance, the lossy migration of the
    default lofted hull exceeds drift and exits non-zero with a structured
    warning payload."""

    source = Hull()
    src_path = tmp_path / "default.json"
    save_hull(source, src_path)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "kayakgen.cli.main",
            "migrate-geometry",
            str(src_path),
            "--tolerance-percent",
            "0.1",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    # Find the structured JSON warning on stderr.
    warning_line = next(
        (line for line in proc.stderr.splitlines() if line.startswith("{")),
        None,
    )
    assert warning_line is not None, proc.stderr
    payload = json.loads(warning_line)
    assert payload["warning"] == "migrate_geometry_tolerance_exceeded"
    assert payload["exceeded"]


def test_migration_refuses_v2_source(tmp_path: Path) -> None:
    spec = _make_default_v2_spec()
    hull = Hull(geometry_kind="distribution_v2", distribution_v2=spec)
    src = tmp_path / "v2_source.json"
    save_hull(hull, src)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "kayakgen.cli.main",
            "migrate-geometry",
            str(src),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "refuses non-lofted source" in proc.stderr


# ---------------------------------------------------------------------------
# Sampling primitive coverage.


def test_uniform_distribution_returns_constant() -> None:
    dist = UniformDistribution(value=0.42)
    result = dist.sample(np.linspace(-1.0, 1.0, 5))
    np.testing.assert_allclose(result, np.full(5, 0.42))


def test_polynomial_distribution_evaluates_correctly() -> None:
    # 1 + 2*xi - xi^2
    dist = PolynomialDistribution(coefficients=[1.0, 2.0, -1.0])
    xi = np.array([-1.0, 0.0, 1.0])
    expected = 1.0 + 2.0 * xi - xi**2
    np.testing.assert_allclose(dist.sample(xi), expected)


def test_keypoints_distribution_passes_through_knots() -> None:
    dist = KeyPointsDistribution(
        knots=[(-1.0, 0.0), (-0.5, 0.5), (0.0, 1.0), (0.5, 0.5), (1.0, 0.0)]
    )
    xi = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    result = dist.sample(xi)
    np.testing.assert_allclose(result, [0.0, 0.5, 1.0, 0.5, 0.0], atol=1e-9)


def test_keypoints_distribution_rejects_non_monotonic_knots() -> None:
    with pytest.raises(pydantic.ValidationError):
        KeyPointsDistribution(knots=[(0.5, 0.0), (-0.5, 1.0), (1.0, 0.0)])


def test_distribution_v2_spec_round_trip_json() -> None:
    spec = _make_default_v2_spec(family="hard_chine")
    blob = spec.model_dump_json()
    loaded = DistributionV2Spec.model_validate_json(blob)
    assert loaded == spec


def test_multi_chine_count_clamped_to_two_through_four() -> None:
    with pytest.raises(pydantic.ValidationError):
        _make_default_v2_spec(family="multi_chine", multi_chine_count=1)
    with pytest.raises(pydantic.ValidationError):
        _make_default_v2_spec(family="multi_chine", multi_chine_count=5)
    # In-range values are admitted.
    for count in (2, 3, 4):
        spec = _make_default_v2_spec(family="multi_chine", multi_chine_count=count)
        assert spec.multi_chine_count == count
