"""Tests for the artifact store + identity layer (RFC 0049)."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import warnings
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kayakgen.cli.main import app
from kayakgen.model.hull import Hull
from kayakgen.search.sweep import SweepSpec, run_sweep
from kayakgen.services.artifact_store import (
    ArtifactIntegrityError,
    ArtifactRef,
    FilesystemArtifactStore,
    SqliteIndex,
    _default_index_path,
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


# ---------------------------------------------------------------------------
# Workflow 0062 / audit R3: index-DB isolation regression


USER_LEVEL_INDEX_DB = Path.home() / ".local" / "share" / "kayakgen" / "index.sqlite"


def test_index_db_isolated_from_user_level_path(
    tmp_path_factory: pytest.TempPathFactory,
    _isolate_kayakgen_index_db_session: Path,
) -> None:
    """Audit R3: no test may write ``~/.local/share/kayakgen/index.sqlite``.

    This test requests no per-test isolation fixture of its own, so the env
    var being set here proves the autouse ``_isolate_kayakgen_index_db``
    fixture in ``tests/conftest.py`` is active for every test. Before
    remediation, sweep/search/CFD runner tests constructed ``SqliteIndex()``
    with the default path and filled the operator's production
    ``kayakgen runs`` read-model with pytest tmp-path phantoms (129/129 rows
    at audit time).
    """

    env = os.environ.get("KAYAKGEN_INDEX_DB")
    assert env, "autouse KAYAKGEN_INDEX_DB isolation fixture is not active"

    resolved = _default_index_path()
    assert resolved == Path(env).expanduser()
    assert resolved != USER_LEVEL_INDEX_DB

    # The isolated path lives inside pytest's tmp tree for this session.
    basetemp = tmp_path_factory.getbasetemp().resolve()
    assert basetemp in resolved.resolve().parents

    # A default-constructed index lands on the isolated path, never the
    # user-level location.
    assert SqliteIndex().path == resolved

    # Session floor (workflow 0062 leak fix): job code that resolves the env
    # var after a test's monkeypatch undo — e.g. an unjoined forked search
    # job finishing on a background thread — must still land in pytest's tmp
    # tree, because the session-scoped fixture pins the restored value.
    session_db = _isolate_kayakgen_index_db_session
    assert session_db != USER_LEVEL_INDEX_DB
    assert basetemp in session_db.resolve().parents
    assert session_db != Path(env).expanduser()


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
# Workflow 0063 / audit R5 (BUG-041): corrupt content addresses are repaired


def test_corrupt_store_file_repaired_on_next_put(
    tmp_path: Path, isolated_index: Path
) -> None:
    """A crash mid-write must not permanently poison a content address.

    Pre-stage truncated bytes at the exact hash path (simulated torn
    write), then put the full payload: the store must detect the
    corruption (length screen, rehash to confirm) and atomically repair
    the store file instead of hard-linking the truncated bytes into the
    canonical layout. Before remediation the ``exists()`` dedupe branch
    linked the corrupt bytes forever.
    """

    payload = {"hello": "world", "rows": list(range(32))}
    full_bytes = json.dumps(payload, indent=2).encode("utf-8")
    artifact_hash = hashlib.sha256(full_bytes).hexdigest()

    run_dir = tmp_path / "run-corrupt"
    store = FilesystemArtifactStore(run_dir, run_id="repair")
    store_path = run_dir / "_store" / f"{artifact_hash}.json"
    store_path.write_bytes(full_bytes[: len(full_bytes) // 2])

    canonical = run_dir / "run.json"
    with pytest.warns(UserWarning, match="repairing"):
        ref = store.put_json("sweep_run_record", payload, canonical_path=canonical)

    assert ref.artifact_hash == artifact_hash
    # the content address holds intact bytes again
    assert store_path.read_bytes() == full_bytes
    # ... and the canonical path received them (not the truncated ones)
    assert canonical.read_bytes() == full_bytes
    if os.name != "nt":
        assert canonical.stat().st_ino == store_path.stat().st_ino
    # no temp sibling left behind, and nothing torn matches the hash glob
    assert list(store_path.parent.glob(".*")) == []


def test_intact_store_file_left_alone_on_dedupe(
    tmp_path: Path, isolated_index: Path
) -> None:
    """The dedupe branch must not rewrite (or warn about) an intact file."""

    run_dir = tmp_path / "run-dedupe"
    store = FilesystemArtifactStore(run_dir, run_id="dedupe")
    ref = store.put_json(
        "sweep_run_record", {"k": 1}, canonical_path=run_dir / "a.json"
    )
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    ino_before = store_path.stat().st_ino
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        again = store.put_json(
            "sweep_run_record", {"k": 1}, canonical_path=run_dir / "b.json"
        )
    assert again.artifact_hash == ref.artifact_hash
    # same inode: the intact occupant was reused, not replaced
    assert store_path.stat().st_ino == ino_before


# ---------------------------------------------------------------------------
# Workflow 0066 / audit G2: reads are SERVE-ONLY-VERIFIED (D050)


def _replace_store_bytes(store_path: Path, data: bytes) -> None:
    """Corrupt a content address without touching its hard-linked canonical.

    ``unlink`` + fresh write breaks the link first, so the canonical path
    keeps the original (intact) inode — the realistic "store mirror rots,
    canonical survives" scenario. In-place writes would corrupt both ends
    through the shared inode and could never exercise the repair rescue.
    """

    store_path.unlink()
    store_path.write_bytes(data)


def test_corrupt_store_read_raises_without_canonical(
    tmp_path: Path, isolated_index: Path
) -> None:
    """Audit G2: a corrupted content address must refuse, not serve.

    Before SERVE-ONLY-VERIFIED, ``_resolve_artifact`` globbed
    ``_store/<hash>.*`` and returned the bytes unverified — corruption
    after write was served silently, forever."""

    run_dir = tmp_path / "run-read-corrupt"
    store = FilesystemArtifactStore(run_dir, run_id="read-corrupt")
    ref = store.put_json("sweep_run_record", {"k": 1})
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    _replace_store_bytes(store_path, b'{"k": "tampered"}')

    with pytest.raises(ArtifactIntegrityError) as excinfo:
        store.get_json(ref)
    # structured: the error names the path and both hashes
    assert excinfo.value.path == store_path
    assert excinfo.value.expected_hash == ref.artifact_hash
    assert excinfo.value.actual_hash != ref.artifact_hash


def test_corrupt_store_read_repaired_from_intact_canonical(
    tmp_path: Path, isolated_index: Path
) -> None:
    """Audit G2: corrupt store bytes + intact independent canonical -> repair."""

    payload = {"hello": "world"}
    run_dir = tmp_path / "run-read-repair"
    store = FilesystemArtifactStore(run_dir, run_id="read-repair")
    canonical = run_dir / "run.json"
    ref = store.put_json("sweep_run_record", payload, canonical_path=canonical)
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    intact = canonical.read_bytes()
    _replace_store_bytes(store_path, intact[: len(intact) // 2])

    with pytest.warns(UserWarning, match="repairing from canonical"):
        recovered = store.get_json(ref)
    assert recovered == payload
    # the content address holds verified bytes again, atomically replaced
    assert store_path.read_bytes() == intact
    # no temp sibling left behind
    assert list(store_path.parent.glob(".*")) == []


def test_corrupt_store_and_canonical_read_raises(
    tmp_path: Path, isolated_index: Path
) -> None:
    """Audit G2: when both copies are corrupt there is no verified source."""

    run_dir = tmp_path / "run-read-both"
    store = FilesystemArtifactStore(run_dir, run_id="read-both")
    canonical = run_dir / "run.json"
    ref = store.put_json("sweep_run_record", {"k": 2}, canonical_path=canonical)
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    _replace_store_bytes(store_path, b"store-rot")
    canonical.unlink()
    canonical.write_bytes(b"canonical-rot")

    with pytest.raises(ArtifactIntegrityError) as excinfo:
        store.get_json(ref)
    assert excinfo.value.expected_hash == ref.artifact_hash


def test_equal_length_bit_rot_caught_by_read_rehash(
    tmp_path: Path, isolated_index: Path
) -> None:
    """Audit §6 sibling: same byte count, different bytes.

    The write-side repair's cheap screen is byte length, so equal-length
    rot sails past it on the put path; the read-side rehash is the layer
    that must catch it. ``get_file`` is exercised here so both public
    read paths (`get_json` above) are pinned."""

    run_dir = tmp_path / "run-bit-rot"
    store = FilesystemArtifactStore(run_dir, run_id="bit-rot")
    ref = store.put_json("sweep_run_record", {"k": 3})
    store_path = run_dir / "_store" / f"{ref.artifact_hash}.json"
    intact = store_path.read_bytes()
    rotted = bytearray(intact)
    rotted[len(rotted) // 2] ^= 0xFF  # flip one bit mid-payload
    assert len(rotted) == len(intact)
    _replace_store_bytes(store_path, bytes(rotted))

    with pytest.raises(ArtifactIntegrityError) as excinfo:
        store.get_file(ref)
    assert excinfo.value.actual_hash != ref.artifact_hash


# ---------------------------------------------------------------------------
# Workflow 0063 / audit R6: SqliteIndex schema versioning (rebuild-not-migrate)


def test_stale_schema_version_db_rebuilt_not_crashed(
    tmp_path: Path, isolated_index: Path
) -> None:
    """Audit R6: a pre-versioning DB (user_version 0) missing a column must
    trigger a rebuild on the next upsert — the index is a rebuildable
    read-model — instead of ``OperationalError`` mid-sweep. ``kayakgen runs
    list`` works against the rebuilt DB."""

    # Stage a stale schema at the env-resolved index path: runs table
    # missing the out_dir column, as the schema looked before RFC 0049 grew.
    conn = sqlite3.connect(isolated_index)
    conn.execute(
        "CREATE TABLE runs (run_id TEXT PRIMARY KEY, kind TEXT, "
        "spec_hash TEXT, run_hash TEXT, created_at INTEGER)"
    )
    conn.execute("INSERT INTO runs VALUES ('stale', 'sweep', 's', 'r', 1)")
    conn.commit()
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
    conn.close()

    db = SqliteIndex()  # resolves KAYAKGEN_INDEX_DB -> the stale DB
    with pytest.warns(UserWarning, match="rebuilding"):
        db.upsert_run(
            run_id="new",
            kind="sweep",
            spec_hash="sh",
            run_hash="rh",
            out_dir=str(tmp_path),
        )

    # Rebuilt: stale phantom dropped, new row present, stamp current.
    assert [r["run_id"] for r in db.list_runs()] == ["new"]
    conn = sqlite3.connect(isolated_index)
    assert (
        conn.execute("PRAGMA user_version").fetchone()[0]
        == SqliteIndex.SCHEMA_VERSION
    )
    conn.close()

    result = CliRunner().invoke(app, ["runs", "list"])
    assert result.exit_code == 0


def test_current_schema_version_db_preserved_on_reopen(
    tmp_path: Path, isolated_index: Path
) -> None:
    """Normal reuse must NOT rebuild: reopening a current-version DB keeps
    its rows and emits no rebuild warning (no data loss outside a genuine
    schema bump)."""

    first = SqliteIndex(isolated_index)
    first.upsert_run(
        run_id="keep",
        kind="sweep",
        spec_hash="sh",
        run_hash="rh",
        out_dir=str(tmp_path),
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        reopened = SqliteIndex(isolated_index)
        rows = reopened.list_runs()
    assert [r["run_id"] for r in rows] == ["keep"]


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
