"""End-to-end aiohttp route tests for /api/generative-jobs/* (RFC 0057 stage 2)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from kayakgen.services.generative_jobs import InProcessGenerativeJobManager
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


def test_post_cancel_and_resume_lifecycle(tmp_path: Path) -> None:
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

            cancel_resp = await client.post(
                f"/api/generative-jobs/{job_id}/cancel"
            )
            assert cancel_resp.status == 200
            cancel_payload = await cancel_resp.json()
            assert cancel_payload["cancellation_requested_at"] is not None

            _wait_for_terminal(manager, job_id)
            final = await (await client.get(f"/api/generative-jobs/{job_id}")).json()
            assert final["state"] in ("resumable", "succeeded")

            if final["state"] == "resumable":
                resume_resp = await client.post(
                    f"/api/generative-jobs/{job_id}/resume"
                )
                assert resume_resp.status == 200, await resume_resp.text()
                _wait_for_terminal(manager, job_id)
                resumed = await (
                    await client.get(f"/api/generative-jobs/{job_id}")
                ).json()
                assert resumed["state"] in ("succeeded", "resumable")
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

    # Submitting empty spec produces a clear status message, not an exception.
    web.state.generative_spec_json = ""
    web.ctrl.submit_generative_search()
    assert "Paste" in (web.state.generative_status or "")

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
