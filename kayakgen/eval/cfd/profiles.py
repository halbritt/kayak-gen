"""Built-in solver dispatch profile factories.

Provides the named ``SolverProfile`` factories used by the CLI/UI dispatch
surface, plus the registry helpers that look profiles up by canonical name
or known alias. Split out from the historical
``kayakgen.eval.cfd.jobs`` per Phase 3A of
``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.
"""

from __future__ import annotations

import sys

from kayakgen.eval.cfd.records import CfdDispatchError, SolverProfile

CFD_RAW_RESULTS_WARNING = "CFD results are raw and unvalidated."
CFD_FIXTURE_RESULTS_WARNING = (
    "Fixture CFD output is not calibrated, validated, or final design fitness."
)
FIXTURE_CASE_TEMPLATE_VERSION = "fixture-local-command-v1"
FIXTURE_RAW_OUTPUT = "raw-result.json"
OPENFOAM_PROFILE_NAME = "openfoam-v2512-interfoam-local"
OPENFOAM_SOLVER_NAME = "OpenFOAM.com OpenFOAM-v2512 interFoam"
OPENFOAM_REQUIRED_VERSION = "v2512"
OPENFOAM_CASE_TEMPLATE_VERSION = "openfoam-v2512-interfoam-dtchull-v1"
OPENFOAM_CASE_ROOT = "case/openfoam"
OPENFOAM_CASE_INPUT = "case/openfoam/kayakgen-case.json"
OPENFOAM_COMMAND_SPEC = "case/openfoam/kayakgen-command.json"
OPENFOAM_FORCE_DAT_OUTPUT = "postProcessing/forces/0/force.dat"
OPENFOAM_RAW_RESULT = "openfoam-raw-result.json"
OPENFOAM_COMMAND_TIMEOUT_SECONDS = 60.0
OPENFOAM_LOG_LIMIT_BYTES = 65536
CFD_OPENFOAM_RESULTS_WARNING = (
    "OpenFOAM adapter skeleton output is not calibrated, validated, or final design fitness."
)
OPENFOAM_SUCCESS_BLOCKED_WARNING = (
    "OpenFOAM command output is parser-readable, but this run did not satisfy "
    "the opt-in/evidence gate for a real succeeded path; raw output remains "
    "unvalidated."
)
OPENFOAM_LOCAL_RUN_ENV_VAR = "KAYAKGEN_OPENFOAM_LOCAL_RUN"
OPENFOAM_SUCCEEDED_RAW_UNVALIDATED_WARNING = (
    "OpenFOAM-v2512 interFoam run completed; raw output is unvalidated and not "
    "calibrated for any design-fitness use."
)


def unavailable_open_surface_profile() -> SolverProfile:
    """Return an unavailable profile that accepts current open-surface packages."""
    return SolverProfile(
        name="unavailable-open-wetted-surface",
        required_mesh_readiness="cfd_surface_candidate",
        adapter_name="unavailable",
        required_mesh_profile="open_wetted_surface_resistance_v1",
    )


def unavailable_watertight_solid_profile() -> SolverProfile:
    """Return an unavailable future profile requiring watertight CFD readiness."""
    return SolverProfile(
        name="unavailable-watertight-solid",
        required_mesh_readiness="cfd_ready",
        adapter_name="unavailable",
        required_mesh_profile="watertight_solid_resistance_v1",
    )


def mock_failing_local_command_profile() -> SolverProfile:
    """Return a local-command profile that deliberately fails for dispatch tests."""
    return SolverProfile(
        name="mock-failing-local-command",
        required_mesh_readiness="cfd_surface_candidate",
        adapter_name="mock_local_command",
        command_template=[
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.write('mock CFD command starting\\n'); "
                "sys.stderr.write('mock CFD command failed intentionally\\n'); "
                "sys.exit(7)"
            ),
        ],
        required_mesh_profile="open_wetted_surface_resistance_v1",
    )


def fixture_local_command_profile() -> SolverProfile:
    """Return the deterministic fixture profile for local command dispatch."""
    return SolverProfile(
        name="fixture-local-command",
        required_mesh_readiness="cfd_surface_candidate",
        adapter_name="fixture_local_command",
        command_template=[
            sys.executable,
            "-m",
            "kayakgen.eval.cfd.fixture_command",
            "--case",
            "case/fixture-case.json",
            "--out",
            FIXTURE_RAW_OUTPUT,
        ],
        required_mesh_profile="open_wetted_surface_resistance_v1",
    )


def openfoam_v2512_interfoam_local_profile() -> SolverProfile:
    """Return the first external-solver skeleton profile selected by D004."""
    return SolverProfile(
        name=OPENFOAM_PROFILE_NAME,
        required_mesh_readiness="cfd_ready",
        adapter_name="openfoam_local",
        command_template=[
            "interFoam",
            "-case",
            OPENFOAM_CASE_ROOT,
        ],
        solver_name=OPENFOAM_SOLVER_NAME,
        solver_version_command=["foamVersion"],
        required_solver_version=OPENFOAM_REQUIRED_VERSION,
        case_template_version=OPENFOAM_CASE_TEMPLATE_VERSION,
        supported_platforms=[
            "Linux primary local install",
            "macOS optional Docker/source route",
            "Windows optional WSL/Docker route",
        ],
        supported_speed_range_mps=(0.1, 6.0),
        supported_fluid_model="local incompressible two-phase water/air interFoam skeleton",
        expected_raw_outputs=[OPENFOAM_FORCE_DAT_OUTPUT],
        install_notes=(
            "Requires OpenFOAM.com OpenFOAM-v2512 on PATH; required CI uses "
            "fake commands and parser fixtures instead of an installed solver."
        ),
        known_limitations=[
            "Ordinary generated packages still require matching OpenFOAM-readable volume mesh evidence.",
            "Real OpenFOAM succeeded run records require explicit RFC 0046 opt-in and remain raw_unvalidated.",
            "Any parsed force.dat value is raw_unvalidated and not calibrated CFD.",
        ],
        timeout_seconds=OPENFOAM_COMMAND_TIMEOUT_SECONDS,
        log_limit_bytes=OPENFOAM_LOG_LIMIT_BYTES,
        required_mesh_profile="watertight_solid_resistance_v1",
    )


def _solver_profiles() -> dict[str, SolverProfile]:
    profiles = (
        unavailable_open_surface_profile(),
        unavailable_watertight_solid_profile(),
        mock_failing_local_command_profile(),
        fixture_local_command_profile(),
        openfoam_v2512_interfoam_local_profile(),
    )
    return {profile.name: profile for profile in profiles}


def _solver_profile_by_name(name: str) -> SolverProfile:
    profiles = _solver_profiles()
    aliases = {
        "unavailable_open_wetted_surface_v1": "unavailable-open-wetted-surface",
        "unavailable_watertight_solid_v1": "unavailable-watertight-solid",
        "mock_failing_local_command_v1": "mock-failing-local-command",
        "fixture_local_command_v1": "fixture-local-command",
        "openfoam_v2512_interfoam_local_v1": OPENFOAM_PROFILE_NAME,
    }
    name = aliases.get(name, name)
    try:
        return profiles[name]
    except KeyError as exc:
        available = ", ".join(sorted(profiles))
        raise CfdDispatchError(
            f"unknown solver profile {name!r}; available profiles: {available}"
        ) from exc


def solver_profile_names() -> tuple[str, ...]:
    """Return the names of built-in local dispatch profiles."""
    return tuple(sorted(_solver_profiles()))


def solver_profiles() -> tuple[SolverProfile, ...]:
    """Return built-in local dispatch profiles in deterministic name order."""
    profiles = _solver_profiles()
    return tuple(profiles[name] for name in sorted(profiles))


def solver_profile_by_name(name: str) -> SolverProfile:
    """Return a built-in local dispatch profile by public name or accepted alias."""
    return _solver_profile_by_name(name)


__all__ = [
    "CFD_FIXTURE_RESULTS_WARNING",
    "CFD_OPENFOAM_RESULTS_WARNING",
    "CFD_RAW_RESULTS_WARNING",
    "FIXTURE_CASE_TEMPLATE_VERSION",
    "FIXTURE_RAW_OUTPUT",
    "OPENFOAM_CASE_INPUT",
    "OPENFOAM_CASE_ROOT",
    "OPENFOAM_CASE_TEMPLATE_VERSION",
    "OPENFOAM_COMMAND_SPEC",
    "OPENFOAM_COMMAND_TIMEOUT_SECONDS",
    "OPENFOAM_FORCE_DAT_OUTPUT",
    "OPENFOAM_LOCAL_RUN_ENV_VAR",
    "OPENFOAM_LOG_LIMIT_BYTES",
    "OPENFOAM_PROFILE_NAME",
    "OPENFOAM_RAW_RESULT",
    "OPENFOAM_REQUIRED_VERSION",
    "OPENFOAM_SOLVER_NAME",
    "OPENFOAM_SUCCEEDED_RAW_UNVALIDATED_WARNING",
    "OPENFOAM_SUCCESS_BLOCKED_WARNING",
    "fixture_local_command_profile",
    "mock_failing_local_command_profile",
    "openfoam_v2512_interfoam_local_profile",
    "solver_profile_by_name",
    "solver_profile_names",
    "solver_profiles",
    "unavailable_open_surface_profile",
    "unavailable_watertight_solid_profile",
]
