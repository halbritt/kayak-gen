"""Static layout checks for the RFC 0033 web workspace shell."""

from __future__ import annotations

import re
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
    assert [option["label"] for option in web_app.CLASS_PRESET_OPTIONS] == [
        "Touring sea kayak",
        "Performance sea kayak",
        "Intermediate surfski",
        "Elite surfski",
        "Custom",
    ]


def test_parameter_slider_labels_spacing_and_accessibility_contract() -> None:
    app_source = Path(web_app.__file__).read_text()
    expected_labels = [label for _key, label, _vmin, _vmax, _step in web_app.SLIDER_DEFS]

    assert expected_labels == [
        "Length (m)",
        "Beam OA (m)",
        "Beam WL (m)",
        "Draft (m)",
        "Deck Height (m)",
        "Prismatic Cp",
        "Midship Cm",
        "Deck Flatness",
        "Parallel Mid-Body",
        "Bow Rake (1=raked)",
        "Stern Rake (1=raked)",
        "Target Speed (kt)",
    ]
    assert 'thumb_label="always"' not in app_source
    assert "thumb_label=True" in app_source
    assert 'classes=f"kg-param-slider kg-param-{key} mt-3"' in app_source
    assert 'classes=f"kg-param-slider kg-param-{key} mt-2"' not in app_source
    assert 'f\'aria-label="{escaped_label}"\'' in app_source
    for key, label, _vmin, _vmax, _step in web_app.SLIDER_DEFS:
        assert web_app._param_row_raw_attrs(key, label) == [
            f'data-param-key="{key}"',
            f'data-testid="param-{key}"',
            'role="group"',
            f'aria-label="{label}"',
        ]


def test_parameter_slider_label_css_uses_existing_tokens() -> None:
    css = web_app.PARAMETER_RAIL_CSS
    app_source = Path(web_app.__file__).read_text()

    assert ".kg-param-slider .v-slider__label {" in css
    assert "font: var(--type-label);" in css
    assert "color: var(--text-secondary);" in css
    assert "white-space: nowrap;" in css
    assert "overflow: hidden;" in css
    assert "text-overflow: ellipsis;" in css
    assert ":root" not in css
    assert "--type-label:" not in css
    assert "--text-secondary:" not in css
    assert "--surface-rail:" not in css
    assert set(re.findall(r"var\((--[^)]+)\)", css)) == {
        "--type-label",
        "--text-secondary",
    }
    assert web_app.ROOT_THEME_CSS.count(":root") == 1
    assert "--type-label:" in web_app.ROOT_THEME_CSS
    assert "--text-secondary:" in web_app.ROOT_THEME_CSS
    assert "--surface-rail:" in web_app.ROOT_THEME_CSS
    assert app_source.count("html_widgets.Style(ROOT_THEME_CSS)") == 1
    assert app_source.count("html_widgets.Style(PARAMETER_RAIL_CSS)") == 1


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


def test_export_menu_rows_are_single_honest_menu_contract() -> None:
    app_source = Path(web_app.__file__).read_text()

    assert [row["label"] for row in web_app.EXPORT_MENU_ROWS] == [
        "Hull STL",
        "Deck STL",
        "Hydro JSON",
        "Stability JSON",
        "Mesh package...",
    ]
    assert [row["status"] for row in web_app.EXPORT_MENU_ROWS] == [
        "enabled",
        "enabled",
        "enabled",
        "unavailable",
        "unavailable",
    ]
    assert [row["available"] for row in web_app.EXPORT_MENU_ROWS] == [
        True,
        True,
        True,
        False,
        False,
    ]
    assert [row["disabled"] for row in web_app.EXPORT_MENU_ROWS] == [
        False,
        False,
        False,
        True,
        True,
    ]
    assert [row["subtitle"] for row in web_app.EXPORT_MENU_ROWS] == [
        "Current open hull inspection surface",
        "Current open deck inspection surface",
        "Current local evaluation data",
        "Use kayakgen stability for current initial-stability JSON.",
        "Mesh package authoring is not enabled in the browser; use kayakgen mesh-package.",
    ]
    assert [row["row_class"] for row in web_app.EXPORT_MENU_ROWS] == [
        "kg-export-row kg-export-hull-stl",
        "kg-export-row kg-export-deck-stl",
        "kg-export-row kg-export-hydro-json",
        "kg-export-row kg-export-stability-json",
        "kg-export-row kg-export-mesh-package",
    ]
    assert [row["action_key"] for row in web_app.EXPORT_MENU_ROWS] == [
        "export_hull_stl",
        "export_deck_stl",
        "export_hydro_json",
        "",
        "",
    ]
    assert "kayakgen stability" in web_app.EXPORT_MENU_ROWS[3]["description"]
    assert "kayakgen mesh-package" in web_app.EXPORT_MENU_ROWS[4]["description"]
    assert "for row in EXPORT_MENU_ROWS:" in app_source
    assert 'title="Hull STL"' not in app_source
    assert 'subtitle="Current open hull inspection surface"' not in app_source


def test_state_snapshot_schema_preserves_current_and_legacy_alias_keys() -> None:
    expected_keys = (
        *HULL_STATE_FIELDS,
        "name",
        "target_speed_kt",
        "class_preset",
        "mesh_package_ref",
        "cfd_mesh_package_ref",
        "cfd_status",
        "status",
        "cfd_payload",
        "cfd_job_payload",
        "cfd_last_payload",
        "cfd_status_lines",
    )
    assert web_app.STATE_SNAPSHOT_KEYS == expected_keys

    web = web_app.create_app(initial_hull=Hull())
    snapshot = web._state_snapshot()

    assert snapshot["mesh_package_ref"] is None
    assert snapshot["cfd_status"] is None
    assert snapshot["status"] is None
    assert snapshot["cfd_payload"] is None
    assert snapshot["cfd_job_payload"] is None
    assert snapshot["cfd_last_payload"] is None
    assert snapshot["cfd_mesh_package_ref"] == ""
    web.state.mesh_package_ref = "build/mesh-package"
    web.state.cfd_status = "queued"
    web.state.cfd_payload = {"run": {"status": "running"}}

    snapshot = web._state_snapshot()
    assert snapshot["mesh_package_ref"] == "build/mesh-package"
    assert snapshot["cfd_status"] == "queued"
    assert snapshot["cfd_payload"] == {"run": {"status": "running"}}

    web.state.mesh_package_ref = None
    web.state.cfd_status = None
    web.state.cfd_payload = None


def test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces() -> None:
    app_source = Path(web_app.__file__).read_text()
    controllers_source = Path(web_app.__file__).with_name("controllers.py").read_text()
    render_source = "\n".join([app_source, controllers_source])

    allowed_phrases = (
        "not final prediction",
        "no accepted final-prediction",
        "not watertight cfd_ready",
        "no hosted worker is running",
    )
    scrubbed = render_source
    for phrase in allowed_phrases:
        assert phrase in render_source
        scrubbed = scrubbed.replace(phrase, "")

    for forbidden in (
        "GZ_max",
        "heel_angle_max_deg",
        "max_gz_m",
        "heel_at_max_gz_deg",
        "range_positive_stability_deg",
        "area_under_positive_gz_m_deg",
        "righting_moment_nm",
        "gz_m",
        "fixture_only",
        "OpenFOAM",
        "SU2",
        "worker queue",
        "calibrated drag",
        "design fitness",
        "cfd_ready",
    ):
        assert forbidden not in scrubbed
    assert "final prediction" not in scrubbed
    assert "hosted" not in scrubbed
    assert "cloud" not in scrubbed


def test_create_app_exposes_workspace_status_state_without_changing_tab_key() -> None:
    web = web_app.create_app(initial_hull=Hull())

    assert web.state.analysis_tab == "analysis"
    assert web.state.mesh_profile_label == "open-wetted-surface"
    assert web.state.mesh_profile_id == "open_wetted_surface_resistance_v1"
    assert web.state.mesh_readiness_level == "unavailable"
    assert web.state.status_segments == [
        "package: open-wetted-surface",
        "readiness: unavailable",
        "resistance: uncalibrated_comparative",
        "cfd: unavailable",
    ]
    assert web.state.validity_badge == "Custom (L/B_wl=8.2)"
    assert web.state.status_package_aria_label == "package: open-wetted-surface; opens mesh tab"
    assert web.state.status_readiness_aria_label == "readiness: unavailable; opens mesh tab"
    assert web.state.cfd_local_banner == web_app.PERSISTENT_COPY["cfd_local_banner"]
    assert web.state.cfd_artifact_strapline == web_app.PERSISTENT_COPY[
        "cfd_artifact_strapline"
    ]


def test_class_preset_reseeds_bounds_and_manual_hull_edit_flips_custom() -> None:
    web = web_app.create_app(initial_hull=Hull())

    web.state.class_preset = "surfski_elite"
    web._apply_class_preset("surfski_elite")

    assert web.state.length_m == 6.1
    assert web.state.beam_oa_m == 0.43
    assert web.state.beam_wl_m == 0.40
    assert web.state.draft_m == 0.11
    assert web.state.Cp == 0.58
    assert web.state.length_m_min == 5.8
    assert web.state.length_m_max == 6.4
    assert web.state.beam_oa_m_min == 0.42
    assert web.state.beam_oa_m_max == 0.46
    assert web.state.beam_wl_m_min == 0.38
    assert web.state.beam_wl_m_max == 0.43
    assert web.state.draft_m_min == 0.09
    assert web.state.draft_m_max == 0.12
    assert web.state.Cp_min == 0.56
    assert web.state.Cp_max == 0.60
    assert web.state.deck_height_m_min == 0.15
    assert web.state.deck_height_m_max == 0.40
    assert web.state.Cm_min == 0.65
    assert web.state.Cm_max == 0.95
    assert web.state.target_speed_kt_min == 1.0
    assert web.state.target_speed_kt_max == 6.0
    assert web.state.validity_badge == "In Elite surfski envelope"

    web.state.length_m = 6.15
    web._on_hull_param_change()

    assert web.state.class_preset == "custom"
    assert web.state.length_m_min == 2.0
    assert web.state.length_m_max == 6.5
    assert web.state.validity_badge == "In Elite surfski envelope"


def test_non_canonical_hull_edit_flips_custom_without_reseeding() -> None:
    web = web_app.create_app(initial_hull=Hull())
    web.state.class_preset = "performance"
    web._apply_class_preset("performance")

    web.state.deck_height_m = 0.24
    web._on_hull_param_change()

    assert web.state.class_preset == "custom"
    assert web.state.length_m == 5.2
    assert web.state.deck_height_m == 0.24
    assert web.state.length_m_min == 2.0
    assert web.state.length_m_max == 6.5


def test_preset_seed_listener_reapplies_bounds_without_custom_flip() -> None:
    web = web_app.create_app(initial_hull=Hull())
    web.state.class_preset = "surfski_elite"
    web._apply_class_preset("surfski_elite")

    web.state.length_m_min = 2.0
    web.state.length_m_max = 6.5
    assert web._state_matches_preset_seed("surfski_elite") is True

    web._on_hull_param_change()

    assert web.state.class_preset == "surfski_elite"
    assert web.state.length_m_min == 5.8
    assert web.state.length_m_max == 6.4
    assert web.state.validity_badge == "In Elite surfski envelope"


def test_target_speed_edit_does_not_flip_class_preset() -> None:
    web = web_app.create_app(initial_hull=Hull())
    web.state.class_preset = "touring"
    web._apply_class_preset("touring")

    web.state.target_speed_kt = 4.0
    web._on_view_param_change()

    assert web.state.class_preset == "touring"
    assert web.state.target_speed_kt == 4.0
    assert web.state.length_m_min == 4.3
    assert web.state.length_m_max == 5.5
    assert web.state.validity_badge == "In Touring sea kayak envelope"


def test_resistance_mesh_and_export_render_contract_is_present() -> None:
    app_source = Path(web_app.__file__).read_text()

    assert "kg-resistance-card" in app_source
    assert "data-testid=\\\"resistance-table\\\"" in app_source
    assert "kg-resistance-row-target" in app_source
    assert "Resistance curve (raw comparative filter)" not in web_app.create_app(
        initial_hull=Hull()
    ).state.analysis_lines
    assert "kg-mesh-profile-select" in app_source
    assert "item_title=\"label\"" in app_source
    assert "kg-export-hull-stl" in app_source
    assert "kg-export-deck-stl" in app_source
    assert "kg-export-hydro-json" in app_source
    assert "kg-export-stability-json" in app_source
    assert "kg-export-mesh-package" in app_source


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
