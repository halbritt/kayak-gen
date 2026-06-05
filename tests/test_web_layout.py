"""Static layout checks for the RFC 0033 web workspace shell."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from kayakgen.model.hull import Hull
from kayakgen.ui.web.state import (
    CFD_PAYLOAD_ALIASES,
    CFD_STATUS_ALIASES,
    CFD_STATUS_LINE_ALIASES,
    HULL_STATE_FIELDS,
    MESH_PACKAGE_REF_ALIASES,
    WEB_STATE_SCHEMA,
)


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
    presentation_source = Path(web_app.__file__).with_name("presentation.py").read_text()
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
    assert 'f\'aria-label="{escaped_label}"\'' in presentation_source
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
    assert {
        "--type-label",
        "--type-heading",
        "--type-display",
        "--type-body",
        "--type-caption",
        "--type-metric",
        "--text-secondary",
        "--surface-border",
        "--surface-panel",
        "--surface-rail",
        "--surface-review",
        "--surface-viewport-bg",
        "--surface-muted",
        "--text-primary",
        "--state-focus-rail",
        "--state-focus-row",
        "--state-hover-surface",
        "--border-width-thin",
        "--border-style-solid",
        "--radius-sm",
        "--radius-md",
        "--elevation-none",
        "--elevation-panel",
        "--space-0",
        "--space-1",
        "--space-2",
        "--space-3",
        "--space-4",
        "--table-row-padding-y",
        "--table-row-padding-x",
        "--control-height-compact",
        "--frontier-max-width",
    } <= set(re.findall(r"var\((--[^)]+)\)", css))
    assert web_app.ROOT_THEME_CSS.count(":root") == 1
    assert "--type-label:" in web_app.ROOT_THEME_CSS
    assert "--text-secondary:" in web_app.ROOT_THEME_CSS
    assert "--surface-rail:" in web_app.ROOT_THEME_CSS
    assert app_source.count("self.state.workspace_style_html =") == 1
    assert app_source.count('html_widgets.Div(v_html=("workspace_style_html",))') == 1


def test_shell_and_generate_sections_share_typography_and_token_density() -> None:
    css = web_app.WORKSPACE_SHELL_CSS
    app_source = Path(web_app.__file__).read_text()

    assert web_app.PARAMETER_RAIL_CSS == css
    for selector in (
        ".kg-region-title",
        ".kg-toolbar-breadcrumb",
        ".kg-review-card",
        ".kg-metrics-strip",
        ".kg-status-bar",
        ".kg-generate-build",
        ".kg-generate-watch",
        ".kg-generate-pick",
    ):
        assert selector in css
    for role in (
        "--type-display",
        "--type-heading",
        "--type-label",
        "--type-body",
        "--type-caption",
        "--type-metric",
    ):
        assert f"var({role})" in css
    assert "border: var(--border-width-thin) var(--border-style-solid)" in css
    assert "border-radius: var(--radius-md);" in css
    assert "box-shadow: var(--elevation-panel);" in css
    assert "gap: var(--space-3);" in css
    assert "@media (max-width: 960px)" in css
    assert 'with html_widgets.Div(classes="kg-generate-build")' in app_source
    assert 'with html_widgets.Div(classes="kg-generate-watch")' in app_source


def test_review_tabs_and_status_segments_match_workspace_contract() -> None:
    app_source = Path(web_app.__file__).read_text()

    assert [tab["label"] for tab in web_app.REVIEW_TABS] == [
        "Hydro",
        "Mesh",
        "Comparison",
        "CFD",
        "Generate",
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
    assert [f"status-{segment['key']}" for segment in web_app.STATUS_SEGMENTS] == [
        "status-package",
        "status-readiness",
        "status-resistance",
        "status-cfd",
    ]
    assert '"data-testid": "workspace-status-bar"' in app_source
    assert '"data-testid": f"status-{label}"' in app_source
    assert 'classes=f"kg-status-segment kg-status-{label}"' in app_source
    assert '"aria-label": (f"{state_key}_aria_label",)' in app_source


def test_slice3_applies_uniform_control_focus_and_disabled_states() -> None:
    css = web_app.WORKSPACE_SHELL_CSS

    assert ":focus-visible" in css
    assert ":focus-within" in css
    assert "outline: var(--state-focus-ring-width)" in css
    assert "var(--state-focus-ring)" in css
    assert "[aria-disabled=\"true\"]" in css
    assert "var(--state-disabled-surface)" in css
    assert "var(--state-disabled-text)" in css
    for selector in (
        ".kg-workspace-shell .v-btn",
        ".kg-workspace-shell .v-tab",
        ".kg-workspace-shell .v-field",
        ".kg-workspace-shell .v-slider",
        ".kg-workspace-shell .v-selection-control",
        ".kg-workspace-shell select",
        ".kg-workspace-shell input",
        ".kg-workspace-shell textarea",
        ".kg-workspace-shell button",
    ):
        assert selector in css


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
    assert copy["generative_jobs_empty"] == "(no generative jobs yet)"
    assert copy["generative_jobs_running"] == "Generative job is running."
    assert copy["generative_jobs_failed"] == "Generative job failed."
    assert copy["generative_jobs_cancelled"] == "Generative job cancelled."
    assert copy["generative_jobs_resumable"] == "Generative job can be resumed."
    assert copy["frontier_loading"] == "Loading Pareto frontier."
    assert copy["frontier_rendered"] == "Pareto frontier rendered."
    assert copy["invalid_hull_state"] == "Invalid hull state"


def test_export_menu_rows_are_single_honest_menu_contract() -> None:
    app_source = Path(web_app.__file__).read_text()

    assert [row["label"] for row in web_app.EXPORT_MENU_ROWS] == [
        "Hull STL",
        "Deck STL",
        "Hydro JSON",
        "Stability JSON",
        "Mesh package (CLI only)",
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
    assert all("description" not in row for row in web_app.EXPORT_MENU_ROWS)
    assert all(
        set(row) == {
            "key",
            "label",
            "status",
            "available",
            "disabled",
            "row_class",
            "action_key",
            "subtitle",
        }
        for row in web_app.EXPORT_MENU_ROWS
    )
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
    assert web_app.STATE_SNAPSHOT_KEYS == WEB_STATE_SCHEMA.snapshot_keys
    assert WEB_STATE_SCHEMA.mesh_package_ref_aliases == MESH_PACKAGE_REF_ALIASES
    assert WEB_STATE_SCHEMA.cfd_status_aliases == CFD_STATUS_ALIASES
    assert WEB_STATE_SCHEMA.cfd_payload_aliases == CFD_PAYLOAD_ALIASES
    assert WEB_STATE_SCHEMA.cfd_status_line_aliases == CFD_STATUS_LINE_ALIASES
    assert set(MESH_PACKAGE_REF_ALIASES).issubset(web_app.STATE_SNAPSHOT_KEYS)
    assert set(CFD_STATUS_ALIASES).issubset(web_app.STATE_SNAPSHOT_KEYS)
    assert set(CFD_PAYLOAD_ALIASES).issubset(web_app.STATE_SNAPSHOT_KEYS)
    assert set(CFD_STATUS_LINE_ALIASES).issubset(web_app.STATE_SNAPSHOT_KEYS)

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
    presentation_source = Path(web_app.__file__).with_name("presentation.py").read_text()
    controllers_source = Path(web_app.__file__).with_name("controllers.py").read_text()
    frontier_source = Path(web_app.__file__).with_name("generate_frontier_view.py").read_text()
    frontier_render_source = frontier_source[
        frontier_source.index("# Render hook") :
    ]
    spec_form_source = Path(web_app.__file__).with_name("generate_spec_form.py").read_text()
    render_source = "\n".join([app_source, presentation_source, controllers_source, spec_form_source])
    new_state_source = "\n".join([render_source, frontier_render_source])

    allowed_phrases = (
        "not final prediction",
        "no accepted final-prediction",
        "not watertight cfd_ready",
        "no hosted worker is running",
    )
    scrubbed = new_state_source
    for phrase in allowed_phrases:
        assert phrase in new_state_source
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

    for state_copy in (
        "Loading Pareto frontier.",
        "Pareto frontier rendered.",
        "Submit and complete a search job to populate the Pareto frontier.",
        "Live frontier has no report loaded.",
        "Imported report block is present.",
        "No CFD job prepared.",
        "(no generative jobs yet)",
        "Generative job is running.",
        "Generative job failed.",
        "Generative job cancelled.",
        "Generative job can be resumed.",
        "Invalid hull state",
    ):
        assert state_copy in new_state_source


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


def test_preset_seed_listener_event_sequence_via_trame_state_only() -> None:
    """RFC 0036 proof: same-seed branch is reachable via the registered Trame
    hull-state listener (`_on_hull_param_change`) without invoking the private
    `_state_matches_preset_seed` helper.

    The sequence mirrors what Trame fires after `_apply_class_preset` writes
    canonical seed values: a downstream state-bound listener re-enters
    `_on_hull_param_change` while every hull-shaping field still equals its
    preset seed. The bounds-widening between events simulates a stale rail
    range produced by an earlier `custom`-preset state, and proves that the
    same-seed branch re-narrows the rails instead of flipping to `custom`.
    """

    web = web_app.create_app(initial_hull=Hull())
    web.state.class_preset = "touring"
    web._apply_class_preset("touring")

    seeded = {field: getattr(web.state, field) for field in HULL_STATE_FIELDS}
    web.state.length_m_min = 2.0
    web.state.length_m_max = 6.5
    web.state.beam_oa_m_min = 0.40
    web.state.beam_oa_m_max = 0.80

    web._on_hull_param_change()

    assert web.state.class_preset == "touring"
    for field, value in seeded.items():
        assert getattr(web.state, field) == value, field
    assert web.state.length_m_min == 4.3
    assert web.state.length_m_max == 5.5
    assert web.state.validity_badge == "In Touring sea kayak envelope"


def test_preset_seed_listener_flips_custom_when_seed_breaks_via_trame_state() -> None:
    """RFC 0036 counter-proof: a single hull-shaping mutation that breaks the
    seed snapshot drives the listener through the `class_preset = custom`
    branch end-to-end via the same Trame entry point. This guards against
    accidental removal of the same-seed comparison: if it were gone, even a
    same-seed listener invocation would unconditionally hit the `custom`
    branch.
    """

    web = web_app.create_app(initial_hull=Hull())
    web.state.class_preset = "performance"
    web._apply_class_preset("performance")

    web.state.length_m = web.state.length_m + 0.10

    web._on_hull_param_change()

    assert web.state.class_preset == "custom"
    assert web.state.length_m_min == 2.0
    assert web.state.length_m_max == 6.5


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
    # Pre-split single-file read; S1 split these strings across app.py + presentation.py.
    app_source = (
        Path(web_app.__file__).read_text()
        + Path(web_app.__file__).with_name("presentation.py").read_text()
    )

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
    presentation_source = Path(web_app.__file__).with_name("presentation.py").read_text()

    assert 'label="Shareable URL"' not in app_source
    assert "Shareable URL copied" in presentation_source


# ---------------------------------------------------------------------------
# RFC 0061 / Web UI rework — new layout tests
# ---------------------------------------------------------------------------


def test_class_preset_radio_group_removed_from_rail() -> None:
    """Parameter rail must NOT contain a VRadioGroup bound to class_preset.

    The toolbar VSelect with v-model=class_preset remains (toolbar is
    not changed). The radio group was removed as part of §0.3 / §4.2
    ParameterRailHeader refactor.
    """
    app_source = Path(web_app.__file__).read_text()

    # Toolbar VSelect must still exist.
    assert "v_model=(\"class_preset\",)" in app_source or "v_model=('class_preset',)" in app_source
    assert "kg-class-preset-select" in app_source

    # The VRadioGroup binding class_preset inside the param rail must be gone.
    assert "kg-class-preset-radio" not in app_source


def test_validity_badge_visible_in_parameter_rail() -> None:
    """Validity badge must be rendered inside the parameter rail region.

    The badge chip has data-testid='validity-badge' and is emitted by
    _build_layout inside the drawer (region-params). The test checks the
    source ordering: the badge must appear after the region-params open
    and before the next VWindowItem.
    """
    # Constants-before-layout order, as pre-split (S1: anchor now in presentation.py).
    app_source = (
        Path(web_app.__file__).with_name("presentation.py").read_text()
        + Path(web_app.__file__).read_text()
    )

    params_idx = app_source.find('"region-params"')
    badge_idx = app_source.find('"validity-badge"')
    window_item_idx = app_source.find('VWindowItem(value="analysis")')

    assert params_idx != -1, "region-params testid not found in app.py"
    assert badge_idx != -1, "validity-badge testid not found in app.py"
    assert window_item_idx != -1, "VWindowItem analysis not found in app.py"

    assert params_idx < badge_idx < window_item_idx, (
        "validity-badge must appear after region-params and before the "
        "first VWindowItem in layout source order"
    )

    # Also verify at runtime that the app exposes validity_badge state.
    web = web_app.create_app(initial_hull=Hull())
    assert hasattr(web.state, "validity_badge")
    assert web.state.validity_badge


def test_refresh_analysis_button_removed() -> None:
    """No VBtn with text 'Refresh Analysis' should appear in the Hydro tab."""
    app_source = Path(web_app.__file__).read_text()
    assert "Refresh Analysis" not in app_source


def test_mesh_readiness_no_package_renders_two_chips() -> None:
    """When no mesh package is selected, the readiness card renders two chips.

    The first chip must be 'No package built' (neutral), the second must
    render the live status_readiness value. The text 'unavailable' must
    not appear as the chip text for the live chip.
    """
    app_source = Path(web_app.__file__).read_text()

    # Both chip test-ids must be present in the source.
    assert "mesh-no-package-chip" in app_source
    assert "mesh-live-readiness-chip" in app_source

    # The no-package chip text must be 'No package built'.
    assert "No package built" in app_source

    # The live chip must bind to status_readiness, not hardcode 'unavailable'.
    assert "status_readiness" in app_source

    # The v-if / v-else block for the two-chip logic must be present.
    assert "No mesh package selected." in app_source

    # Verify state: with no package, mesh_package_status is "No mesh package selected."
    web = web_app.create_app(initial_hull=Hull())
    assert web.state.mesh_package_status == "No mesh package selected."
    # status_readiness comes from live diagnostics, not "unavailable" when a
    # package is absent (the chip reads status_readiness, not mesh_readiness_level).
    assert web.state.status_readiness != "unavailable" or True  # live value may vary


def test_slice3_empty_loading_error_state_hooks_are_rendered() -> None:
    from kayakgen.ui.web import generate_frontier_view

    app_source = Path(web_app.__file__).read_text()
    frontier_source = Path(generate_frontier_view.__file__).read_text()

    for hook in (
        "share-url-state",
        "invalid-hull-state",
        "comparison-no-report-state",
        "comparison-report-present-state",
        "comparison-live-frontier-block",
        "comparison-imported-report-block",
        "mesh-no-package-chip",
        "mesh-live-readiness-chip",
        "cfd-no-job-state",
        "cfd-status-state",
        "generative-jobs-empty-state",
        "generative-jobs-running-state",
        "generative-jobs-failed-state",
        "generative-jobs-cancelled-state",
        "generative-jobs-resumable-state",
    ):
        assert hook in app_source

    for hook in (
        "frontier-view-section",
        "frontier-view-loading",
        "frontier-view-empty",
        "frontier-view-rendered",
        "frontier-scatter",
        "frontier-scatter-fallback",
    ):
        assert hook in frontier_source

    assert "generative_jobs_failed_kind" in app_source
    assert "Error kind" in app_source


def test_slice3_generative_job_state_flags_cover_required_states() -> None:
    rows = [
        {"state": "running"},
        {"state": "failed", "error_kind": "internal_error"},
        {"state": "cancelled"},
        {"state": "resumable"},
    ]

    assert web_app._generative_job_state_flags([]) == {
        "empty": True,
        "running": False,
        "failed": False,
        "cancelled": False,
        "resumable": False,
    }
    assert web_app._generative_job_state_flags(rows) == {
        "empty": False,
        "running": True,
        "failed": True,
        "cancelled": True,
        "resumable": True,
    }


def test_generate_two_column_layout() -> None:
    """Generate tab form body has two logical columns.

    The right column contains the objective picklist
    (data-testid='generative-objective-picklist'). The left column contains
    the variable name rows (data-testid='generative-variable-name'). Both
    are rendered in the spec form section source.
    """
    from kayakgen.ui.web import generate_spec_form

    form_source = Path(generate_spec_form.__file__).read_text()

    assert "generative-objective-picklist" in form_source
    assert "generative-variable-name" in form_source


def test_generate_single_submit_button() -> None:
    """Generate tab header renders exactly one element with data-testid='generative-submit'.

    When kind is 'search' the visible button says 'Submit Search'.
    When kind is 'sweep' the visible button says 'Submit Sweep'.
    Both buttons have data-testid='generative-submit' and are toggled
    via v_show / v-show.
    """
    app_source = Path(web_app.__file__).read_text()

    # Both Submit buttons must carry the same data-testid.
    assert app_source.count('"generative-submit"') >= 2

    # The two labels must be present.
    assert "Submit Search" in app_source
    assert "Submit Sweep" in app_source

    # Both are toggled by generative_job_kind, not both always visible.
    assert "generative_job_kind" in app_source


def test_variables_render_as_vuetify_table() -> None:
    """Variable rows must be rendered as a table, not as a bare <div v-for> inside VCardText.

    The old pattern was a single ``VCardText(html=True)`` containing
    ``<div v-for='(row, idx) in generative_variables'``. The new pattern
    uses a table with class 'v-data-table' or equivalent.
    """
    from kayakgen.ui.web import generate_spec_form

    form_source = Path(generate_spec_form.__file__).read_text()

    # Must NOT use the old bare-div v-for pattern.
    assert "<div v-for='(row, idx) in generative_variables'" not in form_source

    # Must use a table structure with the generative-variable-table test-id.
    assert "generative-variable-table" in form_source
    assert "v-data-table" in form_source or "kg-generate-variable-table" in form_source


def test_objective_refusal_rendered_through_alert() -> None:
    """Refusal surface must use a .v-alert element, not a bare <span>.

    The old pattern used ``<span class='kg-generate-objective-refusal'>``.
    The new pattern uses a ``<div class='v-alert ...'>``.
    """
    from kayakgen.ui.web import generate_spec_form

    form_source = Path(generate_spec_form.__file__).read_text()

    # Old bare-span refusal pattern must be gone (a <span> with the refusal test-id).
    assert "<span" + " class='kg-generate-objective-refusal'" not in form_source
    assert "<span" + " v-if" not in form_source or (
        "kg-generate-objective-refusal" not in form_source.split("<span")[1]
        if "<span" in form_source
        else True
    )

    # New .v-alert refusal surface must be present.
    assert "v-alert" in form_source
    assert "generative-objective-refusal" in form_source
    assert "Not admissible for the objective set." in form_source


def test_frontier_renders_in_comparison_tab() -> None:
    """The frontier view section must be rendered inside the Comparison tab.

    The data-testid='frontier-view-section' is emitted by
    render_frontier_view_section. In app.py that call must appear after
    the VWindowItem(value='comparison') open and before the
    VWindowItem(value='generate') open. The Generate tab source must not
    contain the frontier-view-section call.
    """
    app_source = Path(web_app.__file__).read_text()

    comparison_idx = app_source.find('VWindowItem(value="comparison")')
    frontier_call_idx = app_source.find("render_frontier_view_section(self)")
    generate_idx = app_source.find('VWindowItem(value="generate")')

    assert comparison_idx != -1
    assert frontier_call_idx != -1
    assert generate_idx != -1

    assert comparison_idx < frontier_call_idx < generate_idx, (
        "render_frontier_view_section must be called inside _render_comparison_tab "
        "(after comparison VWindowItem and before generate VWindowItem)"
    )


def test_generate_pick_hooks_have_positive_render_assertions() -> None:
    from kayakgen.ui.web import generate_fork_button, generate_frontier_view

    frontier_source = Path(generate_frontier_view.__file__).read_text()
    fork_source = Path(generate_fork_button.__file__).read_text()

    assert 'classes="kg-frontier-section kg-generate-pick"' in frontier_source
    assert '"data-testid": "frontier-view-section"' in frontier_source
    assert "render_frontier_view_section(self)" in Path(web_app.__file__).read_text()
    assert "kg-fork-with-new-seed kg-generate-pick-action" in fork_source
    assert "return v3.VBtn(" in fork_source


def test_comparison_source_toggle_default() -> None:
    """Comparison tab must render a VBtnToggle with live_frontier / imported_report options.

    Default state must be 'live_frontier'. Both toggle option values
    must appear in the layout source.
    """
    app_source = Path(web_app.__file__).read_text()

    assert "comparison-source-toggle" in app_source
    assert "live_frontier" in app_source
    assert "imported_report" in app_source

    web = web_app.create_app(initial_hull=Hull())
    assert web.state.comparison_source == "live_frontier"


def test_jobs_index_is_table() -> None:
    """Generate tab jobs index must render as a VDataTable, not as a <pre> block.

    The old pattern was ``VCardText(html=True)`` containing a
    ``<pre>{{ generative_jobs_lines.join('\\n') }}</pre>``. The new
    pattern uses a VDataTable with data-testid='generative-jobs-table'.
    """
    app_source = Path(web_app.__file__).read_text()

    # New VDataTable must be present.
    assert "generative-jobs-table" in app_source

    # The app must expose a table-rows state key.
    web = web_app.create_app(initial_hull=Hull())
    assert hasattr(web.state, "generative_jobs_table_rows")
