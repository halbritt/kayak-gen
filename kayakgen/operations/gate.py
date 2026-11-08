"""Run the complete release gate and retain its source-bound outcome."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

SCHEMA_VERSION = "kayakgen-gate-receipt/1"
FAST_PYTEST_ARGS = (
    "--ignore=tests/test_web_browser.py",
    "--ignore=tests/test_generative_jobs_subprocess.py",
    "--ignore=tests/test_cfd_jobs.py",
    "--ignore=tests/test_generated_closed_body_hardening.py",
    "--ignore=tests/test_design_report.py",
    "--ignore=tests/test_generated_closed_body.py",
    "--ignore=tests/test_sweep.py",
    "--ignore=tests/test_active_search_nested_keys.py",
    "--ignore=tests/test_web_layout.py",
    "--ignore=tests/test_generative_jobs_manager.py",
    "--ignore=tests/test_compare.py",
    "--deselect=tests/test_cli.py::test_cfd_fixture_run_and_status_keep_raw_warning_visible",
    "--deselect=tests/test_web.py::test_cfd_routes_fixture_command_success_remains_raw_unvalidated",
)
SUMMARY = re.compile(r"^\d+ (?:passed|failed|skipped|errors?|deselected)(?:, .+)? in [\d.]+s")


class GateInterrupted(Exception):
    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"interrupted by signal {signum}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(root: Path, *arguments: str, env: dict[str, str] | None = None) -> bytes:
    return subprocess.check_output(["git", *arguments], cwd=root, env=env, stderr=subprocess.PIPE)


def _file_fingerprint(root: Path) -> str:
    paths = _git(root, "ls-files", "-c", "-o", "--exclude-standard", "-z").split(b"\0")
    digest = hashlib.sha256()
    for relative in sorted(set(paths) - {b""}):
        path = root / os.fsdecode(relative)
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            marker, content = b"missing", b""
        else:
            if stat.S_ISLNK(mode):
                marker, content = b"120000", os.fsencode(os.readlink(path))
            elif stat.S_ISREG(mode):
                marker = b"100755" if mode & 0o111 else b"100644"
                content = path.read_bytes()
            else:
                raise ValueError(f"unsupported source entry: {relative!r}")
        digest.update(relative + b"\0" + marker + b"\0")
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def source_snapshot(root: Path) -> dict[str, object]:
    """Identify actual candidate bytes without changing its real Git index."""
    fingerprint = _file_fingerprint(root)
    index = Path(
        os.fsdecode(
            _git(root, "rev-parse", "--path-format=absolute", "--git-path", "index")
        ).strip()
    )
    with tempfile.TemporaryDirectory(prefix="kayakgen-gate-index-") as temporary:
        copied_index = Path(temporary) / "index"
        shutil.copyfile(index, copied_index)
        env = {**os.environ, "GIT_INDEX_FILE": str(copied_index)}
        index_tree = _git(root, "write-tree", env=env).decode().strip()
        _git(root, "add", "--all", "--", ".", env=env)
        candidate_tree = _git(root, "write-tree", env=env).decode().strip()
    if fingerprint != _file_fingerprint(root):
        raise ValueError("source changed while capturing its snapshot")
    return {
        "tree_sha": candidate_tree,
        "fingerprint_sha256": fingerprint,
        "head_commit": _git(root, "rev-parse", "HEAD").decode().strip(),
        "index_tree_sha": index_tree,
        "dirty": bool(
            _git(root, "--no-optional-locks", "status", "--porcelain", "--untracked-files=all")
        ),
    }


def renderer_evidence() -> dict[str, object]:
    """Keep declarations distinct from an actual rendering observation."""
    from kayakgen.operations.renderer import RENDERER_ENV_KEYS

    return {
        "declared": {name: os.environ.get(name) for name in RENDERER_ENV_KEYS},
        "actual": {"status": "unobserved", "reason": "renderer probe has not completed"},
    }


def expected_skip_count() -> int:
    return (
        0
        if (
            os.environ.get("KAYAKGEN_OPENFOAM_SMOKE") == "1"
            and os.environ.get("KAYAKGEN_OPENFOAM_LOCAL_RUN") == "1"
        )
        else 4
    )


def _prepare_receipt(root: Path, path: Path | None, run_id: str) -> Path | None:
    if path is None:
        return None
    path = path.absolute()
    resolved = path.resolve()
    if resolved.is_relative_to(root):
        relative = resolved.parent.relative_to(root)
        ignored = subprocess.run(["git", "check-ignore", "-q", "--", f"{relative}/"], cwd=root)
        if ignored.returncode not in (0, 1):
            raise RuntimeError("could not check whether the receipt is ignored")
        if ignored.returncode != 0:
            raise ValueError("receipt must be outside source or in a Git-ignored directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump({"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "running"}, stream)
        stream.write("\n")
    return path


def _write_receipt(path: Path | None, receipt: dict[str, object]) -> None:
    if path is None:
        return
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix="." + path.name + ".", delete=False
    ) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _interrupt_signals():
    received = False

    def interrupt(signum, _frame):
        nonlocal received
        if not received:
            received = True
            raise GateInterrupted(signum)

    previous = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
    try:
        for number in previous:
            signal.signal(number, interrupt)
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def _terminate_owned(command: subprocess.Popen[str]) -> None:
    try:
        os.killpg(command.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        command.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(command.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        command.wait(timeout=5)


def _commands(kind: str = "full") -> list[dict[str, object]]:
    pytest = ("pytest", ["pytest", "-q", *(FAST_PYTEST_ARGS if kind == "fast" else ())])
    ruff = ("ruff", ["ruff", "check", "kayakgen", "tests"])
    return [
        {
            "name": name,
            "argv": [sys.executable, "-m", *args],
            "status": "not_run",
            "exit_code": None,
            "started_at": None,
            "finished_at": None,
            "duration_seconds": 0.0,
        }
        for name, args in ((pytest, ruff) if kind == "full" else (ruff, pytest))
    ]


def _new_receipt(root: Path, run_id: str, kind: str = "full") -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "gate": kind,
        "run_id": run_id,
        "status": "running",
        "exit_code": None,
        "started_at": _now(),
        "finished_at": None,
        "duration_seconds": None,
        "source_before": None,
        "source_after": None,
        "source_unchanged": None,
        "expected_skips": expected_skip_count(),
        "observed_skips": None,
        "interpreter": {
            "executable": sys.executable,
            "resolved_executable": str(Path(sys.executable).resolve()),
            "requested": os.environ.get("KAYAKGEN_PY", sys.executable),
            "version": platform.python_version(),
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
        },
        "renderer": renderer_evidence(),
        "commands": _commands(kind),
        "environment_policy": {
            "pytest_addopts": f"cleared_for_{kind}_gate",
            "inherited_pytest_addopts_present": bool(os.environ.get("PYTEST_ADDOPTS")),
        },
        "repository": str(root),
        "failure_reasons": [],
        "diagnostics": [],
    }


def _command_log(path: Path | None, run_id: str, name: str):
    if path is None:
        return None
    directory = path.parent / f"{path.stem}.{run_id}.logs"
    directory.mkdir(exist_ok=True)
    return (directory / f"{name}.log").open("w", encoding="utf-8")


def _run_command(
    root: Path, command: dict[str, object], receipt: dict[str, object], path: Path | None
) -> int:
    start = time.monotonic()
    command.update(status="running", started_at=_now())
    _write_receipt(path, receipt)
    print(f"[{receipt['gate']}-gate] {' '.join(command['argv'])}", flush=True)
    env = {
        **os.environ,
        "KAYAKGEN_ENFORCE_SKIP_PIN": "1",
        "KAYAKGEN_EXPECTED_SKIPS": str(receipt["expected_skips"]),
    }
    # Environment-only selectors must not quietly narrow the complete gate.
    env.pop("PYTEST_ADDOPTS", None)
    for name, setting in receipt["renderer"]["effective"].items():
        if setting is None:
            env.pop(name, None)
        else:
            env[name] = setting
    log = _command_log(path, receipt["run_id"], command["name"])
    command["log_path"] = log.name if log is not None else None
    process = None
    try:
        process = subprocess.Popen(
            command["argv"],
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=True,
        )
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if log is not None:
                log.write(line)
                log.flush()
            if command["name"] == "pytest" and SUMMARY.match(line.strip()):
                command["summary"] = line.strip()
        command["exit_code"] = process.wait()
        command["status"] = "passed" if command["exit_code"] == 0 else "failed"
    except GateInterrupted:
        command["status"] = "interrupted"
        if process is not None:
            _terminate_owned(process)
            command["exit_code"] = process.returncode
        raise
    except BaseException:
        # A failed log write or launch must not leave this invocation's child alive.
        command["status"] = "failed"
        if process is not None:
            _terminate_owned(process)
            command["exit_code"] = process.returncode
        else:
            command["exit_code"] = 127
        raise
    finally:
        if process is not None and process.stdout is not None:
            process.stdout.close()
        if log is not None:
            log.close()
        command.update(finished_at=_now(), duration_seconds=time.monotonic() - start)
    return command["exit_code"]


def _run_checks(root: Path, receipt: dict[str, object], path: Path | None) -> int:
    for command in receipt["commands"]:
        code = _run_command(root, command, receipt, path)
        if command["name"] == "pytest":
            summary = command.get("summary")
            if summary is not None:
                skipped = re.search(r"(?:^|, )(\d+) skipped", summary)
                receipt["observed_skips"] = int(skipped.group(1)) if skipped else 0
        if code != 0:
            receipt["failure_reasons"].append(command["name"] + "_failed")
            return code if code > 0 else 128 - code
        if command["name"] == "pytest" and (
            summary is None or receipt["observed_skips"] != receipt["expected_skips"]
        ):
            receipt["failure_reasons"].append(
                "pytest_summary_missing" if summary is None else "skip_count_mismatch"
            )
            return 1
    return 0


def _finish_source(root: Path, receipt: dict[str, object]) -> None:
    try:
        receipt["source_after"] = source_snapshot(root)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        receipt["failure_reasons"].append("source_snapshot_failed")
        receipt["diagnostics"].append(str(exc))
        return
    before, after = receipt["source_before"], receipt["source_after"]
    if before is not None:
        receipt["source_unchanged"] = all(
            before[key] == after[key] for key in ("tree_sha", "fingerprint_sha256")
        )
        if not receipt["source_unchanged"]:
            receipt["failure_reasons"].append("source_changed")


def _finalize(
    root: Path, receipt: dict[str, object], path: Path | None, code: int, started: float
) -> int:
    _finish_source(root, receipt)
    if receipt["failure_reasons"] and code == 0:
        code = 1
    if receipt["status"] != "interrupted":
        receipt["status"] = "passed" if code == 0 else "failed"
    receipt.update(exit_code=code, finished_at=_now(), duration_seconds=time.monotonic() - started)
    _write_receipt(path, receipt)
    return code


def run_gate(
    receipt_path: Path | None = None, renderer: str = "software", *, gate_kind: str = "full"
) -> int:
    from kayakgen.operations.renderer import rendering_profile

    if gate_kind not in {"full", "fast"}:
        raise ValueError("gate kind must be the fixed full or fast plan")
    root = Path(
        subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    ).resolve()
    run_id = str(uuid.uuid4())
    path = _prepare_receipt(root, receipt_path, run_id)
    receipt = _new_receipt(root, run_id, gate_kind)
    started = time.monotonic()
    code = 1
    with _interrupt_signals():
        try:
            receipt["source_before"] = source_snapshot(root)
            _write_receipt(path, receipt)
            with rendering_profile(renderer, receipt["renderer"]):
                actual = receipt["renderer"]["actual"]
                print(f"[{gate_kind}-gate] renderer {renderer}: {actual['window_class']} / "
                      f"{actual['opengl_vendor']} / {actual['opengl_renderer']}", flush=True)
                _write_receipt(path, receipt)
                code = _run_checks(root, receipt, path)
        except GateInterrupted as exc:
            receipt["failure_reasons"].append(f"interrupted_signal_{exc.signum}")
            receipt["status"] = "interrupted"
            code = 128 + exc.signum
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            receipt["failure_reasons"].append("gate_execution_failed")
            receipt["diagnostics"].append(str(exc))
            code = 1
        finally:
            try:
                code = _finalize(root, receipt, path, code, started)
            except GateInterrupted as exc:
                # The first signal can arrive while snapshotting/publishing
                # the terminal outcome, after both checks have already passed.
                receipt["failure_reasons"].append(f"interrupted_signal_{exc.signum}")
                receipt["status"] = "interrupted"
                code = _finalize(root, receipt, path, 128 + exc.signum, started)
    print(
        f"[{gate_kind}-gate] {receipt['status']}: {receipt['observed_skips']} skipped, expected {receipt['expected_skips']}",
        flush=True,
    )
    return code


def argument_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=os.environ.get("KAYAKGEN_GATE_RECEIPT"),
        help="New receipt path outside source or in a Git-ignored directory.",
    )
    parser.add_argument(
        "--renderer", choices=("software", "hardware"),
        default=os.environ.get("KAYAKGEN_GATE_RENDERER", "software"),
        help="Verified Mesa software (default) or hardware under the shared host lock.",
    )
    return parser


def gate_entry(kind: str, description: str) -> int:
    args = argument_parser(description).parse_args()
    try:
        return run_gate(args.receipt, args.renderer, gate_kind=kind)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"[{kind}-gate] error: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    return gate_entry("full", __doc__)


if __name__ == "__main__":
    raise SystemExit(main())
