"""CFD request replay preserves completed attempts and their evidence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from kayakgen.eval.cfd.jobs import (
    CfdDispatchError,
    fixture_local_command_profile,
    prepare_local_job,
    read_local_status,
    run_local_job,
)
from kayakgen.eval.mesh_package import write_mesh_package
from kayakgen.model.hull import Hull


def test_repeated_prepare_preserves_completed_attempt(tmp_path: Path) -> None:
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    first = prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4)
    complete = run_local_job(first.job_dir)
    assert complete.status == "succeeded"
    saved = {p.relative_to(first.job_dir): p.read_bytes() for p in first.job_dir.rglob('*') if p.is_file()}
    repeated = prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4)
    assert repeated.job_dir == first.job_dir
    assert repeated.run_record == complete
    assert all((first.job_dir / p).read_bytes() == b for p, b in saved.items())


def test_changed_profile_cannot_reuse_attempt(tmp_path: Path) -> None:
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    first = prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4)
    before = (first.job_dir / "profile.json").read_bytes()
    changed = profile.model_copy(update={"timeout_seconds": 1.0})
    with pytest.raises(CfdDispatchError, match="conflict"):
        prepare_local_job(mesh, tmp_path / "jobs", changed, speed_mps=2.4)
    assert (first.job_dir / "profile.json").read_bytes() == before


def test_explicit_new_attempt_retains_prior_result(tmp_path: Path) -> None:
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    first = prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4)
    old = run_local_job(first.job_dir)
    old_bytes = (first.job_dir / "run.json").read_bytes()
    second = prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4, new_attempt=True)
    assert second.job_dir != first.job_dir
    assert read_local_status(second.job_dir).status == "queued"
    assert run_local_job(second.job_dir).status == "succeeded"
    assert (first.job_dir / "run.json").read_bytes() == old_bytes
    assert read_local_status(first.job_dir) == old
    a = json.loads((first.job_dir / "preparation.json").read_text())
    b = json.loads((second.job_dir / "preparation.json").read_text())
    assert a['request_id'] == b['request_id']
    assert a['attempt_id'] != b['attempt_id']


def test_changed_mesh_bytes_refuse_reuse_and_execution(tmp_path: Path) -> None:
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    job = prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4)
    (mesh / 'hull.stl').write_bytes(b'changed after preparation')
    with pytest.raises(CfdDispatchError, match="conflict"):
        prepare_local_job(mesh, tmp_path / "jobs", profile, speed_mps=2.4)
    with pytest.raises(CfdDispatchError, match="changed"):
        run_local_job(job.job_dir)
    assert read_local_status(job.job_dir).status == "queued"


def test_terminal_run_replay_does_not_execute_or_rewrite(tmp_path: Path) -> None:
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    job = prepare_local_job(mesh, tmp_path / "jobs", fixture_local_command_profile(), speed_mps=2.4)
    first = run_local_job(job.job_dir)
    before = (job.job_dir / "run.json").read_bytes()
    assert run_local_job(job.job_dir) == first
    assert (job.job_dir / "run.json").read_bytes() == before


def test_partial_preparation_is_retained_but_not_published(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from kayakgen.eval.cfd import job_store
    mesh = tmp_path / "mesh"
    jobs = tmp_path / "jobs"
    write_mesh_package(Hull(), mesh, stations=8)
    original = job_store._write_preparation
    def interrupted(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError("injected before directory publication")
    monkeypatch.setattr(job_store, '_write_preparation', interrupted)
    with pytest.raises(OSError, match="injected"):
        prepare_local_job(mesh, jobs, fixture_local_command_profile(), speed_mps=2.4)
    assert not list(jobs.glob('cfd-*'))
    provisional = list(jobs.glob('.*.preparing-*'))
    assert provisional
    with pytest.raises(CfdDispatchError, match="not published"):
        run_local_job(provisional[0])
    monkeypatch.setattr(job_store, '_write_preparation', original)
    job = prepare_local_job(mesh, jobs, fixture_local_command_profile(), speed_mps=2.4)
    assert read_local_status(job.job_dir).status == 'queued'


def test_concurrent_prepare_has_one_publication(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    def prepare():
        try:
            return prepare_local_job(mesh, tmp_path / 'jobs', fixture_local_command_profile(), speed_mps=2.4)
        except CfdDispatchError as exc:
            assert exc.code == 'cfd_job_busy'
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        prepared = [j for j in pool.map(lambda _: prepare(), range(4)) if j is not None]
    assert prepared
    assert len({j.job_dir for j in prepared}) == 1
    assert len(list((tmp_path / 'jobs').glob('cfd-*'))) == 1


def test_concurrent_run_and_prepare_refuse_active_writer(tmp_path: Path) -> None:
    import sys
    import time
    from concurrent.futures import ThreadPoolExecutor
    mesh = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    command = [sys.executable, '-c',
        "import subprocess,sys,time; from pathlib import Path; Path('started').touch(); time.sleep(.5); sys.exit(subprocess.call(sys.argv[1:]))",
        *profile.command_template]
    profile = profile.model_copy(update={'command_template': command})
    job = prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(run_local_job, job.job_dir)
        deadline = time.monotonic() + 5
        while not (job.job_dir / 'started').exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert (job.job_dir / 'started').exists()
        with pytest.raises(CfdDispatchError) as busy:
            run_local_job(job.job_dir)
        assert busy.value.code == 'cfd_job_busy'
        with pytest.raises(CfdDispatchError) as busy:
            prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
        assert busy.value.code == 'cfd_job_busy'
        assert running.result(timeout=10).status == 'succeeded'


def test_failed_terminal_publication_cannot_be_replayed_as_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from kayakgen.eval.cfd import job_store
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    job = prepare_local_job(mesh, tmp_path / 'jobs', fixture_local_command_profile(), speed_mps=2.4)
    publish = job_store._route_cfd_writes_through_store
    def fail_terminal(job_dir, job_spec, *, files):
        if files == (("cfd_run_record", "run.json"),) and json.loads((job_dir / 'run.json').read_text())['status'] == 'succeeded':
            raise OSError('terminal publication failed')
        return publish(job_dir, job_spec, files=files)
    monkeypatch.setattr(job_store, '_route_cfd_writes_through_store', fail_terminal)
    with pytest.raises(OSError, match='publication failed'):
        run_local_job(job.job_dir)
    assert (job.job_dir / 'raw-result.json').is_file()
    assert read_local_status(job.job_dir).status == 'running'
    with pytest.raises(CfdDispatchError) as incomplete:
        run_local_job(job.job_dir)
    assert incomplete.value.code == 'cfd_attempt_incomplete'


def test_cli_and_web_prepare_expose_new_attempt(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from kayakgen.cli.main import app
    from kayakgen.services.cfd_jobs import CfdWebStore, create_cfd_job_payload, run_cfd_job_payload
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    store = CfdWebStore(tmp_path / 'jobs')
    payload = {'mesh_package_ref': str(mesh), 'solver_profile': 'fixture-local-command', 'speed_mps': 2.4}
    first = create_cfd_job_payload(payload, store)
    first_id = first['job']['job_id']
    run_cfd_job_payload(first_id, store)
    assert create_cfd_job_payload(payload, store)['run']['status'] == 'succeeded'
    second = create_cfd_job_payload(payload | {'new_attempt': True}, store)
    assert second['job']['job_id'] != first_id
    command = CliRunner().invoke(app, ['cfd', 'prepare', '--mesh-package', str(mesh), '--out', str(tmp_path / 'jobs'), '--solver-profile', 'fixture-local-command', '--speed-mps', '2.4', '--new-attempt'])
    assert command.exit_code == 0, command.output
    assert 'status: queued' in command.output
    assert len(list((tmp_path / 'jobs').glob('cfd-*'))) == 3


def test_queued_profile_edit_cannot_bypass_mesh_readiness(tmp_path: Path) -> None:
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    job = prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
    changed = profile.model_copy(update={'required_mesh_readiness': 'cfd_ready'})
    (job.job_dir / 'profile.json').write_text(changed.model_dump_json())
    with pytest.raises(CfdDispatchError, match='profile changed'):
        run_local_job(job.job_dir)
    assert read_local_status(job.job_dir).status == 'queued'


def test_profile_drift_refuses_before_any_process_launch(tmp_path: Path) -> None:
    import sys
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    job = prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
    marker = tmp_path / 'unexpected-execution'
    changed = profile.model_copy(update={'command_template': [sys.executable, '-c', f'from pathlib import Path; Path({str(marker)!r}).touch()']})
    (job.job_dir / 'profile.json').write_text(changed.model_dump_json())
    with pytest.raises(CfdDispatchError) as conflict:
        run_local_job(job.job_dir)
    assert conflict.value.code == 'cfd_request_conflict'
    assert not marker.exists()
    assert not (job.job_dir / 'execution-inputs.json').exists()
    assert read_local_status(job.job_dir).status == 'queued'


def test_custom_profile_supplied_to_prepare_executes_unchanged(tmp_path: Path) -> None:
    import sys
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    command = [sys.executable, '-c', "import subprocess,sys; print('custom profile selected'); sys.exit(subprocess.call(sys.argv[1:]))", *profile.command_template]
    custom = profile.model_copy(update={'command_template': command})
    job = prepare_local_job(mesh, tmp_path / 'jobs', custom, speed_mps=2.4)
    assert run_local_job(job.job_dir).status == 'succeeded'
    preparation = json.loads((job.job_dir / 'preparation.json').read_text())
    execution = json.loads((job.job_dir / 'execution-inputs.json').read_text())
    assert preparation['request_id'] == execution['request_id']
    assert preparation['inputs'] == execution['inputs']
    assert 'custom profile selected' in (job.job_dir / 'logs/stdout.log').read_text()


def test_legacy_records_remain_readable_but_cannot_execute_as_new_preparation(tmp_path: Path) -> None:
    import shutil
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    first = prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
    legacy = tmp_path / 'legacy-jobs' / first.job_dir.name
    legacy.mkdir(parents=True)
    for filename in ['job.json', 'profile.json', 'run.json']:
        shutil.copyfile(first.job_dir / filename, legacy / filename)
    assert read_local_status(legacy).status == 'queued'
    with pytest.raises(CfdDispatchError) as unknown:
        run_local_job(legacy)
    assert unknown.value.code == 'cfd_preparation_unverified'
    with pytest.raises(CfdDispatchError) as unknown:
        prepare_local_job(mesh, legacy.parent, profile, speed_mps=2.4)
    assert unknown.value.code == 'cfd_preparation_unverified'
    explicit = prepare_local_job(mesh, legacy.parent, profile, speed_mps=2.4, new_attempt=True)
    assert explicit.job_dir != legacy
    assert run_local_job(explicit.job_dir).status == 'succeeded'
    assert read_local_status(legacy).status == 'queued'


def test_lost_manifest_cannot_promote_raw_preparation_into_execution(tmp_path: Path) -> None:
    mesh = tmp_path / 'mesh'
    write_mesh_package(Hull(), mesh, stations=8)
    profile = fixture_local_command_profile()
    job = prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
    (job.job_dir / '_store/manifest.json').unlink()
    assert (job.job_dir / 'preparation.json').is_file()
    assert read_local_status(job.job_dir).status == 'queued'
    with pytest.raises(CfdDispatchError) as unknown:
        run_local_job(job.job_dir)
    assert unknown.value.code == 'cfd_preparation_unverified'
    assert not (job.job_dir / 'execution-inputs.json').exists()
    assert not (job.job_dir / 'raw-result.json').exists()
    with pytest.raises(CfdDispatchError) as unknown:
        prepare_local_job(mesh, tmp_path / 'jobs', profile, speed_mps=2.4)
    assert unknown.value.code == 'cfd_preparation_unverified'
