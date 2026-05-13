from __future__ import annotations

from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.eval.mesh_package import watertight_solid_profile, write_mesh_package
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.ui.web.controllers import (
    MESH_PROFILE_LABEL_TO_ID,
    WATERTIGHT_SOLID_DISABLED_TOOLTIP,
    evaluation_summary,
    mesh_diagnostics_lines_from_state,
    mesh_package_view_model,
    resistance_table_view_model,
)
from kayakgen.ui.web.state import state_dict_from_hull


def _state(hull: Hull | None = None, **overrides: object) -> dict[str, object]:
    state = state_dict_from_hull(hull or Hull())
    state["target_speed_kt"] = 3.5
    state.update(overrides)
    return state


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
