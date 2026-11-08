"""Concurrent index openers must not treat a fresh schema as stale history."""

import multiprocessing
import sqlite3
from pathlib import Path

from kayakgen.services.artifact_store import SqliteIndex


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
