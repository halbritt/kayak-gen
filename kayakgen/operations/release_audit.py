"""Source-bound installed-byte checks reusable by runtime lifecycle probes."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.resources
import json
import os
from pathlib import Path
import sys
import sysconfig
from urllib.parse import unquote, urlparse

from kayakgen.operations.release_manifest import SourceManifest, file_sha256, require, verify_wheel
from kayakgen.operations.release_stage import normalized_name


def installed_root() -> Path:
    import kayakgen
    require(sys.prefix != sys.base_prefix, 'Release must use a virtual environment')
    require(sys.flags.isolated == 1, 'Installed verification requires Python -I')
    require(not any(key in os.environ for key in ('PYTHONPATH', 'PYTHONHOME')),
            'PYTHONPATH/PYTHONHOME must be absent')
    root = Path(kayakgen.__file__).resolve().parent
    sites = {Path(sysconfig.get_path(key)).resolve() for key in ('purelib', 'platlib')}
    require(root.parent in sites, 'kayakgen import is supplied by a checkout: ' + str(root))
    return root


def module_audit(manifest: SourceManifest) -> dict:
    root = installed_root()
    expected = manifest.hashes()
    result = {}
    for name, module in sorted(sys.modules.copy().items()):
        if name != 'kayakgen' and not name.startswith('kayakgen.'):
            continue
        location = getattr(module, '__file__', None)
        require(location is not None, 'Package module has no auditable origin: ' + name)
        path = Path(location).resolve()
        require(path.is_relative_to(root), 'Module supplied outside release package: ' + name)
        relative = 'kayakgen/' + path.relative_to(root).as_posix()
        require(relative in expected and file_sha256(path) == expected[relative],
                'Imported module differs from selected source: ' + name)
        result[name] = {'path': str(path), 'sha256': expected[relative]}
    return result


def audit_package(root: Path, manifest: SourceManifest) -> dict:
    expected = manifest.hashes()
    actual = {}
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'Installed package contains a symlink: ' + str(path))
        if path.is_file():
            actual['kayakgen/' + path.relative_to(root).as_posix()] = file_sha256(path)
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    require(not missing, 'Installed package missing files: ' + ', '.join(sorted(missing)))
    require(not extra, 'Installed package has unexpected files: ' + ', '.join(sorted(extra)))
    require(actual == expected, 'Installed package bytes differ from selected source')
    return actual


def audit_direct_url(document: dict, wheel: Path) -> None:
    require(not document.get('dir_info', {}).get('editable'), 'Editable install refused')
    url = urlparse(document.get('url', ''))
    require(url.scheme == 'file' and url.netloc in {'', 'localhost'} and not url.query,
            'Installed origin must identify the retained local wheel')
    origin = Path(unquote(url.path))
    require(origin.suffix == '.whl' and file_sha256(origin) == file_sha256(wheel),
            'Installed origin wheel differs from selected wheel bytes')
    # uv may emit archive_info={} for a local hash-locked wheel. Audit its retained
    # origin bytes independently; if PEP610 hashes are present, verify those too.
    recorded = document.get('archive_info', {}).get('hashes', {}).get('sha256')
    require(recorded is None or recorded == file_sha256(wheel), 'Installed wheel hash metadata differs')


def audit_installed(manifest: SourceManifest, wheel: Path, dependencies: dict[str, str]) -> dict:
    """Audit one noneditable environment; caller supplies source-bound wheel and pins.

    This deliberately runs inside the target interpreter with -I and no import-path
    overrides. Lifecycle tools may call it before and after their own runtime probe.
    It neither starts services nor mutates the environment.
    """
    contents = verify_wheel(wheel, manifest)
    root = installed_root()
    files = audit_package(root, manifest)
    distribution = importlib.metadata.distribution('kayakgen')
    require(distribution.version == manifest.package_version, 'Installed version differs')
    for name, data in contents.files:
        if name.startswith(contents.dist_info + '/') and not name.endswith('/RECORD'):
            require(distribution.locate_file(name).read_bytes() == data,
                    'Installed wheel metadata differs: ' + name)
    direct_url = json.loads(distribution.read_text('direct_url.json') or '{}')
    audit_direct_url(direct_url, wheel)
    installed = {}
    for item in importlib.metadata.distributions():
        name = normalized_name(item.metadata['Name'])
        require(name not in installed, 'Duplicate installed distribution: ' + name)
        installed[name] = item.version
    require(installed == {**dependencies, 'kayakgen': manifest.package_version},
            'Installed dependency set differs from the resolved pinned set')
    resources = {}
    package = importlib.resources.files('kayakgen')
    for name in manifest.resources:
        data = package.joinpath(name.removeprefix('kayakgen/')).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(digest == files[name], 'Resource API returned different bytes: ' + name)
        resources[name] = {'bytes': len(data), 'sha256': digest}
    return {'python': sys.executable, 'prefix': sys.prefix, 'package_root': str(root),
            'version': distribution.version, 'files': files, 'resources': resources,
            'dependencies': installed, 'direct_url': direct_url,
            'record_sha256': hashlib.sha256((distribution.read_text('RECORD') or '').encode()).hexdigest(),
            'modules': module_audit(manifest)}
