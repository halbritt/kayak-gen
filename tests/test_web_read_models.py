from __future__ import annotations

import json

from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.eval.mesh_package import watertight_solid_profile, write_mesh_package
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.ui.web.controllers import (
    MESH_PROFILE_LABEL_TO_ID,
    WATERTIGHT_SOLID_DISABLED_TOOLTIP,
    class_preset_options,
    class_preset_read_model,
    evaluation_summary,
    mesh_diagnostics_lines_from_state,
    mesh_package_view_model,
    resistance_table_view_model,
    validity_badge_from_state,
)
from kayakgen.ui.web.state import (
    CFD_PAYLOAD_ALIASES,
    CFD_STATUS_ALIASES,
    CFD_STATUS_LINE_ALIASES,
    MESH_PACKAGE_REF_ALIASES,
    STATE_SNAPSHOT_KEYS,
    state_dict_from_hull,
)


def _state(hull: Hull | None = None, **overrides: object) -> dict[str, object]:
    state = state_dict_from_hull(hull or Hull())
    state["target_speed_kt"] = 3.5
    state.update(overrides)
    return state


def test_class_preset_read_model_returns_defaults_bounds_and_human_labels() -> None:
    options = class_preset_options()
    assert options[0] == {"value": "touring", "label": "Touring sea kayak"}
    assert options[-1] == {"value": "custom", "label": "Custom"}

    model = class_preset_read_model("surfski_elite")

    assert model["preset"] == "surfski_elite"
    assert model["label"] == "Elite surfski"
    assert model["values"] == {
        "length_m": 6.1,
        "beam_oa_m": 0.43,
        "beam_wl_m": 0.40,
        "draft_m": 0.11,
        "Cp": 0.58,
    }
    assert model["bounds"]["length_m"] == {"min": 5.8, "max": 6.4, "default": 6.1}
    assert model["bounds"]["beam_wl_m"] == {"min": 0.38, "max": 0.43, "default": 0.40}


def test_class_preset_read_model_custom_and_unknown_do_not_reseed() -> None:
    assert class_preset_read_model("custom")["values"] == {}
    assert class_preset_read_model("unknown") == class_preset_read_model("custom")


def test_validity_badge_uses_exact_allowed_strings() -> None:
    preset_labels = {
        option["value"]: option["label"]
        for option in class_preset_options()
        if option["value"] != "custom"
    }
    for preset, label in preset_labels.items():
        assert validity_badge_from_state(
            _state(class_preset="custom", **class_preset_read_model(preset)["values"])
        ) == f"In {label} envelope"

    assert validity_badge_from_state(
        _state(class_preset="touring", **class_preset_read_model("touring")["values"])
    ) == "In Touring sea kayak envelope"
    assert validity_badge_from_state(
        _state(Hull(length_m=5.0, beam_oa_m=0.54, beam_wl_m=0.50, draft_m=0.16, Cp=0.62))
    ) == "Custom (L/B_wl=10.0)"
    assert validity_badge_from_state(
        _state(Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65))
    ) == "Custom — sub-touring"
    assert validity_badge_from_state(
        _state(Hull(length_m=6.4, beam_oa_m=0.39, beam_wl_m=0.38, draft_m=0.14, Cp=0.62))
    ) == "Custom — beyond elite"


def test_validity_badge_uses_web_canonical_five_field_envelope() -> None:
    assert validity_badge_from_state(
        _state(
            Hull(
                length_m=5.0,
                beam_oa_m=0.58,
                beam_wl_m=0.53,
                draft_m=0.18,
                Cp=0.54,
            ),
            class_preset="custom",
        )
    ) == "Custom (L/B_wl=9.4)"


def test_evaluation_summary_uses_manifest_profile_readiness_and_cfd_status(
    tmp_path,
) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    summary = evaluation_summary(
        _state(
            cfd_mesh_package_ref=str(mesh_dir),
            cfd_payload={"run": {"status": "running"}},
        )
    )

    assert summary["package"] == {
        "label": "open-wetted-surface",
        "profile_id": "open_wetted_surface_resistance_v1",
    }
    assert summary["readiness"]["level"] == "cfd_surface_candidate"
    assert summary["resistance_claim"]["claim_state"] == "uncalibrated_comparative"
    assert "not_final_performance_prediction" in summary["resistance_claim"]["warnings"]
    assert summary["cfd_status"] == "running"
    assert summary["advisories"] == []


def test_evaluation_summary_exposes_structured_design_advisories() -> None:
    hull = Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65)

    summary = evaluation_summary(_state(hull))

    assert summary["readiness"]["level"] is None
    assert summary["readiness"]["display"] == "unavailable"
    assert summary["advisories"] == [
        {
            "code": CODE_L_BWL_LOW,
            "message": "L/B_wl below touring guidance",
            "field_refs": ["length_m", "beam_wl_m"],
        }
    ]


def test_evaluation_summary_preserves_cfd_status_aliases() -> None:
    for key in CFD_STATUS_ALIASES:
        assert key in STATE_SNAPSHOT_KEYS
        assert evaluation_summary(_state(**{key: "queued"}))["cfd_status"] == "queued"

    for key in CFD_PAYLOAD_ALIASES:
        assert key in STATE_SNAPSHOT_KEYS
        assert (
            evaluation_summary(_state(**{key: {"run": {"status": "running"}}}))[
                "cfd_status"
            ]
            == "running"
        )
        assert evaluation_summary(_state(**{key: {"status": "succeeded"}}))[
            "cfd_status"
        ] == "succeeded"

    for key in CFD_STATUS_LINE_ALIASES:
        assert key in STATE_SNAPSHOT_KEYS
        assert (
            evaluation_summary(_state(**{key: ["CFD local job", "Status: unavailable"]}))[
                "cfd_status"
            ]
            == "unavailable"
        )

    assert set(MESH_PACKAGE_REF_ALIASES).issubset(STATE_SNAPSHOT_KEYS)


def test_mesh_diagnostics_lines_make_welded_counts_primary() -> None:
    state = _state()
    diagnostics = diagnose_mesh(Hull(), part="hull")

    lines = mesh_diagnostics_lines_from_state(state, part="hull")

    assert lines[0] == "Hull diagnostics"
    assert f"Boundary edges: {diagnostics.welded_boundary_edges} (welded primary)" in lines
    assert (
        f"Non-manifold edges: {diagnostics.welded_nonmanifold_edges} (welded primary)"
        in lines
    )
    assert (
        "Raw detail: "
        f"boundary edges {diagnostics.raw_boundary_edges}; "
        f"non-manifold edges {diagnostics.raw_nonmanifold_edges}; "
        f"vertices {diagnostics.profile.vertex_count}; "
        f"welded vertices {diagnostics.profile.welded_vertex_count}"
    ) in lines


def test_mesh_package_view_model_maps_ui_labels_to_profile_ids(tmp_path) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh_dir, stations=8)

    model = mesh_package_view_model(mesh_dir)

    assert model["status"] == "ready"
    assert model["profile"] == {
        "label": "open-wetted-surface",
        "profile_id": MESH_PROFILE_LABEL_TO_ID["open-wetted-surface"],
    }
    options = {option["label"]: option for option in model["profile_options"]}
    assert options["open-wetted-surface"]["profile_id"] == (
        "open_wetted_surface_resistance_v1"
    )
    assert options["watertight-solid"]["profile_id"] == "watertight_solid_resistance_v1"
    assert options["watertight-solid"]["disabled"] is True
    assert options["watertight-solid"]["tooltip"] == WATERTIGHT_SOLID_DISABLED_TOOLTIP
    assert model["diagnostics"]["hull"]["counts"]["boundary_edges"]["primary_basis"] == "welded"
    assert model["diagnostics"]["hull"]["counts"]["boundary_edges"]["raw"] >= 0
    assert "open wetted-surface profile; not watertight cfd_ready" in model["warnings"]


def test_mesh_package_view_model_maps_watertight_profile_manifest_id(tmp_path) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(
        Hull(),
        mesh_dir,
        stations=8,
        solver_profile=watertight_solid_profile(),
    )

    model = mesh_package_view_model(mesh_dir)

    assert model["profile"] == {
        "label": "watertight-solid",
        "profile_id": MESH_PROFILE_LABEL_TO_ID["watertight-solid"],
    }


def test_mesh_package_view_model_rejects_manifest_refs_outside_package(tmp_path) -> None:
    mesh_dir = tmp_path / "mesh"
    write_mesh_package(Hull(), mesh_dir, stations=8)
    outside = tmp_path / "outside.json"
    outside.write_text((mesh_dir / "quality.hull.json").read_text())
    manifest_path = mesh_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["quality_reports"]["hull"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest))

    model = mesh_package_view_model(mesh_dir)

    assert model["diagnostics"]["hull"]["error"] == "artifact_path_outside_package"
    assert "hull: artifact path outside package" in model["warnings"]
    assert "hull: artifact path outside package" in model["artifact_errors"]


def test_resistance_table_inserts_sorted_target_row_when_off_sweep() -> None:
    model = resistance_table_view_model(_state(target_speed_kt=3.7))

    speeds = [row["speed_kt"] for row in model["rows"]]
    assert speeds == [2.0, 3.0, 3.7, 4.0, 5.0, 6.0]
    target_rows = [row for row in model["rows"] if row["is_target"]]
    assert len(target_rows) == 1
    assert target_rows[0]["speed_kt"] == 3.7
    assert target_rows[0]["source"] == "target"
    assert model["metadata"]["claim_state"] == "uncalibrated_comparative"


def test_resistance_table_highlights_fixed_row_when_target_is_within_tolerance() -> None:
    model = resistance_table_view_model(_state(target_speed_kt=3.04))

    speeds = [row["speed_kt"] for row in model["rows"]]
    assert speeds == [2.0, 3.0, 4.0, 5.0, 6.0]
    target_rows = [row for row in model["rows"] if row["is_target"]]
    assert len(target_rows) == 1
    assert target_rows[0]["speed_kt"] == 3.0
    assert target_rows[0]["source"] == "sweep"
