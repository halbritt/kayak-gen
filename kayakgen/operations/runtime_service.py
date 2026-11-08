"""Read-only Linux/systemd observations for the persistent local web service."""
from __future__ import annotations

import json
import http.client
import ipaddress
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit

from kayakgen.operations.release_manifest import file_sha256, require
from kayakgen.operations.release_stage import clean_environment
from kayakgen.services.generative_job_ownership import process_identity

PROPERTIES = ('ActiveState', 'SubState', 'MainPID', 'InvocationID', 'NRestarts',
              'Restart', 'KillMode', 'ExecMainStatus', 'Result', 'ExecStart',
              'FragmentPath', 'WorkingDirectory')
SELECTED_ENV = ('TRAME_ARGS', 'TRAME_SERVER', 'TRAME_BACKEND')
CONSOLE_BODY = '''# -*- coding: utf-8 -*-
import sys
from kayakgen.cli.main import app
if __name__ == "__main__":
    if sys.argv[0].endswith("-script.pyw"):
        sys.argv[0] = sys.argv[0][:-11]
    elif sys.argv[0].endswith(".exe"):
        sys.argv[0] = sys.argv[0][:-4]
    sys.exit(app())
'''
PARSER_PROGRAM = '''import hashlib, inspect, json, pathlib, sys
from importlib import metadata
from trame_server import Server
import kayakgen.cli.main, trame_server.core, trame_server.utils.argument_parser
import wslink.server, wslink.protocol, wslink.backends.aiohttp
sys.argv = json.load(sys.stdin)["argv"]
options, unknown = Server(name="lifecycle-config-observation").cli.parse_known_args()
modules = [kayakgen.cli.main, trame_server.core,
           trame_server.utils.argument_parser, wslink.server, wslink.protocol, wslink.backends.aiohttp]
origins = {module.__name__: {"path": inspect.getfile(module),
    "sha256": hashlib.sha256(pathlib.Path(inspect.getfile(module)).read_bytes()).hexdigest()}
    for module in modules}
print(json.dumps({"timeout": options.timeout, "server": options.server,
    "backend": __import__("os").environ.get("TRAME_BACKEND", "aiohttp"),
    "prefix": sys.prefix, "python": sys.executable, "modules": origins,
    "jobs_in_process_default": inspect.signature(kayakgen.cli.main.serve).parameters["jobs_in_process"].default.default,
    "versions": {name: metadata.version(name) for name in ("kayakgen", "trame-server", "wslink", "aiohttp")},
    "unknown_arguments": unknown}))
'''


def assess_service(samples: list[dict], settings: dict) -> dict:
    """Assess observed continuity; a healthy replacement is still a restart."""
    require(len(samples) >= 2, 'At least two service observations are required')
    first = samples[0]
    reasons = []
    outcome = 'continuous_survival'
    if first['ActiveState'] != 'active' or first['process'] is None:
        reasons.append('service_not_initially_running')
        outcome = 'not_running'
    for sample in samples[1:]:
        if sample['NRestarts'] != first['NRestarts']:
            outcome = 'restarted'
        if sample['process'] is not None and first['process'] is not None:
            identity = ('pid', 'start', 'boot_id')
            if (any(sample['process'][key] != first['process'][key] for key in identity)
                    or sample['InvocationID'] != first['InvocationID']):
                outcome = 'restarted'
            if sample['process']['python'] != first['process']['python']:
                reasons.append('installed_runtime_changed')
        elif outcome != 'restarted':
            outcome = ('clean_exit' if sample['Result'] == 'success'
                       and sample['ExecMainStatus'] == 0 else 'failed_exit')
    if outcome != 'continuous_survival':
        reasons.append('service_' + outcome)
    if any(s['ActiveState'] != 'active' or s['SubState'] != 'running'
           or s['process'] is None or s['process']['state'] == 'Z' for s in samples):
        reasons.append('service_not_continuously_running')
    if any(s['Restart'] != 'always' for s in samples):
        reasons.append('persistent_restart_policy_must_be_always')
    if any(s['KillMode'] != 'process' for s in samples):
        reasons.append('detached_workers_require_kill_mode_process')
    if settings['timeout'] != 0 or settings['server'] is not True:
        reasons.append('persistent_service_requires_effective_timeout_zero_server_mode')
    if settings.get('backend', 'aiohttp') != 'aiohttp':
        reasons.append('unsupported_backend_for_observed_idle_contract')
    return {'accepted': not reasons, 'outcome': outcome, 'reasons': reasons}


def service_snapshot(unit: str) -> dict:
    command = ['systemctl', '--user', 'show', unit]
    command.extend('--property=' + name for name in PROPERTIES)
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
    state = dict(line.split('=', 1) for line in completed.stdout.splitlines())
    for name in ('MainPID', 'NRestarts', 'ExecMainStatus'):
        state[name] = int(state[name])
    pid = state['MainPID']
    identity = process_identity(pid) if pid > 0 else None
    state['process'] = None
    if identity is not None:
        start, boot, status = identity
        proc = Path('/proc') / str(pid)
        argv = [os.fsdecode(arg) for arg in (proc / 'cmdline').read_bytes().split(b'\0') if arg]
        environment = dict(os.fsdecode(entry).split('=', 1)
                           for entry in (proc / 'environ').read_bytes().split(b'\0') if b'=' in entry)
        after_identity = process_identity(pid)
        require(after_identity is not None and after_identity[:2] == identity[:2],
                'Service process changed during identity capture')
        state['process'] = {'pid': pid, 'start': start, 'boot_id': boot, 'state': status,
            'argv': argv, 'python': argv[0], 'cwd': os.readlink(proc / 'cwd'),
            'environment': {key: environment.get(key) for key in SELECTED_ENV}}
    return state


def effective_settings(snapshot: dict) -> dict:
    process = snapshot['process']
    require(process is not None, 'Cannot inspect an absent service process')
    python = Path(process['python'])
    require(python.is_absolute() and python.name.startswith('python'),
            'Service must identify its installed Python interpreter in argv[0]')
    require(python.parent.name == 'bin' and (python.parent.parent / 'pyvenv.cfg').is_file(),
            'Service interpreter must belong to an installed virtual environment')
    require(python.parent.parent == python.parent.parent.resolve(),
            'Service interpreter path must be a stable release path, not a mutable symlink')
    argv = process['argv'][1:]
    console = python.parent / 'kayakgen'
    require(len(argv) >= 2 and Path(argv[0]).resolve() == console and argv[1] == 'serve',
            'Unsupported console invocation; require installed kayakgen serve')
    require(console.read_bytes() == (f'#!{python}\n' + CONSOLE_BODY).encode(),
            'Installed console invocation wrapper differs from the supported entry point')
    require('--jobs-in-process' not in argv, 'In-process jobs do not retain detached ownership')
    environment = clean_environment()
    for name in SELECTED_ENV:
        environment.pop(name, None)
        if process['environment'][name] is not None:
            environment[name] = process['environment'][name]
    completed = subprocess.run([str(python), '-I', '-B', '-c', PARSER_PROGRAM],
        input=json.dumps({'argv': argv}), cwd=process['cwd'], env=environment,
        check=True, capture_output=True, text=True, timeout=15)
    settings = json.loads(completed.stdout)
    require(Path(settings['prefix']).resolve() == python.parent.parent,
            'Effective parser used a different installed environment')
    require(settings['jobs_in_process_default'] is False,
            'Installed serve default no longer establishes detached jobs')
    settings['selected_environment'] = process['environment']
    settings['detached_jobs'] = True
    settings['console'] = {'path': str(console), 'sha256': file_sha256(console)}
    return settings


def listener_owned(pid: int, address, port: int) -> bool:
    proc = Path('/proc') / str(pid)
    inodes = set()
    for descriptor in (proc / 'fd').iterdir():
        try:
            target = os.readlink(descriptor)
        except FileNotFoundError:
            continue  # Descriptor ownership can change while the process runs.
        if target.startswith('socket:['):
            inodes.add(target[8:-1])
    table = proc / 'net' / ('tcp6' if address.version == 6 else 'tcp')
    for line in table.read_text().splitlines()[1:]:
        columns = line.split()
        if columns[3] != '0A' or columns[9] not in inodes:
            continue
        encoded_ip, encoded_port = columns[1].split(':')
        if int(encoded_port, 16) != port:
            continue
        raw = bytes.fromhex(encoded_ip)
        raw = (b''.join(raw[i:i + 4][::-1] for i in range(0, 16, 4))
               if address.version == 6 else raw[::-1])
        bound = ipaddress.ip_address(raw)
        if bound == address or bound.is_unspecified:
            return True
    return False


def check_readiness(snapshot: dict, url: str) -> dict:
    """Prove a loopback HTTP listener belongs to the observed process."""
    parsed = urlsplit(url)
    address = ipaddress.ip_address(parsed.hostname)
    require(parsed.scheme == 'http' and address.is_loopback
            and parsed.username is None and parsed.password is None and not parsed.fragment,
            'Readiness requires an explicit loopback HTTP URL with no credentials or fragment')
    port = parsed.port or 80
    process = snapshot['process']
    require(process is not None and listener_owned(process['pid'], address, port),
            'Readiness listener is not owned by the selected service process')
    connection = http.client.HTTPConnection(str(address), port, timeout=2)
    try:
        path = parsed.path or '/'
        if parsed.query:
            path += '?' + parsed.query
        connection.request('GET', path)
        response = connection.getresponse()
        require(200 <= response.status < 400, f'Readiness HTTP status {response.status} refused')
        response.read(512)
    finally:
        connection.close()
    identity = process_identity(process['pid'])
    require(identity is not None and identity[:2] == (process['start'], process['boot_id']),
            'Service process changed during readiness')
    return {'url': url, 'http_status': response.status, 'listener_owned_by_pid': process['pid'],
            'redirects_followed': False, 'websocket_clients_created': 0,
            'completed_before_idle_observation': True}


def wait_for_readiness(snapshot: dict, url: str) -> dict:
    deadline = time.monotonic() + 10
    while True:
        try:
            return check_readiness(snapshot, url)
        except (OSError, ValueError, http.client.HTTPException) as error:
            if time.monotonic() >= deadline:
                raise ValueError('Service did not establish supported readiness: ' + str(error)) from error
            time.sleep(.2)


def observe_service(unit: str, seconds: float, readiness_url: str) -> dict:
    started = time.monotonic()
    first = service_snapshot(unit)
    settings = effective_settings(first)
    readiness = wait_for_readiness(first, readiness_url)
    idle_started = time.monotonic()
    samples = [first]
    deadline = idle_started + seconds
    while time.monotonic() < deadline:
        time.sleep(min(1., max(0., deadline - time.monotonic())))
        samples.append(service_snapshot(unit))
    idle_finished = time.monotonic()
    after_settings = effective_settings(samples[-1]) if samples[-1]['process'] is not None else None
    assessment = assess_service(samples, settings)
    unchanged = after_settings == settings
    if not unchanged:
        assessment['accepted'] = False
        assessment['reasons'].append('effective_runtime_or_settings_changed')
    readiness_after = None
    if assessment['accepted']:
        try:
            readiness_after = check_readiness(samples[-1], readiness_url)
            readiness_after['completed_before_idle_observation'] = False
            readiness_after['completed_after_idle_observation'] = True
        except (OSError, ValueError, http.client.HTTPException) as error:
            assessment['accepted'] = False
            assessment['reasons'].append('service_readiness_lost_after_idle')
            assessment['readiness_error_after_idle'] = str(error)
    return {'unit': unit, 'requested_observation_s': seconds,
            'elapsed_s': time.monotonic() - started, 'settings': settings,
            'readiness': readiness, 'idle_observed_s': idle_finished - idle_started,
            'readiness_after_idle': readiness_after,
            'settings_after': after_settings, 'runtime_settings_unchanged': unchanged,
            'samples': samples, **assessment,
            'scope': 'read-only installed parser replay and sampled service lifetime; no service mutation'}
