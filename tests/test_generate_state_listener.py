"""RFC 0057 stage 4 / D-9: Generate panel auto-poll listener tests."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from kayakgen.ui.web import generate_state_listener as listener_module
from kayakgen.ui.web.generate_state_listener import (
    GENERATIVE_POLL_IDLE_SECONDS,
    GENERATIVE_POLL_RUNNING_SECONDS,
    GENERATIVE_REFRESH_COALESCE_SECONDS,
    compute_cadence_seconds,
    has_in_flight_jobs,
    install_generate_state_listener,
    stop_generate_state_listener,
    tick_generate_state_listener,
)


@dataclass
class _StubSummary:
    state: str
    job_id: str = "job-1"


@dataclass
class _StubManager:
    summaries: list[_StubSummary] = field(default_factory=list)
    list_calls: int = 0

    def list(self) -> list[_StubSummary]:
        self.list_calls += 1
        return list(self.summaries)


@dataclass
class _StubState:
    analysis_tab: str = "generate"


class _StubCtrl:
    def __init__(self) -> None:
        self.refresh_calls = 0
        self.log_calls = 0
        self.frontier_calls = 0
        self.frontier_view_calls = 0

    def refresh_generative_jobs(self) -> None:
        self.refresh_calls += 1

    def load_generative_log(self) -> None:
        self.log_calls += 1

    def load_generative_frontier(self) -> None:
        self.frontier_calls += 1

    def refresh_generative_frontier_view(self) -> None:
        self.frontier_view_calls += 1


@dataclass
class _StubApp:
    state: _StubState = field(default_factory=_StubState)
    ctrl: _StubCtrl = field(default_factory=_StubCtrl)
    _generative_manager: Any = field(default_factory=_StubManager)
    _generative_poll_handle: Any = None


def test_compute_cadence_seconds_branches() -> None:
    assert compute_cadence_seconds(has_in_flight_jobs=True) == (
        GENERATIVE_POLL_RUNNING_SECONDS
    )
    assert compute_cadence_seconds(has_in_flight_jobs=False) == (
        GENERATIVE_POLL_IDLE_SECONDS
    )


def test_compute_cadence_seconds_honors_overrides() -> None:
    assert (
        compute_cadence_seconds(
            has_in_flight_jobs=True,
            running_seconds=0.25,
            idle_seconds=5.0,
        )
        == 0.25
    )
    assert (
        compute_cadence_seconds(
            has_in_flight_jobs=False,
            running_seconds=0.25,
            idle_seconds=5.0,
        )
        == 5.0
    )


def test_has_in_flight_jobs_states() -> None:
    assert has_in_flight_jobs([]) is False
    assert (
        has_in_flight_jobs([_StubSummary(state="succeeded")]) is False
    )
    assert has_in_flight_jobs([_StubSummary(state="queued")]) is True
    assert has_in_flight_jobs([_StubSummary(state="running")]) is True
    assert (
        has_in_flight_jobs(
            [_StubSummary(state="succeeded"), _StubSummary(state="running")]
        )
        is True
    )


def test_install_listener_triggers_first_refresh() -> None:
    app = _StubApp()
    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.5
    )
    # Allow the immediate first tick to fire.
    time.sleep(0.2)
    stop_generate_state_listener(app)

    assert app.ctrl.refresh_calls >= 1
    assert app._generative_poll_handle is None


def test_install_listener_running_cadence() -> None:
    """When in-flight jobs exist, the listener should refresh quickly."""

    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(state="running")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=5.0
    )
    time.sleep(0.3)
    stop_generate_state_listener(app)

    # At running cadence 0.05s + 0.3s of wall time we expect several refreshes.
    assert app.ctrl.refresh_calls >= 3


def test_install_listener_idle_cadence() -> None:
    """No in-flight jobs → listener should fall back to the idle cadence."""

    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(state="succeeded")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.4
    )
    time.sleep(0.25)
    stop_generate_state_listener(app)

    # 0.25 s of wall time at 0.4 s idle cadence should yield only the initial
    # tick — the second tick hasn't fired yet.
    assert app.ctrl.refresh_calls == 1


def test_listener_refreshes_terminal_detail_panels_once_on_transition() -> None:
    app = _StubApp()
    app.state.generative_job_id = "job-1"  # type: ignore[attr-defined]
    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="running")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    time.sleep(0.12)
    assert app.ctrl.log_calls == 0

    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="succeeded")]
    time.sleep(0.12)
    first_detail_counts = (
        app.ctrl.log_calls,
        app.ctrl.frontier_calls,
        app.ctrl.frontier_view_calls,
    )
    time.sleep(0.12)
    stop_generate_state_listener(app)

    assert first_detail_counts == (1, 1, 1)
    assert (
        app.ctrl.log_calls,
        app.ctrl.frontier_calls,
        app.ctrl.frontier_view_calls,
    ) == first_detail_counts


def test_listener_does_not_refresh_other_job_detail_panel() -> None:
    app = _StubApp()
    app.state.generative_job_id = "job-2"  # type: ignore[attr-defined]
    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="running")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    time.sleep(0.12)
    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="failed")]
    time.sleep(0.12)
    stop_generate_state_listener(app)

    assert app.ctrl.log_calls == 0
    assert app.ctrl.frontier_calls == 0
    assert app.ctrl.frontier_view_calls == 0


def test_listener_skips_detail_refresh_without_selected_job() -> None:
    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="running")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    time.sleep(0.12)
    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="resumable")]
    time.sleep(0.12)
    stop_generate_state_listener(app)

    assert app.ctrl.log_calls == 0
    assert app.ctrl.frontier_calls == 0
    assert app.ctrl.frontier_view_calls == 0


def test_stop_listener_is_idempotent() -> None:
    app = _StubApp()
    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    stop_generate_state_listener(app)
    stop_generate_state_listener(app)  # idempotent


def test_reinstall_listener_stops_prior_thread() -> None:
    app = _StubApp()
    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    first_handle = app._generative_poll_handle
    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    second_handle = app._generative_poll_handle

    assert first_handle is not second_handle
    stop_generate_state_listener(app)


def test_listener_coalesces_nearby_manual_refresh() -> None:
    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(state="running")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    time.sleep(0.08)
    app.ctrl.refresh_generative_jobs()
    calls_after_manual = app.ctrl.refresh_calls
    time.sleep(0.03)
    stop_generate_state_listener(app)

    assert app.ctrl.refresh_calls == calls_after_manual


@pytest.mark.parametrize("manager_raises", [True, False])
def test_listener_survives_manager_exception(manager_raises: bool) -> None:
    """A manager that raises during list() must not crash the listener."""

    app = _StubApp()
    if manager_raises:
        class _ExplodingManager:
            def list(self) -> list[_StubSummary]:
                raise RuntimeError("boom")

        app._generative_manager = _ExplodingManager()

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    time.sleep(0.15)
    stop_generate_state_listener(app)

    # Listener still ticked at least once even though the manager raised.
    assert app.ctrl.refresh_calls >= 1


# ---------------------------------------------------------------------------
# RFC 0058 workflow 0056 / D-16, D-17: stepped-clock seam coverage.
#
# These variants exercise the same observable behavior as the wall-clock
# tests above, but they drive the listener synchronously via
# `tick_generate_state_listener` and monkeypatch `time.sleep` to raise. That
# guards against an accidental wall-clock sleep slipping into the stepped
# code path: if the seam ever calls `time.sleep`, the test fails loudly.
# The original wall-clock tests are intentionally preserved so the seam can
# be validated against current behavior.
# ---------------------------------------------------------------------------


class _SteppingClock:
    """Deterministic clock returning increasing values per call."""

    def __init__(self, start: float = 0.0, step: float = 0.0) -> None:
        self.now = float(start)
        self.step = float(step)

    def __call__(self) -> float:
        value = self.now
        self.now += self.step
        return value


def _raise_on_sleep(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("time.sleep must not be called under the stepped clock")


def _ban_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any `time.sleep` call from the listener module or its callers fail."""

    monkeypatch.setattr(listener_module.time, "sleep", _raise_on_sleep)


def test_stepped_clock_install_does_not_start_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    _ban_sleep(monkeypatch)
    app = _StubApp()
    clock = _SteppingClock(step=0.1)
    install_generate_state_listener(
        app,
        running_seconds=0.05,
        idle_seconds=0.5,
        time_provider=clock,
        clock_step=0.05,
    )
    handle = app._generative_poll_handle
    assert handle is not None
    assert handle.thread is None
    # No work runs until the test ticks the listener.
    assert app.ctrl.refresh_calls == 0
    stop_generate_state_listener(app)


def test_stepped_clock_running_cadence_refreshes_each_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With in-flight jobs, every stepped tick refreshes (modulo coalesce)."""

    _ban_sleep(monkeypatch)
    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(state="running")]
    # Step well past the coalesce window so consecutive ticks all refresh.
    clock = _SteppingClock(step=GENERATIVE_REFRESH_COALESCE_SECONDS * 4)
    install_generate_state_listener(
        app,
        running_seconds=0.05,
        idle_seconds=5.0,
        time_provider=clock,
        clock_step=0.05,
    )
    tick_generate_state_listener(app, iterations=3)
    stop_generate_state_listener(app)

    assert app.ctrl.refresh_calls == 3
    assert app._generative_manager.list_calls == 3


def test_stepped_clock_idle_cadence_refreshes_each_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No in-flight jobs: ticks still drive a refresh each (no real sleep)."""

    _ban_sleep(monkeypatch)
    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(state="succeeded")]
    clock = _SteppingClock(step=GENERATIVE_REFRESH_COALESCE_SECONDS * 4)
    install_generate_state_listener(
        app,
        running_seconds=0.05,
        # An aggressively large idle cadence would block a wall-clock run for
        # ages; the stepped seam ignores it because it never sleeps.
        idle_seconds=60.0,
        time_provider=clock,
        clock_step=0.05,
    )
    tick_generate_state_listener(app, iterations=2)
    stop_generate_state_listener(app)

    assert app.ctrl.refresh_calls == 2


def test_stepped_clock_listener_refreshes_terminal_detail_panels_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ban_sleep(monkeypatch)
    app = _StubApp()
    app.state.generative_job_id = "job-1"  # type: ignore[attr-defined]
    app._generative_manager.summaries = [_StubSummary(job_id="job-1", state="running")]
    clock = _SteppingClock(step=GENERATIVE_REFRESH_COALESCE_SECONDS * 4)
    install_generate_state_listener(
        app,
        running_seconds=0.05,
        idle_seconds=0.05,
        time_provider=clock,
        clock_step=0.05,
    )

    tick_generate_state_listener(app, iterations=2)
    assert app.ctrl.log_calls == 0

    app._generative_manager.summaries = [
        _StubSummary(job_id="job-1", state="succeeded")
    ]
    tick_generate_state_listener(app, iterations=1)
    first_detail_counts = (
        app.ctrl.log_calls,
        app.ctrl.frontier_calls,
        app.ctrl.frontier_view_calls,
    )

    # A second tick on the same terminal state must not re-fire detail refresh.
    tick_generate_state_listener(app, iterations=2)
    stop_generate_state_listener(app)

    assert first_detail_counts == (1, 1, 1)
    assert (
        app.ctrl.log_calls,
        app.ctrl.frontier_calls,
        app.ctrl.frontier_view_calls,
    ) == first_detail_counts


def test_stepped_clock_listener_coalesces_nearby_manual_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual refresh + immediate auto tick collapses to a single callback."""

    _ban_sleep(monkeypatch)
    app = _StubApp()
    app._generative_manager.summaries = [_StubSummary(state="running")]
    # Frozen clock: every read returns the same value, so the coalesce window
    # always swallows the second refresh attempt.
    clock = _SteppingClock(start=100.0, step=0.0)
    install_generate_state_listener(
        app,
        running_seconds=0.05,
        idle_seconds=0.05,
        time_provider=clock,
        clock_step=0.0,
    )

    tick_generate_state_listener(app, iterations=1)
    after_first_tick = app.ctrl.refresh_calls

    app.ctrl.refresh_generative_jobs()  # manual press
    after_manual = app.ctrl.refresh_calls

    tick_generate_state_listener(app, iterations=1)
    stop_generate_state_listener(app)

    assert after_first_tick == 1
    assert after_manual == 2
    # Auto tick was within the coalesce window of the manual press.
    assert app.ctrl.refresh_calls == after_manual


def test_stepped_clock_reinstall_replaces_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ban_sleep(monkeypatch)
    app = _StubApp()
    clock = _SteppingClock(step=0.1)
    install_generate_state_listener(
        app,
        running_seconds=0.05,
        idle_seconds=0.05,
        time_provider=clock,
        clock_step=0.05,
    )
    first_handle = app._generative_poll_handle

    install_generate_state_listener(
        app,
        running_seconds=0.05,
        idle_seconds=0.05,
        time_provider=clock,
        clock_step=0.05,
    )
    second_handle = app._generative_poll_handle

    assert first_handle is not second_handle
    assert second_handle.thread is None  # stepped mode never starts a thread
    stop_generate_state_listener(app)
    assert app._generative_poll_handle is None


def test_tick_is_noop_when_listener_uses_wall_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`tick_generate_state_listener` only drives the stepped-clock seam."""

    _ban_sleep(monkeypatch)
    app = _StubApp()
    # No clock_step → wall-clock mode → a thread would normally start. We
    # immediately stop it so the thread never runs a tick (no sleep involved).
    install_generate_state_listener(
        app,
        running_seconds=60.0,
        idle_seconds=60.0,
    )
    stop_generate_state_listener(app)

    app2 = _StubApp()
    # Wall-clock install again, but tick should refuse to advance it.
    install_generate_state_listener(
        app2,
        running_seconds=60.0,
        idle_seconds=60.0,
    )
    tick_generate_state_listener(app2, iterations=5)
    stop_generate_state_listener(app2)
    # No refresh other than whatever the (now-stopped) wall-clock thread had
    # time to run. The tick call itself contributed nothing.
    assert app2.ctrl.refresh_calls <= 1
