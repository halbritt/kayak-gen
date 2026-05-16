"""``mock_local_command`` solver adapter used by dispatch tests."""

from __future__ import annotations

import json
import subprocess

from kayakgen.eval.cfd.job_store import (
    _run_record_from_result,
    _utc_now,
    _write_command_logs,
)
from kayakgen.eval.cfd.records import (
    CfdRunRecord,
    PreparedSolverCase,
    SolverRawResult,
)


class MockFailingLocalCommandAdapter:
    """Adapter that runs a known local command and records command failure."""

    def prepare(self, case: PreparedSolverCase) -> PreparedSolverCase:
        logs_dir = case.job_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        return case

    def run(self, case: PreparedSolverCase) -> SolverRawResult:
        completed = subprocess.run(
            case.solver_profile.command_template,
            cwd=case.job_dir,
            capture_output=True,
            check=False,
            text=True,
        )
        logs = _write_command_logs(case.job_dir, completed)
        if completed.returncode != 0:
            message = (
                f"solver command exited with code {completed.returncode}; "
                "raw solver output is unvalidated"
            )
            if completed.stderr.strip():
                message = f"{message}: {completed.stderr.strip()}"
            return SolverRawResult(
                status="failed",
                error_kind="command_failed",
                error_message=message,
                logs=logs,
                raw_records={"returncode": completed.returncode},
            )

        output_path = case.job_dir / "raw-result.json"
        raw_records = {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        output_path.write_text(json.dumps(raw_records, indent=2, sort_keys=True) + "\n")
        return SolverRawResult(
            status="succeeded",
            output_manifest=output_path.name,
            logs=logs,
            raw_records=raw_records,
        )

    def collect(self, case: PreparedSolverCase, result: SolverRawResult) -> CfdRunRecord:
        return _run_record_from_result(
            case.job_spec,
            result,
            started_at=_utc_now(),
            finished_at=_utc_now(),
        )


__all__ = ["MockFailingLocalCommandAdapter"]
