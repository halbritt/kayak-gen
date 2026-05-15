from __future__ import annotations

import json

from kayakgen.cli.high_angle_gz import build_high_angle_gz_block
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.eval.mesh_package import watertight_solid_profile, write_mesh_package
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_L_BWL_LOW
from kayakgen.search.compare import (
    CandidateSummary,
    ComparisonReport,
    HighAngleGzDisplay,
)
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
from kayakgen.ui.web.read_models import (
    HIGH_ANGLE_GZ_SECTION_CAPTION,
    HIGH_ANGLE_GZ_SECTION_HEADING,
    web_high_angle_gz_rows,
    web_high_angle_gz_section_html,
    web_high_angle_gz_view_model,
    web_high_angle_gz_view_model_from_json,
)
from kayakgen.ui.web.state import (
    CFD_PAYLOAD_ALIASES,
    CFD_STATUS_ALIASES,
    CFD_STATUS_LINE_ALIASES,
    MESH_PACKAGE_REF_ALIASES,
    STATE_SNAPSHOT_KEYS,
    state_dict_from_hull,
)


def _display_from_block(block: dict[str, object]) -> HighAngleGzDisplay:
    """Adapt a stage-1 ``build_high_angle_gz_block`` dict to the report mirror."""

    summary = block.get("summary") if isinstance(block.get("summary"), dict) else None
    heel_grid = block.get("heel_grid_deg") or []
    return HighAngleGzDisplay(
        available=bool(block.get("available", False)),
        body_profile=str(block.get("body_profile", "")),
        result_semantics=str(block.get("result_semantics", "")),
        method=block.get("method"),
        body_ref=block.get("body_ref"),
        body_type=block.get("body_type"),
        body_diagnostic_ref=block.get("body_diagnostic_ref"),
        heel_grid_deg=[float(value) for value in heel_grid if isinstance(value, (int, float))],
        max_gz_m=summary.get("max_gz") if summary else None,
        heel_at_max_gz_deg=summary.get("heel_at_max_gz") if summary else None,
        range_positive_stability_deg=(
            summary.get("range_positive_stability_deg") if summary else None
        ),
        warnings=[str(value) for value in (block.get("warnings") or [])],
        assumptions=[str(value) for value in (block.get("assumptions") or [])],
        unavailable_reason=(
            block.get("unavailable_reason")
            if isinstance(block.get("unavailable_reason"), dict)
            else None
        ),
    )


def _candidate_summary(
    index: int,
    key: str,
    display: HighAngleGzDisplay | None,
) -> CandidateSummary:
    return CandidateSummary(
        candidate_index=index,
        candidate_key=key,
        status="complete",
        hull_hash=Hull().hash(),
        high_angle_gz_display=display,
    )


def _report_with_high_angle(
    *,
    columns: bool,
    candidates: list[CandidateSummary],
) -> ComparisonReport:
    return ComparisonReport(
        run_name="stage3-web-fixture",
        spec_hash="stage3-web-fixture",
        report_kind="exploratory_frontier",
        objectives=[],
        pareto_front_keys=[],
        candidate_summaries=candidates,
        high_angle_gz_columns=columns,
    )


def _available_display() -> HighAngleGzDisplay:
    block = build_high_angle_gz_block(
        Hull(),
        LoadCase(),
        heel_grid_deg=[0.0, 5.0, 10.0, 15.0, 20.0],
    )
    return _display_from_block(block)


def _unavailable_display() -> HighAngleGzDisplay:
    return HighAngleGzDisplay(
        available=False,
        body_profile="generated_hull_plus_deck_closed_body_v1",
        result_semantics="unvalidated_hydrostatic_comparison",
        method=None,
        warnings=[
            "deck_immersion_assumption",
            "flooding_not_modeled",
            "not_safety_or_seaworthiness_claim",
        ],
        assumptions=["heel_grid: 0..20 deg"],
        unavailable_reason={
            "code": "synthetic_body_not_allowed_for_real_gz",
            "detail": "evaluate_gz_curve returned status != computed",
        },
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


# ---------------------------------------------------------------------------
# RFC 0043 stage 3 web read model: high-angle GZ comparison section.
# ---------------------------------------------------------------------------


def test_web_comparison_hides_high_angle_section_when_columns_false() -> None:
    report = _report_with_high_angle(
        columns=False,
        candidates=[_candidate_summary(0, "cand-a", _available_display())],
    )

    rows = web_high_angle_gz_rows(report)
    view = web_high_angle_gz_view_model(report)
    html_out = web_high_angle_gz_section_html(view)

    assert rows == []
    assert view["visible"] is False
    assert view["rows"] == []
    assert view["heading"] == HIGH_ANGLE_GZ_SECTION_HEADING
    assert view["caption"] == HIGH_ANGLE_GZ_SECTION_CAPTION
    # When hidden the rendered HTML is empty so the Trame ``v-show`` binding
    # collapses without leaving any orphan caption in the DOM.
    assert html_out == ""

    # Round-trip through JSON to mirror the wire path.
    view_from_json = web_high_angle_gz_view_model_from_json(report.model_dump_json())
    assert view_from_json["visible"] is False
    assert view_from_json["rows"] == []


def test_web_comparison_renders_high_angle_rows_when_present() -> None:
    available = _available_display()
    unavailable = _unavailable_display()
    report = _report_with_high_angle(
        columns=True,
        candidates=[
            _candidate_summary(0, "cand-a", available),
            _candidate_summary(1, "cand-b", unavailable),
            _candidate_summary(2, "cand-c", None),
        ],
    )

    view = web_high_angle_gz_view_model(report)
    html_out = web_high_angle_gz_section_html(view)

    assert view["visible"] is True
    assert [row["candidate_key"] for row in view["rows"]] == ["cand-a", "cand-b"]
    # available_display row carries the artifact's max-GZ value.
    available_row = view["rows"][0]
    assert available_row["available"] is True
    assert available_row["result_semantics"] == "unvalidated_hydrostatic_comparison"
    assert available_row["max_gz_m"] is not None
    assert available_row["heel_at_max_gz_deg"] is not None
    assert available_row["range_positive_stability_deg"] is not None
    # unavailable row falls through to the reason-rendering path.
    unavailable_row = view["rows"][1]
    assert unavailable_row["available"] is False
    assert unavailable_row["max_gz_m"] is None
    assert "synthetic_body_not_allowed_for_real_gz" in unavailable_row["unavailable_reason"]
    # HTML carries the section heading and the fixed caption verbatim.
    assert HIGH_ANGLE_GZ_SECTION_HEADING in html_out
    assert HIGH_ANGLE_GZ_SECTION_CAPTION in html_out
    assert 'data-candidate-key="cand-a"' in html_out
    assert 'data-candidate-key="cand-b"' in html_out


def test_web_high_angle_rows_carry_body_load_trim_provenance() -> None:
    available = _available_display()
    report = _report_with_high_angle(
        columns=True,
        candidates=[_candidate_summary(0, "cand-a", available)],
    )

    view = web_high_angle_gz_view_model(report)
    html_out = web_high_angle_gz_section_html(view)
    provenance = view["rows"][0]["provenance_label"]

    # Body / load / trim are present as a single combined line.
    assert provenance.startswith("body: generated_hull_plus_deck_closed_body_v1")
    assert " | load: " in provenance
    assert " | trim: " in provenance
    # Trim slot is the artifact's GZ integration method (encapsulates the
    # fixed-trim policy used at each heel point).
    assert "fixed_trim_generated_body_v1" in provenance
    # The rendered HTML places the provenance line adjacent to the metric
    # values so no bare summary number is shown without context.
    provenance_idx = html_out.index(provenance)
    metrics_idx = html_out.index("max GZ (m)")
    assert provenance_idx < metrics_idx


def test_web_high_angle_rows_show_warnings_and_assumptions() -> None:
    available = _available_display()
    # Force a known assumption so the test does not depend on the evaluator
    # emitting any particular assumption string.
    augmented = available.model_copy(
        update={
            "warnings": [*available.warnings, "deck_immersion_assumption"],
            "assumptions": ["heel_grid=0..20 deg", "default_load_case"],
        }
    )
    report = _report_with_high_angle(
        columns=True,
        candidates=[_candidate_summary(0, "cand-a", augmented)],
    )

    view = web_high_angle_gz_view_model(report)
    html_out = web_high_angle_gz_section_html(view)
    row = view["rows"][0]

    # Warnings / assumptions are preserved on the row exactly.
    assert "deck_immersion_assumption" in row["warnings"]
    assert "default_load_case" in row["assumptions"]
    # They appear in the rendered HTML adjacent to the row's provenance line.
    assert "warning: deck_immersion_assumption" in html_out
    assert "assumption: default_load_case" in html_out


def test_web_high_angle_rows_show_unavailable_reason_when_unavailable() -> None:
    unavailable = _unavailable_display()
    report = _report_with_high_angle(
        columns=True,
        candidates=[_candidate_summary(0, "cand-a", unavailable)],
    )

    view = web_high_angle_gz_view_model(report)
    html_out = web_high_angle_gz_section_html(view)
    row = view["rows"][0]

    assert row["available"] is False
    assert row["max_gz_m"] is None
    assert row["heel_at_max_gz_deg"] is None
    assert row["range_positive_stability_deg"] is None
    assert row["unavailable_reason"] == (
        "synthetic_body_not_allowed_for_real_gz: "
        "evaluate_gz_curve returned status != computed"
    )
    assert "unavailable: synthetic_body_not_allowed_for_real_gz" in html_out
    # No bare metric labels are rendered for an unavailable row.
    assert "max GZ (m)" not in html_out


def test_web_high_angle_section_forbidden_claim_copy_absent() -> None:
    available = _available_display()
    unavailable = _unavailable_display()
    report = _report_with_high_angle(
        columns=True,
        candidates=[
            _candidate_summary(0, "cand-a", available),
            _candidate_summary(1, "cand-b", unavailable),
        ],
    )

    view = web_high_angle_gz_view_model(report)
    html_out = web_high_angle_gz_section_html(view)

    # The fixed caption and the RFC 0024 surface-warning identifiers are
    # negations -- they explicitly say the result is NOT a safety or
    # seaworthiness claim, NOT validated, and NOT calibrated. Those phrases
    # are scrubbed before the forbidden-token sweep so the negation list
    # itself does not trip the regression. Everything else must be free of
    # the forbidden claim copy.
    assert HIGH_ANGLE_GZ_SECTION_CAPTION in html_out
    allowed_negations = (
        HIGH_ANGLE_GZ_SECTION_CAPTION,
        "not_safety_or_seaworthiness_claim",
        "unvalidated_hydrostatic_comparison",
    )
    scrubbed = html_out
    for phrase in allowed_negations:
        scrubbed = scrubbed.replace(phrase, "")

    forbidden_tokens = (
        "safe",
        "seaworthy",
        "validated",
        "calibrated",
        "final prediction",
        "design fitness",
    )
    lowered = scrubbed.lower()
    for token in forbidden_tokens:
        assert token not in lowered, token

    # Lossless display contract: the rendered section asserts the
    # unvalidated-hydrostatic-comparison semantics in every row.
    for row in view["rows"]:
        assert row["result_semantics"] == "unvalidated_hydrostatic_comparison"
