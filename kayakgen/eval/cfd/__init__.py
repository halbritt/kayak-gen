"""CFD evaluation boundary and local dispatch helpers."""

from __future__ import annotations

from kayakgen.eval.cfd.jobs import (
    CFD_FIXTURE_RESULTS_WARNING,
    CFD_OPENFOAM_RESULTS_WARNING,
    CFD_RAW_RESULTS_WARNING,
    CfdDispatchError,
    CfdFixtureRawResult,
    CfdJobPaths,
    CfdJobSpec,
    CfdOpenFoamForceDatResult,
    CfdOpenFoamRawResult,
    CfdRunRecord,
    LocalCfdJob,
    OPENFOAM_PROFILE_NAME,
    PreparedSolverCase,
    SolverProfile,
    SolverRawResult,
    fixture_local_command_profile,
    load_cfd_run_record,
    load_run_record,
    mock_failing_local_command_profile,
    openfoam_v2512_interfoam_local_profile,
    parse_openfoam_force_dat,
    prepare_cfd_job,
    prepare_local_job,
    read_local_status,
    run_cfd_job,
    run_local_job,
    solver_profile_by_name,
    solver_profile_names,
    solver_profiles,
    unavailable_open_surface_profile,
    unavailable_watertight_solid_profile,
)


class CfdNotImplementedError(NotImplementedError):
    """Raised when callers ask for calibrated heavy-CFD evaluation."""


def evaluate_cfd(*_args: object, **_kwargs: object) -> None:
    """Keep calibrated CFD evaluation explicitly out of scope."""
    raise CfdNotImplementedError("heavy CFD evaluation is reserved for a future RFC")


__all__ = [
    "CFD_FIXTURE_RESULTS_WARNING",
    "CFD_OPENFOAM_RESULTS_WARNING",
    "CFD_RAW_RESULTS_WARNING",
    "CfdDispatchError",
    "CfdFixtureRawResult",
    "CfdJobPaths",
    "CfdJobSpec",
    "CfdOpenFoamForceDatResult",
    "CfdOpenFoamRawResult",
    "CfdNotImplementedError",
    "CfdRunRecord",
    "LocalCfdJob",
    "OPENFOAM_PROFILE_NAME",
    "PreparedSolverCase",
    "SolverProfile",
    "SolverRawResult",
    "evaluate_cfd",
    "fixture_local_command_profile",
    "load_cfd_run_record",
    "load_run_record",
    "mock_failing_local_command_profile",
    "openfoam_v2512_interfoam_local_profile",
    "parse_openfoam_force_dat",
    "prepare_cfd_job",
    "prepare_local_job",
    "read_local_status",
    "run_cfd_job",
    "run_local_job",
    "solver_profile_by_name",
    "solver_profile_names",
    "solver_profiles",
    "unavailable_open_surface_profile",
    "unavailable_watertight_solid_profile",
]
