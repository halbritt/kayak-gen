"""``unavailable`` solver adapter used by gate-only profiles."""

from __future__ import annotations

from kayakgen.eval.cfd.job_store import _run_record_from_result, _utc_now
from kayakgen.eval.cfd.records import (
    CfdRunRecord,
    PreparedSolverCase,
    SolverRawResult,
)


class UnavailableSolverAdapter:
    """Adapter for solver profiles that are known to be unavailable."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        return case

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        return SolverRawResult(
            status="unavailable",
            error_kind="solver_unavailable",
            error_message=(
                f"solver profile {case.solver_profile.name!r} is unavailable; "
                "results remain raw and unvalidated"
            ),
        )

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        return _run_record_from_result(
            case.job_spec,
            result,
            started_at=_utc_now(),
            finished_at=_utc_now(),
        )


__all__ = ["UnavailableSolverAdapter"]
