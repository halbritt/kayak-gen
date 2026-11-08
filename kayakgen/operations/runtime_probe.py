"""Actual installed Trame/aiohttp idle controls, including transient clean exits."""
from __future__ import annotations

import argparse
import asyncio
from importlib import metadata
import inspect
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from kayakgen.operations.release_audit import audit_installed
from kayakgen.operations.release_manifest import file_sha256, read_manifest, require, write_json
from kayakgen.operations.release_stage import utc_now
from kayakgen.services.generative_job_ownership import process_identity


def audit_runtime(request_path: Path, digest: str) -> tuple[dict, dict]:
    require(file_sha256(request_path) == digest, 'Installed release request changed')
    request = json.loads(request_path.read_text())
    require(request['schema_version'] == '1', 'Unsupported installed release request')
    require(Path(sys.executable).absolute() == Path(request['python']),
            'Runtime verifier must execute in the selected installed interpreter')
    manifest = read_manifest(Path(request['manifest']), request['manifest_sha256'])
    require(manifest.source_tree == request['source_tree'], 'Runtime source tree differs from manifest')
    wheel = Path(request['wheel'])
    require(file_sha256(wheel) == request['wheel_sha256'], 'Selected runtime wheel changed')
    return request, audit_installed(manifest, wheel, request['dependencies'])


def backend_identity() -> dict:
    import trame_server.core
    import trame_server.utils.argument_parser
    import wslink.protocol
    import wslink.backends.aiohttp
    modules = (trame_server.core, trame_server.utils.argument_parser,
               wslink.protocol, wslink.backends.aiohttp)
    return {'versions': {name: metadata.version(name)
                         for name in ('trame-server', 'wslink', 'aiohttp')},
            'modules': {module.__name__: {'path': inspect.getfile(module),
                'sha256': file_sha256(Path(inspect.getfile(module)))} for module in modules}}


async def probe_backend(timeout: int, observation_s: float) -> dict:
    """Exercise a real backend without clients; always clean up owned listeners."""
    from trame_server import Server
    from wslink.backends.aiohttp import WebAppServer
    require(type(timeout) is int and timeout >= 0, 'Idle timeout must be a nonnegative integer')
    require(math.isfinite(observation_s) and observation_s > 0, 'Observation must be finite and positive')
    options, _ = Server(name='installed-lifetime-control').cli.parse_known_args(
        ['--timeout', str(timeout), '--server'])
    require(options.timeout == timeout and options.server is True, 'Installed parser changed requested controls')
    backend = WebAppServer({'host': '127.0.0.1', 'port': 0, 'timeout': options.timeout,
                            'handle_signals': False})
    ready = asyncio.get_running_loop().create_future()
    task = asyncio.create_task(backend.start(port_callback=ready.set_result))
    started = time.monotonic()
    identity = process_identity(os.getpid())
    record = {'timeout': options.timeout, 'server': options.server,
              'pid': os.getpid(), 'process_identity_before': identity,
              'backend': type(backend).__module__ + '.' + type(backend).__name__,
              'websocket_clients_created': 0, 'identity': backend_identity()}
    try:
        record['port'] = await asyncio.wait_for(ready, 5)
        record['shutdown_scheduled'] = backend._shutdown_task is not None
        if timeout > 0:
            await asyncio.wait_for(asyncio.shield(task), timeout + 3.)
            require(record['shutdown_scheduled'] and backend.completion.done(),
                    'Positive idle timeout did not complete the actual backend')
            record['outcome'] = 'idle_exit'
        else:
            await asyncio.sleep(observation_s)
            require(not task.done() and not backend.completion.done(), 'Timeout zero backend exited early')
            require(not record['shutdown_scheduled'] and backend._shutdown_task is None,
                    'Timeout zero still scheduled an idle shutdown')
            record.update(outcome='continuous_survival_until_cleanup', observation_s=observation_s)
        record['process_identity_after'] = process_identity(os.getpid())
        require(identity[:2] == record['process_identity_after'][:2],
                'Backend control process identity changed')
        record['elapsed_s'] = time.monotonic() - started
    finally:
        backend.shutdown_cancel()
        if backend.runner is not None and not backend.completion.done():
            await backend.stop()
        await asyncio.wait_for(task, 3)
    record['explicit_cleanup_complete'] = True
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timeout', type=int, required=True)
    parser.add_argument('--observe-seconds', type=float, default=1.25)
    args = parser.parse_args()
    require(not args.out.exists(), 'Probe receipt must be new; previous attempts are retained')
    receipt = {'schema_version': 'kayakgen-runtime-probe/1', 'status': 'running',
               'started_at': utc_now(), 'request_sha256': args.request_sha256}
    code = 1
    try:
        request, receipt['installed_before'] = audit_runtime(args.release_request, args.request_sha256)
        receipt['source_tree'] = request['source_tree']
        receipt['probe'] = asyncio.run(probe_backend(args.timeout, args.observe_seconds))
        _, receipt['installed_after'] = audit_runtime(args.release_request, args.request_sha256)
        receipt['status'] = 'passed'
        code = 0
    except Exception:
        receipt.update(status='failed', error=traceback.format_exc())
    except KeyboardInterrupt:
        receipt.update(status='interrupted', error='KeyboardInterrupt')
        code = 130
    finally:
        receipt.update(finished_at=utc_now(), exit_code=code)
        write_json(args.out, receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': str(args.out), 'exit_code': code}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
