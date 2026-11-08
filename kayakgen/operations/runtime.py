"""Verify installed idle controls and optionally a persistent local user service.

Run inside the selected release with Python -I -B. Omitting --unit exercises
backend controls only; it never accepts a persistent deployment.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import traceback

from kayakgen.operations.release_manifest import file_sha256, require, write_json
from kayakgen.operations.release_stage import clean_environment, run_logged, utc_now
from kayakgen.operations.runtime_probe import audit_runtime
from kayakgen.operations.runtime_service import observe_service


def require_matching_backend(control: dict, service: dict) -> None:
    require(all(service['versions'].get(name) == version
                for name, version in control['versions'].items()),
            'Observed service backend differs from the exercised installed dependency versions')
    require(all(service['modules'].get(name, {}).get('sha256') == origin['sha256']
                for name, origin in control['modules'].items()),
            'Observed service backend differs from the exercised installed module bytes')


def idle_controls(request: Path, digest: str, output: Path) -> list[dict]:
    environment = clean_environment()
    environment['WSLINK_READY_MSG'] = ''
    controls = []
    for timeout in (1, 0):
        target = output / f'idle-{timeout}.json'
        command = [sys.executable, '-I', '-B', '-m', 'kayakgen.operations.runtime_probe',
            '--release-request', str(request), '--request-sha256', digest,
            '--out', str(target), '--timeout', str(timeout)]
        execution = run_logged(command, output / f'idle-{timeout}.log',
                               timeout_s=15, env=environment)
        receipt = json.loads(target.read_text())
        require(receipt['status'] == 'passed' and receipt['exit_code'] == 0
                and receipt['request_sha256'] == digest, 'Installed idle control failed')
        controls.append({'timeout': timeout, 'command': execution,
                         'receipt': str(target), 'sha256': file_sha256(target),
                         'probe': receipt['probe']})
    return controls


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-request', type=Path, required=True,
                        help='Source-bound verification-request.json from the release command')
    parser.add_argument('--out', type=Path, required=True, help='New external attempt directory')
    parser.add_argument('--unit', help='Read-only persistent systemd user unit observation')
    parser.add_argument('--observe-seconds', type=float,
                        help='Explicit deployment observation interval; required with --unit')
    parser.add_argument('--readiness-url', help='Explicit loopback HTTP URL; required with --unit')
    args = parser.parse_args(argv)
    require((args.unit is None) == (args.observe_seconds is None),
            '--unit and --observe-seconds must be supplied together')
    require((args.unit is None) == (args.readiness_url is None),
            '--unit and --readiness-url must be supplied together')
    if args.observe_seconds is not None:
        require(math.isfinite(args.observe_seconds) and args.observe_seconds > 0,
                'Deployment observation must be finite and positive')
    args.release_request = args.release_request.expanduser().resolve()
    args.out = args.out.expanduser().resolve()
    require(not args.out.exists(), 'Runtime output must be new; failed attempts are retained')
    require(not args.out.is_relative_to(Path(sys.prefix).resolve()),
            'Runtime output must be outside the installed environment')
    require(not any((parent / '.git').exists() for parent in args.out.parents),
            'Runtime output must be outside source checkouts')
    return args


def main(argv=None) -> int:
    args = arguments(argv)
    args.out.mkdir(parents=True)
    receipt = {'schema_version': 'kayakgen-runtime-receipt/1', 'status': 'running',
        'started_at': utc_now(), 'request_sha256': None, 'unit': args.unit,
        'requested_observation_s': args.observe_seconds,
        'persistent_deployment_accepted': False,
        'scope': 'installed idle controls' if args.unit is None else
                 'installed idle controls plus read-only persistent service observation',
        'service_modified': False}
    write_json(args.out / 'runtime-receipt.json', receipt)
    code = 1
    try:
        digest = file_sha256(args.release_request)
        receipt['request_sha256'] = digest
        request, receipt['installed_before'] = audit_runtime(args.release_request, digest)
        receipt['source_tree'] = request['source_tree']
        receipt['controls'] = idle_controls(args.release_request, digest, args.out)
        if args.unit is not None:
            receipt['service'] = observe_service(args.unit, args.observe_seconds, args.readiness_url)
            require_matching_backend(receipt['controls'][0]['probe']['identity'],
                                     receipt['service']['settings'])
            require(receipt['service']['accepted'], 'Persistent service refused: '
                    + ', '.join(receipt['service']['reasons']))
        _, receipt['installed_after'] = audit_runtime(args.release_request, digest)
        receipt['persistent_deployment_accepted'] = args.unit is not None
        receipt['status'] = 'passed'
        code = 0
    except Exception:
        receipt.update(status='failed', error=traceback.format_exc())
    except KeyboardInterrupt:
        receipt.update(status='interrupted', error='KeyboardInterrupt')
        code = 130
    finally:
        receipt.update(finished_at=utc_now(), exit_code=code)
        write_json(args.out / 'runtime-receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'exit_code': code,
                      'receipt': str(args.out / 'runtime-receipt.json')}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
