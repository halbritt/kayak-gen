"""Static layout checks for the RFC 0033 web workspace shell."""

from __future__ import annotations

from pathlib import Path

import pytest

from kayakgen.model.hull import Hull
from kayakgen.ui.web.state import HULL_STATE_FIELDS


pytest.importorskip("trame", reason="kayakgen[web] not installed")
pytest.importorskip("vtk", reason="kayakgen[web] not installed")

web_app = pytest.importorskip("kayakgen.ui.web.app")


def test_workspace_regions_have_stable_test_ids_classes_and_responsive_hooks() -> None:
    assert web_app.LAYOUT_TEST_IDS == {
        "params": "region-params",
        "geometry": "region-geometry",
        "review": "region-review",
    }
    for region in web_app.LAYOUT_TEST_IDS:
        assert "kg-region" in web_app.REGION_CLASSES[region]
        assert web_app.LAYOUT_TEST_IDS[region].split("-", 1)[1] in web_app.REGION_CLASSES[region]

    assert "kg-collapse-under-960" in web_app.RESPONSIVE_CLASS_HOOKS
    assert "kg-geometry-accordion-under-960" in web_app.RESPONSIVE_CLASS_HOOKS
    assert "kg-review-body-under-960" in web_app.RESPONSIVE_CLASS_HOOKS
    assert "kg-export-menu-under-1200" in web_app.RESPONSIVE_CLASS_HOOKS
    assert "kg-status-wrap-under-960" in web_app.RESPONSIVE_CLASS_HOOKS
    assert "kg-metrics-strip-scroll" in web_app.RESPONSIVE_CLASS_HOOKS


def test_parameter_rail_groups_cover_visible_hull_fields_and_target_speed() -> None:
    grouped = [field for _label, fields in web_app.PARAMETER_GROUPS for field in fields]

    assert grouped == [*HULL_STATE_FIELDS, "target_speed_kt"]
    assert "LCB_frac" not in grouped
    assert "rocker_bow_m" not in grouped
    assert "rocker_stern_m" not in grouped
    assert tuple(web_app.CLASS_PRESETS) == (
        "touring",
        "performance",
        "surfski_int",
        "surfski_elite",
        "custom",
    )


def test_review_tabs_and_status_segments_match_workspace_contract() -> None:
    assert [tab["label"] for tab in web_app.REVIEW_TABS] == [
        "Hydro",
        "Mesh",
        "Comparison",
        "CFD",
        "Advisories",
    ]
    assert [segment["key"] for segment in web_app.STATUS_SEGMENTS] == [
        "package",
        "readiness",
        "resistance",
        "cfd",
    ]
    assert [segment["target_tab"] for segment in web_app.STATUS_SEGMENTS] == [
        "mesh",
        "mesh",
        "analysis",
        "cfd",
    ]


def test_persistent_claim_readiness_and_cfd_copy_is_static_and_exact() -> None:
    copy = web_app.PERSISTENT_COPY

    assert copy["raw_comparative_filter"] == "Raw comparative filter; not final prediction."
    assert "uncalibrated" in copy["resistance_detail"].lower()
    assert copy["high_angle_gz_heading"] == "High-angle GZ unavailable"
    assert copy["mesh_package_readiness_heading"] == "Mesh package readiness"
    assert copy["mesh_package_readiness"] == (
        "Open wetted-surface profile; not watertight cfd_ready."
    )
    assert copy["cfd_local_banner"] == (
        "Local filesystem CFD jobs on this server only; no hosted worker is running."
    )
    assert copy["cfd_artifact_strapline"] == (
        "Raw solver artifact only; not calibrated or validated."
    )
    assert copy["share_toast"] == "Shareable URL copied"


def test_forbidden_high_angle_and_mesh_claim_copy_does_not_creep_into_static_layout() -> None:
    app_source = Path(web_app.__file__).read_text()

    assert "GZ_max" not in app_source
    assert "heel_angle_max_deg" not in app_source
    assert app_source.count("cfd_ready") == 1
    assert "not watertight cfd_ready" in app_source


def test_create_app_exposes_workspace_status_state_without_changing_tab_key() -> None:
    web = web_app.create_app(initial_hull=Hull())

    assert web.state.analysis_tab == "analysis"
    assert web.state.mesh_profile_label == "open-wetted-surface"
    assert web.state.mesh_profile_id == "open_wetted_surface_resistance_v1"
    assert web.state.mesh_readiness_level == "cfd_surface_candidate"
    assert web.state.status_segments == [
        "package: open-wetted-surface",
        "readiness: cfd_surface_candidate",
        "resistance: uncalibrated_comparative",
        "cfd: unavailable",
    ]
    assert web.state.cfd_local_banner == web_app.PERSISTENT_COPY["cfd_local_banner"]
    assert web.state.cfd_artifact_strapline == web_app.PERSISTENT_COPY[
        "cfd_artifact_strapline"
    ]


def test_share_action_keeps_encoded_url_in_state_but_uses_copied_status() -> None:
    web = web_app.create_app(initial_hull=Hull())

    assert web.state.share_status == ""
    web._share_url()

    assert web.state.share_url.startswith("?hull=")
    assert web.state.share_status == "Shareable URL copied"
    assert web.state.share_toast is True


def test_pinned_share_url_field_is_not_rendered_in_layout_source() -> None:
    app_source = Path(web_app.__file__).read_text()

    assert 'label="Shareable URL"' not in app_source
    assert "Shareable URL copied" in app_source
