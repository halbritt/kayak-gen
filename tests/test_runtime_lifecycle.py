"""Persistent acceptance distinguishes continuity from a restarted healthy unit."""
from __future__ import annotations

import copy

import pytest


def running_service():
    return {
        'ActiveState': 'active', 'SubState': 'running', 'MainPID': 41,
        'InvocationID': 'invocation-a', 'NRestarts': 0, 'Restart': 'always',
        'KillMode': 'process', 'ExecMainStatus': 0, 'Result': 'success',
        'process': {'pid': 41, 'start': '123', 'boot_id': 'boot-a',
                    'python': '/releases/tree-a/bin/python', 'state': 'S'},
    }


def test_restarted_healthy_unit_does_not_count_as_continuous_survival():
    from kayakgen.operations.runtime_service import assess_service

    before = running_service()
    after = copy.deepcopy(before)
    after.update(MainPID=73, InvocationID='invocation-b', NRestarts=1)
    after['process'].update(pid=73, start='456')
    verdict = assess_service([before, after], {'timeout': 0, 'server': True})
    assert verdict['outcome'] == 'restarted'
    assert verdict['accepted'] is False
    assert 'service_restarted' in verdict['reasons']


def test_same_pid_cannot_hide_a_different_release_path():
    from kayakgen.operations.runtime_service import assess_service

    before = running_service()
    after = copy.deepcopy(before)
    after['process']['python'] = '/releases/tree-b/bin/python'
    verdict = assess_service([before, after], {'timeout': 0, 'server': True})
    assert not verdict['accepted']
    assert 'installed_runtime_changed' in verdict['reasons']


def test_real_backend_clean_idle_exit_and_timeout_zero_survival():
    import asyncio
    from kayakgen.operations.runtime_probe import probe_backend

    expired = asyncio.run(probe_backend(1, 1.25))
    persistent = asyncio.run(probe_backend(0, 1.25))
    assert expired['outcome'] == 'idle_exit'
    assert expired['shutdown_scheduled'] is True
    assert persistent['outcome'] == 'continuous_survival_until_cleanup'
    assert persistent['shutdown_scheduled'] is False
    assert expired['explicit_cleanup_complete'] and persistent['explicit_cleanup_complete']


@pytest.mark.parametrize('kind,accepted,outcome', [
    ('unchanged', True, 'continuous_survival'),
    ('clean', False, 'clean_exit'),
    ('failed', False, 'failed_exit'),
    ('reused_pid', False, 'restarted'),
    ('restart_counter', False, 'restarted'),
])
def test_observed_service_outcomes_are_distinct(kind, accepted, outcome):
    from kayakgen.operations.runtime_service import assess_service

    before = running_service()
    after = copy.deepcopy(before)
    if kind in ('clean', 'failed'):
        after.update(ActiveState='inactive', SubState='dead', MainPID=0, process=None)
        after.update(Result='success' if kind == 'clean' else 'exit-code',
                     ExecMainStatus=0 if kind == 'clean' else 7)
    if kind == 'reused_pid':
        after['process']['start'] = 'new-process-with-same-pid'
    if kind == 'restart_counter':
        after['NRestarts'] = 1
    verdict = assess_service([before, after], {'timeout': 0, 'server': True})
    assert verdict['accepted'] is accepted
    assert verdict['outcome'] == outcome


@pytest.mark.parametrize('field,value,reason', [
    ('KillMode', 'control-group', 'detached_workers_require_kill_mode_process'),
    ('Restart', 'on-failure', 'persistent_restart_policy_must_be_always'),
])
def test_persistent_acceptance_preserves_detached_unit_policy(field, value, reason):
    from kayakgen.operations.runtime_service import assess_service

    service = running_service()
    service[field] = value
    verdict = assess_service([service, service], {'timeout': 0, 'server': True})
    assert not verdict['accepted'] and reason in verdict['reasons']


def test_positive_timeout_is_valid_control_but_not_persistent_deployment_policy():
    from kayakgen.operations.runtime_service import assess_service

    service = running_service()
    verdict = assess_service([service, service], {'timeout': 1, 'server': True})
    assert not verdict['accepted']
    assert 'persistent_service_requires_effective_timeout_zero_server_mode' in verdict['reasons']


def test_real_cli_refuses_wrong_installed_interpreter_and_retains_failure(tmp_path):
    import hashlib
    import json
    import os
    import subprocess
    import sys

    request = tmp_path / 'release-request.json'
    request.write_text(json.dumps({'schema_version': '1', 'python': '/different/release/bin/python'}))
    output = tmp_path / 'attempt'
    completed = subprocess.run([sys.executable, '-m', 'kayakgen.operations.runtime',
        '--release-request', str(request), '--out', str(output)],
        capture_output=True, text=True, env=os.environ.copy())
    assert completed.returncode == 1
    receipt = json.loads((output / 'runtime-receipt.json').read_text())
    assert receipt['status'] == 'failed'
    assert receipt['persistent_deployment_accepted'] is False
    assert receipt['request_sha256'] == hashlib.sha256(request.read_bytes()).hexdigest()
    assert 'selected installed interpreter' in receipt['error']


def test_same_dependency_version_with_changed_backend_bytes_refuses_acceptance():
    from kayakgen.operations.runtime import require_matching_backend

    identity = {'versions': {'trame-server': '3', 'wslink': '2', 'aiohttp': '3'},
                'modules': {'wslink.protocol': {'path': '/stage/protocol.py', 'sha256': 'a' * 64}}}
    service = copy.deepcopy(identity)
    service['modules']['wslink.protocol']['path'] = '/live/protocol.py'
    require_matching_backend(identity, service)
    service['modules']['wslink.protocol']['sha256'] = 'b' * 64
    with pytest.raises(ValueError, match='backend differs'):
        require_matching_backend(identity, service)


def test_unrelated_real_process_cannot_be_admitted_by_a_serve_argument(tmp_path):
    import subprocess
    import sys
    from kayakgen.operations.runtime_service import effective_settings

    argv = [sys.executable, '-c', 'import time; time.sleep(20)', 'serve']
    child = subprocess.Popen(argv, cwd=tmp_path)
    try:
        snapshot = {'process': {'python': sys.executable, 'argv': argv, 'cwd': str(tmp_path),
            'environment': {'TRAME_ARGS': '--timeout 0 --server',
                            'TRAME_SERVER': '1', 'TRAME_BACKEND': None}}}
        assert child.poll() is None
        with pytest.raises(ValueError, match='console invocation'):
            effective_settings(snapshot)
        assert child.poll() is None
    finally:
        child.terminate()
        child.wait(timeout=3)


@pytest.mark.parametrize('http_status', [200, 302])
def test_actual_http_readiness_requires_listener_ownership(http_status):
    import os
    import select
    import subprocess
    import sys
    from kayakgen.operations.runtime_service import check_readiness
    from kayakgen.services.generative_job_ownership import process_identity

    program = '''import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class Ready(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(int(sys.argv[1])); self.end_headers(); self.wfile.write(b"ready")
    def log_message(self, *args): pass
server = HTTPServer(("127.0.0.1", 0), Ready)
print(server.server_port, flush=True)
server.serve_forever()
'''
    child = subprocess.Popen([sys.executable, '-u', '-c', program, str(http_status)],
                             stdout=subprocess.PIPE, text=True)
    try:
        assert select.select([child.stdout], [], [], 3)[0]
        url = 'http://127.0.0.1:' + child.stdout.readline().strip() + '/'
        start, boot, state = process_identity(child.pid)
        snapshot = {'process': {'pid': child.pid, 'start': start, 'boot_id': boot, 'state': state}}
        ready = check_readiness(snapshot, url)
        assert ready['http_status'] == http_status and ready['listener_owned_by_pid'] == child.pid
        start, boot, state = process_identity(os.getpid())
        unrelated = {'process': {'pid': os.getpid(), 'start': start, 'boot_id': boot, 'state': state}}
        with pytest.raises(ValueError, match='not owned'):
            check_readiness(unrelated, url)
    finally:
        child.terminate()
        child.wait(timeout=3)
        child.stdout.close()


@pytest.mark.parametrize('drop_listener', [False, True])
def test_idle_observation_rechecks_readiness_when_the_process_stays_alive(monkeypatch, drop_listener):
    import select
    import subprocess
    import sys
    from kayakgen.operations import runtime_service as runtime
    from kayakgen.services.generative_job_ownership import process_identity

    program = '''import sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
class Ready(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ready")
    def log_message(self, *args): pass
server = HTTPServer(("127.0.0.1", 0), Ready)
print(server.server_port, flush=True)
if sys.argv[1] == "drop":
    server.handle_request()
    time.sleep(.05)
    server.server_close()
    print("listener-closed", flush=True)
    time.sleep(20)
else:
    server.serve_forever()
'''
    child = subprocess.Popen([sys.executable, '-u', '-c', program,
                              'drop' if drop_listener else 'keep'],
                             stdout=subprocess.PIPE, text=True)
    try:
        assert select.select([child.stdout], [], [], 3)[0]
        url = 'http://127.0.0.1:' + child.stdout.readline().strip() + '/'
        start, boot, state = process_identity(child.pid)
        sample = running_service()
        sample['MainPID'] = child.pid
        sample['process'].update(pid=child.pid, start=start, boot_id=boot, state=state)
        # The real socket lifetime is the oracle; invocation identity is checked
        # separately with the installed console and unrelated-process controls.
        snapshots = []
        listener_closed = []
        def sample_service(unit):
            if snapshots and drop_listener and not listener_closed:
                assert select.select([child.stdout], [], [], 3)[0]
                assert child.stdout.readline().strip() == 'listener-closed'
                listener_closed.append(True)
            snapshots.append(True)
            return copy.deepcopy(sample)
        monkeypatch.setattr(runtime, 'service_snapshot', sample_service)
        monkeypatch.setattr(runtime, 'effective_settings', lambda snapshot:
                            {'timeout': 0, 'server': True, 'backend': 'aiohttp'})
        observed = runtime.observe_service('owned-control.service', .2, url)
        assert child.poll() is None
        assert observed['outcome'] == 'continuous_survival'
        assert observed['accepted'] is (not drop_listener)
        if drop_listener:
            assert 'service_readiness_lost_after_idle' in observed['reasons']
        else:
            assert observed['readiness_after_idle']['http_status'] == 200
            assert observed['readiness_after_idle']['completed_after_idle_observation']
        assert observed['idle_observed_s'] >= .2
    finally:
        child.terminate()
        child.wait(timeout=3)
        child.stdout.close()
