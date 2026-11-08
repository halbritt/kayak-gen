"""Source-bound release checks must reject a wheel that omits declared data."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
from pathlib import Path
import subprocess
import zipfile

import pytest


def source_repo(tmp_path: Path) -> Path:
    repo = tmp_path / 'repo'
    (repo / 'kayakgen/templates').mkdir(parents=True)
    (repo / 'kayakgen/__init__.py').write_text('answer = 42\n')
    (repo / 'kayakgen/templates/sample.dat').write_text('source resource\n')
    (repo / 'pyproject.toml').write_text('''[project]
name = "kayakgen"
version = "0.1.0"
[tool.setuptools.package-data]
kayakgen = ["templates/*.dat"]
''')
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Release test', '-c',
                    'user.email=release@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    return repo


def wheel(tmp_path: Path, package: dict[str, bytes]) -> Path:
    members = {**package, 'kayakgen-0.1.0.dist-info/METADATA':
               b'Metadata-Version: 2.1\nName: kayakgen\nVersion: 0.1.0\n'}
    record_path = 'kayakgen-0.1.0.dist-info/RECORD'
    stream = io.StringIO()
    writer = csv.writer(stream)
    for name, content in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b'=').decode()
        writer.writerow([name, 'sha256=' + digest, len(content)])
    writer.writerow([record_path, '', ''])
    members[record_path] = stream.getvalue().encode()
    path = tmp_path / 'kayakgen-0.1.0-py3-none-any.whl'
    with zipfile.ZipFile(path, 'w') as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def test_declared_nonstandard_resource_is_required_in_built_wheel(tmp_path):
    from kayakgen.operations.release_manifest import source_manifest, verify_wheel

    repo = source_repo(tmp_path)
    manifest = source_manifest(repo, 'HEAD')
    path = wheel(tmp_path, {'kayakgen/__init__.py': b'answer = 42\n'})
    with pytest.raises(ValueError, match='missing.*sample.dat'):
        verify_wheel(path, manifest)


def test_valid_manifest_accepts_changed_resource_counts_and_refuses_tampering(tmp_path):
    from kayakgen.operations.release_manifest import source_manifest, verify_wheel

    repo = source_repo(tmp_path)
    manifest = source_manifest(repo, 'HEAD')
    package = {'kayakgen/__init__.py': b'answer = 42\n',
               'kayakgen/templates/sample.dat': b'source resource\n'}
    assert len(manifest.resources) == 1
    assert verify_wheel(wheel(tmp_path, package), manifest).version == '0.1.0'
    package['kayakgen/templates/sample.dat'] = b'plausible but altered\n'
    with pytest.raises(ValueError, match='differs from source'):
        verify_wheel(wheel(tmp_path, package), manifest)


def test_unexpected_wheel_file_cannot_hide_behind_a_valid_record(tmp_path):
    from kayakgen.operations.release_manifest import source_manifest, verify_wheel

    manifest = source_manifest(source_repo(tmp_path), 'HEAD')
    path = wheel(tmp_path, {'kayakgen/__init__.py': b'answer = 42\n',
                          'kayakgen/templates/sample.dat': b'source resource\n',
                          'kayakgen/old_module.py': b'old = True\n'})
    with pytest.raises(ValueError, match='unexpected runtime files.*old_module'):
        verify_wheel(path, manifest)


def test_an_unpinned_transitive_dependency_is_refused(tmp_path):
    from kayakgen.operations.release_stage import read_pins, resolved_dependencies

    constraints = tmp_path / 'constraints.txt'
    constraints.write_text('Jinja2==3.1.6\n')
    lock = tmp_path / 'dependencies.lock'
    lock.write_text('jinja2==3.1.6 \\\n    --hash=sha256:abc\nmarkupsafe==3.0.3 \\\n    --hash=sha256:def\n')
    with pytest.raises(ValueError, match='lacks supplied exact pin: markupsafe'):
        resolved_dependencies(lock, read_pins(constraints))


@pytest.mark.parametrize('mutation', ['missing', 'altered', 'unexpected', 'symlink'])
def test_installed_namespace_refuses_byte_or_membership_changes(tmp_path, mutation):
    from kayakgen.operations.release_audit import audit_package
    from kayakgen.operations.release_manifest import source_manifest

    repo = source_repo(tmp_path)
    manifest = source_manifest(repo, 'HEAD')
    root = repo / 'kayakgen'
    assert audit_package(root, manifest) == manifest.hashes()
    resource = root / 'templates/sample.dat'
    if mutation == 'missing':
        resource.unlink()
    elif mutation == 'altered':
        resource.write_text('altered resource\n')
    elif mutation == 'unexpected':
        (root / 'old.py').write_text('unexpected = True\n')
    else:
        resource.unlink()
        resource.symlink_to(root / '__init__.py')
    with pytest.raises(ValueError, match='missing|differ|unexpected|symlink'):
        audit_package(root, manifest)


def test_checkout_import_cannot_count_as_installed_verification():
    from kayakgen.operations.release_audit import installed_root

    with pytest.raises(ValueError, match='Python -I|checkout'):
        installed_root()


def test_owner_inputs_are_paired_and_existing_attempts_are_preserved(tmp_path):
    from kayakgen.operations.release import parser, validate_request

    arguments = ['--repo', str(tmp_path), '--source', 'HEAD', '--constraints',
                 str(tmp_path / 'pins'), '--out', str(tmp_path / 'attempt')]
    with pytest.raises(ValueError, match='supplied together'):
        validate_request(parser().parse_args([*arguments, '--hull', 'hull.json']))
    (tmp_path / 'attempt').mkdir()
    (tmp_path / 'attempt/previous-evidence').write_text('retained')
    with pytest.raises(ValueError, match='new directory'):
        validate_request(parser().parse_args(arguments))
    assert (tmp_path / 'attempt/previous-evidence').read_text() == 'retained'


def test_version_wrapper_shifts_bashrc_argument_before_sourcing(tmp_path):
    from kayakgen.operations.release_openfoam import version_command

    bashrc = tmp_path / 'foam bashrc'
    bashrc.write_text('''test "$#" = 0 || return 92
interFoam() { test "$1" = -help || return 93; echo 'Using: OpenFOAM-2512 test-control'; }
''')
    result = subprocess.run(version_command(bashrc), capture_output=True, text=True, timeout=5)
    assert result.returncode == 0
    assert result.stdout == 'Using: OpenFOAM-2512 test-control\n'


def test_failed_command_retains_log_and_failure_receipt(tmp_path):
    import json
    import sys
    from kayakgen.operations.release_stage import clean_environment, run_logged

    log = tmp_path / 'failed.log'
    with pytest.raises(ValueError, match='Command failed'):
        run_logged([sys.executable, '-c', 'print("retained failure"); raise SystemExit(17)'],
                   log, timeout_s=5, env=clean_environment())
    receipt = json.loads(log.with_suffix('.command.json').read_text())
    assert receipt['status'] == 'failed' and receipt['returncode'] == 17
    assert log.read_text() == 'retained failure\n'


def test_input_snapshots_preserve_exact_supplied_settings_and_detect_changes(tmp_path):
    from types import SimpleNamespace
    from kayakgen.operations.release import snapshot_inputs, verify_input_preservation

    owner = tmp_path / 'owner'
    owner.mkdir()
    hull, context = owner / 'hull.json', owner / 'context.json'
    hull.write_bytes(b'{"owner": "physical hull bytes"}\n')
    context.write_bytes(b'{"numerical_relative_tolerance":0.004,"load_kg":117}\n')
    out = tmp_path / 'attempt'
    out.mkdir()
    inputs = snapshot_inputs(SimpleNamespace(hull=hull, context=context), out)
    assert Path(inputs['context']).read_bytes() == context.read_bytes()
    assert all(item['unchanged'] and item['snapshot_unchanged']
               for item in verify_input_preservation(inputs).values())
    context.write_text('changed original')
    evidence = verify_input_preservation(inputs)
    assert not evidence['context']['unchanged'] and evidence['context']['snapshot_unchanged']


def test_wheel_origin_without_optional_hash_is_verified_by_actual_bytes(tmp_path):
    from kayakgen.operations.release_audit import audit_direct_url

    selected, origin = tmp_path / 'selected.whl', tmp_path / 'origin.whl'
    selected.write_bytes(b'wheel control bytes')
    origin.write_bytes(selected.read_bytes())
    audit_direct_url({'url': origin.as_uri(), 'archive_info': {}}, selected)
    origin.write_bytes(b'other wheel bytes')
    with pytest.raises(ValueError, match='origin wheel differs'):
        audit_direct_url({'url': origin.as_uri(), 'archive_info': {}}, selected)


def test_output_symlink_cannot_bypass_checkout_boundary(tmp_path):
    from kayakgen.operations.release import parser, validate_request

    repo = source_repo(tmp_path)
    (repo / 'nested').mkdir()
    alias = tmp_path / 'external-looking-alias'
    alias.symlink_to(repo / 'nested', target_is_directory=True)
    args = parser().parse_args(['--repo', str(repo), '--source', 'HEAD', '--constraints',
                               str(tmp_path / 'pins'), '--out', str(alias / 'attempt')])
    with pytest.raises(ValueError, match='outside a source checkout'):
        validate_request(args)


def test_realized_context_allows_solved_pose_but_refuses_changed_owner_settings():
    from kayakgen.eval.contract import EvaluationContext
    from kayakgen.model.hull import Hull
    from kayakgen.operations.release_workflows import verify_realized_context

    context = EvaluationContext.for_hull(Hull(), equilibrium=True, n_theta=47,
                                         numerical_relative_tolerance=.004)
    posed = context.model_copy(update={'sinkage_m': -.02, 'trim_angle_deg': .1})
    verify_realized_context(context, posed)
    for field, value in [('n_theta', 48), ('numerical_relative_tolerance', .01),
                         ('equilibrium_tolerance_kg', .5)]:
        with pytest.raises(ValueError, match='requested settings'):
            verify_realized_context(context, posed.model_copy(update={field: value}))
    fixed = context.model_copy(update={'equilibrium': False})
    with pytest.raises(ValueError, match='requested settings'):
        verify_realized_context(fixed, fixed.model_copy(update={'sinkage_m': -.02}))
