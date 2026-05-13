"""RFC 0008 web frontend — state round-trip and core-parity checks.

These tests exercise the headless pieces (state encoding, controller
helpers, CLI wiring) without standing up a Trame server. The full Trame
app is exercised manually via `kayakgen serve`; a Playwright smoke test
is reserved for CI.
"""

from __future__ import annotations

import pytest

from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull


pytest.importorskip("trame", reason="kayakgen[web] not installed")


from kayakgen.ui.web.controllers import metrics_from_state, stl_bytes_for_part  # noqa: E402
from kayakgen.ui.web.controllers import (  # noqa: E402
    HullStore,
    analysis_lines_from_state,
    candidate_state_from_report_json,
    clamp_beam_wl_state,
    comparison_view_model_from_json,
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


def test_state_dict_round_trip_via_hull() -> None:
    hull = Hull(name="touring", length_m=5.0, beam_oa_m=0.58, beam_wl_m=0.53)
    state = state_dict_from_hull(hull)
    back = hull_from_state_dict(state)
    assert back == hull


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


def test_create_app_accepts_initial_query() -> None:
    from kayakgen.ui.web.app import create_app

    custom = Hull(name="elite", length_m=6.1, beam_oa_m=0.43, beam_wl_m=0.40)
    web = create_app(initial_query=f"?hull={encode_hull_query(custom)}")
    assert web.state.name == "elite"
    assert web.state.length_m == 6.1


def test_query_string_decoder_handles_missing_hull() -> None:
    assert hull_from_query_string("?x=1") is None


def test_rest_payload_helpers() -> None:
    state = state_dict_from_hull(Hull()) | {"target_speed_kt": 3.5}
    evaluation = evaluation_payload(state)
    assert evaluation["hull_hash"] == Hull().hash()
    store = HullStore()
    stored = store_hull_payload(state, store)
    assert load_hull_payload(stored["id"], store)["schema_version"] == "1"
    assert job_stub_payload()["error"].startswith("heavy CFD")


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
