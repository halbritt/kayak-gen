"""Local subprocess ownership held for the runner's entire lifetime."""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field

PROTOCOL_FILE = "ownership-protocol.json"
OWNER_FILE = "owner.json"
LOCK_FILE = "ownership.lock"


class JobOwnershipError(ValueError):
    """Ownership cannot authorize a new writer or a state publication."""


class JobOwnerBusy(JobOwnershipError):
    """A local runner or admitting manager still holds the job lock."""


class OwnershipProtocol(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1"] = "1"
    backend: Literal["subprocess"] = "subprocess"


def protocol_is_current(job_dir: Path) -> bool:
    try:
        OwnershipProtocol.model_validate_json((job_dir / PROTOCOL_FILE).read_text())
    except (OSError, ValueError):
        return False
    return True


class AttemptOwner(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1"] = "1"
    attempt_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    pid: int = Field(gt=0)
    process_start: str = Field(pattern=r"^(?:[0-9]+|exited)$")
    boot_id: str = Field(pattern=r"^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|exited)$")
    host_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    phase: Literal["admitting", "starting", "running", "launch_failed"]
    recorded_at: float


@dataclass
class JobLease:
    job_dir: Path
    fd: int
    attempt_id: str | None = None


_ACTIVE_LEASE: ContextVar[JobLease | None] = ContextVar("generative_job_lease", default=None)


def _write_json(path: Path, payload: dict) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=path.name, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def mark_subprocess_job(job_dir: Path) -> None:
    if os.name != "posix" or not Path("/proc/self/stat").exists():
        raise JobOwnershipError("subprocess ownership requires local Linux process identity and POSIX locks")
    _host_id()
    _write_json(job_dir / PROTOCOL_FILE, OwnershipProtocol().model_dump(mode="json"))


def _host_id() -> str:
    identity = Path("/etc/machine-id").read_text().strip()
    if len(identity) != 32:
        raise JobOwnershipError("local machine identity is unavailable")
    return identity


def process_identity(pid: int) -> tuple[str, str, str] | None:
    """Read PID-reuse-safe Linux identity; a missing process is known dead."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return None
    # The process name can contain spaces and parentheses. Fields after
    # the last closing parenthesis start with state (field 3).
    fields = stat.rsplit(")", 1)[1].split()
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    return fields[19], boot_id, fields[0]


def read_owner(job_dir: Path) -> AttemptOwner | None:
    try:
        return AttemptOwner.model_validate_json((job_dir / OWNER_FILE).read_text())
    except FileNotFoundError:
        return None


def owner_state(job_dir: Path, attempt_id: str | None) -> Literal["live", "dead", "unknown"]:
    try:
        owner = read_owner(job_dir)
        if owner is None or owner.attempt_id != attempt_id or owner.host_id != _host_id():
            return "unknown"
        if owner.phase == "launch_failed":
            return "dead"
        observed = process_identity(owner.pid)
    except (OSError, ValueError, IndexError):
        return "unknown"
    if observed is None:
        return "dead"
    start, boot, state = observed
    if start != owner.process_start or boot != owner.boot_id or state == "Z":
        return "dead"
    return "live"


@contextmanager
def locked_job(job_dir: Path) -> Iterator[JobLease]:
    import fcntl

    fd = os.open(job_dir / LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise JobOwnerBusy("job owner is still active; automatic replacement refused") from exc
        lease = JobLease(job_dir=job_dir, fd=fd)
        token = _ACTIVE_LEASE.set(lease)
        try:
            yield lease
        finally:
            _ACTIVE_LEASE.reset(token)
    finally:
        # Closing only this reference preserves a lock inherited by the child.
        # LOCK_UN here would release that shared open-file-description lock.
        os.close(fd)


def begin_attempt(lease: JobLease) -> str:
    attempt_id = uuid.uuid4().hex
    lease.attempt_id = attempt_id
    _record_owner(lease, phase="admitting")
    return attempt_id


def _record_owner(
    lease: JobLease, *, phase: Literal["admitting", "starting", "running", "launch_failed"],
    pid: int | None = None, exited: bool = False,
) -> None:
    owner_pid = os.getpid() if pid is None else pid
    observed = None if exited else process_identity(owner_pid)
    if observed is None:
        observed = ("exited", "exited", "X")
    start, boot, _ = observed
    owner = AttemptOwner(
        attempt_id=lease.attempt_id, pid=owner_pid, process_start=start,
        boot_id=boot, host_id=_host_id(), phase=phase, recorded_at=time.time(),
    )
    directory = lease.job_dir / "attempts" / owner.attempt_id
    directory.mkdir(parents=True, exist_ok=True)
    _write_json(directory / f"{phase}.json", owner.model_dump(mode="json"))
    _write_json(lease.job_dir / OWNER_FILE, owner.model_dump(mode="json"))


def record_spawned(lease: JobLease, pid: int, *, exited: bool) -> None:
    _record_owner(lease, phase="starting", pid=pid, exited=exited)


def record_running(lease: JobLease) -> None:
    _record_owner(lease, phase="running")


def record_launch_failure(lease: JobLease) -> None:
    _record_owner(lease, phase="launch_failed")


@contextmanager
def runner_lease(job_dir: Path, attempt_id: str, fd: int) -> Iterator[JobLease]:
    actual = os.fstat(fd)
    expected = (job_dir / LOCK_FILE).stat()
    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
        raise JobOwnershipError("inherited ownership descriptor does not name this job")
    lease = JobLease(job_dir=job_dir, fd=fd, attempt_id=attempt_id)
    token = _ACTIVE_LEASE.set(lease)
    try:
        deadline = time.monotonic() + 5
        while True:
            assert_current_attempt(job_dir, attempt_id)
            owner = read_owner(job_dir)
            if owner.pid == os.getpid():
                break
            if time.monotonic() >= deadline:
                raise JobOwnershipError("admitting manager did not publish worker identity")
            time.sleep(0.005)
        record_running(lease)
        yield lease
    finally:
        _ACTIVE_LEASE.reset(token)
        os.close(fd)


def assert_current_attempt(job_dir: Path, attempt_id: str | None) -> None:
    owner = read_owner(job_dir)
    if owner is None and attempt_id is None and not (job_dir / PROTOCOL_FILE).exists():
        return
    lease = _ACTIVE_LEASE.get()
    if (owner is None or lease is None or lease.job_dir != job_dir
            or owner.attempt_id != attempt_id or lease.attempt_id != attempt_id):
        raise JobOwnershipError("stale or unowned attempt cannot publish job state")


def save_attempt_state(job_dir: Path, payload: dict) -> None:
    attempt_id = payload["attempt_id"]
    assert_current_attempt(job_dir, attempt_id)
    _write_json(job_dir / "attempts" / attempt_id / "job.json", payload)
