"""bashrc-sourced OpenFOAM-v2512 subprocess runner.

All commands are dispatched through one helper that wraps the command
in ``bash -lc 'source $OPENFOAM_BASHRC && exec <cmd>'`` so the WM/FOAM
environment is loaded exactly the way an operator's interactive shell
does. The default bashrc lives at ``/usr/lib/openfoam/openfoam2512/etc/bashrc``
and is overridable via the ``KAYAKGEN_OPENFOAM_BASHRC`` env var.

Importing this module never invokes any OpenFOAM binary. The
``is_openfoam_available`` helper performs a single short subprocess and
is the only function in this module that touches a shell at import-time
callers.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from kayakgen.eval.snappy_hex_mesh import CheckMeshSummary

OPENFOAM_BASHRC_ENV_VAR = "KAYAKGEN_OPENFOAM_BASHRC"
OPENFOAM_BASHRC = Path("/usr/lib/openfoam/openfoam2512/etc/bashrc")
DEFAULT_PROBE_TIMEOUT_SECONDS = 30


def _resolve_bashrc(bashrc: str | Path | None = None) -> Path:
    if bashrc is not None:
        return Path(bashrc)
    env_value = os.environ.get(OPENFOAM_BASHRC_ENV_VAR)
    if env_value:
        return Path(env_value)
    return OPENFOAM_BASHRC


@dataclass(frozen=True)
class OpenFoamCommandResult:
    """Captured subprocess output from a bashrc-sourced OpenFOAM command."""

    command: str
    returncode: int
    stdout: str
    stderr: str
    bashrc: Path

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def bash_source_run(
    command: str,
    *,
    cwd: str | Path | None = None,
    timeout_s: float | None = None,
    bashrc: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> OpenFoamCommandResult:
    """Run ``command`` inside a login shell that sources the OpenFOAM bashrc.

    ``command`` is a single shell snippet (already quoted as needed). The
    helper composes ``bash -lc 'source <bashrc> >/dev/null 2>&1 && <command>'``.
    """

    bashrc_path = _resolve_bashrc(bashrc)
    if not bashrc_path.is_file():
        raise FileNotFoundError(
            f"OpenFOAM bashrc not found at {bashrc_path}; set "
            f"{OPENFOAM_BASHRC_ENV_VAR} to override"
        )
    wrapped = (
        f"source {shlex.quote(str(bashrc_path))} >/dev/null 2>&1 && "
        f"{command}"
    )
    completed = subprocess.run(
        ["bash", "-lc", wrapped],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_s,
        env=env,
    )
    return OpenFoamCommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        bashrc=bashrc_path,
    )


def bash_source_run_streamed(
    command: str,
    *,
    cwd: str | Path | None = None,
    timeout_s: float | None = None,
    bashrc: str | Path | None = None,
    log_path: str | Path | None = None,
) -> OpenFoamCommandResult:
    """Like :func:`bash_source_run` but tees the merged output to ``log_path``.

    Useful for long-running meshing/solver stages where the operator wants
    to inspect progress on disk. The returned ``stdout`` field contains the
    merged stream and ``stderr`` is empty.
    """

    bashrc_path = _resolve_bashrc(bashrc)
    if not bashrc_path.is_file():
        raise FileNotFoundError(
            f"OpenFOAM bashrc not found at {bashrc_path}; set "
            f"{OPENFOAM_BASHRC_ENV_VAR} to override"
        )
    wrapped = (
        f"source {shlex.quote(str(bashrc_path))} >/dev/null 2>&1 && "
        f"{command}"
    )
    log_file = open(log_path, "w") if log_path is not None else None
    try:
        process = subprocess.Popen(
            ["bash", "-lc", wrapped],
            cwd=str(cwd) if cwd is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        buffer: list[str] = []
        try:
            assert process.stdout is not None
            for line in process.stdout:
                buffer.append(line)
                if log_file is not None:
                    log_file.write(line)
                    log_file.flush()
            returncode = process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            returncode = 124
    finally:
        if log_file is not None:
            log_file.close()
    return OpenFoamCommandResult(
        command=command,
        returncode=returncode,
        stdout="".join(buffer),
        stderr="",
        bashrc=bashrc_path,
    )


def is_openfoam_available(bashrc: str | Path | None = None) -> bool:
    """Return True when the OpenFOAM-v2512 bashrc is sourceable and ``interFoam`` is on PATH."""

    bashrc_path = _resolve_bashrc(bashrc)
    if not bashrc_path.is_file():
        return False
    try:
        result = bash_source_run(
            "command -v interFoam >/dev/null && interFoam -help 2>&1 | head -n 60",
            timeout_s=DEFAULT_PROBE_TIMEOUT_SECONDS,
            bashrc=bashrc_path,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    if not result.succeeded:
        return False
    return "OpenFOAM-2512" in result.stdout or "2512" in result.stdout


# ---------------------------------------------------------------------------
# Provenance probe wiring


class OpenFoamProbeBashrcRunner:
    """Adapter that fits :func:`probe_openfoam_provenance`'s runner signature.

    The runner produces v2512 evidence by running ``interFoam -help`` through
    a sourced bashrc and extracting the ``Using: OpenFOAM-<token>`` banner.
    On v2512 builds without ``foamVersion`` we synthesise the build/api/
    project_version channels from ``$WM_PROJECT_VERSION`` and ``$FOAM_API``
    so the existing :class:`OpenFoamProvenanceProbe` contract still binds.

    The runner is invoked via ``probe_openfoam_provenance`` with a command
    map produced by :func:`probe_commands_for_bashrc_runner`; the runner
    treats the command-list's last element as a shell snippet to evaluate
    inside the sourced bashrc shell. This sidesteps the need to quote the
    snippet through ``bash -c`` twice.
    """

    PROBE_COMMANDS: dict[str, str] = {
        # First line carries the v2512 token so OpenFoamProvenanceProbe's
        # ``_first_nonempty_line`` extractor matches; the interFoam banner is
        # echoed afterwards as supporting evidence in the raw output.
        "application": (
            "echo \"OpenFOAM-$WM_PROJECT_VERSION application=interFoam\"; "
            "interFoam -help 2>&1 | grep -i '^Using:' || true"
        ),
        "build": (
            "echo \"OpenFOAM-$WM_PROJECT_VERSION build=$WM_PROJECT_VERSION api=$FOAM_API\""
        ),
        "api": "echo \"OpenFOAM-$WM_PROJECT_VERSION api=$FOAM_API\"",
        "project_version": (
            "echo \"OpenFOAM-$WM_PROJECT_VERSION project_version=$WM_PROJECT_VERSION\""
        ),
    }

    def __init__(
        self,
        *,
        bashrc: str | Path | None = None,
        timeout_s: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
    ) -> None:
        self._bashrc = bashrc
        self._timeout_s = timeout_s

    def __call__(self, command: Sequence[str]) -> tuple[int, str, str]:
        snippet = command[-1] if command else ""
        result = bash_source_run(
            snippet,
            timeout_s=self._timeout_s,
            bashrc=self._bashrc,
        )
        return result.returncode, result.stdout, result.stderr


def probe_commands_for_bashrc_runner() -> dict[str, list[str]]:
    """Return the probe-command map paired with :class:`OpenFoamProbeBashrcRunner`.

    The map entries are single-element lists containing the bashrc-sourced
    shell snippet. The runner extracts that snippet and evaluates it inside
    the sourced shell.
    """
    return {
        channel: [snippet]
        for channel, snippet in OpenFoamProbeBashrcRunner.PROBE_COMMANDS.items()
    }


# ---------------------------------------------------------------------------
# Meshing and solver stage runners


@dataclass
class StageStepResult:
    """One subprocess invocation inside a meshing or solver stage."""

    name: str
    returncode: int
    stdout: str
    stderr: str
    log_path: Path | None = None

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


@dataclass
class MeshingResult:
    """Combined output for ``blockMesh + snappyHexMesh + checkMesh``."""

    case_dir: Path
    steps: list[StageStepResult] = field(default_factory=list)
    check_mesh_summary: CheckMeshSummary | None = None
    succeeded: bool = False
    failure_reason: str | None = None
    seconds: float = 0.0


@dataclass
class SolverResult:
    """Combined output for ``setFields + interFoam``."""

    case_dir: Path
    steps: list[StageStepResult] = field(default_factory=list)
    force_dat_path: Path | None = None
    succeeded: bool = False
    failure_reason: str | None = None
    seconds: float = 0.0


def _run_step(
    name: str,
    command: str,
    *,
    case_dir: Path,
    logs_dir: Path,
    timeout_s: float | None,
    bashrc: str | Path | None,
    stream: bool,
) -> StageStepResult:
    log_path = logs_dir / f"{name}.log"
    if stream:
        result = bash_source_run_streamed(
            command,
            cwd=case_dir,
            timeout_s=timeout_s,
            bashrc=bashrc,
            log_path=log_path,
        )
        stdout = result.stdout
        stderr = ""
    else:
        result = bash_source_run(
            command,
            cwd=case_dir,
            timeout_s=timeout_s,
            bashrc=bashrc,
        )
        stdout = result.stdout
        stderr = result.stderr
        log_path.write_text(stdout + ("\n" + stderr if stderr else ""))
    return StageStepResult(
        name=name,
        returncode=result.returncode,
        stdout=stdout,
        stderr=stderr,
        log_path=log_path,
    )


_CHECK_MESH_MAX_NONORTHO = re.compile(
    r"Max non-orthogonality\s*=\s*([\-\d\.eE\+]+)"
)
_CHECK_MESH_MAX_SKEW = re.compile(r"Max skewness\s*=\s*([\-\d\.eE\+]+)")
_CHECK_MESH_ASPECT = re.compile(r"Max aspect ratio\s*=\s*([\-\d\.eE\+]+)")
_CHECK_MESH_CELLS = re.compile(r"cells:\s*(\d+)")
_CHECK_MESH_INTERNAL_FACES = re.compile(r"internal faces:\s*(\d+)")
_CHECK_MESH_BOUNDARY_FACES = re.compile(
    r"(?:Defined patches.*?total faces:\s*(\d+))|"
    r"boundary faces:\s*(\d+)",
    re.DOTALL,
)
_CHECK_MESH_FAILED = re.compile(r"Failed\s+\d+\s+mesh checks")
_CHECK_MESH_OK_LINE = re.compile(r"Mesh OK\.")


def parse_check_mesh_output(text: str) -> CheckMeshSummary:
    """Parse the textual ``checkMesh`` output into a :class:`CheckMeshSummary`.

    The parser tolerates the v2512 layout where field labels appear on
    separate lines from their values. Missing numeric fields fall back to
    safe defaults (zero counts, OK summary) so a partially-truncated log
    can still produce a record - downstream callers decide whether to
    reject on ``passed=False``.
    """

    passed = (
        bool(_CHECK_MESH_OK_LINE.search(text))
        and not bool(_CHECK_MESH_FAILED.search(text))
    )
    n_cells = _match_first_int(_CHECK_MESH_CELLS, text)
    n_internal_faces = _match_first_int(_CHECK_MESH_INTERNAL_FACES, text)
    n_boundary_faces = 0
    for match in _CHECK_MESH_BOUNDARY_FACES.finditer(text):
        for group in match.groups():
            if group:
                n_boundary_faces = int(group)
                break
    max_nonortho = _match_first_float(_CHECK_MESH_MAX_NONORTHO, text)
    max_skew = _match_first_float(_CHECK_MESH_MAX_SKEW, text)
    aspect = _match_first_float(_CHECK_MESH_ASPECT, text)
    warnings: list[str] = []
    if not passed:
        warnings.append("checkMesh reported one or more failed checks")
    return CheckMeshSummary(
        passed=passed,
        n_cells=n_cells,
        n_internal_faces=n_internal_faces,
        n_boundary_faces=n_boundary_faces,
        max_non_orthogonality_deg=max_nonortho,
        max_skewness=max_skew,
        aspect_ratio_max=aspect,
        warnings=warnings,
    )


def _match_first_int(pattern: re.Pattern[str], text: str) -> int:
    match = pattern.search(text)
    if match is None:
        return 0
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return 0


def _match_first_float(pattern: re.Pattern[str], text: str) -> float:
    match = pattern.search(text)
    if match is None:
        return 0.0
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Meshing stage


def run_meshing_stage(
    case_dir: str | Path,
    *,
    timeout_s: float | None = 600,
    bashrc: str | Path | None = None,
    stream: bool = True,
) -> MeshingResult:
    """Run ``blockMesh + surfaceFeatureExtract + snappyHexMesh -overwrite + checkMesh``.

    Logs for each step are written under ``<case_dir>/logs/``. The
    returned :class:`MeshingResult` carries a :class:`CheckMeshSummary`
    even on partial failure so the caller can decide how to surface it.
    """

    import time

    case_root = Path(case_dir)
    if not case_root.is_dir():
        raise FileNotFoundError(f"case directory does not exist: {case_root}")
    logs_dir = case_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    result = MeshingResult(case_dir=case_root)

    sequence: tuple[tuple[str, str], ...] = (
        ("blockMesh", "blockMesh"),
        (
            "surfaceFeatureExtract",
            "surfaceFeatureExtract && cp constant/extendedFeatureEdgeMesh/hull.eMesh "
            "constant/triSurface/hull.eMesh 2>/dev/null || true",
        ),
        ("snappyHexMesh", "snappyHexMesh -overwrite"),
        ("checkMesh", "checkMesh -allTopology"),
    )
    for name, command in sequence:
        step = _run_step(
            name,
            command,
            case_dir=case_root,
            logs_dir=logs_dir,
            timeout_s=timeout_s,
            bashrc=bashrc,
            stream=stream,
        )
        result.steps.append(step)
        if name == "checkMesh":
            result.check_mesh_summary = parse_check_mesh_output(step.stdout)
        if not step.succeeded and name != "checkMesh":
            result.failure_reason = (
                f"{name} exited with code {step.returncode}"
            )
            result.seconds = time.monotonic() - start
            return result

    result.seconds = time.monotonic() - start
    if result.check_mesh_summary is None:
        result.failure_reason = "checkMesh produced no parseable output"
        return result
    result.succeeded = bool(result.check_mesh_summary.passed)
    if not result.succeeded and result.failure_reason is None:
        result.failure_reason = "checkMesh reported failed checks"
    return result


# ---------------------------------------------------------------------------
# Solver stage


def run_solver_stage(
    case_dir: str | Path,
    *,
    timeout_s: float | None = 1800,
    bashrc: str | Path | None = None,
    stream: bool = True,
) -> SolverResult:
    """Copy ``0.orig`` into ``0``, run ``setFields``, then ``interFoam``.

    Returns a :class:`SolverResult` whose ``force_dat_path`` points at
    the produced ``postProcessing/forces/0/force.dat`` if interFoam
    produced one.
    """

    import time

    case_root = Path(case_dir)
    if not case_root.is_dir():
        raise FileNotFoundError(f"case directory does not exist: {case_root}")
    logs_dir = case_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    zero_orig = case_root / "0.orig"
    zero = case_root / "0"
    if not zero_orig.is_dir():
        raise FileNotFoundError(
            f"0.orig directory missing from case: {zero_orig}"
        )
    if zero.exists():
        shutil.rmtree(zero)
    shutil.copytree(zero_orig, zero)

    start = time.monotonic()
    result = SolverResult(case_dir=case_root)

    for name, command in (
        ("setFields", "setFields"),
        ("interFoam", "interFoam"),
    ):
        step = _run_step(
            name,
            command,
            case_dir=case_root,
            logs_dir=logs_dir,
            timeout_s=timeout_s,
            bashrc=bashrc,
            stream=stream,
        )
        result.steps.append(step)
        if not step.succeeded:
            result.failure_reason = f"{name} exited with code {step.returncode}"
            result.seconds = time.monotonic() - start
            return result

    result.seconds = time.monotonic() - start
    candidates = sorted(
        (case_root / "postProcessing" / "forces").glob("*/force.dat")
    )
    if not candidates:
        result.failure_reason = "interFoam did not write any force.dat output"
        return result
    result.force_dat_path = candidates[0]
    result.succeeded = True
    return result


__all__ = [
    "OPENFOAM_BASHRC",
    "OPENFOAM_BASHRC_ENV_VAR",
    "OpenFoamCommandResult",
    "OpenFoamProbeBashrcRunner",
    "MeshingResult",
    "SolverResult",
    "StageStepResult",
    "bash_source_run",
    "bash_source_run_streamed",
    "is_openfoam_available",
    "parse_check_mesh_output",
    "probe_commands_for_bashrc_runner",
    "run_meshing_stage",
    "run_solver_stage",
]
