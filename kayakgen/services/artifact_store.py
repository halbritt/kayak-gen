"""Filesystem-backed artifact store + SQLite index (RFC 0049).

The store is content-addressed: every persisted artifact lands in a
``_store/<sha256>.<ext>`` mirror under the run directory, and the
canonical "human" paths (``run.json``, ``candidates/<key>/record.json``,
etc.) are *hard links* into that mirror. On Windows (``os.name == "nt"``)
or on filesystems that refuse hard links (e.g. cross-device, network
shares), the store falls back to a copy and emits a warning.

The store keeps a SQLite read-model at the path resolved by
``KAYAKGEN_INDEX_DB`` or ``~/.local/share/kayakgen/index.sqlite``. Schema
matches RFC 0049 § "SQLite index v1". Tables are created on first use;
existing rows are upserted.

Module owns nothing it doesn't persist. The four identity hashes live in
:mod:`kayakgen.services.identity`.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Literal, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field

ArtifactKind = Literal[
    "hull_json",
    "eval_result_json",
    "stability_result_json",
    "mesh_package_manifest",
    "mesh_quality_json",
    "hull_stl",
    "deck_stl",
    "cfd_run_record",
    "cfd_raw_result",
    "openfoam_force_dat",
    "openfoam_polymesh_file",
    "snappy_hex_mesh_evidence",
    "sweep_run_record",
    "sweep_summary_csv",
    "sweep_failures_jsonl",
    "candidate_record",
    "high_angle_gz_artifact",
    "search_run_record",
    "comparison_report",
]

RunKind = Literal["sweep", "search", "cfd", "comparison"]


# ---------------------------------------------------------------------------
# Records


class ArtifactRef(BaseModel):
    """A pointer to a stored artifact (RFC 0049)."""

    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    artifact_hash: str
    run_id: str | None = None
    candidate_key: str | None = None
    relative_path: str | None = None


class RunEvent(BaseModel):
    """An append-only event recorded against a run."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    ts: int = Field(default_factory=lambda: int(time.time()))
    payload: dict[str, Any] = Field(default_factory=dict)


class CandidateSummary(BaseModel):
    """A read-model row produced by ``ArtifactStore.query_candidates``."""

    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    run_id: str
    status: str
    hull_design_hash: str | None = None
    hull_record_hash: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Errors


class ArtifactIntegrityError(RuntimeError):
    """Bytes at a content address fail rehash verification (audit G2, D050).

    The read contract is SERVE-ONLY-VERIFIED: every read path rehashes
    bytes before serving them. A mismatch is repaired from the canonical
    path only when the canonical bytes rehash to the expected address;
    otherwise this error is raised — unverified bytes are never served.
    """

    def __init__(self, *, path: Path, expected_hash: str, actual_hash: str) -> None:
        self.path = path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        super().__init__(
            f"artifact integrity failure at {path}: expected hash "
            f"{expected_hash}, got {actual_hash}; refusing to serve "
            "unverified bytes (SERVE-ONLY-VERIFIED, D050)"
        )


# ---------------------------------------------------------------------------
# Protocol


class ArtifactStore(Protocol):
    def put_json(
        self,
        kind: ArtifactKind,
        payload: BaseModel,
        *,
        run_id: str | None = None,
        candidate_key: str | None = None,
        canonical_path: Path | None = None,
    ) -> ArtifactRef: ...

    def put_file(
        self,
        kind: ArtifactKind,
        path: Path,
        *,
        run_id: str | None = None,
        candidate_key: str | None = None,
    ) -> ArtifactRef: ...

    def get_json(self, ref: ArtifactRef) -> dict[str, Any]: ...

    def get_file(self, ref: ArtifactRef) -> Path: ...

    def record_event(self, run_id: str, event: RunEvent) -> None: ...

    def query_candidates(
        self,
        run_id: str,
        *,
        filters: dict[str, Any] | None = None,
        metrics: Sequence[str] = (),
    ) -> list[CandidateSummary]: ...


# ---------------------------------------------------------------------------
# SQLite index


def _default_index_path() -> Path:
    env = os.environ.get("KAYAKGEN_INDEX_DB")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".local" / "share" / "kayakgen" / "index.sqlite"


class SqliteIndex:
    """SQLite read-model over runs / candidates / metrics / artifacts / events.

    Schema matches RFC 0049 § "SQLite index v1". Tables are created
    lazily on first use; existing rows are upserted by their primary key.

    The schema is stamped with ``PRAGMA user_version = SCHEMA_VERSION``
    (audit R6). On open, a DB stamped lower than the current version is
    dropped and recreated with a ``UserWarning`` — the index is a
    rebuildable read-model over the run directories, so rebuild-not-migrate
    is the deliberate policy (full migration machinery is out of scope).
    Bump ``SCHEMA_VERSION`` whenever a table or column is added or changed.
    """

    #: bump on any schema change; older on-disk stamps trigger a rebuild.
    SCHEMA_VERSION = 1

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else _default_index_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialised = False

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            if not self._initialised:
                self._ensure_schema(conn)
                self._initialised = True
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        """Create the schema, rebuilding first if the stamp is stale.

        Audit R6: ``CREATE TABLE IF NOT EXISTS`` alone meant any column
        addition made every existing operator DB raise ``OperationalError``
        at upsert time, mid-sweep. A fresh (empty) DB is stamped silently;
        a DB at the current version is left untouched apart from the
        idempotent CREATE statements, so normal reuse never drops rows.
        """

        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < self.SCHEMA_VERSION:
            tables = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            if tables:
                warnings.warn(
                    f"kayakgen index at {self.path} has schema version "
                    f"{version} < {self.SCHEMA_VERSION}; rebuilding the "
                    f"read-model (dropping: {', '.join(sorted(tables))}). "
                    "The index is rebuildable from run directories "
                    "(index_run_directory).",
                    stacklevel=4,
                )
                cur = conn.cursor()
                for name in tables:
                    cur.execute(f'DROP TABLE IF EXISTS "{name}"')
            self._create_schema(conn)
            conn.execute(f"PRAGMA user_version = {int(self.SCHEMA_VERSION)}")
        else:
            # Current (or future) stamp: never drop, never downgrade.
            self._create_schema(conn)

    @staticmethod
    def _create_schema(conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
              run_id TEXT PRIMARY KEY,
              kind TEXT,
              spec_hash TEXT,
              run_hash TEXT,
              created_at INTEGER,
              out_dir TEXT
            );
            CREATE TABLE IF NOT EXISTS candidates (
              candidate_key TEXT,
              run_id TEXT,
              status TEXT,
              hull_design_hash TEXT,
              hull_record_hash TEXT,
              created_at INTEGER,
              PRIMARY KEY (run_id, candidate_key)
            );
            CREATE TABLE IF NOT EXISTS metrics (
              run_id TEXT,
              candidate_key TEXT,
              metric_name TEXT,
              metric_value REAL,
              PRIMARY KEY (run_id, candidate_key, metric_name)
            );
            CREATE TABLE IF NOT EXISTS artifacts (
              artifact_hash TEXT PRIMARY KEY,
              kind TEXT,
              run_id TEXT,
              candidate_key TEXT,
              byte_count INTEGER,
              created_at INTEGER,
              relative_path TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
              event_id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT,
              ts INTEGER,
              kind TEXT,
              payload TEXT
            );
            CREATE TABLE IF NOT EXISTS generative_jobs (
              job_id TEXT PRIMARY KEY,
              job_kind TEXT,
              spec_hash TEXT,
              state TEXT,
              output_dir TEXT,
              run_id TEXT,
              run_hash TEXT,
              started_at REAL,
              completed_at REAL,
              realized_evaluations INTEGER,
              completed_count INTEGER,
              failed_count INTEGER,
              constraint_failed_count INTEGER,
              pending_count INTEGER,
              updated_at INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_runs_kind ON runs (kind);
            CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs (created_at);
            CREATE INDEX IF NOT EXISTS idx_candidates_hull_design_hash
              ON candidates (hull_design_hash);
            CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics (metric_name);
            CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON artifacts (kind);
            CREATE INDEX IF NOT EXISTS idx_generative_jobs_state
              ON generative_jobs (state);
            CREATE INDEX IF NOT EXISTS idx_generative_jobs_kind
              ON generative_jobs (job_kind);
            """
        )

    # -- writes ------------------------------------------------------------

    def upsert_run(
        self,
        *,
        run_id: str,
        kind: RunKind,
        spec_hash: str,
        run_hash: str,
        out_dir: str,
        created_at: int | None = None,
    ) -> None:
        ts = created_at if created_at is not None else int(time.time())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO runs (run_id, kind, spec_hash, run_hash, created_at, out_dir)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                  kind=excluded.kind,
                  spec_hash=excluded.spec_hash,
                  run_hash=excluded.run_hash,
                  created_at=excluded.created_at,
                  out_dir=excluded.out_dir
                """,
                (run_id, kind, spec_hash, run_hash, ts, out_dir),
            )

    def upsert_candidate(
        self,
        *,
        run_id: str,
        candidate_key: str,
        status: str,
        hull_design_hash: str | None,
        hull_record_hash: str | None,
        created_at: int | None = None,
    ) -> None:
        ts = created_at if created_at is not None else int(time.time())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO candidates
                  (run_id, candidate_key, status, hull_design_hash, hull_record_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, candidate_key) DO UPDATE SET
                  status=excluded.status,
                  hull_design_hash=excluded.hull_design_hash,
                  hull_record_hash=excluded.hull_record_hash,
                  created_at=excluded.created_at
                """,
                (run_id, candidate_key, status, hull_design_hash, hull_record_hash, ts),
            )

    def upsert_metrics(
        self,
        *,
        run_id: str,
        candidate_key: str,
        metrics: dict[str, float],
    ) -> None:
        if not metrics:
            return
        with self._conn() as conn:
            for name, value in metrics.items():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                conn.execute(
                    """
                    INSERT INTO metrics (run_id, candidate_key, metric_name, metric_value)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(run_id, candidate_key, metric_name) DO UPDATE SET
                      metric_value=excluded.metric_value
                    """,
                    (run_id, candidate_key, name, numeric),
                )

    def upsert_artifact(
        self,
        *,
        artifact_hash: str,
        kind: ArtifactKind,
        run_id: str | None,
        candidate_key: str | None,
        byte_count: int,
        relative_path: str | None,
        created_at: int | None = None,
    ) -> None:
        ts = created_at if created_at is not None else int(time.time())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO artifacts
                  (artifact_hash, kind, run_id, candidate_key, byte_count, created_at, relative_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_hash) DO UPDATE SET
                  kind=excluded.kind,
                  run_id=excluded.run_id,
                  candidate_key=excluded.candidate_key,
                  byte_count=excluded.byte_count,
                  created_at=excluded.created_at,
                  relative_path=excluded.relative_path
                """,
                (artifact_hash, kind, run_id, candidate_key, byte_count, ts, relative_path),
            )

    def insert_event(self, *, run_id: str, event: RunEvent) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO events (run_id, ts, kind, payload) VALUES (?, ?, ?, ?)",
                (run_id, event.ts, event.kind, json.dumps(event.payload, sort_keys=True)),
            )

    def upsert_generative_job(
        self,
        *,
        job_id: str,
        job_kind: str,
        spec_hash: str,
        state: str,
        output_dir: str,
        run_id: str | None = None,
        run_hash: str | None = None,
        started_at: float | None = None,
        completed_at: float | None = None,
        realized_evaluations: int = 0,
        completed_count: int = 0,
        failed_count: int = 0,
        constraint_failed_count: int = 0,
        pending_count: int = 0,
        updated_at: int | None = None,
    ) -> None:
        """Insert or update a row in the ``generative_jobs`` table (RFC 0057)."""

        ts = updated_at if updated_at is not None else int(time.time())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO generative_jobs
                  (job_id, job_kind, spec_hash, state, output_dir, run_id, run_hash,
                   started_at, completed_at, realized_evaluations, completed_count,
                   failed_count, constraint_failed_count, pending_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                  job_kind=excluded.job_kind,
                  spec_hash=excluded.spec_hash,
                  state=excluded.state,
                  output_dir=excluded.output_dir,
                  run_id=excluded.run_id,
                  run_hash=excluded.run_hash,
                  started_at=excluded.started_at,
                  completed_at=excluded.completed_at,
                  realized_evaluations=excluded.realized_evaluations,
                  completed_count=excluded.completed_count,
                  failed_count=excluded.failed_count,
                  constraint_failed_count=excluded.constraint_failed_count,
                  pending_count=excluded.pending_count,
                  updated_at=excluded.updated_at
                """,
                (
                    job_id,
                    job_kind,
                    spec_hash,
                    state,
                    output_dir,
                    run_id,
                    run_hash,
                    started_at,
                    completed_at,
                    realized_evaluations,
                    completed_count,
                    failed_count,
                    constraint_failed_count,
                    pending_count,
                    ts,
                ),
            )

    # -- reads -------------------------------------------------------------

    def list_runs(
        self,
        *,
        kind: RunKind | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT run_id, kind, spec_hash, run_hash, created_at, out_dir FROM runs"
        params: list[Any] = []
        if kind is not None:
            sql += " WHERE kind = ?"
            params.append(kind)
        sql += " ORDER BY created_at ASC, run_id ASC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def list_generative_jobs(
        self,
        *,
        state: str | None = None,
        job_kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """List rows from the ``generative_jobs`` table (RFC 0057)."""

        sql = (
            "SELECT job_id, job_kind, spec_hash, state, output_dir, run_id, "
            "run_hash, started_at, completed_at, realized_evaluations, "
            "completed_count, failed_count, constraint_failed_count, "
            "pending_count, updated_at FROM generative_jobs"
        )
        params: list[Any] = []
        clauses: list[str] = []
        if state is not None:
            clauses.append("state = ?")
            params.append(state)
        if job_kind is not None:
            clauses.append("job_kind = ?")
            params.append(job_kind)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at ASC, job_id ASC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def candidates_for_run(
        self,
        run_id: str,
        *,
        metrics: Sequence[str] = (),
    ) -> list[CandidateSummary]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT candidate_key, run_id, status, hull_design_hash, hull_record_hash
                FROM candidates WHERE run_id = ?
                ORDER BY candidate_key ASC
                """,
                (run_id,),
            ).fetchall()
            metric_rows: dict[tuple[str, str], float] = {}
            if metrics:
                placeholders = ",".join("?" for _ in metrics)
                m = conn.execute(
                    f"""
                    SELECT candidate_key, metric_name, metric_value
                    FROM metrics WHERE run_id = ? AND metric_name IN ({placeholders})
                    """,
                    (run_id, *metrics),
                ).fetchall()
                for row in m:
                    metric_rows[(row["candidate_key"], row["metric_name"])] = row["metric_value"]
            else:
                m = conn.execute(
                    """
                    SELECT candidate_key, metric_name, metric_value
                    FROM metrics WHERE run_id = ?
                    """,
                    (run_id,),
                ).fetchall()
                for row in m:
                    metric_rows[(row["candidate_key"], row["metric_name"])] = row["metric_value"]

        out: list[CandidateSummary] = []
        for row in rows:
            ck = row["candidate_key"]
            metrics_for = {
                name: value
                for (key, name), value in metric_rows.items()
                if key == ck
            }
            out.append(
                CandidateSummary(
                    candidate_key=ck,
                    run_id=row["run_id"],
                    status=row["status"],
                    hull_design_hash=row["hull_design_hash"],
                    hull_record_hash=row["hull_record_hash"],
                    metrics=metrics_for,
                )
            )
        return out

    def metric_count(self, run_id: str) -> int:
        with self._conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM metrics WHERE run_id = ?", (run_id,)
            ).fetchone()["c"]


# ---------------------------------------------------------------------------
# Filesystem store


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` via a temp sibling + ``os.replace``.

    Audit R5 / BUG-041 (2026-06-06): a bare ``write_bytes`` interrupted
    mid-write leaves truncated bytes at the content address. The temp
    sibling is dot-prefixed so a crash between write and rename can never
    leave a file matching the ``_store/<hash>.*`` glob that
    ``_resolve_artifact`` serves reads from.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _link_or_copy(src: Path, dst: Path) -> None:
    """Hard-link ``src`` to ``dst``; fall back to copy with a warning."""

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        try:
            if dst.stat().st_ino == src.stat().st_ino:
                return
        except OSError:
            pass
        dst.unlink()
    if os.name == "nt":
        shutil.copyfile(src, dst)
        warnings.warn(
            "kayakgen artifact store falling back to copy on Windows; "
            f"hard-links unsupported for {dst}",
            stacklevel=2,
        )
        return
    try:
        os.link(src, dst)
    except OSError as exc:
        shutil.copyfile(src, dst)
        warnings.warn(
            "kayakgen artifact store could not hard-link "
            f"({exc}); copied {src} -> {dst}",
            stacklevel=2,
        )


class FilesystemArtifactStore:
    """Content-addressed store backed by ``<run_dir>/_store/``.

    The canonical layout (``run.json``, ``candidates/<key>/...``) is the
    compatibility export. Each ``put_*`` writes to ``_store/<hash>.<ext>``
    first and then hard-links the canonical path into that mirror. The
    SQLite index is updated in the same call.

    If ``_store/`` is missing on read (manual removal), the store
    re-derives the hash from the canonical path and re-creates the mirror,
    emitting a ``UserWarning``.

    Reads are SERVE-ONLY-VERIFIED (audit G2, D050): every read path
    rehashes bytes before serving. Corrupt store bytes are repaired from
    the canonical path when its bytes rehash to the expected address;
    otherwise the read raises :class:`ArtifactIntegrityError` — unverified
    bytes are never served.
    """

    def __init__(
        self,
        run_dir: Path | str,
        *,
        run_id: str | None = None,
        index: SqliteIndex | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.store_dir = self.run_dir / "_store"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or self.run_dir.name
        self.index = index if index is not None else SqliteIndex()
        self._events_path = self.store_dir / "events.jsonl"

    # -- writes ------------------------------------------------------------

    def _extension_for(self, kind: ArtifactKind, canonical_path: Path | None) -> str:
        if canonical_path is not None and canonical_path.suffix:
            return canonical_path.suffix
        if kind.endswith("_json") or kind in ("candidate_record", "cfd_run_record",
                                              "sweep_run_record", "search_run_record",
                                              "comparison_report", "snappy_hex_mesh_evidence",
                                              "high_angle_gz_artifact"):
            return ".json"
        if kind == "sweep_summary_csv":
            return ".csv"
        if kind == "sweep_failures_jsonl":
            return ".jsonl"
        if kind in ("hull_stl", "deck_stl"):
            return ".stl"
        if kind == "openfoam_force_dat":
            return ".dat"
        return ".bin"

    def _store_path(self, artifact_hash: str, extension: str) -> Path:
        return self.store_dir / f"{artifact_hash}{extension}"

    @staticmethod
    def _verify_or_repair_store_file(
        store_path: Path, artifact_hash: str, data: bytes
    ) -> None:
        """Repair corrupt bytes occupying a content address (audit R5).

        The dedupe branch used to trust ``exists()`` blindly: a crash
        mid-write left truncated bytes at ``_store/<hash>`` and every
        later put of the same content silently hard-linked the corrupt
        bytes into canonical run layouts. Byte length is the cheap
        screen; on mismatch the occupant is rehashed to confirm
        corruption before being atomically replaced with the intact
        payload. An intact occupant is left untouched (normal dedupe).
        """

        try:
            existing_size = store_path.stat().st_size
        except OSError:
            existing_size = -1
        if existing_size == len(data):
            return
        existing_hash: str | None
        try:
            existing_hash = _hash_bytes(store_path.read_bytes())
        except OSError:
            existing_hash = None
        if existing_hash == artifact_hash:
            return
        warnings.warn(
            "kayakgen artifact store found corrupt bytes at "
            f"{store_path} (size {existing_size} != {len(data)}, "
            f"hash {existing_hash!r}); repairing with intact payload",
            stacklevel=2,
        )
        _atomic_write_bytes(store_path, data)

    def _put_bytes(
        self,
        kind: ArtifactKind,
        data: bytes,
        *,
        run_id: str | None,
        candidate_key: str | None,
        canonical_path: Path | None,
    ) -> ArtifactRef:
        artifact_hash = _hash_bytes(data)
        extension = self._extension_for(kind, canonical_path)
        store_path = self._store_path(artifact_hash, extension)
        if store_path.exists():
            self._verify_or_repair_store_file(store_path, artifact_hash, data)
        else:
            _atomic_write_bytes(store_path, data)
        relative_path: str | None = None
        if canonical_path is not None:
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            if canonical_path.exists():
                canonical_path.unlink()
            _link_or_copy(store_path, canonical_path)
            try:
                relative_path = str(canonical_path.relative_to(self.run_dir))
            except ValueError:
                relative_path = str(canonical_path)
        self.index.upsert_artifact(
            artifact_hash=artifact_hash,
            kind=kind,
            run_id=run_id if run_id is not None else self.run_id,
            candidate_key=candidate_key,
            byte_count=len(data),
            relative_path=relative_path,
        )
        return ArtifactRef(
            kind=kind,
            artifact_hash=artifact_hash,
            run_id=run_id if run_id is not None else self.run_id,
            candidate_key=candidate_key,
            relative_path=relative_path,
        )

    def put_json(
        self,
        kind: ArtifactKind,
        payload: BaseModel | dict[str, Any],
        *,
        run_id: str | None = None,
        candidate_key: str | None = None,
        canonical_path: Path | None = None,
    ) -> ArtifactRef:
        """Write ``payload`` (Pydantic model or dict) as JSON bytes.

        The bytes are the exact same Pydantic-emitted JSON the legacy
        callers used (``model_dump_json(indent=2)``) so canonical paths
        remain byte-stable.
        """

        if isinstance(payload, BaseModel):
            text = payload.model_dump_json(indent=2)
        else:
            text = json.dumps(payload, indent=2)
        return self._put_bytes(
            kind,
            text.encode("utf-8"),
            run_id=run_id,
            candidate_key=candidate_key,
            canonical_path=canonical_path,
        )

    def put_bytes(
        self,
        kind: ArtifactKind,
        data: bytes,
        *,
        run_id: str | None = None,
        candidate_key: str | None = None,
        canonical_path: Path | None = None,
    ) -> ArtifactRef:
        """Write arbitrary bytes (e.g. CSV) and mirror at canonical_path."""

        return self._put_bytes(
            kind,
            data,
            run_id=run_id,
            candidate_key=candidate_key,
            canonical_path=canonical_path,
        )

    def put_file(
        self,
        kind: ArtifactKind,
        path: Path,
        *,
        run_id: str | None = None,
        candidate_key: str | None = None,
    ) -> ArtifactRef:
        """Ingest an existing file at ``path`` and mirror it into _store/."""

        data = path.read_bytes()
        return self._put_bytes(
            kind,
            data,
            run_id=run_id,
            candidate_key=candidate_key,
            canonical_path=path,
        )

    # -- reads -------------------------------------------------------------

    def _repair_store_from_canonical(
        self, ref: ArtifactRef, store_path: Path
    ) -> Path | None:
        """Repair corrupt store bytes from an intact canonical copy (audit G2).

        Mirrors the write-side repair (``_verify_or_repair_store_file``):
        only canonical bytes that rehash to the expected content address
        may overwrite the corrupt occupant, via the same atomic replace.
        Returns ``None`` when no canonical path exists, it cannot be read,
        or its bytes do not rehash to ``ref.artifact_hash`` — the caller
        must then refuse to serve. Note a hard-linked canonical shares the
        corrupt inode, so this rescue only fires when the canonical is an
        independent copy (copy fallback, or rewritten out-of-band).
        """

        if ref.relative_path is None:
            return None
        canonical = self.run_dir / ref.relative_path
        try:
            data = canonical.read_bytes()
        except OSError:
            return None
        if _hash_bytes(data) != ref.artifact_hash:
            return None
        warnings.warn(
            "kayakgen artifact store found corrupt bytes at "
            f"{store_path} on read; repairing from canonical {canonical} "
            "(SERVE-ONLY-VERIFIED, D050)",
            stacklevel=3,
        )
        _atomic_write_bytes(store_path, data)
        return store_path

    def _resolve_artifact(self, ref: ArtifactRef) -> Path:
        # Try store first. SERVE-ONLY-VERIFIED (audit G2, D050): rehash
        # before serving on every read path. Before this, a content
        # address corrupted after write was served silently, forever;
        # repair only fired on the next put of identical content.
        for path in self.store_dir.glob(f"{ref.artifact_hash}.*"):
            if not path.is_file():
                continue
            actual = _hash_bytes(path.read_bytes())
            if actual == ref.artifact_hash:
                return path
            repaired = self._repair_store_from_canonical(ref, path)
            if repaired is not None:
                return repaired
            raise ArtifactIntegrityError(
                path=path, expected_hash=ref.artifact_hash, actual_hash=actual
            )
        # Re-derive from canonical path if available.
        if ref.relative_path is not None:
            canonical = self.run_dir / ref.relative_path
            if canonical.exists():
                data = canonical.read_bytes()
                derived = _hash_bytes(data)
                if derived != ref.artifact_hash:
                    # Audit G2/G6: this branch used to warn and serve the
                    # mismatched bytes anyway; fail closed instead.
                    raise ArtifactIntegrityError(
                        path=canonical,
                        expected_hash=ref.artifact_hash,
                        actual_hash=derived,
                    )
                warnings.warn(
                    "kayakgen artifact store missing _store/ entry for "
                    f"{ref.artifact_hash}; re-deriving from {canonical}",
                    stacklevel=2,
                )
                extension = canonical.suffix or ".bin"
                store_path = self._store_path(derived, extension)
                if not store_path.exists():
                    _atomic_write_bytes(store_path, data)
                return store_path
        raise FileNotFoundError(
            f"artifact {ref.artifact_hash} not found under {self.store_dir}"
        )

    def get_json(self, ref: ArtifactRef) -> dict[str, Any]:
        path = self._resolve_artifact(ref)
        return json.loads(path.read_text())

    def get_file(self, ref: ArtifactRef) -> Path:
        return self._resolve_artifact(ref)

    # -- events ------------------------------------------------------------

    def record_event(self, run_id: str, event: RunEvent) -> None:
        line = json.dumps(
            {"run_id": run_id, "ts": event.ts, "kind": event.kind, "payload": event.payload},
            sort_keys=True,
        )
        with self._events_path.open("a") as fh:
            fh.write(line + "\n")
        self.index.insert_event(run_id=run_id, event=event)

    # -- queries -----------------------------------------------------------

    def query_candidates(
        self,
        run_id: str,
        *,
        filters: dict[str, Any] | None = None,
        metrics: Sequence[str] = (),
    ) -> list[CandidateSummary]:
        results = self.index.candidates_for_run(run_id, metrics=metrics)
        if not filters:
            return results
        filtered: list[CandidateSummary] = []
        for row in results:
            ok = True
            for key, value in filters.items():
                if key == "status":
                    if row.status != value:
                        ok = False
                        break
                elif key == "hull_design_hash":
                    if row.hull_design_hash != value:
                        ok = False
                        break
                else:
                    metric_value = row.metrics.get(key)
                    if metric_value != value:
                        ok = False
                        break
            if ok:
                filtered.append(row)
        return filtered


# ---------------------------------------------------------------------------
# Convenience helpers used by sweep/search/cfd migration


def index_run_directory(
    run_dir: Path | str,
    *,
    run_id: str,
    kind: RunKind,
    spec_hash: str,
    run_hash_value: str,
    index: SqliteIndex | None = None,
) -> SqliteIndex:
    """Register a run directory in the SQLite index.

    Returns the index instance (created on demand) so callers can chain
    candidate/metric upserts.
    """

    db = index if index is not None else SqliteIndex()
    db.upsert_run(
        run_id=run_id,
        kind=kind,
        spec_hash=spec_hash,
        run_hash=run_hash_value,
        out_dir=str(Path(run_dir)),
    )
    return db


def index_candidates(
    *,
    run_id: str,
    candidate_rows: Iterable[dict[str, Any]],
    index: SqliteIndex,
) -> None:
    """Bulk-upsert candidate rows and their metrics.

    Each row must carry ``candidate_key``, ``status``, optional
    ``hull_design_hash`` / ``hull_record_hash``, and a ``metrics`` dict.
    """

    for row in candidate_rows:
        ck = row["candidate_key"]
        index.upsert_candidate(
            run_id=run_id,
            candidate_key=ck,
            status=row.get("status", "unknown"),
            hull_design_hash=row.get("hull_design_hash"),
            hull_record_hash=row.get("hull_record_hash"),
        )
        metrics = row.get("metrics") or {}
        if metrics:
            index.upsert_metrics(
                run_id=run_id,
                candidate_key=ck,
                metrics=metrics,
            )


__all__ = [
    "ArtifactKind",
    "ArtifactRef",
    "ArtifactStore",
    "CandidateSummary",
    "FilesystemArtifactStore",
    "RunEvent",
    "RunKind",
    "SqliteIndex",
    "index_candidates",
    "index_run_directory",
]
