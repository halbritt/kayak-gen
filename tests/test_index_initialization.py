"""Concurrent index openers must not treat a fresh schema as stale history."""

import multiprocessing
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from kayakgen.services.artifact_store import (
    SqliteIndex,
    index_candidates,
)


def test_simultaneous_process_initializers_preserve_both_runs(tmp_path: Path) -> None:
    """Force the actual unprotected-version-read race without timing retries.

    A read made outside a transaction captures version zero in both processes.
    The second reader then waits for the first commit before acting on that
    stale observation. Transaction-protected reads need no injected delay: the
    database lock prevents that stale observation in the first place.
    """
    context = multiprocessing.get_context("fork")
    start = context.Barrier(2)
    unprotected_reads = context.Barrier(2)
    first_committed = context.Event()
    results = context.Queue()
    path = tmp_path / "shared.sqlite"
    connect = sqlite3.connect

    def initialize(role: int) -> None:
        class RacingConnection(sqlite3.Connection):
            def execute(self, sql, parameters=()):
                if sql == "PRAGMA user_version" and not self.in_transaction:
                    cursor = super().execute(sql, parameters)
                    version = cursor.fetchone()
                    cursor.close()
                    unprotected_reads.wait(timeout=10)
                    if role == 1 and not first_committed.wait(timeout=10):
                        raise TimeoutError("first initializer did not commit")
                    return super().execute("SELECT ?", version)
                return super().execute(sql, parameters)

        sqlite3.connect = lambda *a, **kw: connect(*a, factory=RacingConnection, **kw)
        try:
            start.wait(timeout=10)
            SqliteIndex(path).upsert_run(
                run_id=f"run-{role}", kind="sweep", spec_hash="s", run_hash="r",
                out_dir=str(tmp_path / f"run-{role}"),
            )
            results.put(None)
        except Exception as exc:
            results.put(repr(exc))
        finally:
            if role == 0:
                first_committed.set()

    children = [context.Process(target=initialize, args=(role,)) for role in range(2)]
    try:
        for child in children:
            child.start()
        for child in children:
            child.join(timeout=15)
            assert child.exitcode == 0
        assert [results.get(timeout=5) for _ in children] == [None, None]
        with connect(path) as connection:
            assert connection.execute("PRAGMA user_version").fetchone()[0] == SqliteIndex.SCHEMA_VERSION
            assert connection.execute("SELECT run_id FROM runs ORDER BY run_id").fetchall() == [
                ("run-0",), ("run-1",),
            ]
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)


def test_index_candidates_commits_batch_in_one_transaction(tmp_path: Path) -> None:
    path = tmp_path / "batch.sqlite"
    db = SqliteIndex(path)
    db.upsert_run(run_id="run-a", kind="search", spec_hash="s", run_hash="r", out_dir=str(tmp_path / "run-a"))

    def interrupted_rows():
        yield {
            "candidate_key": "cand-0",
            "status": "complete",
            "hull_design_hash": "d0",
            "hull_record_hash": "r0",
            "metrics": {"GM0_m": 0.05},
        }
        raise RuntimeError("interrupted mid-batch")

    try:
        index_candidates(run_id="run-a", candidate_rows=interrupted_rows(), index=db)
    except RuntimeError:
        pass
    assert db.candidates_for_run("run-a") == []


def test_writer_waits_for_concurrent_lock_within_busy_timeout(tmp_path: Path) -> None:
    path = tmp_path / "locked.sqlite"
    base = SqliteIndex(path)
    assert base.BUSY_TIMEOUT_S >= 30.0
    base.upsert_run(run_id="run-1", kind="search", spec_hash="s", run_hash="r", out_dir=str(tmp_path / "run-1"))

    locked = threading.Event()
    release = threading.Event()

    def hold_lock() -> None:
        holder = sqlite3.connect(path)
        try:
            holder.execute("BEGIN IMMEDIATE")
            locked.set()
            release.wait(timeout=5.0)
            holder.commit()
        finally:
            holder.close()

    thread = threading.Thread(target=hold_lock)
    thread.start()
    try:
        assert locked.wait(timeout=5.0)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            SqliteIndex(path, busy_timeout_s=0.02).upsert_artifact(
                artifact_hash="h-short",
                kind="candidate_record",
                run_id="run-1",
                candidate_key="c0",
                byte_count=2,
                relative_path="candidates/c0.record.json",
            )
        threading.Timer(0.12, release.set).start()
        SqliteIndex(path, busy_timeout_s=1.0).upsert_artifact(
            artifact_hash="h-ok",
            kind="candidate_record",
            run_id="run-1",
            candidate_key="c1",
            byte_count=2,
            relative_path="candidates/c1.record.json",
        )
    finally:
        release.set()
        thread.join(timeout=5.0)

    refs = base.artifact_refs_for_run("run-1")
    assert [r.artifact_hash for r in refs] == ["h-ok"]


def test_concurrent_artifact_stores_and_candidate_batches_do_not_lock(tmp_path: Path) -> None:
    path = tmp_path / "shared.sqlite"
    go_flag = tmp_path / "go.flag"
    worker_code = """
import sys, time
from pathlib import Path
from kayakgen.services.artifact_store import FilesystemArtifactStore, SqliteIndex, index_candidates

tmp_path = Path(sys.argv[1])
role = int(sys.argv[2])
path = tmp_path / "shared.sqlite"
ready = tmp_path / f"ready-{role}"
go_flag = tmp_path / "go.flag"
index = SqliteIndex(path)
ready.write_text("1")
deadline = time.monotonic() + 15.0
while not go_flag.exists():
    if time.monotonic() > deadline:
        raise TimeoutError("start flag timed out")
    time.sleep(0.005)
run_dir = tmp_path / f"search-{role}"
store = FilesystemArtifactStore.open_run(
    run_dir, kind="search", spec_hash=f"spec-{role}", run_hash_value=f"hash-{role}", index=index,
)
rows = []
for i in range(25):
    ck = f"c-{role}-{i:03d}"
    hull_file = run_dir / "candidates" / f"{ck}.hull.json"
    hull_file.parent.mkdir(parents=True, exist_ok=True)
    hull_file.write_text(f'{{"role": {role}, "i": {i}}}')
    store.put_file("hull_json", hull_file, candidate_key=ck)
    store.put_json(
        "candidate_record", {"candidate_key": ck, "i": i},
        candidate_key=ck, canonical_path=run_dir / "candidates" / f"{ck}.record.json",
    )
    rows.append({
        "candidate_key": ck, "status": "complete",
        "hull_design_hash": f"dh-{role}-{i}", "hull_record_hash": f"rh-{role}-{i}",
        "metrics": {f"m{k}": float(i + k) for k in range(12)},
    })
index_candidates(run_id=store.run_id, candidate_rows=rows, index=index)
"""
    children = [
        subprocess.Popen(
            [sys.executable, "-c", worker_code, str(tmp_path), str(role)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for role in range(4)
    ]
    try:
        deadline = time.monotonic() + 15.0
        while not all((tmp_path / f"ready-{role}").exists() for role in range(4)):
            assert time.monotonic() < deadline, "workers did not reach barrier"
            time.sleep(0.01)
        go_flag.write_text("go")
        for child in children:
            out, err = child.communicate(timeout=30)
            assert child.returncode == 0, out + err
        db = SqliteIndex(path)
        runs = db.list_runs()
        assert len(runs) == 4
        for row in runs:
            cands = db.candidates_for_run(row["run_id"])
            assert len(cands) == 25
            assert db.metric_count(row["run_id"]) == 25 * 12
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
