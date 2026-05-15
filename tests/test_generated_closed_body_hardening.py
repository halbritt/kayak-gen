"""RFC 0040 generated-body hardening matrix.

Exercises the RFC 0022 generated hull-plus-deck closed body across a
parameter matrix covering rake, waterline beam, draft, prismatic, and
midship coefficients. Each fixture round-trips the closed-volume
diagnostic, asserts the body remains a closed evaluation body (positive
signed volume, self-intersection recorded, source hull hash present),
and confirms the ordinary generated mesh package stays below
``cfd_ready`` when assessed against the default open wetted-surface
resistance profile.

The hardening matrix complements
``tests/test_generated_closed_body.py`` by binding each parameter slice
to the solver-readiness contract surface and recording the expected
blocker/warning reasons the readiness report emits when the package
lacks volume-mesh evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from kayakgen.eval.closed_volume import (
    ClosedVolumeBody,
    ClosedVolumeDiagnostics,
    diagnose_closed_volume_body,
    generated_hull_plus_deck_closed_body,
)
from kayakgen.eval.mesh_package import (
    closed_volume_solver_readiness_report,
    open_wetted_surface_profile,
    write_mesh_package,
)
from kayakgen.model.hull import Hull


GENERATED_PROFILE = "generated_hull_plus_deck_closed_body_v1"
GENERATED_BODY_TYPE = "generated_hull_plus_deck_closed_body"

# Solver dispatch shapes used by readiness-report tests. The first profile
# describes what an ordinary open wetted-surface request looks like and
# the second describes the watertight-solid dispatch a CFD job needs.
OPEN_DISPATCH_PROFILE: dict[str, str] = {
    "name": "open-wetted-surface",
    "required_mesh_profile": "open_wetted_surface_resistance_v1",
    "required_mesh_readiness": "cfd_surface_candidate",
}
WATERTIGHT_DISPATCH_PROFILE: dict[str, str] = {
    "name": "unavailable-watertight-solid",
    "required_mesh_profile": "watertight_solid_resistance_v1",
    "required_mesh_readiness": "cfd_ready",
}


@dataclass(frozen=True)
class HardeningCase:
    """A single parameter slice in the hardening matrix."""

    case_id: str
    hull: Hull
    note: str


def _matrix_cases() -> list[HardeningCase]:
    """Return the parameter-matrix fixtures the hardening tests exercise."""

    return [
        HardeningCase(
            case_id="default",
            hull=Hull(name="hardening-default"),
            note="default raked Hull init",
        ),
        HardeningCase(
            case_id="exact-plumb",
            hull=Hull(
                name="hardening-exact-plumb",
                bow_rake=0.0,
                stern_rake=0.0,
            ),
            note="bow_rake=0 and stern_rake=0",
        ),
        HardeningCase(
            case_id="mixed-rake-plumb-bow",
            hull=Hull(
                name="hardening-mixed-rake-plumb-bow",
                bow_rake=0.0,
                stern_rake=1.0,
            ),
            note="plumb bow, raked stern",
        ),
        HardeningCase(
            case_id="mixed-rake-plumb-stern",
            hull=Hull(
                name="hardening-mixed-rake-plumb-stern",
                bow_rake=1.0,
                stern_rake=0.0,
            ),
            note="raked bow, plumb stern",
        ),
        HardeningCase(
            case_id="waterline-pinch",
            hull=Hull(
                name="hardening-waterline-pinch",
                beam_oa_m=0.60,
                beam_wl_m=0.46,
                bow_rake=0.0,
                stern_rake=0.0,
            ),
            note="beam_wl_m markedly less than beam_oa_m",
        ),
        HardeningCase(
            case_id="shallow-draft",
            hull=Hull(name="hardening-shallow-draft", draft_m=0.09),
            note="draft_m near elite surfski lower bound",
        ),
        HardeningCase(
            case_id="deep-draft",
            hull=Hull(name="hardening-deep-draft", draft_m=0.14),
            note="draft_m at touring upper bound",
        ),
        HardeningCase(
            case_id="low-cp",
            hull=Hull(name="hardening-low-cp", Cp=0.50),
            note="prismatic coefficient near class lower bound",
        ),
        HardeningCase(
            case_id="high-cp",
            hull=Hull(name="hardening-high-cp", Cp=0.62),
            note="prismatic coefficient above elite class default",
        ),
        HardeningCase(
            case_id="low-cm",
            hull=Hull(name="hardening-low-cm", Cm=0.70),
            note="midship coefficient near lower bound",
        ),
        HardeningCase(
            case_id="high-cm",
            hull=Hull(name="hardening-high-cm", Cm=0.95),
            note="midship coefficient near upper bound",
        ),
    ]


MATRIX = _matrix_cases()


def _matrix_ids(cases: list[HardeningCase]) -> list[str]:
    return [case.case_id for case in cases]


def _build_body(hull: Hull) -> ClosedVolumeBody:
    return generated_hull_plus_deck_closed_body(hull, stations=10)


def _assert_diagnostic_contract(
    diagnostics: ClosedVolumeDiagnostics,
    hull: Hull,
    *,
    case_id: str,
) -> None:
    """Verify the generated body satisfies the closed-volume contract."""

    # Body-ref identity: hash present, matches the source hull, and the
    # body_id is recorded so manifest cross-checks have a stable handle.
    assert diagnostics.source_hull_hash, case_id
    assert diagnostics.source_hull_hash == hull.hash(), case_id
    assert diagnostics.body_id, case_id

    # Profile / body type identity: this is a generated kayak body and
    # the profile pins the RFC 0022 contract surface.
    assert diagnostics.body_type == GENERATED_BODY_TYPE, case_id
    assert diagnostics.profile_name == GENERATED_PROFILE, case_id

    # Readiness must be closed_volume with no blocking reasons.
    assert diagnostics.readiness.level == "closed_volume", case_id
    assert diagnostics.readiness.reasons == [], case_id

    # Topology counters: closed body has zero boundary/non-manifold edges,
    # zero degenerate or non-finite faces, and no out-of-range indices.
    assert diagnostics.raw_boundary_edges == 0, case_id
    assert diagnostics.welded_boundary_edges == 0, case_id
    assert diagnostics.raw_nonmanifold_edges == 0, case_id
    assert diagnostics.welded_nonmanifold_edges == 0, case_id
    assert diagnostics.degenerate_faces == 0, case_id
    assert diagnostics.nonfinite_vertices == 0, case_id
    assert diagnostics.nonfinite_faces == 0, case_id
    assert diagnostics.invalid_face_indices == 0, case_id

    # Self-intersection must be recorded (not the RFC 0016 stub) and pass.
    assert diagnostics.self_intersection_status == "passed", case_id
    assert (
        diagnostics.self_intersection_algorithm
        != "not_checked_rfc0016_compatibility"
    ), case_id
    assert diagnostics.self_intersection_pair_count == 0, case_id
    assert diagnostics.self_intersection_example_pairs == [], case_id

    # Positive signed volume strictly above tolerance.
    tolerance = diagnostics.policy.tolerances.signed_volume_tolerance_m3
    assert diagnostics.signed_volume_m3 > tolerance, case_id

    # Closed-volume bodies never claim cfd_ready under RFC 0022.
    assert diagnostics.cfd_ready is False, case_id

    # Waterline metadata is recorded without cutting the body.
    waterline = diagnostics.waterline_metadata
    assert waterline is not None, case_id
    assert waterline.waterline_z_m == pytest.approx(0.0), case_id
    expected_beam_wl = (
        hull.beam_wl_m if hull.beam_wl_m is not None else hull.beam_oa_m
    )
    assert waterline.beam_wl_m == pytest.approx(expected_beam_wl), case_id


def _blocker_codes(report) -> set[str]:
    return {blocker.code for blocker in report.blockers}


def _warning_codes(report) -> set[str]:
    return {warning.code for warning in report.warnings}


@pytest.mark.parametrize(
    "case", MATRIX, ids=_matrix_ids(MATRIX)
)
def test_generated_body_diagnostics_round_trip(case: HardeningCase) -> None:
    """Each matrix slice round-trips the closed-volume diagnostic contract."""

    body = _build_body(case.hull)
    diagnostics = diagnose_closed_volume_body(body)

    _assert_diagnostic_contract(diagnostics, case.hull, case_id=case.case_id)

    # Serialization round-trip preserves every field including body_ref hash
    # and self-intersection records.
    serialized = diagnostics.model_dump_json()
    loaded = ClosedVolumeDiagnostics.model_validate_json(serialized)
    assert loaded == diagnostics, case.case_id


@pytest.mark.parametrize(
    "case", MATRIX, ids=_matrix_ids(MATRIX)
)
def test_generated_body_signed_volume_positive(case: HardeningCase) -> None:
    """Each matrix slice produces a strictly positive signed volume."""

    body = _build_body(case.hull)
    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.signed_volume_m3 > 0.0, case.case_id
    assert (
        diagnostics.signed_volume_m3
        > diagnostics.policy.tolerances.signed_volume_tolerance_m3
    ), case.case_id


@pytest.mark.parametrize(
    "case", MATRIX, ids=_matrix_ids(MATRIX)
)
def test_generated_body_self_intersection_recorded(
    case: HardeningCase,
) -> None:
    """Each matrix slice records a non-stub self-intersection status."""

    body = _build_body(case.hull)
    diagnostics = diagnose_closed_volume_body(body)

    assert diagnostics.self_intersection_status == "passed", case.case_id
    # The RFC 0021 conservative check must have actually run, not been
    # bypassed under the RFC 0016 compatibility profile.
    assert (
        diagnostics.self_intersection_algorithm
        == "assembled_welded_aabb_triangle_pairs_v1"
    ), case.case_id
    assert (
        diagnostics.policy.self_intersection_policy
        == "required_rfc0021_conservative"
    ), case.case_id


@pytest.mark.parametrize(
    "case", MATRIX, ids=_matrix_ids(MATRIX)
)
def test_ordinary_generated_package_stays_below_cfd_ready(
    case: HardeningCase,
    tmp_path: Path,
) -> None:
    """Ordinary generated packages must remain below ``cfd_ready``.

    Per workflow 0052/0053 decisions, the generated open wetted-surface
    package never promotes to ``cfd_ready`` because it lacks verified
    volume-mesh evidence. This test confirms that for every hardening
    case the readiness manifest, the open-profile readiness report, and
    the watertight dispatch readiness report all block on the absence
    of the closed-body diagnostic and volume mesh.
    """

    profile = open_wetted_surface_profile()
    manifest = write_mesh_package(
        case.hull,
        tmp_path,
        stations=8,
        solver_profile=profile,
    )

    # Surface manifest never reaches cfd_ready and never claims to be the
    # generated closed body itself.
    assert manifest.readiness.level != "cfd_ready", case.case_id
    assert manifest.readiness_authority == "surface_diagnostics", case.case_id
    assert manifest.body_ref is None, case.case_id
    assert manifest.closed_volume_diagnostic is None, case.case_id
    assert manifest.volume_mesh_diagnostic is None, case.case_id

    # The readiness report against an open dispatch records the expected
    # blockers for missing generated-body and volume-mesh evidence. The
    # ``open_surface_not_closed_body`` code is reserved for the watertight
    # dispatch path; the open dispatch should not raise it.
    open_report = closed_volume_solver_readiness_report(
        manifest,
        solver_profile=OPEN_DISPATCH_PROFILE,
    )
    assert open_report.gate_status == "blocked", case.case_id
    assert open_report.input_semantics == "not_solver_input", case.case_id
    open_blockers = _blocker_codes(open_report)
    assert {"generated_body_missing", "volume_mesh_missing"} <= open_blockers, (
        case.case_id,
        open_blockers,
    )
    open_warnings = _warning_codes(open_report)
    assert "raw_solver_output_not_validated" in open_warnings, case.case_id
    assert "readiness_authority_not_volume_mesh" in open_warnings, case.case_id

    # Watertight dispatch additionally blocks because the package solver
    # profile does not match and the package is not a closed-volume body.
    watertight_report = closed_volume_solver_readiness_report(
        manifest,
        solver_profile=WATERTIGHT_DISPATCH_PROFILE,
    )
    assert watertight_report.gate_status == "blocked", case.case_id
    watertight_blockers = _blocker_codes(watertight_report)
    assert {
        "solver_profile_not_satisfied",
        "open_surface_not_closed_body",
        "generated_body_missing",
        "volume_mesh_missing",
    } <= watertight_blockers, (case.case_id, watertight_blockers)


@pytest.mark.parametrize(
    "case", MATRIX, ids=_matrix_ids(MATRIX)
)
def test_generated_body_diagnostic_paired_with_open_manifest_still_blocked(
    case: HardeningCase,
    tmp_path: Path,
) -> None:
    """Even when the closed-body diagnostic is provided, the open
    wetted-surface manifest stays below ``cfd_ready`` because no volume
    mesh evidence backs the package. The readiness report should drop
    the ``generated_body_missing`` blocker but retain
    ``volume_mesh_missing`` and emit the
    ``generated_body_not_solver_input`` warning that documents why a
    generated closed body alone is not solver input.
    """

    profile = open_wetted_surface_profile()
    manifest = write_mesh_package(
        case.hull,
        tmp_path,
        stations=8,
        solver_profile=profile,
    )

    body = _build_body(case.hull)
    diagnostics = diagnose_closed_volume_body(body)
    _assert_diagnostic_contract(diagnostics, case.hull, case_id=case.case_id)

    # The diagnostic body_ref must match the body we attach; since the
    # ordinary manifest has no body_ref of its own we copy the diagnostic
    # body_id in to exercise the matching branch.
    manifest = manifest.model_copy(update={"body_ref": diagnostics.body_id})

    report = closed_volume_solver_readiness_report(
        manifest,
        solver_profile=OPEN_DISPATCH_PROFILE,
        closed_volume_diagnostics=diagnostics,
        self_intersection_diagnostics=diagnostics,
    )

    assert report.gate_status == "blocked", case.case_id
    blockers = _blocker_codes(report)
    # generated_body_missing no longer fires because evidence is present.
    assert "generated_body_missing" not in blockers, case.case_id
    # Volume mesh evidence is still absent, so dispatch remains blocked.
    assert "volume_mesh_missing" in blockers, case.case_id
    # Warnings document the generated-body-as-evidence-only stance.
    warnings = _warning_codes(report)
    assert "generated_body_not_solver_input" in warnings, case.case_id
    assert "raw_solver_output_not_validated" in warnings, case.case_id

    # The closed-body diagnostic is still not cfd_ready and the report
    # surfaces the generated profile name from the diagnostic.
    assert diagnostics.cfd_ready is False, case.case_id
    assert report.body_profile == GENERATED_PROFILE, case.case_id
    assert report.body_ref == diagnostics.body_id, case.case_id
