"""RFC 0057 stage 4 / D-9: Generate panel auto-poll listener tests."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from kayakgen.ui.web.generate_state_listener import (
    GENERATIVE_POLL_IDLE_SECONDS,
    GENERATIVE_POLL_RUNNING_SECONDS,
    compute_cadence_seconds,
    has_in_flight_jobs,
    install_generate_state_listener,
    stop_generate_state_listener,
)


@dataclass
class _StubSummary:
    state: str


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

    def refresh_generative_jobs(self) -> None:
        self.refresh_calls += 1


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


def test_install_listener_idle_when_panel_hidden() -> None:
    """Listener skips refresh when the panel tab is not active."""

    app = _StubApp(state=_StubState(analysis_tab="analysis"))
    app._generative_manager.summaries = [_StubSummary(state="running")]

    install_generate_state_listener(
        app, running_seconds=0.05, idle_seconds=0.05
    )
    time.sleep(0.2)
    stop_generate_state_listener(app)

    # The initial tick fires regardless; subsequent ticks are skipped while
    # the panel is hidden.
    assert app.ctrl.refresh_calls == 1


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
