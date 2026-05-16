"""RFC 0045 hash-binding tests for ``bind_evidence_to_mesh_package``.

Covers the three structured rejection codes
(``closed_body_hash_mismatch``, ``snappy_evidence_body_mismatch``,
``polymesh_artifact_drift``) and the happy path that promotes a
freshly-rendered watertight mesh package to ``cfd_ready`` against the
``watertight_solid_resistance_v1`` profile.

No real OpenFOAM binary is invoked - evidence records are constructed
inline with passing checkMesh, valid dictionary hashes, and a v2512
provenance probe. ``is_openfoam_available`` is monkeypatched off
defensively in case any code path probes the toolchain.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kayakgen.eval.cfd.jobs import OpenFoamProvenanceProbe
from kayakgen.eval.closed_volume import generated_hull_plus_deck_body
from kayakgen.eval.mesh_package import (
    closed_volume_solver_readiness_report_from_package,
    watertight_solid_profile,
    write_mesh_package,
)
from kayakgen.eval.snappy_hex_mesh import (
    SNAPPYHEXMESH_BODY_PROFILE,
    CheckMeshSummary,
    MeshEvidenceBindError,
    SnappyHexMeshEvidence,
    SnappyHexMeshPatchEntry,
    bind_evidence_to_mesh_package,
    build_snappy_hex_mesh_evidence,
    closed_body_content_sha256,
    compute_dict_hashes,
    default_snappy_hex_mesh_dict_scaffold,
)
from kayakgen.model.hull import Hull


WATERTIGHT_DISPATCH_PROFILE = {
    "name": "rfc0045-watertight-solid",
    "required_mesh_profile": "watertight_solid_resistance_v1",
    "required_mesh_readiness": "cfd_ready",
}


def _accepted_v2512_provenance() -> OpenFoamProvenanceProbe:
    return OpenFoamProvenanceProbe(
        application="OpenFOAM-v2512",
        build="OpenFOAM-v2512-abc1234",
        api="2512",
        project_version="OpenFOAM-v2512",
        env_project_version=None,
        raw={"application": "OpenFOAM-v2512", "api": "2512"},
    )


def _passing_check_mesh() -> CheckMeshSummary:
    return CheckMeshSummary(
        passed=True,
        n_cells=8_000,
        n_internal_faces=24_000,
        n_boundary_faces=2_400,
        max_non_orthogonality_deg=55.0,
        max_skewness=2.5,
        aspect_ratio_max=10.0,
        warnings=[],
    )


def _fully_bound_evidence(
    hull: Hull,
    *,
    body_ref_hash: str | None = None,
    artifact_checksums: dict[str, str] | None = None,
) -> SnappyHexMeshEvidence:
    body = generated_hull_plus_deck_body(hull, stations=8)
    scaffolds = default_snappy_hex_mesh_dict_scaffold(body)
    dict_hashes = compute_dict_hashes(scaffolds)
    resolved_hash = body_ref_hash if body_ref_hash is not None else closed_body_content_sha256(body)
    return build_snappy_hex_mesh_evidence(
        body_ref_hash=resolved_hash,
        dictionary_hashes=dict_hashes,
        patch_metadata=[
            SnappyHexMeshPatchEntry(
                name="hull",
                marker="wall:hull",
                role="wetted_body",
                face_count=2_400,
            ),
            SnappyHexMeshPatchEntry(
                name="farfield",
                marker="patch:farfield",
                role="farfield",
                face_count=1_200,
            ),
        ],
        check_mesh=_passing_check_mesh(),
        artifact_checksums=artifact_checksums or {
            "volume_mesh": "a" * 64,
            "snappyHexMeshDict": "b" * 64,
        },
        openfoam_provenance=_accepted_v2512_provenance(),
    )


def _disable_openfoam_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defensively pin ``is_openfoam_available`` to False for binding tests."""
    monkeypatch.setattr(
        "kayakgen.eval.cfd.openfoam_v2512_interfoam.runner.is_openfoam_available",
        lambda *_args, **_kwargs: False,
    )


def test_bind_evidence_promotes_to_cfd_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fully-bound evidence promotes the watertight package to cfd_ready."""
    _disable_openfoam_probe(monkeypatch)
    hull = Hull(name="rfc0045-happy-path", bow_rake=0.0, stern_rake=0.0)
    evidence = _fully_bound_evidence(hull)
    body = generated_hull_plus_deck_body(hull, stations=8)
    closed_hash = closed_body_content_sha256(body)

    diagnostic = bind_evidence_to_mesh_package(
        evidence,
        closed_body_hash=closed_hash,
        polymesh_dir=None,
    )

    package_dir = tmp_path / "package"
    manifest = write_mesh_package(
        hull,
        package_dir,
        solver_profile=watertight_solid_profile(),
        stations=8,
        bound_volume_mesh_diagnostic=diagnostic,
    )

    assert manifest.readiness.level == "cfd_ready"
    assert manifest.readiness_authority == "verified_watertight_volume_mesh_evidence"
    assert manifest.volume_mesh_diagnostic == "volume-mesh-diagnostic.json"
    assert manifest.closed_volume_diagnostic == "closed-volume-diagnostic.json"
    assert "volume_mesh_diagnostic" in manifest.evidence_hashes

    report = closed_volume_solver_readiness_report_from_package(
        package_dir,
        solver_profile=WATERTIGHT_DISPATCH_PROFILE,
    )
    assert report.gate_status == "ready_for_profile"
    assert report.input_semantics == "profile_input_candidate"
    assert report.blocker_reasons == []


def test_bind_evidence_rejects_closed_body_hash_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An evidence body_ref_hash that does not match the current hull is rejected."""
    _disable_openfoam_probe(monkeypatch)
    hull = Hull(name="rfc0045-closed-body-mismatch", bow_rake=0.0, stern_rake=0.0)
    evidence = _fully_bound_evidence(hull, body_ref_hash="d" * 64)
    body = generated_hull_plus_deck_body(hull, stations=8)
    closed_hash = closed_body_content_sha256(body)

    with pytest.raises(MeshEvidenceBindError) as exc_info:
        bind_evidence_to_mesh_package(
            evidence,
            closed_body_hash=closed_hash,
            polymesh_dir=None,
        )

    assert exc_info.value.code == "closed_body_hash_mismatch"
    assert "closed-body hash" in exc_info.value.message


def test_bind_evidence_rejects_snappy_evidence_body_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An evidence record claiming a non-canonical body_profile is rejected."""
    _disable_openfoam_probe(monkeypatch)
    hull = Hull(name="rfc0045-body-profile-mismatch", bow_rake=0.0, stern_rake=0.0)
    body = generated_hull_plus_deck_body(hull, stations=8)
    closed_hash = closed_body_content_sha256(body)
    fully_bound = _fully_bound_evidence(hull)
    # Mutate the evidence to claim an unsupported body_profile while leaving
    # the body_ref_hash matching the canonical hull. The binding gate must
    # surface ``snappy_evidence_body_mismatch`` before the closed-body hash
    # comparison succeeds.
    tampered_payload = json.loads(fully_bound.model_dump_json())
    tampered_payload["body_profile"] = "some_other_body_profile_v1"
    tampered_payload["dispatch_state"] = "pending_evidence"
    tampered_payload["dispatch_blocker_codes"] = ["missing_body_profile"]
    evidence = SnappyHexMeshEvidence.model_construct(**tampered_payload)

    with pytest.raises(MeshEvidenceBindError) as exc_info:
        bind_evidence_to_mesh_package(
            evidence,
            closed_body_hash=closed_hash,
            polymesh_dir=None,
        )

    assert exc_info.value.code == "snappy_evidence_body_mismatch"
    assert SNAPPYHEXMESH_BODY_PROFILE in exc_info.value.message


def test_bind_evidence_rejects_polymesh_artifact_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A drifted on-disk polyMesh artifact must reject with the structured code."""
    _disable_openfoam_probe(monkeypatch)
    hull = Hull(name="rfc0045-polymesh-drift", bow_rake=0.0, stern_rake=0.0)
    polymesh_dir = tmp_path / "polyMesh"
    polymesh_dir.mkdir()
    # Lay down a points file whose on-disk content does NOT match the
    # checksum we will write into the evidence record.
    points_path = polymesh_dir / "points"
    points_path.write_bytes(b"drifted-points-bytes")
    actual_hash = hashlib.sha256(points_path.read_bytes()).hexdigest()
    recorded_hash = "0" * 64
    assert recorded_hash != actual_hash
    evidence = _fully_bound_evidence(
        hull,
        artifact_checksums={
            "points": recorded_hash,
            "volume_mesh": "a" * 64,
        },
    )
    body = generated_hull_plus_deck_body(hull, stations=8)
    closed_hash = closed_body_content_sha256(body)

    with pytest.raises(MeshEvidenceBindError) as exc_info:
        bind_evidence_to_mesh_package(
            evidence,
            closed_body_hash=closed_hash,
            polymesh_dir=polymesh_dir,
        )

    assert exc_info.value.code == "polymesh_artifact_drift"
    assert "points" in exc_info.value.message


def test_default_mesh_package_invocation_unchanged_when_bind_evidence_absent(
    tmp_path: Path,
) -> None:
    """Without ``bound_volume_mesh_diagnostic`` the manifest JSON is byte-equal."""
    hull = Hull(name="rfc0045-byte-equal-regression", bow_rake=0.0, stern_rake=0.0)
    package_a = tmp_path / "a"
    package_b = tmp_path / "b"

    manifest_a = write_mesh_package(hull, package_a, stations=8)
    manifest_b = write_mesh_package(
        hull,
        package_b,
        stations=8,
        bound_volume_mesh_diagnostic=None,
    )

    assert manifest_a == manifest_b
    bytes_a = (package_a / "manifest.json").read_bytes()
    bytes_b = (package_b / "manifest.json").read_bytes()
    assert bytes_a == bytes_b
    assert manifest_a.readiness.level != "cfd_ready"
    assert manifest_a.volume_mesh_diagnostic is None
    assert manifest_a.readiness_authority == "surface_diagnostics"
