"""Auto-poll wiring for the Generate panel (RFC 0057 stage 4 / D-9).

The listener refreshes the Generate panel's jobs index on a cadence:

- ``GENERATIVE_POLL_RUNNING_SECONDS`` (default 1.0 s) while any job is in
  ``{queued, running}``.
- ``GENERATIVE_POLL_IDLE_SECONDS`` (default 10.0 s) otherwise.

It is cancellable: tearing down the app via :func:`stop_generate_state_listener`
sets a stop flag and the next tick exits cleanly. The listener coalesces its
own refresh with a near-simultaneous manual "Refresh Jobs" press so one click
does not double-hit the manager.
"""

from __future__ import annotations

import threading
import time
from typing import Any

GENERATIVE_POLL_RUNNING_SECONDS = 1.0
"""Polling cadence while any job is in flight."""

GENERATIVE_POLL_IDLE_SECONDS = 10.0
"""Polling cadence while all jobs are terminal (or the panel is idle)."""

GENERATIVE_REFRESH_COALESCE_SECONDS = 0.05
"""Minimum spacing between manual and auto refresh callbacks."""

_IN_FLIGHT_STATES = frozenset({"queued", "running"})
_DETAIL_REFRESH_STATES = frozenset({"succeeded", "failed", "resumable"})


class _PollHandle:
    """Tracks the listener thread and its stop flag for a single app."""

    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.lock = threading.Lock()
        self.job_states: dict[str, str] = {}
        self.last_refresh_at = 0.0
        self.in_auto_refresh = False
        self.original_refresh: Any | None = None


def install_generate_state_listener(
    app: Any,
    *,
    running_seconds: float = GENERATIVE_POLL_RUNNING_SECONDS,
    idle_seconds: float = GENERATIVE_POLL_IDLE_SECONDS,
) -> None:
    """Install the auto-poll listener on a :class:`KayakgenApp`.

    Idempotent: re-installing on the same app stops the prior listener first.
    """

    stop_generate_state_listener(app)

    handle = _PollHandle()
    handle.original_refresh = getattr(app.ctrl, "refresh_generative_jobs", None)
    app._generative_poll_handle = handle  # noqa: SLF001 - app extension hook
    if _can_wrap_refresh_callback(handle.original_refresh):
        app.ctrl.refresh_generative_jobs = _wrap_manual_refresh(  # noqa: SLF001
            handle,
            handle.original_refresh,
        )

    def _tick() -> None:
        while not handle.stop_event.is_set():
            summaries = _list_summaries(app)
            _refresh_jobs(app, handle, force=not handle.job_states)
            _refresh_terminal_details(app, handle, summaries)
            _remember_states(handle, summaries)
            cadence = compute_cadence_seconds(
                has_in_flight_jobs=has_in_flight_jobs(summaries),
                running_seconds=running_seconds,
                idle_seconds=idle_seconds,
            )
            if handle.stop_event.wait(timeout=cadence):
                return

    handle.thread = threading.Thread(
        target=_tick,
        name="generative-poll-listener",
        daemon=True,
    )
    handle.thread.start()


def stop_generate_state_listener(app: Any) -> None:
    """Stop the installed listener if any. Safe to call repeatedly."""

    handle = getattr(app, "_generative_poll_handle", None)
    if handle is None:
        return
    handle.stop_event.set()
    if handle.thread is not None:
        handle.thread.join(timeout=2.0)
    if _can_wrap_refresh_callback(handle.original_refresh):
        app.ctrl.refresh_generative_jobs = handle.original_refresh  # noqa: SLF001
    app._generative_poll_handle = None  # noqa: SLF001


def compute_cadence_seconds(
    *,
    has_in_flight_jobs: bool,
    running_seconds: float = GENERATIVE_POLL_RUNNING_SECONDS,
    idle_seconds: float = GENERATIVE_POLL_IDLE_SECONDS,
) -> float:
    """Return the next poll interval given whether any job is in flight.

    Public helper so tests can verify the cadence rule without touching
    Trame state or the manager.
    """

    return running_seconds if has_in_flight_jobs else idle_seconds


def has_in_flight_jobs(summaries: list[Any]) -> bool:
    """Return True if any :class:`GenerativeJobSummary` is queued or running."""

    return any(
        getattr(summary, "state", None) in _IN_FLIGHT_STATES for summary in summaries
    )


def _list_summaries(app: Any) -> list[Any]:
    manager = getattr(app, "_generative_manager", None)
    if manager is None:
        return []
    try:
        return list(manager.list())
    except Exception:  # noqa: BLE001
        return []


def _wrap_manual_refresh(handle: _PollHandle, callback: Any) -> Any:
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        result = callback(*args, **kwargs)
        if not handle.in_auto_refresh:
            with handle.lock:
                handle.last_refresh_at = time.monotonic()
        return result

    return _wrapped


def _can_wrap_refresh_callback(callback: Any) -> bool:
    """Return True for plain callbacks that can be replaced safely.

    Trame controller functions are mutable dispatcher objects; replacing a
    controller slot with a wrapper around the dispatcher can feed the wrapper
    back into the same dispatcher and recurse. Plain test doubles and simple
    app objects are safe to wrap.
    """

    if callback is None:
        return False
    module_name = str(type(callback).__module__)
    return not module_name.startswith("trame_server.")


def _refresh_jobs(app: Any, handle: _PollHandle, *, force: bool = False) -> None:
    callback = getattr(app.ctrl, "refresh_generative_jobs", None)
    if callback is None:
        return
    now = time.monotonic()
    with handle.lock:
        if (
            not force
            and now - handle.last_refresh_at < GENERATIVE_REFRESH_COALESCE_SECONDS
        ):
            return
        handle.in_auto_refresh = True
    try:
        callback()
    except Exception:  # noqa: BLE001 - never crash the listener
        pass
    finally:
        with handle.lock:
            handle.in_auto_refresh = False
            handle.last_refresh_at = time.monotonic()


def _refresh_terminal_details(app: Any, handle: _PollHandle, summaries: list[Any]) -> None:
    selected_job_id = str(getattr(app.state, "generative_job_id", "") or "").strip()
    for summary in summaries:
        job_id = str(getattr(summary, "job_id", "") or "")
        state = str(getattr(summary, "state", "") or "")
        previous = handle.job_states.get(job_id)
        if (
            job_id
            and state in _DETAIL_REFRESH_STATES
            and previous is not None
            and previous != state
        ):
            _refresh_detail_panels(app, selected_job_id=selected_job_id, job_id=job_id)


def _refresh_detail_panels(app: Any, *, selected_job_id: str, job_id: str) -> None:
    if not selected_job_id or selected_job_id != job_id:
        return
    for callback_name in (
        "load_generative_log",
        "load_generative_frontier",
        "refresh_generative_frontier_view",
    ):
        callback = getattr(app.ctrl, callback_name, None)
        if callback is None:
            continue
        try:
            callback()
        except Exception:  # noqa: BLE001 - detail refresh is best-effort
            pass


def _remember_states(handle: _PollHandle, summaries: list[Any]) -> None:
    handle.job_states = {
        str(getattr(summary, "job_id", "")): str(getattr(summary, "state", ""))
        for summary in summaries
        if getattr(summary, "job_id", None)
    }


__all__ = [
    "GENERATIVE_POLL_IDLE_SECONDS",
    "GENERATIVE_POLL_RUNNING_SECONDS",
    "GENERATIVE_REFRESH_COALESCE_SECONDS",
    "compute_cadence_seconds",
    "has_in_flight_jobs",
    "install_generate_state_listener",
    "stop_generate_state_listener",
]
