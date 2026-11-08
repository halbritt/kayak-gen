"""Real bounded legacy-fixture OpenFOAM smoke; never an owner-hull validation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import sys
import traceback

from kayakgen.operations.release_audit import module_audit
from kayakgen.operations.release_manifest import file_sha256, read_manifest, require, write_json
from kayakgen.operations.release_stage import clean_environment, run_logged, utc_now


def version_command(bashrc: Path) -> list[str]:
    # OpenFOAM's bashrc consumes inherited positional arguments. Capture then shift
    # before sourcing, or the bashrc filename can be recursively sourced as an arg.
    return ['bash', '--noprofile', '--norc', '-c',
            'kayakgen_foam_bashrc="$1"; shift; '
            'source "$kayakgen_foam_bashrc" >/dev/null 2>&1 '
            "&& set -o pipefail && interFoam -help | sed -n '/^Using:/p'",
            'installed-foam-version', str(bashrc)]


def version_preflight(out: Path, bashrc: Path) -> dict:
    from kayakgen.eval.cfd.jobs import OPENFOAM_REQUIRED_VERSION, probe_openfoam_provenance
    from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
        OpenFoamProbeBashrcRunner, probe_commands_for_bashrc_runner)
    command = run_logged(version_command(bashrc), out / 'solver-version.log',
                         timeout_s=30, env=clean_environment())
    banner = (out / 'solver-version.log').read_text()
    require(re.search(r'^Using: OpenFOAM-2512(?:\s|$)', banner, re.MULTILINE) is not None,
            'Actual interFoam help did not produce the required OpenFOAM-2512 banner')
    probe = probe_openfoam_provenance(runner=OpenFoamProbeBashrcRunner(bashrc=bashrc),
                                    commands=probe_commands_for_bashrc_runner())
    accepted, reason = probe.matches_required(OPENFOAM_REQUIRED_VERSION)
    record = {'command': command, 'actual_banner': banner, 'provenance': probe.model_dump(mode='json'),
              'accepted': accepted, 'reason': reason}
    write_json(out / 'solver-preflight.json', record)
    require(accepted, 'Actual typed OpenFOAM provenance refused: ' + str(reason))
    return record


def write_closed_stl(path: Path, hull) -> None:
    import numpy as np
    from stl import Mode, mesh as stl_mesh
    from kayakgen.eval.closed_volume import generated_hull_plus_deck_body
    body = generated_hull_plus_deck_body(hull, stations=8)
    triangles = [np.asarray(part.vertices)[np.asarray(part.faces, dtype=int)] for part in body.parts]
    vectors = np.concatenate(triangles)
    mesh = stl_mesh.Mesh(np.zeros(len(vectors), dtype=stl_mesh.Mesh.dtype))
    mesh.vectors[:] = vectors
    mesh.save(str(path), mode=Mode.BINARY)


def case_spec(stl: Path):
    from kayakgen.eval.cfd.openfoam_v2512_interfoam import OpenFoamCaseSpec, domain_bounds_from_stl
    bounds = domain_bounds_from_stl(stl)
    return OpenFoamCaseSpec(
        hull_stl_path=stl, domain_bounds=bounds, background_cell_size_m=.25,
        hull_refinement_levels=(2, 3), location_in_mesh=(bounds[0] + .5, 0., bounds[5] - .5),
        end_time_s=.05, delta_t_s=.01, inlet_speed_ms=2., max_global_cells=800_000,
        waterline_z_m=0., rho_inf_kg_m3=1000., water_rho_kg_m3=1000., water_nu_m2_s=1.09e-6)


def resource_render(out: Path) -> dict:
    from kayakgen.model.hull import Hull
    from kayakgen.eval.cfd.openfoam_v2512_interfoam import render_case
    out.mkdir()
    stl = out / 'legacy-closed-body.stl'
    write_closed_stl(stl, Hull())
    spec, target = case_spec(stl), out / 'case'
    render_case(spec, target, stage='meshing')
    mesh_control = file_sha256(target / 'system/controlDict')
    render_case(spec, target, stage='solve')
    solve_control = file_sha256(target / 'system/controlDict')
    require(mesh_control != solve_control, 'Resource rendering did not select distinct case stages')
    return {'mesh_control_sha256': mesh_control, 'solve_control_sha256': solve_control,
            'rendered_files': tree_hashes(target)}


def tree_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): file_sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file()}


def execute_pipeline(args, receipt: dict) -> None:
    from kayakgen.eval.cfd.openfoam_v2512_interfoam import (
        render_case, run_meshing_stage, run_solver_stage)
    from kayakgen.eval.cfd.jobs import parse_openfoam_force_dat
    spec = case_spec(args.stl.absolute())
    receipt['case_spec'] = spec.model_dump(mode='json')
    render_case(spec, args.case, stage='meshing')
    mesh = run_meshing_stage(args.case, timeout_s=args.step_timeout, bashrc=args.bashrc)
    receipt['meshing'] = asdict(mesh)
    require(mesh.succeeded and mesh.check_mesh_summary is not None and mesh.check_mesh_summary.passed,
            'Real OpenFOAM meshing failed: ' + str(mesh.failure_reason))
    render_case(spec, args.case, stage='solve')
    solved = run_solver_stage(args.case, timeout_s=args.step_timeout, bashrc=args.bashrc)
    receipt['solver'] = asdict(solved)
    require(solved.succeeded and solved.force_dat_path is not None,
            'Real OpenFOAM solve failed: ' + str(solved.failure_reason))
    forces = parse_openfoam_force_dat(solved.force_dat_path)
    require(forces.sample_count >= 1, 'Real solver produced no force samples')
    receipt.update(force_result=forces.model_dump(mode='json'),
                   force_dat_sha256=file_sha256(solved.force_dat_path))


def pipeline(args) -> int:
    args.case = args.case.absolute()
    args.case.mkdir(parents=True, exist_ok=True)
    receipt = {'started_at': utc_now(), 'status': 'running', 'semantics': 'real OpenFOAM-v2512'}
    try:
        manifest = read_manifest(args.manifest, args.manifest_sha256)
        receipt['modules_before'] = module_audit(manifest)
        execute_pipeline(args, receipt)
        receipt['modules_after'] = module_audit(manifest)
        receipt['status'] = 'passed'
        return 0
    except Exception:
        receipt.update(status='failed', error=traceback.format_exc())
        return 1
    finally:
        receipt['finished_at'] = utc_now()
        # Runner results carry Paths; preserve their actual values in evidence.
        receipt = json.loads(json.dumps(receipt, default=str))
        write_json(args.case / 'installed-pipeline.json', receipt)


def prepare_fixture(out: Path, args):
    from kayakgen.model.hull import Hull
    from kayakgen.eval.mesh_package import write_watertight_volume_mesh_handoff_package
    from kayakgen.eval.cfd.jobs import OPENFOAM_PROFILE_NAME
    from kayakgen.eval.cfd.profiles import solver_profile_by_name
    from kayakgen.eval.cfd.job_store import prepare_local_job
    out.mkdir()
    hull = Hull(name='installed-release-legacy-openfoam-smoke')
    mesh_dir, stl = out / 'mesh', out / 'legacy-closed-body.stl'
    mesh_manifest = write_watertight_volume_mesh_handoff_package(
        hull, mesh_dir, stations=8, closed_body_stations=8, include_fixture_volume_mesh=True)
    write_closed_stl(stl, hull)
    profile = solver_profile_by_name(OPENFOAM_PROFILE_NAME).model_copy(update={
        'name': 'installed-release-openfoam-v2512-smoke', 'allow_real_solver_execution': True,
        'required_solver_version': '2512', 'timeout_seconds': 6 * args.step_timeout + 60,
        'solver_version_command': version_command(args.bashrc),
        'command_template': [sys.executable, '-I', '-B', '-m',
            'kayakgen.operations.release_openfoam', '--case', 'case/openfoam', '--stl', str(stl),
            '--bashrc', str(args.bashrc), '--step-timeout', str(args.step_timeout),
            '--manifest', str(args.manifest), '--manifest-sha256', args.manifest_sha256]})
    job = prepare_local_job(mesh_dir, out / 'jobs', profile, speed_mps=2.,
                            seawater_density_kg_m3=1000., kinematic_viscosity_m2_s=1.09e-6)
    return job, mesh_manifest


def cfd_workflow(out: Path, args) -> dict:
    from kayakgen.eval.cfd.job_store import run_cfd_job, load_cfd_run_record
    job, mesh_manifest = prepare_fixture(out, args)
    profile_sha = file_sha256(job.job_dir / 'profile.json')
    record = run_cfd_job(job.job_dir)
    require(record.status == 'succeeded',
            f'Real installed CFD failed: {record.error_kind}: {record.error_message}; {job.job_dir}')
    require(record.claim_state == 'raw_unvalidated' and record.accepted_uses == [],
            'CFD claim ceiling widened')
    require(record.raw_records.get('claim_state') == 'raw_unvalidated'
            and record.raw_records.get('accepted_uses') == [], 'Raw CFD claim ceiling widened')
    require(record.solver_execution_audit is not None
            and record.real_solver_execution_opt_in == 'profile_flag', 'Real execution audit missing')
    pipeline_path = job.job_dir / 'case/openfoam/installed-pipeline.json'
    require(json.loads(pipeline_path.read_text())['status'] == 'passed', 'Actual pipeline failed')
    require(file_sha256(job.job_dir / 'profile.json') == profile_sha, 'Immutable CFD profile changed')
    before = tree_hashes(job.job_dir)
    require(run_cfd_job(job.job_dir) == load_cfd_run_record(job.job_dir), 'Terminal replay changed result')
    require(before == tree_hashes(job.job_dir), 'Terminal replay rewrote completed artifacts')
    return {'fixture_scope': 'default legacy closed body, 8 stations, fixture volume handoff, real solver',
            'owner_hull_cfd_verified': False, 'mesh_manifest': mesh_manifest.model_dump(mode='json'),
            'profile_sha256': profile_sha, 'job_dir': str(job.job_dir),
            'run': record.model_dump(mode='json'), 'pipeline_sha256': file_sha256(pipeline_path),
            'terminal_replay_unchanged': True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('case', 'stl', 'bashrc', 'manifest'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--step-timeout', type=float, required=True)
    return pipeline(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
