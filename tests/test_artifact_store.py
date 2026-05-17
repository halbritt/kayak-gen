"""Tests for the artifact store + identity layer (RFC 0049)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.model.hull import Hull
from kayakgen.search.sweep import SweepSpec, run_sweep
from kayakgen.services.artifact_store import (
    ArtifactRef,
    FilesystemArtifactStore,
    SqliteIndex,
)
from kayakgen.services.identity import (
    design_hash_for_hull,
    record_hash,
    run_hash,
)


# ---------------------------------------------------------------------------
# Identity invariance


def test_design_hash_invariant_under_rename() -> None:
    a = Hull(name="A")
    b = Hull(name="B")
    assert a.design_hash() == b.design_hash()
    assert a.hash() != b.hash()


def test_design_hash_differs_when_cp_changes() -> None:
    base = Hull()
    perturbed = base.model_copy(update={"Cp": base.Cp + 0.02})
    assert base.design_hash() != perturbed.design_hash()


def test_design_hash_invariant_under_json_key_order() -> None:
    h = Hull()
    payload = {
        "geometry_kind": "lofted",
        "LCB_frac": h.LCB_frac,
        "rocker_stern_m": h.rocker_stern_m,
        "rocker_bow_m": h.rocker_bow_m,
        "stern_rake": h.stern_rake,
        "bow_rake": h.bow_rake,
        "center_box_ratio": h.center_box_ratio,
        "deck_flatness": h.deck_flatness,
        "Cm": h.Cm,
        "Cp": h.Cp,
        "deck_height_m": h.deck_height_m,
        "draft_m": h.draft_m,
        "beam_wl_m": h.beam_wl_m,
        "beam_oa_m": h.beam_oa_m,
        "length_m": h.length_m,
    }
    shuffled = dict(reversed(list(payload.items())))
    assert record_hash(payload) == record_hash(shuffled)


def test_record_hash_differs_when_payload_differs() -> None:
    assert record_hash({"a": 1}) != record_hash({"a": 2})


def test_run_hash_pin_uses_version() -> None:
    spec = {"name": "x"}
    a = run_hash(spec, "0.1.0")
    b = run_hash(spec, "0.1.1")
    assert a != b


# ---------------------------------------------------------------------------
# Backwards compatibility: Hull.hash() byte-stable with record_hash()


@pytest.mark.parametrize(
    "hull",
    [
        Hull(),
        Hull(name="rename-me"),
        Hull(length_m=4.5, beam_oa_m=0.5, beam_wl_m=0.45),
        Hull(bow_rake=0.0, stern_rake=0.0),
        Hull(Cp=0.58, Cm=0.85, deck_flatness=8.0),
    ],
)
def test_hash_equals_record_hash(hull: Hull) -> None:
    assert hull.hash() == hull.record_hash()


def test_design_hash_matches_explicit_helper() -> None:
    h = Hull()
    assert h.design_hash() == design_hash_for_hull(h)


# ---------------------------------------------------------------------------
# Filesystem store round-trip


@pytest.fixture
def isolated_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "index.sqlite"
    monkeypatch.setenv("KAYAKGEN_INDEX_DB", str(db))
    return db


def test_filesystem_store_round_trip(tmp_path: Path, isolated_index: Path) -> None:
    run_dir = tmp_path / "run-a"
    store = FilesystemArtifactStore(run_dir, run_id="round-trip")
    canonical = run_dir / "run.json"
    ref = store.put_json(
        "sweep_run_record",
        {"hello": "world"},
        canonical_path=canonical,
    )
    # canonical path holds the bytes verbatim
    assert json.loads(canonical.read_text()) == {"hello": "world"}
    # _store/ mirror exists
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    assert store_path.exists()
    # hard-link inode equality on non-Windows
    if os.name != "nt":
        assert canonical.stat().st_ino == store_path.stat().st_ino
    # read-back returns the same payload
    assert store.get_json(ref) == {"hello": "world"}


def test_filesystem_store_redrives_when_store_missing(
    tmp_path: Path, isolated_index: Path
) -> None:
    run_dir = tmp_path / "run-b"
    store = FilesystemArtifactStore(run_dir, run_id="redrive")
    canonical = run_dir / "spec.json"
    ref = store.put_json(
        "sweep_run_record",
        {"k": 1},
        canonical_path=canonical,
    )
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    store_path.unlink()
    with pytest.warns(UserWarning):
        recovered = store.get_json(
            ArtifactRef(
                kind=ref.kind,
                artifact_hash=ref.artifact_hash,
                relative_path=ref.relative_path,
            )
        )
    assert recovered == {"k": 1}


# ---------------------------------------------------------------------------
# SQLite index after one run_sweep


def _tiny_spec() -> SweepSpec:
    return SweepSpec(
        name="tiny",
        base_hull={"beam_oa_m": 0.60},
        variables={
            "beam_wl_m": {"kind": "values", "values": [0.50, 0.55]},
            "Cp": {"kind": "values", "values": [0.54]},
        },
    )


def test_sqlite_index_rows_after_run_sweep(
    tmp_path: Path, isolated_index: Path
) -> None:
    out = tmp_path / "sweep-run"
    run = run_sweep(_tiny_spec(), out)
    assert run.completed_count == 2

    conn = sqlite3.connect(isolated_index)
    conn.row_factory = sqlite3.Row
    runs = conn.execute("SELECT * FROM runs").fetchall()
    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    metrics = conn.execute("SELECT * FROM metrics").fetchall()
    conn.close()

    assert len(runs) == 1
    assert runs[0]["kind"] == "sweep"
    assert len(candidates) == run.completed_count
    assert {c["status"] for c in candidates} == {"complete"}
    assert all(c["hull_design_hash"] for c in candidates)
    # every candidate carries the four legacy numeric metrics:
    expected_metric_names = {
        "displaced_mass_kg",
        "wetted_surface_m2",
        "GM0_m",
        "Cp_actual",
    }
    by_candidate: dict[str, set[str]] = {}
    for row in metrics:
        by_candidate.setdefault(row["candidate_key"], set()).add(row["metric_name"])
    for ck, names in by_candidate.items():
        assert expected_metric_names.issubset(names), ck


def test_runs_list_command_deterministic_order(
    tmp_path: Path, isolated_index: Path
) -> None:
    # Two sweep runs in distinct directories, same spec.
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_sweep(_tiny_spec(), first)
    run_sweep(_tiny_spec(), second)

    runner = CliRunner()
    result = runner.invoke(app, ["runs", "list", "--kind", "sweep"])
    assert result.exit_code == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    # Order is created_at ASC, run_id ASC — deterministic across calls.
    second_call = runner.invoke(app, ["runs", "list", "--kind", "sweep"])
    assert second_call.exit_code == 0
    assert [line for line in second_call.stdout.splitlines() if line.strip()] == lines


# ---------------------------------------------------------------------------
# Legacy run directory loads without an index


def test_legacy_run_directory_loads_without_index(
    tmp_path: Path, isolated_index: Path
) -> None:
    out = tmp_path / "legacy"
    run_sweep(_tiny_spec(), out)
    # Strip the _store/ mirror to simulate a legacy run.
    import shutil

    store_dir = out / "_store"
    if store_dir.exists():
        shutil.rmtree(store_dir)
    # Canonical files are still byte-readable.
    payload = json.loads((out / "run.json").read_text())
    assert payload["candidate_count"] == 2
    # Reattaching a store on top should not corrupt anything; it should
    # re-derive entries from canonical paths on read.
    store = FilesystemArtifactStore(out, run_id="legacy")
    ref = store.put_file("sweep_run_record", out / "run.json")
    assert (out / "_store" / f"{ref.artifact_hash}.json").exists()


# ---------------------------------------------------------------------------
# SqliteIndex helper API


def test_sqlite_index_upsert_run_and_query(
    tmp_path: Path, isolated_index: Path
) -> None:
    db = SqliteIndex(isolated_index)
    db.upsert_run(
        run_id="r1",
        kind="sweep",
        spec_hash="sh",
        run_hash="rh",
        out_dir=str(tmp_path),
    )
    db.upsert_candidate(
        run_id="r1",
        candidate_key="ck1",
        status="complete",
        hull_design_hash="dh",
        hull_record_hash="rh",
    )
    db.upsert_metrics(run_id="r1", candidate_key="ck1", metrics={"GM0_m": 0.1})
    rows = db.candidates_for_run("r1", metrics=("GM0_m",))
    assert len(rows) == 1
    assert rows[0].metrics == {"GM0_m": 0.1}
