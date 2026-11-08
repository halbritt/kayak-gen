"""Deadlines include silent output and descendants retaining stdout."""
from __future__ import annotations

import shlex
import sys
import time
from pathlib import Path

from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import bash_source_run_streamed


def _bashrc(tmp_path: Path) -> Path:
    path = tmp_path / 'empty.bashrc'
    path.write_text('')
    return path


def _is_running(pid: int) -> bool:
    path = Path(f'/proc/{pid}/stat')
    if not path.exists():
        return False
    return path.read_text().split()[2] != 'Z'


def test_silent_command_timeout_is_whole_command_deadline(tmp_path: Path) -> None:
    started = time.monotonic()
    result = bash_source_run_streamed('sleep 5', bashrc=_bashrc(tmp_path), timeout_s=.15)
    assert result.returncode == 124
    assert time.monotonic() - started < 2


def test_descendant_holding_pipe_does_not_outlive_timeout(tmp_path: Path) -> None:
    pid_file = tmp_path / 'child.pid'
    command = f"sleep 5 & echo $! > {shlex.quote(str(pid_file))}; exit 0"
    started = time.monotonic()
    result = bash_source_run_streamed(command, bashrc=_bashrc(tmp_path), timeout_s=.2)
    assert result.returncode == 124
    assert time.monotonic() - started < 2
    child = int(pid_file.read_text())
    deadline = time.monotonic() + 1
    while _is_running(child) and time.monotonic() < deadline:
        time.sleep(.01)
    assert not _is_running(child)


def test_continuous_unterminated_output_obeys_deadline(tmp_path: Path) -> None:
    script = tmp_path / 'writer.py'
    script.write_text("import os,time\nend=time.monotonic()+5\nwhile time.monotonic()<end:\n os.write(1,b'x'*8192)\n time.sleep(.001)\n")
    log = tmp_path / 'solver.log'
    started = time.monotonic()
    result = bash_source_run_streamed(
        f'{shlex.quote(sys.executable)} {shlex.quote(str(script))}',
        bashrc=_bashrc(tmp_path), timeout_s=.25, log_path=log,
    )
    assert result.returncode == 124
    assert time.monotonic() - started < 2
    assert log.stat().st_size > 65536
    assert len(result.stdout.encode()) < 65650
    assert 'truncated' in result.stdout


def test_log_is_complete_while_returned_capture_is_bounded_tail(tmp_path: Path) -> None:
    script = tmp_path / 'output.py'
    script.write_text("import os\nos.write(1,b'a'*200000+b'FINAL SUMMARY\\n')\n")
    log = tmp_path / 'solver.log'
    result = bash_source_run_streamed(
        f'{shlex.quote(sys.executable)} {shlex.quote(str(script))}',
        bashrc=_bashrc(tmp_path), timeout_s=2, log_path=log,
    )
    assert result.succeeded
    assert log.read_bytes() == b'a'*200000+b'FINAL SUMMARY\n'
    assert result.stdout.endswith('FINAL SUMMARY\n')
    assert len(result.stdout.encode()) < 65650


def test_output_and_exit_code_are_preserved(tmp_path: Path) -> None:
    log = tmp_path / 'solver.log'
    result = bash_source_run_streamed('printf "first\\n"; printf "second\\n" >&2; exit 7', bashrc=_bashrc(tmp_path), timeout_s=2, log_path=log)
    assert result.returncode == 7
    assert result.stdout == 'first\nsecond\n'
    assert log.read_text() == result.stdout
    assert result.stderr == ''
