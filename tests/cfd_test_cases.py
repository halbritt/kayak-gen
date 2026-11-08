"""Custom solver fixtures use real preparation instead of editing published inputs."""
from __future__ import annotations

from kayakgen.eval.cfd.job_store import load_profile, prepare_local_job
from kayakgen.eval.cfd.records import CfdJobPaths, LocalCfdJob


def prepare_profile_attempt(job: CfdJobPaths | LocalCfdJob, **updates: object) -> LocalCfdJob:
    spec = job.job if isinstance(job, CfdJobPaths) else job.job_spec
    profile = load_profile(job.job_dir).model_copy(update=updates)
    return prepare_local_job(
        (job.job_dir / spec.mesh_package_ref).resolve(), job.job_dir.parent, profile,
        hull_ref=spec.hull_ref, speed_mps=spec.speed_mps,
        seawater_density_kg_m3=spec.seawater_density_kg_m3,
        kinematic_viscosity_m2_s=spec.kinematic_viscosity_m2_s,
        new_attempt=True,
    )
