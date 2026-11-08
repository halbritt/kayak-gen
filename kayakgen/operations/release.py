"""Build, stage and exercise an immutable noneditable release outside a checkout.

Usage: python -m kayakgen.operations.release --repo REPO --source REVISION
       --constraints EXACT_PINS --out NEW_DIRECTORY [--hull HULL --context CONTEXT]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import sys
import traceback

from kayakgen.operations.release_manifest import (
    export_source, file_sha256, require, source_manifest, verify_wheel, write_json)
from kayakgen.operations.release_stage import (
    StageRequest, clean_environment, run_logged, stage_environment, utc_now)


def validate_request(args) -> None:
    require((args.hull is None) == (args.context is None), '--hull and --context must be supplied together')
    require(math.isfinite(args.step_timeout) and args.step_timeout > 0, 'CFD deadline must be positive')
    require(math.isfinite(args.timeout) and args.timeout >= 2 * (6 * args.step_timeout + 60) + 180,
            'Worker deadline must cover version/solver command bounds and workflow allowance')
    args.out = args.out.expanduser().resolve()
    require(not args.out.exists(), 'Release output must be a new directory; failed attempts are retained')
    require(not any((parent / '.git').exists() for parent in (args.out, *args.out.parents)),
            'Release output must be outside a source checkout')
    for name in ('repo', 'constraints', 'python', 'bashrc', 'hull', 'context'):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, value.expanduser().absolute())
    for source in (args.hull, args.context):
        if source is not None:
            require(not args.out.resolve().is_relative_to(source.resolve().parent),
                    'Release output must be outside the supplied input directory')


def snapshot_inputs(args, out: Path) -> dict:
    inputs = {'hull': None, 'context': None, 'originals': {}}
    if args.hull is None:
        return inputs
    directory = out / 'inputs'
    directory.mkdir()
    for name in ('hull', 'context'):
        source = getattr(args, name)
        target = directory / (name + '.json')
        content = source.read_bytes()
        target.write_bytes(content)
        digest = file_sha256(target)
        require(file_sha256(source) == digest, 'Supplied input changed while snapshotting: ' + str(source))
        inputs[name] = str(target)
        inputs['originals'][name] = {'path': str(source), 'sha256': digest}
    return inputs


def build_release(args, receipt: dict) -> tuple[dict, Path]:
    manifest = source_manifest(args.repo, args.source)
    receipt.update(source_tree=manifest.source_tree, source_commit=manifest.source_commit)
    manifest_path = args.out / 'source-manifest.json'
    write_json(manifest_path, manifest.document())
    source = args.out / 'source'
    export_source(args.repo, manifest.source_tree, source)
    wheels = args.out / 'wheels'
    wheels.mkdir()
    uv = shutil.which('uv')
    require(uv is not None, 'Installed uv executable is required')
    run_logged([uv, '--no-config', 'build', str(source), '--wheel', '--out-dir', str(wheels),
                '--python', str(args.python), '--no-python-downloads'],
               args.out / 'build.log', timeout_s=300, env=clean_environment())
    candidates = list(wheels.glob('*.whl'))
    require(len(candidates) == 1, 'Build must produce exactly one wheel')
    wheel = candidates[0]
    contents = verify_wheel(wheel, manifest)
    receipt['wheel'] = {'path': str(wheel), 'sha256': file_sha256(wheel),
                        'version': contents.version, 'package_files': len(manifest.files),
                        'resources': len(manifest.resources)}
    receipt['manifest_sha256'] = file_sha256(manifest_path)
    stage = stage_environment(StageRequest(wheel, args.constraints, args.python, args.out / 'stage'))
    write_json(args.out / 'stage-receipt.json', stage)
    receipt['stage'] = stage
    return manifest.document(), manifest_path


def worker_environment(out: Path, bashrc: Path) -> dict[str, str]:
    environment = clean_environment()
    for directory in ('cache', 'config', 'tmp', 'matplotlib'):
        (out / directory).mkdir()
    environment.update(KAYAKGEN_INDEX_DB=str(out / 'isolated-index.sqlite'),
        XDG_CACHE_HOME=str(out / 'cache'), XDG_CONFIG_HOME=str(out / 'config'),
        TMPDIR=str(out / 'tmp'), MPLCONFIGDIR=str(out / 'matplotlib'), OPENBLAS_NUM_THREADS='1',
        KAYAKGEN_OPENFOAM_BASHRC=str(bashrc), LIBGL_ALWAYS_SOFTWARE='1',
        __EGL_VENDOR_LIBRARY_FILENAMES='/usr/share/glvnd/egl_vendor.d/50_mesa.json',
        VTK_DEFAULT_OPENGL_WINDOW='vtkEGLRenderWindow')
    return environment


def run_worker(args, receipt: dict, manifest: dict, manifest_path: Path, inputs: dict) -> None:
    stage = receipt['stage']
    request = {'schema_version': '1', 'source_tree': manifest['source_tree'],
        'manifest': str(manifest_path), 'manifest_sha256': receipt['manifest_sha256'],
        'wheel': receipt['wheel']['path'], 'wheel_sha256': receipt['wheel']['sha256'],
        'python': stage['python'], 'dependencies': stage['dependencies'], 'inputs': inputs,
        'output': str(args.out / 'workflows'), 'bashrc': str(args.bashrc), 'step_timeout': args.step_timeout}
    request_path = args.out / 'verification-request.json'
    write_json(request_path, request)
    request_sha = file_sha256(request_path)
    receipt.update(request_sha256=request_sha, worker_receipt=str(args.out / 'workflows/verification-receipt.json'))
    environment = worker_environment(args.out, args.bashrc)
    receipt['worker_environment'] = {key: environment[key] for key in (
        'KAYAKGEN_INDEX_DB', 'LIBGL_ALWAYS_SOFTWARE', '__EGL_VENDOR_LIBRARY_FILENAMES',
        'VTK_DEFAULT_OPENGL_WINDOW')}
    run_logged([stage['python'], '-I', '-B', '-m', 'kayakgen.operations.release_verify',
                '--request', str(request_path), '--request-sha256', request_sha],
               args.out / 'worker.log', timeout_s=args.timeout, env=environment)
    require(file_sha256(request_path) == request_sha, 'Installed worker request changed')
    result = json.loads(Path(receipt['worker_receipt']).read_text())
    require(result['status'] == 'passed' and result['request_sha256'] == request_sha,
            'Installed workflows did not produce matching successful evidence')
    require(file_sha256(manifest_path) == receipt['manifest_sha256'], 'Source manifest changed')
    require(file_sha256(Path(receipt['wheel']['path'])) == receipt['wheel']['sha256'], 'Wheel changed')


def verify_input_preservation(inputs: dict) -> dict:
    result = {}
    for name, original in inputs['originals'].items():
        path = Path(original['path'])
        unchanged = path.is_file() and file_sha256(path) == original['sha256']
        snapshot = Path(inputs[name])
        snapshot_unchanged = snapshot.is_file() and file_sha256(snapshot) == original['sha256']
        result[name] = {**original, 'unchanged': unchanged, 'snapshot_unchanged': snapshot_unchanged}
    return result


def release(args) -> int:
    validate_request(args)
    args.out.mkdir(parents=True)
    receipt = {'schema_version': '1', 'started_at': utc_now(), 'status': 'running',
               'authority': 'new inactive stage only; no live service/current-link changes'}
    inputs = {'hull': None, 'context': None, 'originals': {}}
    code = 0
    try:
        inputs = snapshot_inputs(args, args.out)
        manifest, manifest_path = build_release(args, receipt)
        run_worker(args, receipt, manifest, manifest_path, inputs)
        receipt['status'] = 'passed'
    except Exception:
        receipt.update(status='failed', error=traceback.format_exc())
        (args.out / 'failure.txt').write_text(receipt['error'])
        code = 1
    finally:
        preservation = verify_input_preservation(inputs)
        receipt['input_preservation'] = preservation
        if not all(item['unchanged'] and item['snapshot_unchanged'] for item in preservation.values()):
            receipt.update(status='failed', input_error='Supplied input or its snapshot changed')
            code = 1
        receipt['finished_at'] = utc_now()
        write_json(args.out / 'release-receipt.json', receipt)
    print(f'Release verification: {receipt["status"]}; {args.out / "release-receipt.json"}')
    return code


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'constraints', 'out'):
        result.add_argument('--' + name, type=Path, required=True)
    result.add_argument('--source', required=True, help='Git commit or tree; resolved once to immutable tree')
    result.add_argument('--python', type=Path, default=Path(sys.executable))
    result.add_argument('--hull', type=Path)
    result.add_argument('--context', type=Path)
    result.add_argument('--bashrc', type=Path, default=Path('/usr/lib/openfoam/openfoam2512/etc/bashrc'))
    result.add_argument('--timeout', type=float, default=900., help='Installed worker deadline in seconds')
    result.add_argument('--step-timeout', type=float, default=45., help='Each real OpenFOAM command deadline')
    return result


def main() -> int:
    return release(parser().parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
