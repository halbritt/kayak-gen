"""OpenFOAM-v2512 case-template and parser hardening tests.

These tests pin the locked case-template version, the v2512 provenance probe
contract, and the v2512 force.dat parser layout. None of them invoke a real
OpenFOAM binary; the provenance probe accepts an injected runner so the
adapter contract can be exercised entirely offline.

See RFC 0041 (CFD readiness handoff) and workflow 0052 successor decisions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kayakgen.eval.cfd.jobs import (
    CfdDispatchError,
    CfdOpenFoamForceDatResult,
    CfdOpenFoamRawResult,
    OPENFOAM_CASE_TEMPLATE_VERSION,
    OPENFOAM_FORCE_DAT_OUTPUT,
    OPENFOAM_PROFILE_NAME,
    OPENFOAM_REQUIRED_VERSION,
    OPENFOAM_SOLVER_NAME,
    OpenFoamProvenanceProbe,
    openfoam_v2512_interfoam_local_profile,
    parse_openfoam_force_dat,
    probe_openfoam_provenance,
    solver_profile_by_name,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "openfoam_v2512"
CANONICAL_FIXTURE = FIXTURE_ROOT / "force_canonical.dat"
LEGACY_V2306_FIXTURE = FIXTURE_ROOT / "force_v2306_legacy.dat"
CORRUPT_FIXTURE = FIXTURE_ROOT / "force_corrupt.dat"


# ---------------------------------------------------------------------------
# Case-template and profile shape


def test_openfoam_case_template_version_constant_is_locked() -> None:
    """Stage 2 locks the case-template version string used everywhere."""
    assert OPENFOAM_CASE_TEMPLATE_VERSION == "openfoam-v2512-interfoam-dtchull-v1"


def test_openfoam_profile_reports_required_mesh_profile_and_case_template() -> None:
    """The profile contract surfaces the locked mesh profile + case template."""
    profile = openfoam_v2512_interfoam_local_profile()
    by_name = solver_profile_by_name(OPENFOAM_PROFILE_NAME)
    assert profile == by_name
    assert profile.required_mesh_profile == "watertight_solid_resistance_v1"
    assert profile.case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
    assert profile.required_solver_version == OPENFOAM_REQUIRED_VERSION
    assert profile.solver_name == OPENFOAM_SOLVER_NAME
    assert profile.expected_raw_outputs == [OPENFOAM_FORCE_DAT_OUTPUT]
    assert profile.required_mesh_readiness == "cfd_ready"
    assert profile.adapter_name == "openfoam_local"
    assert profile.result_semantics == "raw_unvalidated"
    assert profile.claim_state == "raw_unvalidated"
    assert profile.accepted_uses == []


# ---------------------------------------------------------------------------
# Provenance probe (application/build/API), with injectable runner


def _runner_for(
    commands_map: dict[tuple[str, ...], tuple[int, str, str]],
) -> "callable":
    """Build an OpenFoamProbeRunner that returns canned outputs by command tuple."""

    def _runner(command: list[str]) -> tuple[int, str, str]:
        return commands_map[tuple(command)]

    return _runner


def test_provenance_probe_accepts_application_build_api_channels() -> None:
    """When the solver-reported probes confirm v2512, provenance is accepted."""
    runner = _runner_for(
        {
            ("interFoam", "-help"): (
                0,
                "Build  : OpenFOAM-v2512-abc1234\n",
                "",
            ),
            ("foamVersion", "-build"): (0, "OpenFOAM-v2512-abc1234\n", ""),
            ("foamVersion", "-api"): (0, "2512\n", ""),
            ("foamVersion",): (0, "OpenFOAM-v2512\n", ""),
        }
    )

    probe = probe_openfoam_provenance(runner=runner, env={})

    assert isinstance(probe, OpenFoamProvenanceProbe)
    assert probe.application is not None and "v2512" in probe.application
    assert probe.build is not None and "v2512" in probe.build
    assert probe.api == "2512"
    assert probe.project_version is not None and "v2512" in probe.project_version
    assert probe.env_project_version is None
    accepted, reason = probe.matches_required("v2512")
    assert accepted is True
    assert reason is None


def test_provenance_probe_rejects_env_only_v2512_evidence() -> None:
    """A bare $WM_PROJECT_VERSION is NOT sufficient v2512 evidence on its own."""

    def runner(command: list[str]) -> tuple[int, str, str]:
        # Every probe fails; only the env variable claims v2512.
        return (127, "", "command not found")

    probe = probe_openfoam_provenance(
        runner=runner, env={"WM_PROJECT_VERSION": "v2512"}
    )

    assert probe.application is None
    assert probe.build is None
    assert probe.api is None
    assert probe.project_version is None
    assert probe.env_project_version == "v2512"
    accepted, reason = probe.matches_required("v2512")
    assert accepted is False
    assert reason is not None
    assert "WM_PROJECT_VERSION" in reason


def test_provenance_probe_rejects_when_no_channel_reports_required_token() -> None:
    """A solver that reports only v2306 must not satisfy the v2512 contract."""

    def runner(command: list[str]) -> tuple[int, str, str]:
        return (0, "OpenFOAM-v2306\n", "")

    probe = probe_openfoam_provenance(runner=runner, env={})
    accepted, reason = probe.matches_required("v2512")
    assert accepted is False
    assert reason is not None
    assert "v2512" in reason


# ---------------------------------------------------------------------------
# Parser robustness fixtures


def test_parser_accepts_canonical_v2512_force_dat() -> None:
    """The canonical v2512 fixture (real interFoam smoke output, no porous
    columns) parses into total/pressure/viscous force triples."""
    parsed = parse_openfoam_force_dat(
        CANONICAL_FIXTURE,
        source_ref="fixtures/openfoam_v2512/force_canonical.dat",
    )

    assert isinstance(parsed, CfdOpenFoamForceDatResult)
    assert parsed.source_ref == "fixtures/openfoam_v2512/force_canonical.dat"
    assert parsed.sample_count == 5
    assert parsed.last_sample.time_s == pytest.approx(0.05)
    # values copied verbatim from the smoke-captured force.dat
    assert parsed.last_sample.total_force_n == pytest.approx(
        (14.0680819, -0.244039645, 1095.24974)
    )
    assert parsed.last_sample.pressure_force_n == pytest.approx(
        (9.15223143, -0.242915878, 1095.41104)
    )
    assert parsed.last_sample.viscous_force_n == pytest.approx(
        (4.91585045, -0.00112376755, -0.161301754)
    )
    assert parsed.last_sample.porous_force_n == pytest.approx((0.0, 0.0, 0.0))
    assert parsed.last_sample.porous_recorded is False
    assert parsed.last_sample.drag_force_n == pytest.approx(14.0680819)
    assert parsed.claim_state == "raw_unvalidated"
    assert parsed.accepted_uses == []


def test_parser_accepts_canonical_v2512_force_dat_with_porous() -> None:
    """The 13-field with-porous variant parses and flags porous_recorded."""
    parsed = parse_openfoam_force_dat(
        Path(__file__).parent
        / "fixtures"
        / "openfoam_v2512"
        / "force_canonical_with_porous.dat"
    )
    assert parsed.sample_count == 2
    assert parsed.last_sample.porous_recorded is True
    assert parsed.last_sample.porous_force_n == pytest.approx((8.0, 0.0, 0.0))


def test_parser_rejects_v2306_legacy_force_dat_with_unsupported_layout() -> None:
    """Legacy parenthesised-tuple layout must be rejected, not silently parsed."""
    with pytest.raises(CfdDispatchError) as excinfo:
        parse_openfoam_force_dat(LEGACY_V2306_FIXTURE)

    assert excinfo.value.code == "unsupported_layout"
    message = str(excinfo.value).lower()
    assert "v2512" in message or "parenthes" in message or "tabular" in message


def test_parser_rejects_corrupt_short_force_dat() -> None:
    """A truncated/corrupt file with too few numeric fields is rejected."""
    with pytest.raises(CfdDispatchError) as excinfo:
        parse_openfoam_force_dat(CORRUPT_FIXTURE)

    # The corrupt fixture trips header detection first because its only
    # header line uses the legacy parenthesised-tuple notation. Either
    # error code is acceptable as long as the parser refuses to produce a
    # spurious sample.
    assert excinfo.value.code in {"malformed_output", "unsupported_layout"}


def test_parser_rejects_missing_force_dat_path(tmp_path: Path) -> None:
    """A missing file yields ``missing_output``, not a stray IO error."""
    missing = tmp_path / "no-such-force.dat"
    with pytest.raises(CfdDispatchError) as excinfo:
        parse_openfoam_force_dat(missing)
    assert excinfo.value.code == "missing_output"


# ---------------------------------------------------------------------------
# Succeeded path remains BLOCKED until ALL invariants bind


def test_succeeded_raw_result_invariants_bind_case_template_and_payload_class() -> None:
    """A v2512 raw result requires raw_unvalidated payload and the locked template.

    This guards the four invariants that gate ``succeeded``:
      * mesh profile == watertight_solid_resistance_v1
      * mesh readiness == cfd_ready
      * case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
      * result_semantics / claim_state == raw_unvalidated, accepted_uses == []
    """
    raw = CfdOpenFoamRawResult(
        job_id="cfd-openfoam-fixture",
        solver_name=OPENFOAM_SOLVER_NAME,
        solver_version="OpenFOAM-v2512",
        speed_mps=2.4,
        seawater_density_kg_m3=1025.0,
        kinematic_viscosity_m2_s=1.19e-6,
        mesh_profile="watertight_solid_resistance_v1",
        mesh_readiness="cfd_ready",
        drag_force_n=5.5,
        raw_output_refs=["postProcessing/forces/0/force.dat"],
        command=["interFoam", "-case", "case/openfoam"],
        version_command=["foamVersion"],
        returncode=0,
    )
    assert raw.case_template_version == OPENFOAM_CASE_TEMPLATE_VERSION
    assert raw.result_semantics == "raw_unvalidated"
    assert raw.claim_state == "raw_unvalidated"
    assert raw.accepted_uses == []
    assert raw.mesh_profile == "watertight_solid_resistance_v1"
    assert raw.mesh_readiness == "cfd_ready"


def test_succeeded_raw_result_rejects_non_v2512_case_template() -> None:
    """The raw result schema literal forbids any non-v2512 case template tag."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CfdOpenFoamRawResult(
            job_id="cfd-openfoam-fixture",
            solver_name=OPENFOAM_SOLVER_NAME,
            solver_version="OpenFOAM-v2512",
            case_template_version="some-other-template-v1",  # type: ignore[arg-type]
            speed_mps=2.4,
            seawater_density_kg_m3=1025.0,
            kinematic_viscosity_m2_s=1.19e-6,
            mesh_profile="watertight_solid_resistance_v1",
            mesh_readiness="cfd_ready",
            raw_output_refs=["postProcessing/forces/0/force.dat"],
            command=["interFoam"],
            version_command=["foamVersion"],
            returncode=0,
        )


def test_succeeded_raw_result_rejects_promotion_to_calibrated_payload() -> None:
    """The payload class is locked to raw_unvalidated; calibrated claims rejected."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CfdOpenFoamRawResult(
            job_id="cfd-openfoam-fixture",
            solver_name=OPENFOAM_SOLVER_NAME,
            solver_version="OpenFOAM-v2512",
            speed_mps=2.4,
            seawater_density_kg_m3=1025.0,
            kinematic_viscosity_m2_s=1.19e-6,
            mesh_profile="watertight_solid_resistance_v1",
            mesh_readiness="cfd_ready",
            raw_output_refs=["postProcessing/forces/0/force.dat"],
            command=["interFoam"],
            version_command=["foamVersion"],
            returncode=0,
            claim_state="calibrated_model",
        )
