"""Render-verification tests for workflow 0037 inline-help additions.

Closes audit batch R2 (AUD-O-001/002/003/004/006 + the in-app copy side of
AUD-O-007) from the 2026-05-25 release_candidate audit. Mirrors the
serialised-layout introspection pattern from ``tests/test_web_layout.py``:
no Trame round-trip, no Playwright, just import the rendered app and read
source / state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kayakgen.model.hull import Hull

pytest.importorskip("trame", reason="kayakgen[web] not installed")
pytest.importorskip("vtk", reason="kayakgen[web] not installed")

web_app = pytest.importorskip("kayakgen.ui.web.app")
generate_spec_form = pytest.importorskip("kayakgen.ui.web.generate_spec_form")
evaluation = pytest.importorskip("kayakgen.services.evaluation")


# ---------------------------------------------------------------------------
# AUD-O-001 — validity badge title tooltip covers all four envelope states
# ---------------------------------------------------------------------------


def test_validity_badge_title_covers_all_states() -> None:
    """``_refresh_validity_badge`` populates ``validity_badge_title`` with
    operator-facing copy for every documented envelope state."""

    web = web_app.create_app(initial_hull=Hull())

    cases = {
        "In Elite surfski envelope": ("Elite surfski", "Advisory"),
        "In Intermediate surfski envelope": (
            "Intermediate surfski",
            "Advisory",
        ),
        "Custom — sub-touring": ("below", "touring"),
        "Custom — beyond elite": ("exceeds", "elite-surfski"),
        "Custom (L/B_wl=9.2)": ("9.2", "Custom design"),
    }
    for badge, expected_fragments in cases.items():
        web.state.validity_badge = badge
        title = web_app.validity_badge_title_for(badge)
        # Direct helper result must contain the expected fragments…
        assert title, f"validity_badge_title empty for {badge!r}"
        for fragment in expected_fragments:
            assert fragment in title, (
                f"Tooltip for {badge!r} missing fragment {fragment!r}: {title!r}"
            )
        # …and must avoid internal jargon.
        assert "RFC " not in title
        assert "claim_state" not in title


def test_validity_badge_chip_binds_title_attribute() -> None:
    """The VChip rendering ``{{ validity_badge }}`` must bind a ``title``
    attribute to the live ``validity_badge_title`` state field."""

    app_source = Path(web_app.__file__).read_text()
    # The chip block must reference validity_badge_title in the bound attrs.
    assert "validity_badge_title" in app_source
    # The state init must seed the title field alongside the aria-label.
    web = web_app.create_app(initial_hull=Hull())
    assert hasattr(web.state, "validity_badge_title")
    assert isinstance(web.state.validity_badge_title, str)
    assert web.state.validity_badge_title  # non-empty default


# ---------------------------------------------------------------------------
# AUD-O-002 — comparison-source toggle subtitle distinguishes both modes
# ---------------------------------------------------------------------------


def test_comparison_source_toggle_subtitle_present() -> None:
    """The Comparison-tab toggle ships visible subtitle copy for both
    ``live_frontier`` and ``imported_report`` so neither value depends on
    clicking the button to discover its meaning."""

    app_source = Path(web_app.__file__).read_text()

    # Subtitle copy constants — defined in app.py.
    assert "Live frontier: candidates from this session" in app_source
    assert "Imported report: a saved design-report JSON" in app_source

    # Subtitle data-testid lands in the rendered HTML helper block.
    assert "comparison-source-help" in app_source

    # Per-button ``title`` tooltip must also reference the same constants.
    assert "COMPARISON_TOGGLE_LIVE_FRONTIER_HELP" in app_source
    assert "COMPARISON_TOGGLE_IMPORTED_REPORT_HELP" in app_source


# ---------------------------------------------------------------------------
# AUD-O-003 — mesh chip-pair tooltip explains both chips
# ---------------------------------------------------------------------------


def test_mesh_chip_pair_tooltips_present() -> None:
    """Both ``mesh-no-package-chip`` and ``mesh-live-readiness-chip`` carry
    a ``title`` tooltip with the documented explanation."""

    app_source = Path(web_app.__file__).read_text()

    # The no-package chip must be tagged with its title constant.
    assert "MESH_NO_PACKAGE_CHIP_TITLE" in app_source
    assert "MESH_LIVE_READINESS_CHIP_TITLE" in app_source
    assert "mesh-no-package-chip" in app_source
    assert "mesh-live-readiness-chip" in app_source

    # The constants themselves must carry operator-facing copy.
    assert "No CFD mesh package has been generated" in web_app.MESH_NO_PACKAGE_CHIP_TITLE
    assert "Live hull/deck readiness" in web_app.MESH_LIVE_READINESS_CHIP_TITLE


def test_slice3_state_hooks_are_present_in_inline_help_contract() -> None:
    """Slice 3 state surfaces keep stable hooks alongside existing help hooks."""

    from kayakgen.ui.web import generate_frontier_view

    app_source = Path(web_app.__file__).read_text()
    frontier_source = Path(generate_frontier_view.__file__).read_text()

    for hook in (
        "share-url-state",
        "invalid-hull-state",
        "comparison-no-report-state",
        "comparison-report-present-state",
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
        "frontier-view-loading",
        "frontier-view-empty",
        "frontier-view-rendered",
    ):
        assert hook in frontier_source


# ---------------------------------------------------------------------------
# AUD-O-004 — submit-button disabled reason
# ---------------------------------------------------------------------------


def _seed_valid_form_state(web: object) -> None:
    """Seed a complete + valid form-state on ``web.state``."""

    state = web.state
    state.generative_variables = [
        {
            "name": "beam_wl_m",
            "kind": "uniform",
            "min": 0.46,
            "max": 0.54,
            "count": 5,
            "values": "",
        }
    ]
    state.generative_job_kind = "search"
    state.generative_selected_objective_metrics = ["GM0_m"]
    state.generative_objective_options = ["GM0_m", "displaced_mass_kg"]
    state.generative_objective_directions = {"GM0_m": "max"}
    state.generative_evaluators = {"cfd_in_loop": False}
    state.generative_cfd_in_loop_status = "opt_in_only"
    state.generative_cfd_in_loop_acknowledged = False


def test_submit_disabled_when_no_variables() -> None:
    """An empty variables table must surface the no-variables blocking
    reason on both ``generative_submit_disabled`` and
    ``generative_submit_blocking_reason``."""

    web = web_app.create_app(initial_hull=Hull())
    _seed_valid_form_state(web)
    web.state.generative_variables = []

    generate_spec_form.refresh_submit_blocking_reason(web)

    assert web.state.generative_submit_disabled is True
    assert (
        web.state.generative_submit_blocking_reason
        == generate_spec_form.SUBMIT_BLOCKING_REASON_NO_VARIABLES
    )

    # And the visible span markup must reference the live state.
    app_source = Path(web_app.__file__).read_text()
    assert "submit-blocking-reason-search" in app_source
    assert "submit-blocking-reason-sweep" in app_source
    assert "generative_submit_blocking_reason" in app_source


def test_submit_enabled_when_form_valid() -> None:
    """A submittable form-state must produce an empty reason + an enabled
    Submit button."""

    web = web_app.create_app(initial_hull=Hull())
    _seed_valid_form_state(web)

    generate_spec_form.refresh_submit_blocking_reason(web)

    assert web.state.generative_submit_disabled is False
    assert web.state.generative_submit_blocking_reason == ""


def test_submit_disabled_when_no_objective_selected() -> None:
    """Search-kind with zero selected objectives surfaces the no-objective
    reason."""

    web = web_app.create_app(initial_hull=Hull())
    _seed_valid_form_state(web)
    web.state.generative_selected_objective_metrics = []

    generate_spec_form.refresh_submit_blocking_reason(web)

    assert web.state.generative_submit_disabled is True
    assert (
        web.state.generative_submit_blocking_reason
        == generate_spec_form.SUBMIT_BLOCKING_REASON_NO_OBJECTIVE
    )


def test_submit_button_has_aria_describedby() -> None:
    """Both kind-aware Submit buttons must point ``aria-describedby`` at the
    visible blocking-reason span."""

    app_source = Path(web_app.__file__).read_text()
    assert 'aria-describedby": "submit-blocking-reason-search' in app_source
    assert 'aria-describedby": "submit-blocking-reason-sweep' in app_source
    assert 'disabled=("generative_submit_disabled' in app_source


# ---------------------------------------------------------------------------
# AUD-O-006 — mesh-diagnostic threshold guidance
# ---------------------------------------------------------------------------


def test_mesh_diagnostics_rows_have_operator_facing_labels() -> None:
    """The diagnostic rows are English (no underscored dict keys) and the
    must-be-zero counts carry threshold guidance in the label."""

    web = web_app.create_app(initial_hull=Hull())
    state = web._state_snapshot()
    rows = evaluation.mesh_diagnostics_rows_from_state(state, part="hull")

    assert rows, "mesh_diagnostics_rows_from_state returned no rows"
    labels = [row["label"] for row in rows]
    # No raw dict keys in any label.
    for label in labels:
        assert "_" not in label, f"label {label!r} looks like a raw dict key"

    # Threshold guidance is embedded in the label slot, not a separate column.
    joined = "\n".join(labels)
    assert "Non-manifold edges (must be 0)" in joined
    assert "Degenerate faces (must be 0)" in joined
    assert "Boundary edges (perimeter; acceptable)" in joined
    assert "Readiness level" in joined


# ---------------------------------------------------------------------------
# AUD-O-007 — high-angle GZ alert drops RFC citations
# ---------------------------------------------------------------------------


def test_high_angle_gz_alert_drops_rfc_citations() -> None:
    """The high-angle GZ alert copy must point operators at the CLI / import
    recovery paths and must not cite RFCs."""

    copy = web_app.HIGH_ANGLE_GZ_COPY
    assert "RFC 0020" not in copy
    assert "RFC 0024" not in copy
    assert "RFC " not in copy
    # Recovery copy must mention the CLI command and the Comparison tab.
    assert "kayakgen stability --high-angle-gz" in copy
    assert "Comparison" in copy
    # Plain-English heading still works.
    assert "high-angle" in copy.lower()


# ---------------------------------------------------------------------------
# Wire-payload stability (AUD-P-004 regression)
# ---------------------------------------------------------------------------


_SEARCH_TOP_LEVEL_KEYS: set[str] = {
    "schema_version",
    "name",
    "base_hull",
    "search_space",
    "algorithm",
    "objectives",
    "evaluators",
    "budget",
}
_SWEEP_TOP_LEVEL_KEYS: set[str] = {
    "schema_version",
    "name",
    "base_hull",
    "variables",
    "evaluators",
}


def test_build_spec_from_form_state_wire_payload_stable() -> None:
    """``build_spec_from_form_state`` returns the same dict shape for both
    job kinds across the R2 inline-help additions. Closes AUD-P-004
    regression coverage for the wire payload."""

    # Valid search state.
    web = web_app.create_app(initial_hull=Hull())
    _seed_valid_form_state(web)
    web.state.generative_spec_name = "regression-search"
    web.state.generative_base_hull = {"length_m": 5.2}
    web.state.generative_algorithm_kind = "nsga2"
    web.state.generative_nsga2_population_size = 8
    web.state.generative_nsga2_generations = 2
    web.state.generative_seed = 1
    web.state.generative_max_evaluations = 16

    spec = generate_spec_form.build_spec_from_form_state(web.state)
    assert isinstance(spec, dict)
    assert set(spec.keys()) == _SEARCH_TOP_LEVEL_KEYS
    assert isinstance(spec["schema_version"], str)
    assert isinstance(spec["name"], str)
    assert isinstance(spec["base_hull"], dict)
    assert isinstance(spec["search_space"], dict)
    assert isinstance(spec["algorithm"], dict)
    assert isinstance(spec["objectives"], list)
    assert isinstance(spec["evaluators"], dict)
    assert isinstance(spec["budget"], dict)

    # Invalid state — empty variables — must raise (the gate predates R2
    # and must still raise after the inline-help additions).
    web2 = web_app.create_app(initial_hull=Hull())
    _seed_valid_form_state(web2)
    web2.state.generative_variables = []
    with pytest.raises(generate_spec_form.GenerateSpecFormError):
        generate_spec_form.build_spec_from_form_state(web2.state)

    # Sweep wire shape coverage on a separate state.
    web3 = web_app.create_app(initial_hull=Hull())
    _seed_valid_form_state(web3)
    web3.state.generative_job_kind = "sweep"
    web3.state.generative_spec_name = "regression-sweep"
    web3.state.generative_base_hull = {"length_m": 5.2}
    sweep_spec = generate_spec_form.build_spec_from_form_state(web3.state)
    assert isinstance(sweep_spec, dict)
    assert set(sweep_spec.keys()) == _SWEEP_TOP_LEVEL_KEYS
    assert isinstance(sweep_spec["variables"], dict)
    assert isinstance(sweep_spec["evaluators"], dict)
