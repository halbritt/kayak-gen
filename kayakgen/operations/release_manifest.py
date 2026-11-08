"""Bind wheel contents to immutable Git source and its declared package data."""
from __future__ import annotations

import base64
import csv
from dataclasses import asdict, dataclass
from email.parser import BytesParser
import fnmatch
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tomllib
import zipfile


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, document: object) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def relative_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and str(path) == name,
            f'Unsafe archive member: {name}')
    return path


@dataclass(frozen=True)
class SourceFile:
    path: str
    sha256: str


@dataclass(frozen=True)
class SourceManifest:
    schema_version: str
    source_tree: str
    source_commit: str | None
    package_version: str
    files: tuple[SourceFile, ...]
    resources: tuple[str, ...]

    def document(self) -> dict:
        return asdict(self)

    def hashes(self) -> dict[str, str]:
        return {entry.path: entry.sha256 for entry in self.files}


def read_manifest(path: Path, expected_sha256: str) -> SourceManifest:
    require(file_sha256(path) == expected_sha256, 'Source manifest changed')
    document = json.loads(path.read_text())
    require(document['schema_version'] == '1', 'Unsupported source manifest version')
    files = tuple(SourceFile(**entry) for entry in document['files'])
    require(len({entry.path for entry in files}) == len(files), 'Duplicate manifest paths')
    for entry in files:
        relative_member(entry.path)
        require(entry.path.startswith('kayakgen/'), 'Manifest path is outside kayakgen')
        require(re.fullmatch('[0-9a-f]{64}', entry.sha256) is not None,
                'Invalid manifest content digest')
    resources = tuple(document['resources'])
    require(set(resources).issubset(entry.path for entry in files),
            'Manifest resources are missing file records')
    return SourceManifest(document['schema_version'], document['source_tree'],
                          document['source_commit'], document['package_version'], files, resources)


def git_bytes(repo: Path, *arguments: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(repo), *arguments])


def source_identity(repo: Path, reference: str) -> tuple[str, str | None]:
    tree = git_bytes(repo, 'rev-parse', '--verify', '--end-of-options', reference + '^{tree}')
    tree = tree.decode().strip()
    commit = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify',
                             '--end-of-options', reference + '^{commit}'],
                            capture_output=True, text=True)
    return tree, commit.stdout.strip() if commit.returncode == 0 else None


def package_blobs(repo: Path, tree: str) -> dict[str, bytes]:
    records = git_bytes(repo, 'ls-tree', '-r', '-z', tree, '--', 'kayakgen').split(b'\0')
    entries = []
    for record in filter(None, records):
        header, name = record.split(b'\t', 1)
        mode, kind, oid = header.decode().split()
        require(kind == 'blob' and mode in {'100644', '100755'},
                'Package source must contain regular files')
        entries.append((name.decode(), oid))
    query = ''.join(oid + '\n' for _, oid in entries).encode()
    content = subprocess.check_output(['git', '-C', str(repo), 'cat-file', '--batch'], input=query)
    blobs = {}
    offset = 0
    for name, oid in entries:
        end = content.index(b'\n', offset)
        actual, kind, size = content[offset:end].decode().split()
        require(actual == oid and kind == 'blob', 'Git source batch identity differs')
        offset = end + 1
        blobs[name] = content[offset:offset + int(size)]
        offset += int(size) + 1
    return blobs


def declared_resources(blobs: dict[str, bytes], package_data: dict) -> set[str]:
    resources = set()
    package_dirs = {str(PurePosixPath(name).parent) for name in blobs
                    if name.endswith('/__init__.py')}
    for package, patterns in package_data.items():
        require(isinstance(patterns, list) and all(isinstance(p, str) for p in patterns),
                'Invalid setuptools package-data declaration')
        directories = package_dirs if package == '*' else {package.replace('.', '/')}
        for directory in directories:
            prefix = directory + '/'
            for name in blobs:
                if name.startswith(prefix) and any(
                    fnmatch.fnmatchcase(name[len(prefix):], pattern) for pattern in patterns
                ):
                    resources.add(name)
    return resources


def source_manifest(repo: Path, reference: str) -> SourceManifest:
    tree, commit = source_identity(repo, reference)
    configuration = tomllib.loads(git_bytes(repo, 'show', tree + ':pyproject.toml').decode())
    require(configuration['project']['name'] == 'kayakgen', 'Source project must be kayakgen')
    blobs = package_blobs(repo, tree)
    package_data = configuration.get('tool', {}).get('setuptools', {}).get('package-data', {})
    resources = declared_resources(blobs, package_data)
    required = resources | {name for name in blobs if name.endswith('.py')}
    require('kayakgen/__init__.py' in required, 'Source package is missing __init__.py')
    files = tuple(SourceFile(name, hashlib.sha256(blobs[name]).hexdigest())
                  for name in sorted(required))
    return SourceManifest('1', tree, commit, configuration['project']['version'],
                          files, tuple(sorted(resources)))


def export_source(repo: Path, tree: str, target: Path) -> None:
    require(not target.exists(), 'Source export already exists')
    target.mkdir()
    archive = git_bytes(repo, 'archive', tree)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for entry in stream:
            name = entry.name.rstrip('/')
            path = relative_member(name)
            if path.parts[0] == 'build' or any(p.endswith('.egg-info') for p in path.parts):
                continue  # Tracked historical build outputs must not seed a new wheel.
            destination = target.joinpath(*path.parts)
            if entry.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                require(entry.isfile(), 'Source export contains unsupported non-regular entry')
                destination.parent.mkdir(parents=True, exist_ok=True)
                member = stream.extractfile(entry)
                require(member is not None, 'Source archive member is unreadable')
                destination.write_bytes(member.read())
                destination.chmod(entry.mode & 0o777)


@dataclass(frozen=True)
class WheelContents:
    files: tuple[tuple[str, bytes], ...]
    dist_info: str
    version: str

    def members(self) -> dict[str, bytes]:
        return dict(self.files)


def read_wheel(path: Path) -> WheelContents:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Wheel contains duplicate archive members')
        members = {name: archive.read(name) for name in names if not name.endswith('/')}
    for name in members:
        relative_member(name)
    metadata = [name for name in members if name.endswith('.dist-info/METADATA')]
    require(len(metadata) == 1, 'Wheel must have exactly one METADATA file')
    info = BytesParser().parsebytes(members[metadata[0]])
    require((info['Name'] or '').lower() == 'kayakgen', 'Wheel project must be kayakgen')
    dist_info = metadata[0].rsplit('/', 1)[0]
    require(all(name.startswith(('kayakgen/', dist_info + '/')) for name in members),
            'Wheel contains unsupported installation paths')
    verify_record(members, dist_info)
    return WheelContents(tuple(sorted(members.items())), dist_info, info['Version'])


def verify_record(members: dict[str, bytes], dist_info: str) -> None:
    own_record = dist_info + '/RECORD'
    require(own_record in members, 'Wheel is missing RECORD')
    rows = list(csv.reader(io.StringIO(members[own_record].decode())))
    require(all(len(row) == 3 for row in rows), 'Wheel RECORD rows must have three fields')
    require(len(rows) == len({row[0] for row in rows}), 'Wheel RECORD repeats members')
    require({row[0] for row in rows} == set(members), 'Wheel RECORD member set differs')
    for name, encoded, size in rows:
        if name == own_record:
            require(encoded == size == '', 'Wheel RECORD self-hash must be empty')
            continue
        require(encoded.startswith('sha256='), 'Wheel RECORD lacks required SHA256')
        digest = base64.urlsafe_b64encode(hashlib.sha256(members[name]).digest()).rstrip(b'=')
        require(encoded == 'sha256=' + digest.decode() and size == str(len(members[name])),
                'Wheel RECORD content differs: ' + name)


def verify_wheel(path: Path, manifest: SourceManifest) -> WheelContents:
    wheel = read_wheel(path)
    require(wheel.version == manifest.package_version, 'Wheel version differs from source')
    package = {name: content for name, content in wheel.files if name.startswith('kayakgen/')}
    expected = manifest.hashes()
    missing, extra = set(expected) - set(package), set(package) - set(expected)
    require(not missing, 'Wheel missing declared runtime files: ' + ', '.join(sorted(missing)))
    require(not extra, 'Wheel contains unexpected runtime files: ' + ', '.join(sorted(extra)))
    for name, content in package.items():
        require(hashlib.sha256(content).hexdigest() == expected[name],
                'Wheel content differs from source: ' + name)
    return wheel
