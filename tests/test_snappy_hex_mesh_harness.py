"""Deterministic ``snappyHexMesh`` evidence-harness tests for OpenFOAM-v2512.

These tests pin the workflow 0052 D011 contract: a locked case-template
version, deterministic dictionary scaffolds keyed by body identity,
hash-based dispatch gates that REJECT missing evidence, and the rule that
ordinary generated packages never gain a ``cfd_ready`` promotion path
merely because the harness module is imported.

No real ``snappyHexMesh`` is invoked.
"""

from __future__ import annotations

import pytest

from kayakgen.eval.closed_volume import (
    ClosedVolumeBody,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.cfd.jobs import OpenFoamProvenanceProbe
from kayakgen.eval.mesh_package import (
    closed_volume_solver_readiness_report_from_package,
    watertight_solid_profile,
    write_watertight_volume_mesh_handoff_package,
)
from kayakgen.eval.snappy_hex_mesh import (
    REQUIRED_DICT_KEYS,
    SNAPPYHEXMESH_CASE_TEMPLATE_VERSION,
    CheckMeshSummary,
    SnappyHexMeshDispatchState,  # noqa: F401  (imported for type re-export check)
    SnappyHexMeshEvidence,
    SnappyHexMeshPatchEntry,
    build_snappy_hex_mesh_evidence,
    compute_dict_hashes,
    default_snappy_hex_mesh_dict_scaffold,
    snappy_hex_mesh_volume_mesh_diagnostic,
)
from kayakgen.eval.volume_mesh import (
    snappy_hex_mesh_volume_mesh_diagnostic as snappy_volume_diagnostic_via_volume_mesh,
)
from kayakgen.model.hull import Hull


def _accepted_v2512_provenance() -> OpenFoamProvenanceProbe:
    return OpenFoamProvenanceProbe(
        application="OpenFOAM-v2512",
        build="OpenFOAM-v2512-abc1234",
        api="2512",
        project_version="OpenFOAM-v2512",
        env_project_version=None,
        raw={"application": "OpenFOAM-v2512", "api": "2512"},
    )


def _passing_check_mesh(n_cells: int = 8_000) -> CheckMeshSummary:
    return CheckMeshSummary(
        passed=True,
        n_cells=n_cells,
        n_internal_faces=n_cells * 3,
        n_boundary_faces=2_400,
        max_non_orthogonality_deg=55.0,
        max_skewness=2.5,
        aspect_ratio_max=10.0,
        warnings=[],
    )


def _hull_body() -> ClosedVolumeBody:
    hull = Hull(name="snappy-harness", bow_rake=0.0, stern_rake=0.0)
    return generated_hull_plus_deck_body(hull, stations=6, section_points=8)


def _fully_bound_evidence_kwargs(body: ClosedVolumeBody) -> dict[str, object]:
    scaffolds = default_snappy_hex_mesh_dict_scaffold(body)
    dict_hashes = compute_dict_hashes(scaffolds)
    body_ref_hash = body.source_hull_hash or "no-hash"
    return {
        "body_ref_hash": body_ref_hash,
        "dictionary_hashes": dict_hashes,
        "patch_metadata": [
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
        "check_mesh": _passing_check_mesh(),
        "artifact_checksums": {
            "volume_mesh": "a" * 64,
            "snappyHexMeshDict": "b" * 64,
        },
        "openfoam_provenance": _accepted_v2512_provenance(),
    }


# ---------------------------------------------------------------------------
# Locked constants and deterministic scaffolds


def test_snappyhexmesh_case_template_version_constant_is_locked() -> None:
    """Stage 2 locks the snappyHexMesh case-template version string."""
    assert (
        SNAPPYHEXMESH_CASE_TEMPLATE_VERSION
        == "openfoam-v2512-snappyhexmesh-watertight-v1"
    )
    assert set(REQUIRED_DICT_KEYS) == {
        "controlDict",
        "snappyHexMeshDict",
        "meshQualityDict",
        "surfaceFeatureExtractDict",
        "blockMeshDict",
    }


def test_default_dict_scaffolds_are_deterministic_given_body_hash() -> None:
    """Two calls with the same body produce byte-identical scaffolds and hashes."""
    body = _hull_body()
    scaffolds_first = default_snappy_hex_mesh_dict_scaffold(body)
    scaffolds_second = default_snappy_hex_mesh_dict_scaffold(body)

    assert set(scaffolds_first) == set(REQUIRED_DICT_KEYS)
    assert scaffolds_first == scaffolds_second
    assert compute_dict_hashes(scaffolds_first) == compute_dict_hashes(scaffolds_second)


def test_dict_hashes_change_when_scaffold_changes() -> None:
    """Editing any scaffold byte changes that dictionary's SHA-256 digest."""
    body = _hull_body()
    scaffolds = default_snappy_hex_mesh_dict_scaffold(body)
    baseline_hashes = compute_dict_hashes(scaffolds)

    mutated = dict(scaffolds)
    mutated["snappyHexMeshDict"] = (
        scaffolds["snappyHexMeshDict"] + "// mutated for harness test\n"
    )
    mutated_hashes = compute_dict_hashes(mutated)

    assert mutated_hashes["snappyHexMeshDict"] != baseline_hashes["snappyHexMeshDict"]
    for key in REQUIRED_DICT_KEYS:
        if key == "snappyHexMeshDict":
            continue
        assert mutated_hashes[key] == baseline_hashes[key]


# ---------------------------------------------------------------------------
# Dispatch rejection: every gate is required


def test_evidence_rejects_missing_dictionary_hashes() -> None:
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    kwargs["dictionary_hashes"] = {"controlDict": "deadbeef" * 8}
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "pending_evidence"
    assert "missing_dictionary_hashes" in evidence.dispatch_blocker_codes


def test_evidence_rejects_missing_check_mesh() -> None:
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    kwargs["check_mesh"] = None
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "pending_evidence"
    assert "missing_check_mesh" in evidence.dispatch_blocker_codes


def test_evidence_rejects_missing_v2512_provenance() -> None:
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    kwargs["openfoam_provenance"] = None
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "pending_evidence"
    assert "missing_openfoam_provenance" in evidence.dispatch_blocker_codes


def test_evidence_rejects_non_v2512_provenance_when_otherwise_bound() -> None:
    """A solver that only reports v2306 must not satisfy the v2512 contract."""
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    kwargs["openfoam_provenance"] = OpenFoamProvenanceProbe(
        application="OpenFOAM-v2306",
        build="OpenFOAM-v2306-deadbee",
        api="2306",
        project_version="OpenFOAM-v2306",
        env_project_version=None,
        raw={"application": "OpenFOAM-v2306"},
    )
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]
    assert evidence.dispatch_state == "pending_evidence"
    assert "openfoam_provenance_not_v2512" in evidence.dispatch_blocker_codes


def test_evidence_rejects_missing_body_ref_hash() -> None:
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    kwargs["body_ref_hash"] = ""
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "pending_evidence"
    assert "missing_body_ref_hash" in evidence.dispatch_blocker_codes


def test_evidence_rejects_check_mesh_failed_marker() -> None:
    """A ``checkMesh`` report with passed=False must surface as a blocker."""
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    failing = _passing_check_mesh()
    kwargs["check_mesh"] = failing.model_copy(
        update={"passed": False, "warnings": ["mesh failed checkMesh"]}
    )
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "pending_evidence"
    assert "check_mesh_failed" in evidence.dispatch_blocker_codes


def test_direct_construction_with_evidence_recorded_and_missing_field_raises() -> None:
    """Constructing the model directly with evidence_recorded must validate gates."""
    with pytest.raises(ValueError):
        SnappyHexMeshEvidence(
            body_ref_hash="",
            dictionary_hashes={},
            patch_metadata=[],
            check_mesh=None,
            artifact_checksums={},
            openfoam_provenance=None,
            dispatch_state="evidence_recorded",
            dispatch_blocker_codes=[],
        )


# ---------------------------------------------------------------------------
# Happy path: every gate satisfied


def test_fully_bound_evidence_records_dispatch_state_evidence_recorded() -> None:
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "evidence_recorded"
    assert evidence.dispatch_blocker_codes == []
    assert evidence.case_template_version == SNAPPYHEXMESH_CASE_TEMPLATE_VERSION
    assert evidence.body_profile == "generated_hull_plus_deck_closed_body_v1"
    assert set(evidence.dictionary_hashes) == set(REQUIRED_DICT_KEYS)
    assert evidence.check_mesh is not None
    assert evidence.check_mesh.passed is True
    assert any(p.role == "wetted_body" for p in evidence.patch_metadata)
    assert evidence.openfoam_provenance is not None


def test_volume_mesh_module_re_exports_diagnostic_translator() -> None:
    """The volume-mesh module exposes the harness translation helper."""
    body = _hull_body()
    evidence = build_snappy_hex_mesh_evidence(
        **_fully_bound_evidence_kwargs(body)
    )  # type: ignore[arg-type]
    direct = snappy_hex_mesh_volume_mesh_diagnostic(evidence)
    via_volume_mesh = snappy_volume_diagnostic_via_volume_mesh(evidence)
    assert direct is not None and via_volume_mesh is not None
    # Both call sites should agree on the same diagnostic content.
    assert direct.body_ref == via_volume_mesh.body_ref
    assert direct.boundary_patches == via_volume_mesh.boundary_patches


# ---------------------------------------------------------------------------
# Diagnostic translation refuses to promote on partial evidence


def test_snappy_hex_mesh_diagnostic_returns_none_for_partial_evidence() -> None:
    """Partial evidence must NOT translate into a volume-mesh diagnostic."""
    body = _hull_body()
    kwargs = _fully_bound_evidence_kwargs(body)
    kwargs["check_mesh"] = None
    evidence = build_snappy_hex_mesh_evidence(**kwargs)  # type: ignore[arg-type]

    assert evidence.dispatch_state == "pending_evidence"
    assert snappy_hex_mesh_volume_mesh_diagnostic(evidence) is None
    assert snappy_volume_diagnostic_via_volume_mesh(evidence) is None


def test_fully_bound_evidence_translates_to_cfd_ready_volume_mesh_diagnostic() -> None:
    """When every gate passes, translation yields a cfd_ready diagnostic."""
    body = _hull_body()
    evidence = build_snappy_hex_mesh_evidence(
        **_fully_bound_evidence_kwargs(body)
    )  # type: ignore[arg-type]

    diagnostic = snappy_hex_mesh_volume_mesh_diagnostic(evidence)
    assert diagnostic is not None
    assert diagnostic.readiness.level == "cfd_ready"
    assert diagnostic.mesher_name == "openfoam-v2512-snappyhexmesh"
    assert diagnostic.body_type == "generated_hull_plus_deck_closed_body"
    assert diagnostic.cell_count > 0
    assert diagnostic.boundary_face_count > 0
    patch_names = {patch.name for patch in diagnostic.boundary_patches}
    assert "hull" in patch_names


# ---------------------------------------------------------------------------
# Ordinary packages remain below cfd_ready after the module is importable


def test_ordinary_generated_package_stays_below_cfd_ready_after_harness_module_present(
    tmp_path,
) -> None:
    """Importing the harness module must NOT auto-promote ordinary packages.

    The default watertight handoff path (no fixture mesh, no harness
    evidence) MUST stay below ``cfd_ready`` even when the harness module
    is imported into the process.
    """
    # Importing the module here is intentional - it mirrors a real consumer
    # that may pull in the harness alongside ordinary mesh-package writers.
    import kayakgen.eval.snappy_hex_mesh as _harness_module  # noqa: F401

    hull = Hull(name="ordinary-package", bow_rake=0.0, stern_rake=0.0)
    package_dir = tmp_path / "ordinary-package"
    manifest = write_watertight_volume_mesh_handoff_package(
        hull,
        package_dir,
        stations=6,
        closed_body_stations=6,
        include_fixture_volume_mesh=False,
    )
    assert manifest.readiness.level != "cfd_ready"
    assert manifest.readiness_authority == "surface_diagnostics"

    profile = watertight_solid_profile()
    report = closed_volume_solver_readiness_report_from_package(
        package_dir,
        solver_profile=profile,
        required_mesh_profile=profile.profile_name,
    )
    assert report.gate_status == "blocked"
    assert report.input_semantics == "not_solver_input"
