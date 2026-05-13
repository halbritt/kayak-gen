"""CFD evaluation boundary and local dispatch helpers."""

from __future__ import annotations

from kayakgen.eval.cfd.jobs import (
    CFD_RAW_RESULTS_WARNING,
    CfdDispatchError,
    CfdJobPaths,
    CfdJobSpec,
    CfdRunRecord,
    LocalCfdJob,
    PreparedSolverCase,
    SolverProfile,
    SolverRawResult,
    load_cfd_run_record,
    load_run_record,
    mock_failing_local_command_profile,
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
    "CFD_RAW_RESULTS_WARNING",
    "CfdDispatchError",
    "CfdJobPaths",
    "CfdJobSpec",
    "CfdNotImplementedError",
    "CfdRunRecord",
    "LocalCfdJob",
    "PreparedSolverCase",
    "SolverProfile",
    "SolverRawResult",
    "evaluate_cfd",
    "load_cfd_run_record",
    "load_run_record",
    "mock_failing_local_command_profile",
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
