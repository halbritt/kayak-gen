"""Create a new inactive environment from a source-verified wheel and exact pins."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

from kayakgen.operations.release_manifest import file_sha256, require, write_json


@dataclass(frozen=True)
class StageRequest:
    wheel: Path
    constraints: Path
    python: Path
    output: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_name(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


def clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in ('PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', 'UV_CONSTRAINT',
                'UV_OVERRIDE', 'UV_PROJECT', 'UV_BUILD_CONSTRAINT'):
        environment.pop(key, None)
    environment.update(UV_PYTHON_DOWNLOADS='never', PYTHONDONTWRITEBYTECODE='1')
    return environment


def terminate_command(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=3)


def run_logged(argv: list[str], log: Path, *, timeout_s: float, env: dict[str, str]) -> dict:
    started = time.monotonic()
    record = {'argv': argv, 'cwd': str(log.parent), 'started_at': utc_now(),
              'status': 'running', 'timeout_s': timeout_s}
    write_json(log.with_suffix('.command.json'), record)
    try:
        with log.open('w') as stream:
            process = subprocess.Popen(argv, cwd=log.parent, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                terminate_command(process)
                record['status'] = 'timed_out'
                code = 124
        record.update(returncode=code, status='passed' if code == 0 else record['status'])
        if code != 0 and record['status'] == 'running':
            record['status'] = 'failed'
        require(code == 0, f'Command failed ({code}); inspect {log}')
    except Exception as error:
        record.update(status='failed' if record['status'] == 'running' else record['status'],
                      error=str(error))
        raise
    finally:
        record.update(finished_at=utc_now(), elapsed_s=time.monotonic() - started)
        if log.exists():
            record['log_sha256'] = file_sha256(log)
        write_json(log.with_suffix('.command.json'), record)
    return record


def read_pins(path: Path) -> dict[str, str]:
    pins = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)', line.strip())
        require(match is not None, 'Constraints must contain exact name==version pins')
        name, version = normalized_name(match[1]), match[2]
        require(name not in pins, 'Duplicate dependency pin: ' + name)
        pins[name] = version
    require('jinja2' in pins, 'HTML verification requires an explicit Jinja2 pin')
    return pins


def resolved_dependencies(path: Path, pins: dict[str, str]) -> dict[str, str]:
    resolved = {}
    for line in path.read_text().splitlines():
        if not line or line[0].isspace() or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;\\]+)\s*(?:\\)?', line)
        require(match is not None, 'Unexpected resolved requirement: ' + line)
        name, version = normalized_name(match[1]), match[2]
        require(pins.get(name) == version, 'Resolved dependency lacks supplied exact pin: ' + name)
        require(name not in resolved, 'Duplicate resolved dependency: ' + name)
        resolved[name] = version
    require(bool(resolved), 'Dependency resolution returned no packages')
    return resolved


def stage_environment(request: StageRequest) -> dict:
    pins = read_pins(request.constraints)
    output = request.output
    output.mkdir()
    wheel = output / request.wheel.name
    shutil.copyfile(request.wheel, wheel)
    shutil.copyfile(request.constraints, output / 'constraints.txt')
    extras = 'desktop,web,builder'
    (output / 'requirements.in').write_text(
        f'kayakgen[{extras}] @ {wheel.as_uri()}\nJinja2=={pins["jinja2"]}\n')
    environment = clean_environment()
    uv = shutil.which('uv')
    require(uv is not None, 'Installed uv executable is required')
    run_logged([uv, '--no-config', 'pip', 'compile', str(output / 'requirements.in'),
                '--constraints', str(output / 'constraints.txt'), '--generate-hashes',
                '--no-emit-package', 'kayakgen', '--no-annotate', '--no-header',
                '--only-binary', ':all:', '--python', str(request.python),
                '--output-file', str(output / 'dependencies.lock')],
               output / 'resolve.log', timeout_s=300, env=environment)
    resolved = resolved_dependencies(output / 'dependencies.lock', pins)
    lock = (output / 'dependencies.lock').read_text()
    lock += (f'\nkayakgen[{extras}] @ {wheel.as_uri()} \\\n'
             f'    --hash=sha256:{file_sha256(wheel)}\n')
    (output / 'runtime.lock').write_text(lock)
    release = output / 'environment'
    run_logged([uv, '--no-config', 'venv', '--python', str(request.python),
                '--no-python-downloads', str(release)], output / 'venv.log',
               timeout_s=60, env=environment)
    python = release / 'bin/python'
    run_logged([uv, '--no-config', 'pip', 'install', '--python', str(python),
                '--require-hashes', '--no-deps', '--only-binary', ':all:', '--link-mode', 'copy',
                '-r', str(output / 'runtime.lock')], output / 'install.log',
               timeout_s=300, env=environment)
    run_logged([uv, '--no-config', 'pip', 'check', '--python', str(python)],
               output / 'dependency-check.log', timeout_s=60, env=environment)
    return {'release': str(release), 'python': str(python), 'dependencies': resolved,
            'selected_extras': extras.split(','), 'html_renderer': 'jinja2',
            'pdf_extra_requested': False, 'runtime_lock_sha256': file_sha256(output / 'runtime.lock')}
