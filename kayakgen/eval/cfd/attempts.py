"""Local attempt admission and immutable input snapshots."""
from __future__ import annotations

import fcntl
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict

from kayakgen.eval.cfd.records import CfdDispatchError, CfdJobSpec, SolverProfile
from kayakgen.eval.mesh_package import MeshPackageManifest


class CfdRequestInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mesh_manifest: MeshPackageManifest
    mesh_files: dict[str, str]
    profile: SolverProfile
    hull_ref: str | None
    speed_mps: float
    seawater_density_kg_m3: float
    kinematic_viscosity_m2_s: float

    def fingerprint(self) -> str:
        encoded = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()


class CfdPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    request_id: str
    attempt_id: str
    inputs: CfdRequestInputs
    job_spec: CfdJobSpec


def mesh_file_hashes(mesh_dir: Path, manifest: MeshPackageManifest) -> dict[str, str]:
    refs = {
        manifest.hull_json, *manifest.quality_reports.values(), *manifest.surfaces.values(),
        *manifest.volume_mesh_artifacts.values(),
    }
    refs.update(ref for ref in (
        manifest.closed_volume_diagnostic,
        manifest.self_intersection_diagnostic, manifest.volume_mesh_diagnostic,
    ) if ref is not None)
    hashes = {}
    root = mesh_dir.resolve()
    for ref in sorted(refs):
        target = (root / ref).resolve()
        if not target.is_relative_to(root):
            raise CfdDispatchError("mesh input escapes package", code="invalid_mesh_ref")
        files = sorted(target.rglob("*")) if target.is_dir() else [target]
        for path in files:
            if path.is_file():
                hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            elif not path.exists():
                raise CfdDispatchError(f"mesh input is missing: {path}", code="missing_artifact")
    return hashes


@contextmanager
def exclusive_request(job_dir: Path) -> Iterator[None]:
    """The same advisory lock covers preparation and every attempt's run."""
    request_name = job_dir.name.split("-attempt-", 1)[0]
    lock_path = job_dir.parent / f".{request_name}.lock"
    job_dir.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CfdDispatchError("CFD request has an active writer", code="cfd_job_busy") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
