"""RFC 0008 web frontend — state round-trip and core-parity checks.

These tests exercise the headless pieces (state encoding, controller
helpers, CLI wiring) without standing up a Trame server. The full Trame
app is exercised manually via `kayakgen serve`; a Playwright smoke test
is reserved for CI.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from kayakgen.eval.cfd.jobs import CFD_FIXTURE_RESULTS_WARNING
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.mesh_package import watertight_solid_profile, write_mesh_package
from kayakgen.model.advisory import design_advisory
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.model.distribution_v2 import (
    DistributionV2Spec,
    KeyPointsDistribution,
    PolynomialDistribution,
)


pytest.importorskip("trame", reason="kayakgen[web] not installed")


from kayakgen.ui.web.controllers import metrics_from_state, stl_bytes_for_part  # noqa: E402
from kayakgen.ui.web.controllers import (  # noqa: E402
    CFD_RAW_RESULTS_WARNING,
    CfdWebError,
    CfdWebStore,
    HullStore,
    analysis_view_model,
    analysis_lines_from_state,
    candidate_state_from_report_json,
    clamp_beam_wl_state,
    comparison_view_model_from_json,
    cfd_error_lines_from_payload,
    cfd_job_status_payload,
    cfd_raw_result_lines_from_payload,
    cfd_status_lines_from_payload,
    evaluation_payload,
    hull_from_web_state,
    job_stub_payload,
    load_hull_payload,
    register_rest_routes,
    store_hull_payload,
    validation_error_payload,
)
from kayakgen.ui.web.state import (  # noqa: E402
    HULL_STATE_FIELDS,
    decode_hull_query,
    encode_hull_query,
    hull_from_query_string,
    hull_from_state_dict,
    state_dict_from_hull,
)


def _distribution_v2_hull() -> Hull:
    spec = DistributionV2Spec(
        waterline_half_breadth=KeyPointsDistribution(
            knots=[(-1.0, 0.0), (-0.5, 0.20), (0.0, 0.275), (0.5, 0.20), (1.0, 0.0)]
        ),
        draft_profile=KeyPointsDistribution(
            knots=[(-1.0, 0.0), (-0.5, 0.10), (0.0, 0.12), (0.5, 0.10), (1.0, 0.0)]
        ),
        section_area_curve=PolynomialDistribution(coefficients=[0.04, 0.0, -0.04]),
        deck_freeboard=KeyPointsDistribution(
            knots=[(-1.0, 0.04), (0.0, 0.11), (1.0, 0.04)]
        ),
        rocker=KeyPointsDistribution(
            knots=[(-1.0, 0.0), (-0.5, 0.0), (0.0, 0.0), (0.5, 0.0), (1.0, 0.0)]
        ),
        cross_section_family="round",
        deadrise_deg=0.0,
    )
    return Hull(
        name="v2-web",
        geometry_kind="distribution_v2",
        distribution_v2=spec,
    )


def test_state_dict_round_trip_via_hull() -> None:
    hull = Hull(name="touring", length_m=5.0, beam_oa_m=0.58, beam_wl_m=0.53)
    state = state_dict_from_hull(hull)
    back = hull_from_state_dict(state)
    assert "stern_rake" in state
    assert back == hull


def test_state_dict_round_trip_preserves_distribution_v2_payload() -> None:
    hull = _distribution_v2_hull()

    state = state_dict_from_hull(hull)
    back = hull_from_state_dict(state)

    assert back == hull
    assert state["loaded_hull_payload"]["geometry_kind"] == "distribution_v2"
    assert state["loaded_hull_payload"]["distribution_v2"]["cross_section_family"] == "round"


def test_hull_from_web_state_converts_unsupported_hull_after_slider_edit() -> None:
    hull = _distribution_v2_hull()
    state = state_dict_from_hull(hull)

    assert hull_from_web_state(state) == hull

    state["length_m"] = hull.length_m + 0.1
    converted = hull_from_web_state(state)

    assert converted.geometry_kind == "lofted"
    assert converted.distribution_v2 is None
    assert converted.length_m == pytest.approx(hull.length_m + 0.1)


def test_url_query_round_trip_bit_equal() -> None:
    hull = Hull(name="elite", length_m=6.1, beam_oa_m=0.43, beam_wl_m=0.40, Cp=0.58, bow_rake=0.0)
    encoded = encode_hull_query(hull)
    assert isinstance(encoded, str) and len(encoded) > 0
    decoded = decode_hull_query(encoded)
    assert decoded == hull
    assert decoded.hash() == hull.hash()


def test_state_dict_drops_unknown_keys() -> None:
    state = {field: getattr(Hull(), field) for field in HULL_STATE_FIELDS}
    state["target_speed_kt"] = 4.2  # viewing param, not a Hull field
    state["junk"] = "ignored"
    hull = hull_from_state_dict(state)
    assert hull == Hull()


def test_metrics_match_evaluate_hydrostatics() -> None:
    hull = Hull()
    state = state_dict_from_hull(hull) | {"target_speed_kt": 3.5}
    m = metrics_from_state(state, stations=60)
    h = evaluate_hydrostatics(hull, stations=60)
    assert abs(m["displaced_mass_kg"] - h.displaced_mass_kg) < 1e-6
    assert abs(m["wetted_surface_m2"] - h.wetted_surface_m2) < 1e-6
    assert abs(m["l_over_bwl"] - hull.length_m / hull.beam_oa_m) < 1e-6
    assert m["advisory_warnings"] == ()
    assert m["Rt_N"] == m["Rv_N"] + m["Rw_N"]
    assert m["resistance_claim_state"] == "uncalibrated_comparative"
    assert "comparative_filter" in m["resistance_accepted_uses"]
    assert "not_final_performance_prediction" in m["resistance_warnings"]


def test_compact_metrics_lines_include_resistance_claim_warning() -> None:
    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())

    assert any("Total" in line and "N" in line for line in web.state.metrics_lines)
    assert any("uncalibrated_comparative" in line for line in web.state.metrics_lines)
    assert any(
        "raw comparative filter" in line and "not final prediction" in line
        for line in web.state.metrics_lines
    )


def test_analysis_lines_include_units_and_resistance_warnings() -> None:
    state = state_dict_from_hull(Hull()) | {"target_speed_kt": 3.5}

    lines = analysis_lines_from_state(state)

    assert "Hydrostatics" in lines
    assert any("Displacement" in line and "kg" in line for line in lines)
    assert any("Resistance curve" in line for line in lines)
    assert any("kt" in line and "Rt N" in line for line in lines)
    assert "  comparative_filter_only" in lines


def test_analysis_model_keeps_design_and_resistance_warnings_separate() -> None:
    state = state_dict_from_hull(Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65))

    model = analysis_view_model(state)

    assert model["design_warnings"] == ["L/B_wl below touring guidance"]
    assert "not_final_performance_prediction" in model["resistance_warnings"]
    assert model["design_validity"]["findings"][0]["code"] == CODE_L_BWL_LOW


def test_web_state_clamps_beam_wl_before_metrics_and_validation() -> None:
    state = state_dict_from_hull(Hull(beam_oa_m=0.55, beam_wl_m=0.50)) | {
        "beam_wl_m": 0.80,
        "target_speed_kt": 3.5,
    }
    normalized = clamp_beam_wl_state(state)
    assert normalized["beam_wl_m"] == 0.55
    assert hull_from_web_state(state).beam_wl_m == 0.55
    metrics = metrics_from_state(state, stations=40)
    assert abs(metrics["l_over_bwl"] - Hull().length_m / 0.55) < 1e-6


def test_web_metrics_design_warnings_use_shared_validity_report() -> None:
    hull = Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65)
    state = state_dict_from_hull(hull) | {"target_speed_kt": 3.5}

    metrics = metrics_from_state(state, stations=40)
    advisory = design_advisory(hull)

    assert metrics["advisory_warnings"] == advisory.warnings
    assert metrics["design_warning_codes"] == advisory.design_validity.codes()
    assert metrics["design_validity"]["findings"][0]["code"] == CODE_L_BWL_LOW


def test_validation_error_payload_is_stable_and_controlled() -> None:
    with pytest.raises(Exception) as exc_info:
        hull_from_web_state(state_dict_from_hull(Hull()) | {"length_m": -1.0})
    payload = validation_error_payload(exc_info.value)
    assert payload["error"] == "invalid_hull_state"
    assert payload["details"][0]["field"] == "length_m"
    assert payload["details"][0]["type"] == "greater_than"
    assert "validation error" not in payload["details"][0]["message"].lower()


def test_export_stl_yields_binary() -> None:
    state = state_dict_from_hull(Hull()) | {"target_speed_kt": 3.5}
    blob = stl_bytes_for_part(state, "hull")
    assert isinstance(blob, (bytes, bytearray))
    assert len(blob) >= 84  # at least the binary STL header + count
    import struct

    n_tris = struct.unpack("<I", blob[80:84])[0]
    assert len(blob) == 84 + n_tris * 50


def test_create_app_does_not_start_server() -> None:
    """Smoke: instantiate the app factory without binding a port."""
    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())
    # State should reflect the initial hull
    assert web.state.length_m == 4.5
    assert web.state.target_speed_kt == 3.5
    assert "unavailable-open-wetted-surface" in web.state.cfd_profile_options
    assert any(CFD_RAW_RESULTS_WARNING in line for line in web.state.cfd_status_lines)
    # Reset clears overrides
    web.state.length_m = 5.0
    web._reset()
    assert web.state.length_m == 4.5
    assert web.state.analysis_tab == "analysis"
    assert any("Hydrostatics" in line for line in web.state.analysis_lines)


def test_comparison_view_model_preserves_candidates_and_warnings(tmp_path) -> None:
    from kayakgen.search.compare import build_comparison_report
    from kayakgen.search.sweep import SweepSpec, run_sweep

    spec = SweepSpec(
        name="web-compare",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )
    run_sweep(spec, tmp_path)
    report = build_comparison_report(tmp_path)

    model = comparison_view_model_from_json(report.model_dump_json())

    assert model["status"] == "2 candidates, 1 pareto"
    assert model["candidate_options"] == [0, 1]
    assert any("GM0_m (max)" in line for line in model["lines"])
    assert any("Candidates" in line for line in model["lines"])


def test_comparison_view_model_reports_invalid_json() -> None:
    model = comparison_view_model_from_json("{not-json")

    assert model["status"].startswith("Invalid comparison report:")
    assert model["lines"] == []
    assert model["candidate_options"] == []


def test_candidate_state_reload_applies_parameters_only(tmp_path) -> None:
    from kayakgen.search.compare import build_comparison_report
    from kayakgen.search.sweep import SweepSpec, run_sweep

    spec = SweepSpec(
        name="web-reload",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50]}},
    )
    run_sweep(spec, tmp_path)
    report = build_comparison_report(tmp_path)
    current = state_dict_from_hull(Hull(length_m=5.2, beam_oa_m=0.60, beam_wl_m=0.60))

    updated = candidate_state_from_report_json(report.model_dump_json(), 0, current)

    assert updated["length_m"] == 5.2
    assert updated["beam_oa_m"] == 0.60
    assert updated["beam_wl_m"] == 0.50


def test_create_app_loads_comparison_and_applies_candidate(tmp_path) -> None:
    from kayakgen.search.compare import build_comparison_report
    from kayakgen.search.sweep import SweepSpec, run_sweep
    from kayakgen.ui.web.app import create_app

    spec = SweepSpec(
        name="web-app-reload",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50]}},
    )
    run_sweep(spec, tmp_path)
    report = build_comparison_report(tmp_path)
    web = create_app(initial_hull=Hull(beam_oa_m=0.60, beam_wl_m=0.60))

    web.state.comparison_json = report.model_dump_json()
    web._load_comparison()
    web._load_selected_candidate()

    assert web.state.comparison_status == "Applied sweep parameters for candidate 0"
    assert web.state.beam_oa_m == 0.60
    assert web.state.beam_wl_m == 0.50
    # The stage 1/2 sweep run does not attach high-angle GZ artifacts, so the
    # stage 3 display section stays hidden for a default sweep -- preserving
    # the "hide by default" contract from RFC 0043 stage 3.
    assert web.state.high_angle_gz_section_visible is False
    assert web.state.high_angle_gz_section_html == ""


def test_create_app_surfaces_high_angle_gz_section_when_columns_present() -> None:
    """End-to-end wiring: a stage 3 report drives the Trame state visibly."""

    from kayakgen.cli.high_angle_gz import build_high_angle_gz_block
    from kayakgen.eval.contract import LoadCase
    from kayakgen.search.compare import (
        CandidateSummary,
        ComparisonReport,
        HighAngleGzDisplay,
    )
    from kayakgen.ui.web.app import create_app

    block = build_high_angle_gz_block(
        Hull(),
        LoadCase(),
        heel_grid_deg=[0.0, 5.0, 10.0, 15.0, 20.0],
    )
    summary_block = block.get("summary") or {}
    display = HighAngleGzDisplay(
        available=bool(block.get("available")),
        body_profile=str(block.get("body_profile", "")),
        result_semantics=str(block.get("result_semantics", "")),
        method=block.get("method"),
        body_ref=block.get("body_ref"),
        body_type=block.get("body_type"),
        body_diagnostic_ref=block.get("body_diagnostic_ref"),
        heel_grid_deg=list(block.get("heel_grid_deg", [])),
        max_gz_m=summary_block.get("max_gz"),
        heel_at_max_gz_deg=summary_block.get("heel_at_max_gz"),
        range_positive_stability_deg=summary_block.get("range_positive_stability_deg"),
        warnings=list(block.get("warnings", [])),
        assumptions=list(block.get("assumptions", [])),
    )
    report = ComparisonReport(
        run_name="stage3-web-app-fixture",
        spec_hash="stage3-web-app-fixture",
        report_kind="exploratory_frontier",
        objectives=[],
        pareto_front_keys=[],
        candidate_summaries=[
            CandidateSummary(
                candidate_index=0,
                candidate_key="cand-a",
                status="complete",
                hull_hash=Hull().hash(),
                high_angle_gz_display=display,
            )
        ],
        high_angle_gz_columns=True,
    )

    web = create_app(initial_hull=Hull())
    web.state.comparison_json = report.model_dump_json()
    web._load_comparison()

    assert web.state.high_angle_gz_section_visible is True
    section_html = web.state.high_angle_gz_section_html
    assert "High-angle GZ (display-only)" in section_html
    assert (
        "Unvalidated hydrostatic comparison; not safety, seaworthiness, "
        "calibrated, validated, or final-prediction claim"
    ) in section_html
    assert "body: generated_hull_plus_deck_closed_body_v1" in section_html
    assert "cand-a" in section_html


def test_create_app_renders_nonblank_offscreen_scene() -> None:
    """Headless visual smoke for the VTK scene used by VtkRemoteView."""
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    from kayakgen.ui.web.app import create_app

    web = create_app(initial_hull=Hull())
    assert web._renderer.GetActors().GetNumberOfItems() == 2
    assert web._render_window.GetInteractor() is not None

    web._render_window.Render()
    image_filter = vtk.vtkWindowToImageFilter()
    image_filter.SetInput(web._render_window)
    image_filter.Update()

    image = image_filter.GetOutput()
    assert image.GetDimensions()[0:2] == (300, 300)
    pixels = vtk_to_numpy(image.GetPointData().GetScalars())
    assert pixels.size > 0
    assert int(pixels.max()) > int(pixels.min())


def test_load_from_query_seeds_state() -> None:
    from kayakgen.ui.web.app import create_app

    custom = Hull(
        name="touring",
        length_m=5.0,
        beam_oa_m=0.58,
        beam_wl_m=0.53,
        Cp=0.54,
        draft_m=0.12,
    )
    web = create_app()
    web.load_from_query(encode_hull_query(custom))
    assert web.state.name == "touring"
    assert web.state.length_m == 5.0
    assert abs(web.state.beam_wl_m - 0.53) < 1e-9
    assert any("Hydrostatics" in line for line in web.state.analysis_lines)


def test_load_and_share_preserve_distribution_v2_until_slider_edit() -> None:
    from kayakgen.ui.web.app import create_app

    hull = _distribution_v2_hull()
    web = create_app(initial_hull=hull)

    assert web._current_hull() == hull
    assert web.state.unsupported_hull_editing_visible is True
    assert "preserved" in web.state.unsupported_hull_editing_warning.lower()

    web._share_url()
    shared_before_edit = hull_from_query_string(web.state.share_url)
    assert shared_before_edit == hull

    web.state.length_m = hull.length_m + 0.1
    web._on_hull_param_change()

    converted = web._current_hull()
    assert converted.geometry_kind == "lofted"
    assert converted.distribution_v2 is None
    assert converted.length_m == pytest.approx(hull.length_m + 0.1)
    assert "converted" in web.state.unsupported_hull_editing_warning.lower()

    web._share_url()
    shared_after_edit = hull_from_query_string(web.state.share_url)
    assert shared_after_edit is not None
    assert shared_after_edit.geometry_kind == "lofted"


def test_create_app_accepts_initial_query() -> None:
    from kayakgen.ui.web.app import create_app

    custom = Hull(
        name="elite",
        length_m=6.1,
        beam_oa_m=0.43,
        beam_wl_m=0.40,
        draft_m=0.11,
        Cp=0.58,
    )
    web = create_app(initial_query=f"?hull={encode_hull_query(custom)}")
    assert web.state.name == "elite"
    assert web.state.length_m == 6.1
    assert web.state.beam_oa_m == 0.43
    assert web.state.beam_wl_m == 0.40
    assert web.state.draft_m == 0.11
    assert web.state.Cp == 0.58
    assert any("Hydrostatics" in line for line in web.state.analysis_lines)


def test_query_string_decoder_handles_missing_hull() -> None:
    assert hull_from_query_string("?x=1") is None


def test_rest_payload_helpers() -> None:
    state = state_dict_from_hull(Hull()) | {"target_speed_kt": 3.5}
    evaluation = evaluation_payload(state)
    assert evaluation["hull_hash"] == Hull().hash()
    assert evaluation["design_validity"]["findings"] == []
    store = HullStore()
    stored = store_hull_payload(state, store)
    assert load_hull_payload(stored["id"], store)["schema_version"] == "1"
    stub = job_stub_payload()
    assert stub["error"].startswith("heavy CFD")
    assert stub["result_semantics"] == "raw_unvalidated"
    assert stub["warning"] == CFD_RAW_RESULTS_WARNING


def test_register_rest_routes_on_router_like_app() -> None:
    class Router:
        def __init__(self) -> None:
            self.routes: list[tuple[str, str]] = []

        def add_post(self, path, _handler) -> None:
            self.routes.append(("POST", path))

        def add_get(self, path, _handler) -> None:
            self.routes.append(("GET", path))

    class App:
        def __init__(self) -> None:
            self.router = Router()

    app = App()
    register_rest_routes(app)
    assert ("POST", "/api/evaluate") in app.router.routes
    assert ("POST", "/api/stl") in app.router.routes
    assert ("POST", "/api/hulls") in app.router.routes
    assert ("GET", "/api/hulls/{id}") in app.router.routes
    assert ("POST", "/api/jobs") in app.router.routes
    assert ("GET", "/api/jobs/{id}") in app.router.routes
    assert ("GET", "/api/cfd/profiles") in app.router.routes
    assert ("POST", "/api/cfd/jobs") in app.router.routes
    assert ("GET", "/api/cfd/jobs/{job_id}") in app.router.routes
    assert ("POST", "/api/cfd/jobs/{job_id}/run") in app.router.routes
    assert ("GET", "/api/cfd/jobs/{job_id}/logs") in app.router.routes
    assert ("GET", "/api/cfd/jobs/{job_id}/raw-result") in app.router.routes
    assert ("GET", "/api/generative-jobs") in app.router.routes
    assert ("POST", "/api/generative-jobs/search") in app.router.routes
    assert ("POST", "/api/generative-jobs/sweep") in app.router.routes
    assert ("GET", "/api/generative-jobs/{job_id}") in app.router.routes
    assert ("GET", "/api/generative-jobs/{job_id}/log") in app.router.routes
    assert ("GET", "/api/generative-jobs/{job_id}/frontier") in app.router.routes
    assert ("POST", "/api/generative-jobs/{job_id}/cancel") in app.router.routes
    assert ("POST", "/api/generative-jobs/{job_id}/resume") in app.router.routes


def test_cfd_routes_prepare_status_run_and_raw_absence(tmp_path) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, cfd_store=CfdWebStore(tmp_path / "jobs"))
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            profiles_response = await client.get("/api/cfd/profiles")
            profiles = await profiles_response.json()
            assert profiles_response.status == 200
            assert profiles["warning"] == CFD_RAW_RESULTS_WARNING
            assert "unavailable-open-wetted-surface" in {
                profile["name"] for profile in profiles["profiles"]
            }

            create_response = await client.post(
                "/api/cfd/jobs",
                json={
                    "mesh_package_ref": str(mesh_dir),
                    "solver_profile": "unavailable-open-wetted-surface",
                    "speed_mps": 2.4,
                },
            )
            created = await create_response.json()
            assert create_response.status == 201
            assert created["run"]["status"] == "queued"
            assert created["result_semantics"] == "raw_unvalidated"
            assert created["warning"] == CFD_RAW_RESULTS_WARNING

            job_id = created["job_id"]
            status_response = await client.get(f"/api/cfd/jobs/{job_id}")
            status = await status_response.json()
            assert status_response.status == 200
            assert status["run"]["status"] == "queued"

            run_response = await client.post(f"/api/cfd/jobs/{job_id}/run")
            run = await run_response.json()
            assert run_response.status == 200
            assert run["run"]["status"] == "unavailable"
            assert run["run"]["error_kind"] == "solver_unavailable"
            assert run["warning"] == CFD_RAW_RESULTS_WARNING

            logs_response = await client.get(f"/api/cfd/jobs/{job_id}/logs")
            logs = await logs_response.json()
            assert logs_response.status == 404
            assert logs["error"] == "logs_not_found"
            assert logs["warning"] == CFD_RAW_RESULTS_WARNING

            raw_response = await client.get(f"/api/cfd/jobs/{job_id}/raw-result")
            raw = await raw_response.json()
            assert raw_response.status == 404
            assert raw["error"] == "raw_result_not_found"
            assert raw["warning"] == CFD_RAW_RESULTS_WARNING

            (tmp_path / "jobs" / job_id / "run.json").unlink()
            missing_run_response = await client.get(f"/api/cfd/jobs/{job_id}")
            missing_run = await missing_run_response.json()
            assert missing_run_response.status == 404
            assert missing_run["error"] == "run_record_not_found"
        finally:
            await client.close()

    asyncio.run(scenario())


def test_cfd_routes_readiness_unknown_profile_and_job_id_errors(tmp_path) -> None:
    open_mesh_dir = tmp_path / "open-mesh"
    write_mesh_package(Hull(), open_mesh_dir, stations=8)
    mesh_dir = tmp_path / "watertight-mesh"
    write_mesh_package(
        Hull(),
        mesh_dir,
        stations=8,
        solver_profile=watertight_solid_profile(),
    )
    store = CfdWebStore(tmp_path / "jobs")

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, cfd_store=store)
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            rejected_response = await client.post(
                "/api/cfd/jobs",
                json={
                    "mesh_package_ref": str(mesh_dir),
                    "solver_profile": "unavailable-watertight-solid",
                    "speed_mps": 2.4,
                },
            )
            rejected = await rejected_response.json()
            assert rejected_response.status == 422
            assert rejected["error"] == "mesh_readiness_rejected"
            assert rejected["required_mesh_readiness"] == "cfd_ready"
            assert rejected["observed_mesh_readiness"] == "stl_surface"
            assert rejected["warning"] == CFD_RAW_RESULTS_WARNING

            unknown_response = await client.post(
                "/api/cfd/jobs",
                json={
                    "mesh_package_ref": str(mesh_dir),
                    "solver_profile": "does-not-exist",
                    "speed_mps": 2.4,
                },
            )
            unknown = await unknown_response.json()
            assert unknown_response.status == 400
            assert unknown["error"] == "unknown_solver_profile"
            assert "unavailable-open-wetted-surface" in unknown["available_solver_profiles"]

            mismatch_response = await client.post(
                "/api/cfd/jobs",
                json={
                    "mesh_package_ref": str(open_mesh_dir),
                    "solver_profile": "unavailable-watertight-solid",
                    "speed_mps": 2.4,
                },
            )
            mismatch = await mismatch_response.json()
            assert mismatch_response.status == 422
            assert mismatch["error"] == "solver_profile_mismatch"
            assert mismatch["mesh_profile_mismatch"] == {
                "required": "watertight_solid_resistance_v1",
                "observed": "open_wetted_surface_resistance_v1",
            }
        finally:
            await client.close()

    asyncio.run(scenario())

    with pytest.raises(CfdWebError) as exc_info:
        cfd_job_status_payload("../secret", store)
    assert exc_info.value.status == 400
    assert exc_info.value.payload["error"] == "invalid_job_id"


def test_cfd_routes_failed_command_logs_and_artifact_bounds(tmp_path) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, cfd_store=CfdWebStore(tmp_path / "jobs"))
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            create_response = await client.post(
                "/api/cfd/jobs",
                json={
                    "mesh_package_ref": str(mesh_dir),
                    "solver_profile": "mock-failing-local-command",
                    "speed_mps": 2.4,
                },
            )
            created = await create_response.json()
            assert create_response.status == 201
            job_id = created["job_id"]
            job_dir = created["job_dir"]

            run_response = await client.post(f"/api/cfd/jobs/{job_id}/run")
            run = await run_response.json()
            assert run_response.status == 200
            assert run["run"]["status"] == "failed"
            assert run["run"]["error_kind"] == "command_failed"
            assert "mock CFD command failed intentionally" in run["run"]["error_message"]

            logs_response = await client.get(f"/api/cfd/jobs/{job_id}/logs")
            logs = await logs_response.json()
            assert logs_response.status == 200
            assert logs["logs"]["stdout"]["content"] == "mock CFD command starting\n"
            assert logs["logs"]["stderr"]["content"] == "mock CFD command failed intentionally\n"

            raw_absent_response = await client.get(f"/api/cfd/jobs/{job_id}/raw-result")
            raw_absent = await raw_absent_response.json()
            assert raw_absent_response.status == 404
            assert raw_absent["error"] == "raw_result_not_found"

            run_path = tmp_path / "jobs" / job_id / "run.json"
            run_data = json.loads(run_path.read_text())
            run_data["logs"]["stdout"] = "../outside.log"
            run_path.write_text(json.dumps(run_data, indent=2) + "\n")
            traversal_response = await client.get(f"/api/cfd/jobs/{job_id}/logs")
            traversal = await traversal_response.json()
            assert traversal_response.status == 400
            assert traversal["error"] == "artifact_path_outside_job"

            run_data["status"] = "succeeded"
            run_data["logs"] = {}
            run_data["output_manifest"] = "raw-result.json"
            run_path.write_text(json.dumps(run_data, indent=2) + "\n")
            (tmp_path / "jobs" / job_id / "raw-result.json").write_text("{not-json")
            malformed_response = await client.get(f"/api/cfd/jobs/{job_id}/raw-result")
            malformed = await malformed_response.json()
            assert malformed_response.status == 422
            assert malformed["error"] == "malformed_raw_result"
            assert malformed["artifact_ref"] == "raw-result.json"
            assert job_dir.endswith(job_id)
        finally:
            await client.close()

    asyncio.run(scenario())


def test_cfd_routes_fixture_command_success_remains_raw_unvalidated(tmp_path) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    async def scenario() -> None:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer

        app = web.Application()
        register_rest_routes(app, cfd_store=CfdWebStore(tmp_path / "jobs"))
        client = TestClient(TestServer(app))
        await client.start_server()
        try:
            profiles_response = await client.get("/api/cfd/profiles")
            profiles = await profiles_response.json()
            fixture_profile = next(
                profile for profile in profiles["profiles"]
                if profile["name"] == "fixture-local-command"
            )
            assert fixture_profile["adapter_name"] == "fixture_local_command"
            assert fixture_profile["result_semantics"] == "raw_unvalidated"
            assert fixture_profile["claim_state"] == "raw_unvalidated"
            assert fixture_profile["accepted_uses"] == []

            create_response = await client.post(
                "/api/cfd/jobs",
                json={
                    "mesh_package_ref": str(mesh_dir),
                    "solver_profile": "fixture-local-command",
                    "speed_mps": 2.4,
                },
            )
            created = await create_response.json()
            assert create_response.status == 201
            assert created["result_semantics"] == "raw_unvalidated"
            assert created["warning"] == CFD_RAW_RESULTS_WARNING
            assert created["run"]["status"] == "queued"
            assert created["run"]["claim_state"] == "raw_unvalidated"

            job_id = created["job_id"]
            run_response = await client.post(f"/api/cfd/jobs/{job_id}/run")
            run = await run_response.json()
            assert run_response.status == 200
            assert run["result_semantics"] == "raw_unvalidated"
            assert run["warning"] == CFD_RAW_RESULTS_WARNING
            assert run["run"]["status"] == "succeeded"
            assert run["run"]["result_semantics"] == "raw_unvalidated"
            assert run["run"]["claim_state"] == "raw_unvalidated"
            assert run["run"]["accepted_uses"] == []
            assert CFD_FIXTURE_RESULTS_WARNING in run["run"]["warnings"]

            logs_response = await client.get(f"/api/cfd/jobs/{job_id}/logs")
            logs = await logs_response.json()
            assert logs_response.status == 200
            assert logs["result_semantics"] == "raw_unvalidated"
            assert logs["warning"] == CFD_RAW_RESULTS_WARNING
            assert "stdout" in logs["logs"]

            raw_response = await client.get(f"/api/cfd/jobs/{job_id}/raw-result")
            raw = await raw_response.json()
            assert raw_response.status == 200
            assert raw["result_semantics"] == "raw_unvalidated"
            assert raw["warning"] == CFD_RAW_RESULTS_WARNING
            raw_result = raw["artifact"]["raw_result"]
            assert raw_result["claim_state"] == "raw_unvalidated"
            assert raw_result["accepted_uses"] == []
            assert raw_result["validation_fixture_ids"] == []
            assert raw_result["calibration_fixture_ids"] == []
            assert raw_result["drag_force_n"] > 0.0
            assert CFD_FIXTURE_RESULTS_WARNING in raw_result["warnings"]

            status_lines = cfd_status_lines_from_payload(run)
            assert any("still raw solver output" in line for line in status_lines)
            raw_lines = cfd_raw_result_lines_from_payload(raw)
            assert any("not calibrated or validated" in line for line in raw_lines)
        finally:
            await client.close()

    asyncio.run(scenario())


def test_cfd_browser_lines_keep_problem_states_raw_and_visible() -> None:
    payload = {
        "job": {"job_id": "cfd-test", "solver_profile": "mock-failing-local-command"},
        "run": {
            "job_id": "cfd-test",
            "status": "failed",
            "solver_profile": "mock-failing-local-command",
            "error_kind": "command_failed",
            "error_message": "mock failure",
        },
    }

    lines = cfd_status_lines_from_payload(payload)

    assert CFD_RAW_RESULTS_WARNING in lines
    assert any("Status: failed" in line for line in lines)
    assert any("Terminal problem state" in line for line in lines)

    error_lines = cfd_error_lines_from_payload(
        {
            "error": "mesh_readiness_rejected",
            "message": "readiness rejected",
            "solver_profile": "unavailable-watertight-solid",
            "required_mesh_readiness": "cfd_ready",
            "observed_mesh_readiness": "stl_surface",
            "mesh_profile_mismatch": {
                "required": "watertight_solid_resistance_v1",
                "observed": "open_wetted_surface_resistance_v1",
            },
        },
        title="CFD job preparation rejected",
    )
    assert "CFD job preparation rejected" in error_lines
    assert any(
        "Readiness: required cfd_ready, observed stl_surface" in line
        for line in error_lines
    )
