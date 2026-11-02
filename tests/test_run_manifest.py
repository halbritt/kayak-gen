"""Durable expected hashes and identity survive loss of the SQLite projection."""

from pathlib import Path

import pytest

from kayakgen.services.artifact_store import (
    ArtifactIntegrityError,
    FilesystemArtifactStore,
    SqliteIndex,
)


def test_manifest_preserves_identity_and_refuses_corruption_without_index(tmp_path: Path) -> None:
    db_path = tmp_path / "index.sqlite"
    run_dir = tmp_path / "run"
    store = FilesystemArtifactStore.open_run(
        run_dir,
        kind="sweep",
        spec_hash="spec",
        run_hash_value="versioned",
        index=SqliteIndex(db_path),
    )
    ref = store.put_json(
        "sweep_run_record", {"name": "original"}, canonical_path=run_dir / "run.json"
    )
    identity = store.manifest.model_dump(exclude={"artifacts"})
    db_path.unlink()
    reopened = FilesystemArtifactStore(run_dir, index=SqliteIndex(db_path))
    assert reopened.run_id == store.run_id
    assert reopened.manifest.model_dump(exclude={"artifacts"}) == identity
    assert reopened.ref_for_relative_path("run.json") == ref
    assert reopened.get_json(ref) == {"name": "original"}
    (run_dir / "run.json").write_text('{"name":"forged"}')
    with pytest.raises(ArtifactIntegrityError):
        reopened.get_json_by_relative_path("run.json")


@pytest.mark.parametrize("filters", [{"kind": "candidate_record"}, {"candidate_key": "wrong"}])
def test_known_manifest_path_never_downgrades_on_filter_mismatch(tmp_path: Path, filters) -> None:
    store = FilesystemArtifactStore.open_run(
        tmp_path / "run", kind="sweep", spec_hash="s", run_hash_value="h"
    )
    store.put_json(
        "sweep_run_record", {"name": "original"}, canonical_path=store.run_dir / "run.json"
    )
    with pytest.raises(ValueError, match="metadata mismatch"):
        store.get_json_by_relative_path("run.json", **filters)


def test_adopting_legacy_run_preserves_known_hashes_and_reports_unknown(tmp_path: Path) -> None:
    db = SqliteIndex(tmp_path / "db.sqlite")
    run_dir = tmp_path / "legacy"
    legacy = FilesystemArtifactStore(run_dir, run_id="legacy-id", index=db)
    db.upsert_run(
        run_id="legacy-id",
        kind="sweep",
        spec_hash="s",
        run_hash="old-version",
        out_dir=str(run_dir),
        created_at=7,
    )
    known = legacy.put_json(
        "sweep_run_record", {"name": "original"}, canonical_path=run_dir / "run.json"
    )
    (run_dir / "run.json").write_text('{"name":"forged"}')
    (run_dir / "unknown.json").write_text('{"unknown":true}')
    adopted = FilesystemArtifactStore.open_run(
        run_dir, kind="sweep", spec_hash="s", run_hash_value="old-version", index=db
    )
    assert adopted.run_id == "legacy-id"
    assert adopted.manifest.created_at == 7
    assert not adopted.manifest.provenance_complete
    assert adopted.ref_for_relative_path("run.json") == known
    assert adopted.ref_for_relative_path("unknown.json") is None
    with pytest.raises(ArtifactIntegrityError):
        adopted.get_json_by_relative_path("run.json")


@pytest.mark.parametrize(
    "old_location", ["absent", "same_instance", "no_manifest", "different_instance"]
)
def test_relocation_requires_unambiguous_previous_location(
    tmp_path: Path, old_location: str
) -> None:
    import shutil

    original = tmp_path / "original"
    moved = tmp_path / "moved"
    store = FilesystemArtifactStore.open_run(
        original, kind="sweep", spec_hash="s", run_hash_value="h"
    )
    store.put_json("sweep_run_record", {"name": "n"}, canonical_path=original / "run.json")
    shutil.copytree(original, moved)
    if old_location == "absent":
        shutil.rmtree(original)
    elif old_location == "no_manifest":
        (original / "_store" / "manifest.json").unlink()
    elif old_location == "different_instance":
        shutil.rmtree(original)
        FilesystemArtifactStore.open_run(
            original, kind="sweep", spec_hash="other", run_hash_value="other"
        )
    if old_location in {"same_instance", "no_manifest"}:
        with pytest.raises(ValueError, match="location"):
            FilesystemArtifactStore.open_run(moved, kind="sweep", spec_hash="s", run_hash_value="h")
    else:
        reopened = FilesystemArtifactStore.open_run(
            moved, kind="sweep", spec_hash="s", run_hash_value="h"
        )
        assert reopened.run_id == store.run_id
        assert reopened.get_json_by_relative_path("run.json") == {"name": "n"}
        assert reopened.manifest.location == str(moved.resolve())


def test_unknown_legacy_identity_stays_incomplete_across_reopen(tmp_path: Path) -> None:
    run_dir = tmp_path / "legacy"
    run_dir.mkdir()
    (run_dir / "run.json").write_text('{"name":"legacy"}')
    first = FilesystemArtifactStore.open_run(
        run_dir, kind="sweep", spec_hash="s", run_hash_value="today"
    )
    second = FilesystemArtifactStore.open_run(
        run_dir, kind="sweep", spec_hash="s", run_hash_value="tomorrow"
    )
    assert second.run_id == first.run_id
    assert second.manifest.run_hash is None
    assert not second.manifest.provenance_complete
    assert second.ref_for_relative_path("run.json") is None


def test_foreign_run_override_is_refused_before_artifact_changes(tmp_path: Path) -> None:
    store = FilesystemArtifactStore.open_run(
        tmp_path / "run", kind="sweep", spec_hash="s", run_hash_value="h"
    )
    target = store.run_dir / "run.json"
    ref = store.put_json("sweep_run_record", {"old": True}, canonical_path=target)
    with pytest.raises(ValueError, match="run_id conflicts"):
        store.put_json("sweep_run_record", {"new": True}, canonical_path=target, run_id="foreign")
    assert store.get_json(ref) == {"old": True}
    assert store.get_json_by_relative_path("run.json") == {"old": True}


def test_failed_manifest_publication_keeps_previous_trusted_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    import os

    store = FilesystemArtifactStore.open_run(
        tmp_path / "run", kind="sweep", spec_hash="s", run_hash_value="h"
    )
    target = store.run_dir / "run.json"
    previous = store.put_json("sweep_run_record", {"old": True}, canonical_path=target)
    replace = os.replace
    with monkeypatch.context() as patch:

        def fail_manifest(source, destination):
            if Path(destination).name == "manifest.json":
                raise OSError("manifest publication failed")
            return replace(source, destination)

        patch.setattr(os, "replace", fail_manifest)
        with pytest.raises(OSError, match="manifest publication failed"):
            store.put_json("sweep_run_record", {"new": True}, canonical_path=target)
    reopened = FilesystemArtifactStore(store.run_dir)
    assert reopened.ref_for_relative_path("run.json") == previous
    assert reopened.get_json_by_relative_path("run.json") == {"old": True}
    reopened.put_json("sweep_run_record", {"new": True}, canonical_path=target)
    assert reopened.get_json_by_relative_path("run.json") == {"new": True}


def test_reindex_restores_exact_identity_and_bindings_after_projection_loss(tmp_path: Path) -> None:
    from kayakgen.services.artifact_store import reindex_run

    db_path = tmp_path / "db.sqlite"
    store = FilesystemArtifactStore.open_run(
        tmp_path / "run",
        kind="sweep",
        spec_hash="s",
        run_hash_value="versioned",
        index=SqliteIndex(db_path),
    )
    ref = store.put_json(
        "sweep_run_record", {"candidates": []}, canonical_path=store.run_dir / "run.json"
    )
    before = store.index.list_runs()
    db_path.unlink()
    first = reindex_run(store.run_dir, index=SqliteIndex(db_path))
    second = reindex_run(store.run_dir, index=SqliteIndex(db_path))
    assert first == second
    assert first.provenance_complete
    assert SqliteIndex(db_path).list_runs() == before
    assert (
        SqliteIndex(db_path).artifact_ref_for_relative_path(
            run_dir=store.run_dir, relative_path="run.json"
        )
        == ref
    )


def test_projection_failure_recovers_from_manifest_and_reindex_is_transactional(
    tmp_path: Path,
) -> None:
    import sqlite3
    from kayakgen.services.artifact_store import reindex_run

    db_path = tmp_path / "db.sqlite"
    store = FilesystemArtifactStore.open_run(
        tmp_path / "run",
        kind="sweep",
        spec_hash="s",
        run_hash_value="h",
        index=SqliteIndex(db_path),
    )
    before = store.index.list_runs()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TRIGGER refuse_binding BEFORE INSERT ON artifact_occurrences BEGIN SELECT RAISE(ABORT, 'projection failed'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="projection failed"):
        store.put_json(
            "sweep_run_record", {"candidates": []}, canonical_path=store.run_dir / "run.json"
        )
    reopened = FilesystemArtifactStore(store.run_dir, index=SqliteIndex(db_path))
    assert reopened.get_json_by_relative_path("run.json") == {"candidates": []}
    with pytest.raises(sqlite3.IntegrityError, match="projection failed"):
        reindex_run(store.run_dir, index=SqliteIndex(db_path))
    assert store.index.list_runs() == before
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TRIGGER refuse_binding")
    recovered = reindex_run(store.run_dir, index=SqliteIndex(db_path))
    assert recovered.artifact_count == 1
    assert (
        store.index.artifact_ref_for_relative_path(run_dir=store.run_dir, relative_path="run.json")
        is not None
    )


def _produce_run(kind: str, root: Path) -> Path:
    if kind == "sweep":
        from kayakgen.search.sweep import SweepSpec, run_sweep

        spec = SweepSpec(
            name="recovery",
            base_hull={"beam_oa_m": 0.6},
            variables={"beam_wl_m": {"kind": "values", "values": [0.5, 0.55]}},
        )
        run_sweep(spec, root / "run")
        return root / "run"
    if kind == "search":
        from kayakgen.search.active.runner import run_search
        from kayakgen.search.active.spec import SearchSpec

        spec = SearchSpec.model_validate(
            {
                "name": "recovery",
                "base_hull": {"beam_oa_m": 0.6},
                "search_space": {"beam_wl_m": {"kind": "uniform", "min": 0.45, "max": 0.55}},
                "algorithm": {"kind": "nsga2", "population_size": 4, "generations": 1, "seed": 9},
                "budget": {"max_evaluations": 4},
            }
        )
        root.mkdir(parents=True, exist_ok=True)
        source = root / "input.json"
        source.write_text(spec.model_dump_json())
        result = run_search(source, root / "run")
        assert result.final_frontier_keys
        return root / "run"
    from kayakgen.eval.cfd.job_store import prepare_local_job
    from kayakgen.eval.cfd.profiles import unavailable_open_surface_profile
    from kayakgen.eval.mesh_package import write_mesh_package
    from kayakgen.model.hull import Hull

    write_mesh_package(Hull(), root / "mesh", stations=8)
    job = prepare_local_job(
        root / "mesh", root / "jobs", unavailable_open_surface_profile(), speed_mps=2.4
    )
    return job.job_dir


@pytest.mark.parametrize("kind", ["sweep", "search", "cfd"])
def test_actual_writer_recovery_preserves_metadata_metrics_and_occurrences(
    tmp_path: Path, kind: str
) -> None:
    from typer.testing import CliRunner
    from kayakgen.cli.main import app

    run_dir = _produce_run(kind, tmp_path)
    store = FilesystemArtifactStore(run_dir)
    before = store.index.list_runs()
    candidates = store.index.candidates_for_run(store.run_id)
    refs = store.index.artifact_refs_for_run(store.run_id)
    assert store.manifest.provenance_complete
    store.index.path.unlink()
    cli = CliRunner()
    for _ in range(2):
        outcome = cli.invoke(app, ["runs", "reindex", str(run_dir)])
        assert outcome.exit_code == 0, outcome.output
        assert "provenance=complete" in outcome.stdout
        db = SqliteIndex()
        assert db.list_runs() == before
        assert db.candidates_for_run(store.run_id) == candidates
        assert db.artifact_refs_for_run(store.run_id) == refs


@pytest.mark.parametrize("mutation", ["corrupt_bytes", "malformed_manifest", "missing_binding", "wrong_kind"])
def test_modern_reindex_and_comparison_refuse_provenance_loss(
    tmp_path: Path, mutation: str
) -> None:
    import json
    from typer.testing import CliRunner
    from kayakgen.cli.main import app
    from kayakgen.search.compare import build_comparison_report

    run_dir = _produce_run("sweep", tmp_path)
    manifest_path = run_dir / "_store" / "manifest.json"
    if mutation == "corrupt_bytes":
        (run_dir / "run.json").write_text('{"name":"forged"}')
    elif mutation == "malformed_manifest":
        manifest_path.write_text("{")
    else:
        payload = json.loads(manifest_path.read_bytes())
        if mutation == "wrong_kind":
            payload["artifacts"]["run.json"]["kind"] = "candidate_record"
        else:
            del payload["artifacts"]["run.json"]
        manifest_path.write_text(json.dumps(payload))
    SqliteIndex().path.unlink()
    with pytest.raises((ValueError, ArtifactIntegrityError)):
        build_comparison_report(run_dir)
    outcome = CliRunner().invoke(app, ["runs", "reindex", str(run_dir)])
    assert outcome.exit_code == 1


def test_unknown_legacy_cli_import_is_explicit_and_idempotent(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from kayakgen.cli.main import app

    run_dir = tmp_path / "legacy"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(
        '{"name":"legacy", "spec_hash":"known-spec", "candidates":[]}'
    )
    cli = CliRunner()
    for _ in range(2):
        outcome = cli.invoke(app, ["runs", "reindex", str(run_dir), "--run-id", "legacy-import"])
        assert outcome.exit_code == 0, outcome.output
        assert "incomplete legacy provenance" in outcome.output
        assert "provenance=incomplete" in outcome.stdout
        rows = SqliteIndex().list_runs()
        assert len(rows) == 1
        assert rows[0]["run_id"] == "legacy-import"
        assert rows[0]["run_hash"] is None
    conflict = cli.invoke(app, ["runs", "reindex", str(run_dir), "--run-id", "other"])
    assert conflict.exit_code == 1


def test_manifest_paths_use_physical_run_root_for_absolute_alias(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    store = FilesystemArtifactStore.open_run(
        Path("run"), kind="sweep", spec_hash="s", run_hash_value="h"
    )
    ref = store.put_json(
        "sweep_run_record", {"name": "n"}, canonical_path=tmp_path / "run" / "run.json"
    )
    assert ref.relative_path == "run.json"
    reopened = FilesystemArtifactStore(tmp_path / "run")
    assert reopened.get_json_by_relative_path("run.json") == {"name": "n"}


def test_failed_cfd_manifest_update_keeps_prior_operational_record(
    tmp_path: Path, monkeypatch
) -> None:
    import os
    from kayakgen.eval.cfd.job_store import load_run_record, run_local_job

    run_dir = _produce_run("cfd", tmp_path)
    previous = load_run_record(run_dir / "run.json")
    replace = os.replace
    with monkeypatch.context() as patch:

        def fail_manifest(source, destination):
            if Path(destination).name == "manifest.json":
                raise OSError("manifest publication failed")
            return replace(source, destination)

        patch.setattr(os, "replace", fail_manifest)
        with pytest.raises(OSError, match="manifest publication failed"):
            run_local_job(run_dir)
    assert load_run_record(run_dir / "run.json") == previous


def test_duplicate_basename_runs_remain_distinct_and_resume_keeps_identity(tmp_path: Path) -> None:
    from kayakgen.search.sweep import SweepSpec, run_sweep
    from kayakgen.services.artifact_store import reindex_run

    a = _produce_run("sweep", tmp_path / "a")
    b = _produce_run("sweep", tmp_path / "b")
    first, second = FilesystemArtifactStore(a), FilesystemArtifactStore(b)
    assert first.run_id != second.run_id
    assert first.manifest.run_hash == second.manifest.run_hash
    assert len(first.index.list_runs()) == 2
    spec = SweepSpec.model_validate_json((a / "spec.json").read_bytes())
    run_sweep(spec, a, resume=True)
    assert FilesystemArtifactStore(a).run_id == first.run_id
    candidates = first.index.candidates_for_run(first.run_id)
    reindex_run(a)
    assert first.index.candidates_for_run(first.run_id) == candidates


def test_index_known_copy_collision_does_not_publish_new_location(tmp_path: Path) -> None:
    import shutil
    from kayakgen.services.artifact_store import reindex_run
    original = _produce_run("sweep", tmp_path / "original")
    stale_copy, moved = tmp_path / "stale-copy", tmp_path / "moved"
    shutil.copytree(original, stale_copy)
    shutil.move(original, moved)
    reindex_run(moved)
    manifest_path = stale_copy / "_store" / "manifest.json"
    before = manifest_path.read_bytes()
    rows = SqliteIndex().list_runs()
    with pytest.raises(ValueError, match="location"):
        reindex_run(stale_copy)
    assert manifest_path.read_bytes() == before
    assert SqliteIndex().list_runs() == rows


def test_summary_csv_preserves_crlf_under_windows_text_translation(tmp_path: Path, monkeypatch) -> None:
    write_text = Path.write_text

    def windows_write_text(path, text, encoding=None, errors=None, newline=None):
        return write_text(path, text, encoding=encoding, errors=errors,
                          newline="\r\n" if newline is None else newline)

    monkeypatch.setattr(Path, "write_text", windows_write_text)
    run_dir = _produce_run("sweep", tmp_path)
    summary = (run_dir / "summary.csv").read_bytes()
    assert summary.count(b"\r\n") == 3
    assert b"\r\r\n" not in summary
