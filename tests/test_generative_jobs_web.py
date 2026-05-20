"""End-to-end aiohttp route tests for /api/generative-jobs/* (RFC 0057 stage 2)."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import pytest

from kayakgen.services.generative_jobs import (
    GenerativeJobSummary,
    InProcessGenerativeJobManager,
    SubprocessGenerativeJobManager,
)
from kayakgen.ui.web.controllers import register_rest_routes


def _sweep_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "web-sweep",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "variables": {
            "beam_wl_m": {"kind": "values", "values": [0.48, 0.50, 0.52]},
        },
        "evaluators": {"hydrostatics": True},
    }


def _search_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "web-search",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "search_space": {
            "beam_wl_m": {"kind": "uniform", "min": 0.46, "max": 0.54},
        },
        "algorithm": {
            "kind": "nsga2",
            "population_size": 4,
            "generations": 2,
            "seed": 7,
        },
        "objectives": [
            {"metric": "GM0_m", "direction": "max"},
            {"metric": "displaced_mass_kg", "direction": "min"},
        ],
        "constraints": [],
        "evaluators": {"hydrostatics": True},
        "budget": {"max_evaluations": 999},
    }


def _wait_for_terminal(
    manager: InProcessGenerativeJobManager, job_id: str, timeout: float = 120.0
) -> None:
    """Block until the manager's worker thread for ``job_id`` exits."""

    manager.join(job_id, timeout=timeout)


def _wait_for_realized_evaluation(
    manager: InProcessGenerativeJobManager,
    job_id: str,
    *,
    timeout: float = 10.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if manager.get(job_id).progress.realized_evaluations >= 1:
            return
        time.sleep(0.01)
    raise AssertionError("job did not emit a candidate before timeout")


def _controlled_cancel_runner(
    _spec: Any,
    _out_dir: str | Path,
    resume: bool = False,
    *,
    progress_sink: Any | None = None,
) -> object:
    assert resume is False
    assert progress_sink is not None
    progress_sink.candidate_completed(
        candidate_key="controlled-candidate",
        status="complete",
        generation=None,
        iteration=0,
        realized_evaluations=1,
    )
    progress_sink.checkpoint(
        generation=None,
        iteration=0,
        realized_evaluations=1,
    )
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if progress_sink.should_cancel():
            return object()
        time.sleep(0.01)
    raise AssertionError("controlled runner did not observe cancellation")


def test_post_generative_sweep_returns_201_and_persists(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await client.post(
                "/api/generative-jobs/sweep",
                json={"spec": _sweep_payload()},
            )
            payload = await resp.json()
            assert resp.status == 201, payload
            assert payload["job_kind"] == "sweep"
            assert payload["state"] in ("queued", "running", "succeeded")
            assert payload["result_semantics"] == "raw_unvalidated"
            job_id = payload["job_id"]

            _wait_for_terminal(manager, job_id)

            status = await (await client.get(f"/api/generative-jobs/{job_id}")).json()
            assert status["state"] == "succeeded"
            assert status["progress"]["realized_evaluations"] == 3
        finally:
            await client.close()

    asyncio.run(scenario())


def test_post_generative_search_and_frontier(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            create = await client.post(
                "/api/generative-jobs/search",
                json={"spec": _search_payload()},
            )
            assert create.status == 201, await create.text()
            payload = await create.json()
            job_id = payload["job_id"]

            _wait_for_terminal(manager, job_id)

            frontier_resp = await client.get(
                f"/api/generative-jobs/{job_id}/frontier"
            )
            assert frontier_resp.status == 200
            frontier = await frontier_resp.json()
            assert frontier["result_semantics"] == "raw_unvalidated"
            assert frontier["frontier_available"] is True
            assert frontier["frontier"], frontier
            row = frontier["frontier"][0]
            assert "candidate_key" in row
            assert "parameters" in row
            assert "summary" in row
        finally:
            await client.close()

    asyncio.run(scenario())


def test_get_generative_jobs_lists_summaries(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            create = await client.post(
                "/api/generative-jobs/sweep",
                json={"spec": _sweep_payload()},
            )
            job_id = (await create.json())["job_id"]
            _wait_for_terminal(manager, job_id)

            listing = await (await client.get("/api/generative-jobs")).json()
            assert listing["result_semantics"] == "raw_unvalidated"
            assert any(j["job_id"] == job_id for j in listing["jobs"])

            filtered = await (
                await client.get("/api/generative-jobs?state=succeeded&kind=sweep")
            ).json()
            assert all(j["state"] == "succeeded" for j in filtered["jobs"])
            assert all(j["job_kind"] == "sweep" for j in filtered["jobs"])
        finally:
            await client.close()

    asyncio.run(scenario())


def test_post_cancel_lifecycle_requires_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "kayakgen.search.sweep.run_sweep",
        _controlled_cancel_runner,
    )
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            payload = _sweep_payload()
            payload["variables"] = {  # type: ignore[index]
                "beam_wl_m": {
                    "kind": "values",
                    "values": [0.46 + 0.005 * i for i in range(40)],
                },
            }
            create = await client.post(
                "/api/generative-jobs/sweep", json={"spec": payload}
            )
            job_id = (await create.json())["job_id"]
            _wait_for_realized_evaluation(manager, job_id)

            cancel_resp = await client.post(
                f"/api/generative-jobs/{job_id}/cancel"
            )
            assert cancel_resp.status == 200
            cancel_payload = await cancel_resp.json()
            assert cancel_payload["cancellation_requested_at"] is not None

            _wait_for_terminal(manager, job_id)
            final = await (await client.get(f"/api/generative-jobs/{job_id}")).json()
            assert final["state"] == "resumable"
            assert final["error"]["kind"] == "cancelled_by_operator"
            assert final["resumable_from_checkpoint"] is True
        finally:
            await client.close()

    asyncio.run(scenario())


def test_get_log_returns_progress_lines(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            create = await client.post(
                "/api/generative-jobs/sweep", json={"spec": _sweep_payload()}
            )
            job_id = (await create.json())["job_id"]
            _wait_for_terminal(manager, job_id)

            log_resp = await client.get(f"/api/generative-jobs/{job_id}/log")
            assert log_resp.status == 200
            log_payload = await log_resp.json()
            assert log_payload["job_id"] == job_id
            assert "candidate " in log_payload["log"]
            assert log_payload["cursor"] >= len(log_payload["log"].encode("utf-8")) - 1

            tail_resp = await client.get(
                f"/api/generative-jobs/{job_id}/log?since={log_payload['cursor']}"
            )
            tail = await tail_resp.json()
            assert tail["log"] == ""
        finally:
            await client.close()

    asyncio.run(scenario())


def test_post_search_rejects_missing_spec(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await client.post("/api/generative-jobs/search", json={})
            assert resp.status == 400
            payload = await resp.json()
            assert payload["error"] == "missing_spec"
        finally:
            await client.close()

    asyncio.run(scenario())


def test_get_missing_job_returns_404(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await client.get("/api/generative-jobs/does-not-exist")
            assert resp.status == 404
            payload = await resp.json()
            assert payload["error"] == "job_not_found"
        finally:
            await client.close()

    asyncio.run(scenario())


def test_resume_succeeded_job_returns_409(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    job = manager.start(spec_payload=_sweep_payload(), job_kind="sweep")
    manager.join(job.job_id, timeout=120.0)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            current = await (
                await client.get(f"/api/generative-jobs/{job.job_id}")
            ).json()
            assert current["state"] == "succeeded"
            resp = await client.post(
                f"/api/generative-jobs/{job.job_id}/resume"
            )
            assert resp.status == 409
            payload = await resp.json()
            assert payload["error"] == "job_not_resumable"
        finally:
            await client.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "path",
    [
        "/api/generative-jobs",
        "/api/generative-jobs/search",
        "/api/generative-jobs/sweep",
    ],
)
def test_routes_registered_with_default_manager(tmp_path: Path, path: str) -> None:
    """The default manager is created lazily when none is passed."""

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_jobs_root=tmp_path / "jobs")
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            if path.endswith("/search") or path.endswith("/sweep"):
                resp = await client.post(path, json={})
                assert resp.status in (400, 422)
            else:
                resp = await client.get(path)
                assert resp.status == 200
        finally:
            await client.close()

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Trame Generate panel (RFC 0057 stage 2) — exercises controller callbacks.
# ---------------------------------------------------------------------------


def test_generate_panel_submit_and_refresh(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "KAYAKGEN_GENERATIVE_JOBS_ROOT", str(tmp_path / "jobs")
    )
    from kayakgen.model.hull import Hull
    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())
    assert "generate" in {tab["value"] for tab in __import__(
        "kayakgen.ui.web.app", fromlist=["REVIEW_TABS"]
    ).REVIEW_TABS}
    assert web.state.generative_jobs_root.endswith("jobs")
    assert "no generative jobs yet" not in (web.state.generative_status or "")

    # The primary form path can serialize to the raw JSON escape hatch.
    web.state.generative_spec_json = ""
    web.ctrl.apply_form_to_json()
    assert '"schema_version": "1"' in web.state.generative_spec_json
    assert "Form spec copied" in (web.state.generative_status or "")

    # Submitting an invalid JSON body is reported but never raises.
    web.state.generative_spec_json = "{not json"
    web.ctrl.submit_generative_sweep()
    assert "not valid JSON" in (web.state.generative_status or "")

    # Submitting a valid sweep spec drives the job to terminal state.
    payload = {
        "schema_version": "1",
        "name": "panel-sweep",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "variables": {
            "beam_wl_m": {"kind": "values", "values": [0.48, 0.50, 0.52]},
        },
        "evaluators": {"hydrostatics": True},
    }
    web.state.generative_spec_json = __import__("json").dumps(payload)
    web.ctrl.submit_generative_sweep()
    assert "Submitted sweep" in (web.state.generative_status or "")
    job_id = web.state.generative_job_id
    assert job_id

    web._generative_manager.join(job_id, timeout=120.0)

    web.ctrl.refresh_generative_jobs()
    assert any(job_id in line for line in web.state.generative_jobs_lines)

    web.ctrl.load_generative_log()
    assert any("candidate" in line for line in web.state.generative_log_lines)


def test_generate_panel_form_submit_uses_controller_callback(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "KAYAKGEN_GENERATIVE_JOBS_ROOT", str(tmp_path / "jobs")
    )
    from kayakgen.model.hull import Hull
    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())
    assert isinstance(web._generative_manager, SubprocessGenerativeJobManager)

    web.state.generative_spec_json = ""
    web.state.generative_job_kind = "sweep"
    web.state.generative_variables = [
        {
            "name": "beam_wl_m",
            "kind": "choice",
            "min": 0.0,
            "max": 0.0,
            "count": 0,
            "values": "0.48, 0.50",
        }
    ]
    web.ctrl.submit_generative_sweep()
    assert "Submitted sweep" in (web.state.generative_status or "")
    assert '"variables"' in web.state.generative_spec_json
    job_id = web.state.generative_job_id

    web._generative_manager.join(job_id, timeout=120.0)
    web.ctrl.refresh_generative_jobs()
    assert any(job_id in line for line in web.state.generative_jobs_lines)


def test_generate_panel_renders_stage4_sections_and_fork_buttons(
    tmp_path: Path, monkeypatch
) -> None:
    from kayakgen.model.hull import Hull
    from kayakgen.ui.web import app as app_module
    from kayakgen.ui.web.app import create_app
    from kayakgen.ui.web.generate_state_listener import stop_generate_state_listener

    calls: list[str] = []

    def fake_render_fork_button(app, *, job_summary):  # noqa: ANN001
        calls.append(job_summary["job_id"])
        return None

    class FakeManager:
        jobs_root = tmp_path / "jobs"

        def list(self, *args, **kwargs):  # noqa: ANN002, ANN003
            return [
                GenerativeJobSummary(
                    job_id="done-job",
                    job_kind="search",
                    spec_hash="abc",
                    state="succeeded",
                    output_dir=str(tmp_path / "out"),
                ),
                GenerativeJobSummary(
                    job_id="running-job",
                    job_kind="search",
                    spec_hash="def",
                    state="running",
                    output_dir=str(tmp_path / "out2"),
                ),
            ]

    monkeypatch.setattr(app_module, "render_fork_button", fake_render_fork_button)
    web = create_app(initial_hull=Hull(), generative_manager=FakeManager())
    try:
        assert calls == ["done-job"]
        assert hasattr(web.ctrl, "apply_form_to_json")
        assert hasattr(web.ctrl, "refresh_generative_frontier_view")
    finally:
        stop_generate_state_listener(web)


def test_generate_panel_cancel_and_resume_status_lines(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "KAYAKGEN_GENERATIVE_JOBS_ROOT", str(tmp_path / "jobs")
    )
    from kayakgen.model.hull import Hull
    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())

    # Empty job id triggers a status hint, not a crash.
    web.state.generative_job_id = ""
    web.ctrl.cancel_generative_job()
    assert "Enter a job id" in (web.state.generative_status or "")
    web.ctrl.resume_generative_job()
    assert "Enter a job id" in (web.state.generative_status or "")
