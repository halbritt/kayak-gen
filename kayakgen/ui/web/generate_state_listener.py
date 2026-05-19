"""Auto-poll wiring for the Generate panel (RFC 0057 stage 4 / D-9).

The listener refreshes the Generate panel's jobs index on a cadence:

- ``GENERATIVE_POLL_RUNNING_SECONDS`` (default 1.0 s) while any job is in
  ``{queued, running}``.
- ``GENERATIVE_POLL_IDLE_SECONDS`` (default 10.0 s) otherwise.

It is cancellable: tearing down the app via :func:`stop_generate_state_listener`
sets a stop flag and the next tick exits cleanly. The listener never duplicates
a manual "Refresh Jobs" press — the underlying ``refresh_generative_jobs``
controller callback is idempotent (it just re-reads
:meth:`InProcessGenerativeJobManager.list`).

The listener is intentionally light: it does not poll if the Generate tab is
not the active review tab (``app.state.analysis_tab != "generate"``); the
operator only needs live updates while looking at the panel.
"""

from __future__ import annotations

import threading
from typing import Any

GENERATIVE_POLL_RUNNING_SECONDS = 1.0
"""Polling cadence while any job is in flight."""

GENERATIVE_POLL_IDLE_SECONDS = 10.0
"""Polling cadence while all jobs are terminal (or the panel is idle)."""

_IN_FLIGHT_STATES = frozenset({"queued", "running"})


class _PollHandle:
    """Tracks the listener thread and its stop flag for a single app."""

    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None


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
    app._generative_poll_handle = handle  # noqa: SLF001 - app extension hook

    def _tick() -> None:
        # First refresh happens immediately so the panel is non-empty.
        try:
            app.ctrl.refresh_generative_jobs()
        except Exception:  # noqa: BLE001 - never crash the listener
            pass

        while not handle.stop_event.is_set():
            cadence = _next_cadence(app, running_seconds, idle_seconds)
            if handle.stop_event.wait(timeout=cadence):
                return
            try:
                if _panel_visible(app):
                    app.ctrl.refresh_generative_jobs()
            except Exception:  # noqa: BLE001 - never crash the listener
                pass

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


def _panel_visible(app: Any) -> bool:
    """The Generate tab must be active for the poll to refresh.

    Lets the operator switch to another review tab without paying the
    1 s cadence.
    """

    try:
        return getattr(app.state, "analysis_tab", "") == "generate"
    except Exception:  # noqa: BLE001
        return False


def _next_cadence(app: Any, running_seconds: float, idle_seconds: float) -> float:
    manager = getattr(app, "_generative_manager", None)
    if manager is None:
        return idle_seconds
    try:
        summaries = manager.list()
    except Exception:  # noqa: BLE001
        return idle_seconds
    return compute_cadence_seconds(
        has_in_flight_jobs=has_in_flight_jobs(summaries),
        running_seconds=running_seconds,
        idle_seconds=idle_seconds,
    )


__all__ = [
    "GENERATIVE_POLL_IDLE_SECONDS",
    "GENERATIVE_POLL_RUNNING_SECONDS",
    "compute_cadence_seconds",
    "has_in_flight_jobs",
    "install_generate_state_listener",
    "stop_generate_state_listener",
]


