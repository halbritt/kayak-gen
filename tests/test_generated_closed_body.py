"""Generated hull-plus-deck closed-body acceptance and plumb-stem semantics."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pytest

from kayakgen.eval import closed_volume as closed_volume_module
from kayakgen.eval.closed_volume import (
    ClosedVolumeBody,
    ClosedVolumeDiagnostics,
    diagnose_closed_volume_body,
    dispatch_evidence_satisfies_profile,
)
from kayakgen.eval.generated_closed_body import (
    generated_hull_plus_deck_closed_body as compatibility_closed_body,
)
from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.eval.mesh_package import write_mesh_package
from kayakgen.model.classes import CLASSES
from kayakgen.model.geometry import LoftedHullGeometry
from kayakgen.model.hull import Hull


GENERATED_PROFILE = "generated_hull_plus_deck_closed_body_v1"
GENERATED_BODY_TYPE = "generated_hull_plus_deck_closed_body"


def _arrays(body) -> tuple[np.ndarray, np.ndarray]:
    part = body.parts[0]
    return np.asarray(part.vertices, dtype=float), np.asarray(part.faces, dtype=np.int64)


def _face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    triangles = vertices[faces]
    return np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])


def test_exact_plumb_endpoints_have_nonzero_terminal_sections() -> None:
    hull = Hull(bow_rake=0.0, stern_rake=0.0)
    vertices, _faces = _arrays(_generated_body(hull, stations=6))

    bow = vertices[np.isclose(vertices[:, 0], -hull.length_m / 2)]
    stern = vertices[np.isclose(vertices[:, 0], hull.length_m / 2)]

    assert np.ptp(bow[:, 1]) > 0.5
    assert np.ptp(bow[:, 2]) > 0.2
    assert np.ptp(stern[:, 1]) > 0.5
    assert np.ptp(stern[:, 2]) > 0.2


def test_generated_plumb_body_diagnostics_prove_closed_positive_volume() -> None:
    body = _generated_body(
        Hull(bow_rake=0.0, stern_rake=0.0),
        stations=4,
    )

    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.signed_volume_m3 > 0.0
    assert diagnostics.self_intersection_status == "passed"
    assert diagnostics.cfd_ready is False


def test_plumb_cap_normals_are_mirrored_under_x_convention() -> None:
    hull = Hull(bow_rake=0.0, stern_rake=0.0)
    vertices, faces = _arrays(_generated_body(hull, stations=4))
    normals = _face_normals(vertices, faces)
    face_x = vertices[faces][:, :, 0]

    bow_cap = np.isclose(face_x, -hull.length_m / 2).all(axis=1)
    stern_cap = np.isclose(face_x, hull.length_m / 2).all(axis=1)

    assert bow_cap.sum() > 0
    assert stern_cap.sum() > 0
    assert normals[bow_cap, 0].max() < 0.0
    assert normals[stern_cap, 0].min() > 0.0


def test_default_raked_generated_body_uses_apex_closure_without_degenerate_faces() -> None:
    diagnostics = diagnose_closed_volume_body(
        _generated_body(Hull(), stations=4)
    )

    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.signed_volume_m3 > 0.0
    assert diagnostics.self_intersection_status == "passed"


def test_generated_body_closes_when_waterline_beam_differs_from_overall_beam() -> None:
    diagnostics = diagnose_closed_volume_body(
        _generated_body(
            Hull(bow_rake=0.0, stern_rake=0.0, beam_oa_m=0.60, beam_wl_m=0.50),
            stations=4,
        )
    )

    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.self_intersection_status == "passed"


@pytest.mark.parametrize(
    ("case_name", "hull"),
    [
        ("touring-preset", CLASSES["touring"].default_hull()),
        ("elite-surfski-preset", CLASSES["surfski_elite"].default_hull()),
        ("plumb-bow-raked-stern", Hull(bow_rake=0.0, stern_rake=1.0)),
        ("raked-bow-plumb-stern", Hull(bow_rake=1.0, stern_rake=0.0)),
        (
            "beam-waterline-not-overall",
            Hull(beam_oa_m=0.62, beam_wl_m=0.46, bow_rake=0.0),
        ),
        ("low-draft-envelope", Hull(draft_m=0.10)),
        ("high-draft-envelope", Hull(draft_m=0.14)),
        ("low-cp-envelope", Hull(Cp=0.50)),
        ("high-cp-envelope", Hull(Cp=0.60)),
        ("low-cm-envelope", Hull(Cm=0.70)),
        ("high-cm-envelope", Hull(Cm=0.95)),
    ],
)
def test_generated_closed_body_hardening_matrix_cases_close(
    case_name: str,
    hull: Hull,
) -> None:
    diagnostics = diagnose_closed_volume_body(_generated_body(hull, stations=10))

    _assert_closed_generated_body(diagnostics)
    assert diagnostics.source_hull_hash == hull.hash(), case_name


def test_open_plumb_stl_surface_remains_inspection_mesh_not_closed_body() -> None:
    diagnostics = diagnose_mesh(Hull(bow_rake=0.0), stations=24)

    assert diagnostics.readiness.level == "stl_surface"
    assert diagnostics.raw_boundary_edges > 0
    assert diagnostics.welded_boundary_edges > 0
    assert "mesh has boundary edges and is not a closed volume" in diagnostics.warnings


def _builder() -> Any:
    builder = getattr(closed_volume_module, "generated_hull_plus_deck_body", None)
    if builder is None:
        builder = getattr(
            closed_volume_module,
            "generated_hull_plus_deck_closed_body",
            None,
        )
    if builder is None:
        pytest.fail(
            "kayakgen.eval.closed_volume must expose an RFC 0022 builder such as "
            "generated_hull_plus_deck_body() for "
            "generated_hull_plus_deck_closed_body_v1 bodies"
        )
    return builder


def _generated_body(hull: Hull, *, stations: int = 12) -> ClosedVolumeBody:
    return _builder()(hull, stations=stations)


def test_generated_closed_body_compatibility_import_uses_generated_profile() -> None:
    body = compatibility_closed_body(Hull(name="rfc0022-compat"), stations=6)
    diagnostics = diagnose_closed_volume_body(body)

    assert body.body_type == GENERATED_BODY_TYPE
    assert diagnostics.profile_name == GENERATED_PROFILE
    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.cfd_ready is False


def _assert_closed_generated_body(diagnostics: ClosedVolumeDiagnostics) -> None:
    assert diagnostics.profile_name == GENERATED_PROFILE
    assert diagnostics.body_type == GENERATED_BODY_TYPE
    assert diagnostics.readiness.level == "closed_volume"
    assert diagnostics.cfd_ready is False
    assert diagnostics.raw_boundary_edges == 0
    assert diagnostics.welded_boundary_edges == 0
    assert diagnostics.raw_nonmanifold_edges == 0
    assert diagnostics.welded_nonmanifold_edges == 0
    assert diagnostics.nonfinite_vertices == 0
    assert diagnostics.nonfinite_faces == 0
    assert diagnostics.invalid_face_indices == 0
    assert diagnostics.degenerate_faces == 0
    assert diagnostics.self_intersection_status == "passed"
    assert diagnostics.self_intersection_algorithm != "not_checked_rfc0016_compatibility"
    assert (
        diagnostics.signed_volume_m3
        > diagnostics.policy.tolerances.signed_volume_tolerance_m3
    )


def _all_vertices(body: ClosedVolumeBody) -> np.ndarray:
    return np.vstack(
        [np.asarray(part.vertices, dtype=float) for part in body.parts]
    )


def _iter_part_triangles(
    body: ClosedVolumeBody,
) -> Iterable[tuple[np.ndarray, np.ndarray]]:
    for part in body.parts:
        vertices = np.asarray(part.vertices, dtype=float)
        faces = np.asarray(part.faces, dtype=int)
        for face in faces:
            yield vertices[face], face


def _assert_face_normals_point_outward(body: ClosedVolumeBody) -> None:
    vertices = _all_vertices(body)
    centroid = vertices.mean(axis=0)
    signed_normal_offsets: list[float] = []
    for triangle, _face in _iter_part_triangles(body):
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        signed_normal_offsets.append(float(normal @ (triangle.mean(axis=0) - centroid)))

    assert signed_normal_offsets
    assert min(signed_normal_offsets) >= -1e-10


def _dump_value(model: Any, *paths: tuple[str, ...]) -> Any:
    dumped = model.model_dump(mode="json") if hasattr(model, "model_dump") else model
    for path in paths:
        current = dumped
        for key in path:
            if not isinstance(current, dict) or key not in current:
                break
            current = current[key]
        else:
            return current
    joined = ", ".join(".".join(path) for path in paths)
    pytest.fail(f"expected serialized field at one of: {joined}")


def _numeric_metadata_value(metadata: Any, *keys: str) -> float:
    assert isinstance(metadata, dict)
    for key in keys:
        if key in metadata:
            return float(metadata[key])
    pytest.fail(f"expected numeric waterline metadata key in {keys}")


def test_generated_closed_body_policy_round_trips_with_source_metadata() -> None:
    hull = Hull(name="rfc0022-policy")
    body = _generated_body(hull)
    loaded_body = ClosedVolumeBody.model_validate_json(body.model_dump_json())

    assert loaded_body == body
    assert body.body_type == GENERATED_BODY_TYPE
    assert body.policy.profile_name == GENERATED_PROFILE
    assert body.policy.body_type == GENERATED_BODY_TYPE
    assert body.policy.waterline_semantics == "metadata_only"
    assert body.policy.normal_orientation == "outward_positive_signed_volume"
    assert body.policy.self_intersection_policy == "required_rfc0021_conservative"
    assert body.policy.cfd_readiness_policy == "never_claim_cfd_ready"
    assert body.policy.cap_policy != "not_applicable_explicit_mesh"
    assert body.policy.deck_join_policy != "not_applicable_explicit_mesh"
    assert "bow" in body.policy.cap_policy
    assert "stern" in body.policy.cap_policy
    assert "sheer" in body.policy.deck_join_policy
    assert body.policy.tolerances.vertex_weld_tolerance_m > 0.0
    assert body.policy.tolerances.self_intersection_tolerance_m >= 0.0

    assert _dump_value(
        body,
        ("source_hull_hash",),
        ("metadata", "source_hull_hash"),
        ("policy", "source_hull_hash"),
    ) == hull.hash()
    assert _dump_value(body, ("units",), ("metadata", "units"), ("policy", "units")) == "m"
    coordinate_system = _dump_value(
        body,
        ("coordinate_system",),
        ("metadata", "coordinate_system"),
        ("policy", "coordinate_system"),
    )
    assert isinstance(coordinate_system, dict)
    assert coordinate_system.get("waterline_z_m") == pytest.approx(0.0)

    waterline = _dump_value(
        body,
        ("waterline_metadata",),
        ("metadata", "waterline_metadata"),
        ("metadata", "waterline"),
        ("policy", "waterline_metadata"),
    )
    assert _numeric_metadata_value(waterline, "waterline_z_m", "z_m") == pytest.approx(
        0.0
    )
    assert _numeric_metadata_value(waterline, "beam_wl_m", "beam_m") == pytest.approx(
        hull.beam_oa_m
    )


def test_generated_closed_body_is_deterministic_and_does_not_use_display_stl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hull = Hull(name="rfc0022-deterministic", beam_wl_m=0.50)

    def _forbidden_display_stl(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("display STL export must not be used for closed bodies")

    monkeypatch.setattr(LoftedHullGeometry, "generate_stl", _forbidden_display_stl)

    first = _generated_body(hull, stations=16)
    second = _generated_body(hull, stations=16)

    assert first.model_dump_json() == second.model_dump_json()
    assert _dump_value(first, ("source_hull_hash",), ("metadata", "source_hull_hash")) == (
        hull.hash()
    )


@pytest.mark.parametrize("bow_rake", [1.0, 0.0])
def test_generated_closed_body_closes_default_and_plumb_rake_end_caps(
    bow_rake: float,
) -> None:
    hull = Hull(name=f"rfc0022-rake-{bow_rake}", bow_rake=bow_rake)
    body = _generated_body(hull, stations=20)
    diagnostics = diagnose_closed_volume_body(body)

    _assert_closed_generated_body(diagnostics)
    assert body.policy.cap_policy == "explicit_bow_stern_endpoint_ring_caps"
    assert len(body.parts) == 1
    assert diagnostics.part_diagnostics[0].raw_boundary_edges == 0
    assert diagnostics.part_diagnostics[0].welded_boundary_edges == 0
    assert diagnostics.part_diagnostics[0].degenerate_faces == 0

    vertices = _all_vertices(body)
    faces = np.asarray(body.parts[0].faces, dtype=int)
    bow_vertex_indices = set(np.flatnonzero(vertices[:, 0] == vertices[:, 0].min()))
    stern_vertex_indices = set(np.flatnonzero(vertices[:, 0] == vertices[:, 0].max()))
    if bow_rake == 0.0:
        assert any(set(face.tolist()) <= bow_vertex_indices for face in faces)
        assert any(set(face.tolist()) <= stern_vertex_indices for face in faces)
    else:
        assert len(bow_vertex_indices) == 1
        assert len(stern_vertex_indices) == 1
        assert any(set(face.tolist()) & bow_vertex_indices for face in faces)
        assert any(set(face.tolist()) & stern_vertex_indices for face in faces)


def test_plumb_rake_preserves_more_closed_body_volume_than_default_rake() -> None:
    default_body = _generated_body(Hull(name="rfc0022-default-rake"), stations=20)
    plumb_body = _generated_body(
        Hull(name="rfc0022-plumb-rake", bow_rake=0.0),
        stations=20,
    )

    default_diagnostics = diagnose_closed_volume_body(default_body)
    plumb_diagnostics = diagnose_closed_volume_body(plumb_body)

    _assert_closed_generated_body(default_diagnostics)
    _assert_closed_generated_body(plumb_diagnostics)
    assert plumb_diagnostics.signed_volume_m3 > default_diagnostics.signed_volume_m3


def test_generated_closed_body_joins_waterline_beam_to_outer_sheer() -> None:
    hull = Hull(
        name="rfc0022-join",
        beam_oa_m=0.62,
        beam_wl_m=0.46,
        draft_m=0.13,
        deck_height_m=0.25,
        bow_rake=0.0,
    )
    body = _generated_body(hull, stations=18)
    diagnostics = diagnose_closed_volume_body(body)
    vertices = _all_vertices(body)

    _assert_closed_generated_body(diagnostics)
    assert max(abs(vertices[:, 1])) == pytest.approx(hull.beam_oa_m / 2.0, rel=0.02)

    waterline_vertices = vertices[np.abs(vertices[:, 2]) <= 1e-7]
    assert len(waterline_vertices) > 0
    assert max(abs(waterline_vertices[:, 1])) == pytest.approx(
        hull.beam_oa_m / 2.0,
        rel=0.03,
    )
    assert np.any(
        np.isclose(
            np.abs(waterline_vertices[:, 1]),
            hull.beam_wl_m / 2.0,
            rtol=0.03,
            atol=1e-8,
        )
    )
    assert np.any(
        (vertices[:, 2] > 0.0)
        & (np.abs(vertices[:, 1]) > hull.beam_wl_m / 2.0 + 0.02)
    )
    assert "sheer" in body.policy.deck_join_policy
    assert "weld" in body.policy.deck_join_policy or "shared" in body.policy.deck_join_policy


def test_generated_closed_body_records_waterline_metadata_without_cutting_body() -> None:
    hull = Hull(
        name="rfc0022-waterline",
        beam_wl_m=0.49,
        draft_m=0.14,
        deck_height_m=0.27,
    )
    body = _generated_body(hull)
    vertices = _all_vertices(body)
    waterline = _dump_value(
        body,
        ("waterline_metadata",),
        ("metadata", "waterline_metadata"),
        ("metadata", "waterline"),
        ("policy", "waterline_metadata"),
    )

    assert body.policy.waterline_semantics == "metadata_only"
    assert _numeric_metadata_value(waterline, "waterline_z_m", "z_m") == pytest.approx(
        0.0
    )
    assert _numeric_metadata_value(waterline, "beam_wl_m", "beam_m") == pytest.approx(
        hull.beam_wl_m
    )
    assert vertices[:, 2].min() < -0.9 * hull.draft_m
    assert vertices[:, 2].max() > 0.0


def test_generated_closed_body_diagnostics_round_trip_with_outward_normals() -> None:
    body = _generated_body(Hull(name="rfc0022-diagnostics"), stations=18)
    diagnostics = diagnose_closed_volume_body(body)
    loaded = ClosedVolumeDiagnostics.model_validate_json(diagnostics.model_dump_json())

    assert loaded == diagnostics
    _assert_closed_generated_body(loaded)
    _assert_face_normals_point_outward(body)


def test_display_stl_mesh_package_and_cfd_readiness_remain_separate(
    tmp_path,
) -> None:
    hull = Hull(name="rfc0022-separation")
    body = _generated_body(hull, stations=16)
    diagnostics = diagnose_closed_volume_body(body)
    manifest = write_mesh_package(hull, tmp_path, stations=8)

    _assert_closed_generated_body(diagnostics)
    assert diagnostics.cfd_ready is False
    assert manifest.surfaces == {"hull": "hull.stl", "deck": "deck.stl"}
    assert manifest.readiness.level != "closed_volume"
    assert manifest.readiness.level != "cfd_ready"
    assert "generated_closed_body" not in manifest.model_dump_json()
    assert not any("closed_body" in path.name for path in tmp_path.iterdir())
    assert dispatch_evidence_satisfies_profile(
        diagnostics.model_dump(mode="json"),
        GENERATED_PROFILE,
        "cfd_ready",
    ) is False
    assert dispatch_evidence_satisfies_profile(
        diagnostics.model_dump(mode="json"),
        "watertight_solid_resistance_v1",
        "cfd_ready",
    ) is False
