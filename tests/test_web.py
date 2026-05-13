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
    evaluation_payload,
    job_stub_payload,
    load_hull_payload,
    register_rest_routes,
    store_hull_payload,
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
    assert m["Rt_N"] == m["Rv_N"] + m["Rw_N"]


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


def test_load_from_query_seeds_state() -> None:
    from kayakgen.ui.web.app import create_app

    custom = Hull(name="touring", length_m=5.0, beam_oa_m=0.58, beam_wl_m=0.53, Cp=0.54, draft_m=0.12)
    web = create_app()
    web.load_from_query(encode_hull_query(custom))
    assert web.state.name == "touring"
    assert web.state.length_m == 5.0
    assert abs(web.state.beam_wl_m - 0.53) < 1e-9


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
