"""Local CFD job dispatch contracts (compatibility shim).

This module records solver-dispatch state only. It does not validate or
calibrate solver physics, and every result record is marked raw/unvalidated.

Phase 3A of ``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`` split the
historical 2,600-line implementation into focused sibling modules under
``kayakgen.eval.cfd``. This module now re-exports every public name from
those siblings so existing ``from kayakgen.eval.cfd.jobs import ...``
imports continue to work byte-stably. New code should prefer the
canonical homes:

- contracts → :mod:`kayakgen.eval.cfd.records`
- built-in profiles → :mod:`kayakgen.eval.cfd.profiles`
- job preparation / persistence → :mod:`kayakgen.eval.cfd.job_store`
- mesh package validation → :mod:`kayakgen.eval.cfd.manifest_validation`
- solver provenance → :mod:`kayakgen.eval.cfd.provenance`
- parsers → :mod:`kayakgen.eval.cfd.parsers.openfoam_forces`
- adapters → :mod:`kayakgen.eval.cfd.adapters`
"""

from __future__ import annotations

from kayakgen.eval.cfd.adapters.fixture import (
    CfdFixtureCaseInput,
    CfdFixtureCommandOutput,
    CfdFixtureCommandSpec,
    CfdFixtureMeshSummary,
    CfdFixtureMeshSummaryFile,
    CfdFixtureRawResult,
    FixtureLocalCommandAdapter,
)
from kayakgen.eval.cfd.adapters.mock import MockFailingLocalCommandAdapter
from kayakgen.eval.cfd.adapters.openfoam_v2512 import (
    CfdOpenFoamCaseInput,
    CfdOpenFoamCommandSpec,
    CfdOpenFoamMeshSummary,
    CfdOpenFoamRawResult,
    OpenFoamLocalAdapter,
    resolve_real_solver_execution_opt_in,
)
from kayakgen.eval.cfd.adapters.unavailable import UnavailableSolverAdapter
from kayakgen.eval.cfd.job_store import (
    load_cfd_run_record,
    load_run_record,
    prepare_cfd_job,
    prepare_local_job,
    read_local_status,
    run_cfd_job,
    run_local_job,
)
from kayakgen.eval.cfd.manifest_validation import READINESS_ORDER
from kayakgen.eval.cfd.parsers.openfoam_forces import (
    CfdOpenFoamForceDatResult,
    CfdOpenFoamForceDatSample,
    parse_openfoam_force_dat,
)
from kayakgen.eval.cfd.profiles import (
    CFD_FIXTURE_RESULTS_WARNING,
    CFD_OPENFOAM_RESULTS_WARNING,
    CFD_RAW_RESULTS_WARNING,
    FIXTURE_CASE_TEMPLATE_VERSION,
    FIXTURE_RAW_OUTPUT,
    OPENFOAM_CASE_INPUT,
    OPENFOAM_CASE_ROOT,
    OPENFOAM_CASE_TEMPLATE_VERSION,
    OPENFOAM_COMMAND_SPEC,
    OPENFOAM_COMMAND_TIMEOUT_SECONDS,
    OPENFOAM_FORCE_DAT_OUTPUT,
    OPENFOAM_LOCAL_RUN_ENV_VAR,
    OPENFOAM_LOG_LIMIT_BYTES,
    OPENFOAM_PROFILE_NAME,
    OPENFOAM_RAW_RESULT,
    OPENFOAM_REQUIRED_VERSION,
    OPENFOAM_SOLVER_NAME,
    OPENFOAM_SUCCEEDED_RAW_UNVALIDATED_WARNING,
    OPENFOAM_SUCCESS_BLOCKED_WARNING,
    fixture_local_command_profile,
    mock_failing_local_command_profile,
    openfoam_v2512_interfoam_local_profile,
    solver_profile_by_name,
    solver_profile_names,
    solver_profiles,
    unavailable_open_surface_profile,
    unavailable_watertight_solid_profile,
)
from kayakgen.eval.cfd.provenance import (
    OPENFOAM_PROBE_COMMANDS,
    OpenFoamProbeRunner,
    OpenFoamProvenanceProbe,
    probe_openfoam_provenance,
)
from kayakgen.eval.cfd.records import (
    CfdAdapterName,
    CfdDispatchError,
    CfdJobPaths,
    CfdJobSpec,
    CfdRunRecord,
    CfdRunStatus,
    LocalCfdJob,
    PreparedSolverCase,
    RealSolverExecutionOptIn,
    SolverAdapter,
    SolverExecutionAudit,
    SolverProfile,
    SolverRawResult,
)

__all__ = [
    "CFD_FIXTURE_RESULTS_WARNING",
    "CFD_OPENFOAM_RESULTS_WARNING",
    "CFD_RAW_RESULTS_WARNING",
    "CfdAdapterName",
    "CfdDispatchError",
    "CfdFixtureCaseInput",
    "CfdFixtureCommandOutput",
    "CfdFixtureCommandSpec",
    "CfdFixtureMeshSummary",
    "CfdFixtureMeshSummaryFile",
    "CfdFixtureRawResult",
    "CfdJobPaths",
    "CfdJobSpec",
    "CfdOpenFoamCaseInput",
    "CfdOpenFoamCommandSpec",
    "CfdOpenFoamForceDatResult",
    "CfdOpenFoamForceDatSample",
    "CfdOpenFoamMeshSummary",
    "CfdOpenFoamRawResult",
    "CfdRunRecord",
    "CfdRunStatus",
    "FIXTURE_CASE_TEMPLATE_VERSION",
    "FIXTURE_RAW_OUTPUT",
    "FixtureLocalCommandAdapter",
    "LocalCfdJob",
    "MockFailingLocalCommandAdapter",
    "OPENFOAM_CASE_INPUT",
    "OPENFOAM_CASE_ROOT",
    "OPENFOAM_CASE_TEMPLATE_VERSION",
    "OPENFOAM_COMMAND_SPEC",
    "OPENFOAM_COMMAND_TIMEOUT_SECONDS",
    "OPENFOAM_FORCE_DAT_OUTPUT",
    "OPENFOAM_LOCAL_RUN_ENV_VAR",
    "OPENFOAM_LOG_LIMIT_BYTES",
    "OPENFOAM_PROBE_COMMANDS",
    "OPENFOAM_PROFILE_NAME",
    "OPENFOAM_RAW_RESULT",
    "OPENFOAM_REQUIRED_VERSION",
    "OPENFOAM_SOLVER_NAME",
    "OPENFOAM_SUCCEEDED_RAW_UNVALIDATED_WARNING",
    "OPENFOAM_SUCCESS_BLOCKED_WARNING",
    "OpenFoamLocalAdapter",
    "OpenFoamProbeRunner",
    "OpenFoamProvenanceProbe",
    "PreparedSolverCase",
    "READINESS_ORDER",
    "RealSolverExecutionOptIn",
    "SolverAdapter",
    "SolverExecutionAudit",
    "SolverProfile",
    "SolverRawResult",
    "UnavailableSolverAdapter",
    "fixture_local_command_profile",
    "load_cfd_run_record",
    "load_run_record",
    "mock_failing_local_command_profile",
    "openfoam_v2512_interfoam_local_profile",
    "parse_openfoam_force_dat",
    "prepare_cfd_job",
    "prepare_local_job",
    "probe_openfoam_provenance",
    "read_local_status",
    "resolve_real_solver_execution_opt_in",
    "run_cfd_job",
    "run_local_job",
    "solver_profile_by_name",
    "solver_profile_names",
    "solver_profiles",
    "unavailable_open_surface_profile",
    "unavailable_watertight_solid_profile",
]
