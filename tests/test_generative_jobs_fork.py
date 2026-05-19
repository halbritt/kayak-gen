"""Fork-with-new-seed primitive + route tests (RFC 0057 stage 4, D-12)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from kayakgen.services.generative_jobs import InProcessGenerativeJobManager
from kayakgen.services.generative_jobs_fork import (
    ForkError,
    fork_generative_job,
)
from kayakgen.ui.web.controllers import register_rest_routes


def _search_spec_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "fork-search",
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


def _sweep_spec_payload() -> dict[str, object]:
    return {
        "schema_version": "1",
        "name": "fork-sweep",
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


def test_fork_generative_job_clones_with_new_seed(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    source = mgr.start(
        spec_payload=_search_spec_payload(), job_kind="search"
    )
    mgr.join(source.job_id, timeout=120.0)
    final = mgr.get(source.job_id)
    assert final.state == "succeeded"

    forked = fork_generative_job(mgr, source.job_id, new_seed=999)

    assert forked.job_id != source.job_id
    assert forked.forked_from == source.job_id
    assert forked.job_kind == "search"

    forked_spec_path = tmp_path / forked.job_id / "spec.json"
    forked_spec = json.loads(forked_spec_path.read_text())
    assert forked_spec["algorithm"]["seed"] == 999
    # Source spec is unchanged.
    source_spec = json.loads((tmp_path / source.job_id / "spec.json").read_text())
    assert source_spec["algorithm"]["seed"] == 7

    mgr.join(forked.job_id, timeout=120.0)
    forked_final = mgr.get(forked.job_id)
    assert forked_final.state in ("succeeded", "failed", "resumable")
    # The forked_from marker survives the run-to-terminal lifecycle.
    assert forked_final.forked_from == source.job_id


def test_fork_sweep_raises_fork_error(tmp_path: Path) -> None:
    mgr = InProcessGenerativeJobManager(jobs_root=tmp_path)

    sweep = mgr.start(
        spec_payload=_sweep_spec_payload(), job_kind="sweep"
    )
    mgr.join(sweep.job_id, timeout=120.0)

    with pytest.raises(ForkError, match="sweep"):
        fork_generative_job(mgr, sweep.job_id, new_seed=999)


def test_fork_route_returns_201_with_new_job(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    source = manager.start(
        spec_payload=_search_spec_payload(), job_kind="search"
    )
    manager.join(source.job_id, timeout=120.0)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await client.post(
                f"/api/generative-jobs/{source.job_id}/fork",
                json={"new_seed": 999},
            )
            assert resp.status == 201, await resp.text()
            payload = await resp.json()
            assert payload["forked_from"] == source.job_id
            assert payload["job_id"] != source.job_id
            assert payload["result_semantics"] == "raw_unvalidated"
            assert payload["job_kind"] == "search"
        finally:
            await client.close()

    asyncio.run(scenario())


def test_fork_route_400_when_new_seed_missing(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    source = manager.start(
        spec_payload=_search_spec_payload(), job_kind="search"
    )
    manager.join(source.job_id, timeout=120.0)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            missing = await client.post(
                f"/api/generative-jobs/{source.job_id}/fork", json={}
            )
            assert missing.status == 400
            missing_payload = await missing.json()
            assert missing_payload["error"] == "missing_new_seed"

            wrong_type = await client.post(
                f"/api/generative-jobs/{source.job_id}/fork",
                json={"new_seed": "not-an-int"},
            )
            assert wrong_type.status == 400
            wrong_payload = await wrong_type.json()
            assert wrong_payload["error"] == "missing_new_seed"
        finally:
            await client.close()

    asyncio.run(scenario())


def test_fork_route_404_when_source_unknown(tmp_path: Path) -> None:
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
                "/api/generative-jobs/does-not-exist/fork",
                json={"new_seed": 42},
            )
            assert resp.status == 404
            payload = await resp.json()
            assert payload["error"] == "job_not_found"
        finally:
            await client.close()

    asyncio.run(scenario())


def test_fork_route_400_on_sweep_source(tmp_path: Path) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    sweep = manager.start(
        spec_payload=_sweep_spec_payload(), job_kind="sweep"
    )
    manager.join(sweep.job_id, timeout=120.0)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, generative_manager=manager)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            resp = await client.post(
                f"/api/generative-jobs/{sweep.job_id}/fork",
                json={"new_seed": 999},
            )
            assert resp.status == 400
            payload = await resp.json()
            assert payload["error"] == "cannot_fork_sweep"
        finally:
            await client.close()

    asyncio.run(scenario())
