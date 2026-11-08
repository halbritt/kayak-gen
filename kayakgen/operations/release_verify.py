"""Isolated installed worker for the maintained release command."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import traceback

from kayakgen.operations.release_audit import audit_installed, module_audit
from kayakgen.operations.release_manifest import file_sha256, read_manifest, require, write_json
from kayakgen.operations.release_openfoam import cfd_workflow, resource_render, version_preflight
from kayakgen.operations.release_stage import utc_now
from kayakgen.operations.release_workflows import analytical_workflow, builder_exports, surface_exports


def verify(request: dict, receipt: dict) -> None:
    manifest = read_manifest(Path(request['manifest']), request['manifest_sha256'])
    wheel = Path(request['wheel'])
    require(file_sha256(wheel) == request['wheel_sha256'], 'Selected wheel changed')
    require(Path(sys.executable).absolute() == Path(request['python']), 'Worker interpreter differs')
    out = Path(request['output'])
    receipt['installed_before'] = audit_installed(manifest, wheel, request['dependencies'])
    # Test the exact immutable profile version wrapper before expensive evaluation.
    receipt['solver_preflight'] = version_preflight(out, Path(request['bashrc']))
    receipt['resource_render'] = resource_render(out / 'resource-render')
    receipt['analytical'], hull, source = analytical_workflow(out / 'analytical', request['inputs'])
    receipt['surface_exports'] = surface_exports(out, hull, source)
    receipt['builder_exports'] = builder_exports(out, hull, source)
    args = SimpleNamespace(bashrc=Path(request['bashrc']), step_timeout=request['step_timeout'],
                           manifest=Path(request['manifest']), manifest_sha256=request['manifest_sha256'])
    receipt['cfd'] = cfd_workflow(out / 'cfd', args)
    receipt['installed_after'] = audit_installed(manifest, wheel, request['dependencies'])
    receipt['modules_final'] = module_audit(manifest)
    receipt['scope'] = ('Installed selected evaluation, persist/reload, guarded HTML report, '
                        'exports and real bounded legacy-fixture CFD smoke')


def worker(request_path: Path, expected_sha256: str) -> int:
    require(file_sha256(request_path) == expected_sha256, 'Release verification request changed')
    request = json.loads(request_path.read_text())
    require(request['schema_version'] == '1', 'Unsupported release verification request')
    out = Path(request['output'])
    out.mkdir()
    receipt = {'schema_version': '1', 'started_at': utc_now(), 'status': 'running',
               'request_sha256': expected_sha256, 'source_tree': request['source_tree']}
    code = 0
    try:
        verify(request, receipt)
        receipt['status'] = 'passed'
    except Exception:
        receipt.update(status='failed', error=traceback.format_exc())
        (out / 'failure.txt').write_text(receipt['error'])
        code = 1
    finally:
        if file_sha256(request_path) != expected_sha256:
            receipt.update(status='failed', error='Release verification request changed during execution')
            code = 1
        receipt['finished_at'] = utc_now()
        write_json(out / 'verification-receipt.json', receipt)
    print(f'Installed verification: {receipt["status"]}; {out / "verification-receipt.json"}')
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args()
    return worker(args.request, args.request_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
