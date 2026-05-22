"""Rendered desktop layout checks for slider-label visibility."""

from __future__ import annotations

import pytest

pytest.importorskip("matplotlib", reason="kayakgen[desktop] is not installed")
pytest.importorskip("PyQt6", reason="kayakgen[desktop] is not installed")

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

from kayakgen.ui.desktop import KayakGUI
from kayakgen.ui.parameter_metadata import label_with_unit


def _area_overlap(a: Bbox, b: Bbox, *, min_px: float = 0.5) -> bool:
    width = min(a.x1, b.x1) - max(a.x0, b.x0)
    height = min(a.y1, b.y1) - max(a.y0, b.y0)
    return width > min_px and height > min_px


def _assert_inside(inner: Bbox, outer: Bbox, *, label: str) -> None:
    assert inner.width > 0, f"{label} has no rendered width"
    assert inner.height > 0, f"{label} has no rendered height"
    assert inner.x0 >= outer.x0, f"{label} is clipped by the left figure edge"
    assert inner.x1 <= outer.x1, f"{label} is clipped by the right figure edge"
    assert inner.y0 >= outer.y0, f"{label} is clipped by the bottom figure edge"
    assert inner.y1 <= outer.y1, f"{label} is clipped by the top figure edge"


@pytest.mark.parametrize("canvas_px", [None, (1440, 900), (1920, 1080)])
def test_desktop_slider_labels_are_visible_and_unobstructed(
    monkeypatch, canvas_px: tuple[int, int] | None
) -> None:
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)

    gui = KayakGUI()
    if canvas_px is not None:
        width_px, height_px = canvas_px
        gui.fig.set_size_inches(width_px / gui.fig.dpi, height_px / gui.fig.dpi)
    gui.fig.canvas.draw()
    renderer = gui.fig.canvas.get_renderer()
    fig_bbox = gui.fig.bbox

    label_bboxes: dict[str, Bbox] = {}
    slider_track_bboxes: dict[str, Bbox] = {}
    valtext_bboxes: dict[str, Bbox] = {}
    for key, expected_label, _vmin, _vmax in KayakGUI.SLIDERS:
        slider = gui.sliders[key]
        # RFC 0061: slider labels are sourced from the
        # HullParameterMetadata / VIEW_PARAMETER_METADATA registry via
        # ``label_with_unit``; the SLIDERS tuple's second column is the
        # same value, but assert against the registry helper so a
        # regression in the SLIDERS-construction path also trips here.
        assert slider.label.get_text() == expected_label
        assert slider.label.get_text() == label_with_unit(key)
        assert slider.label.get_fontsize() == 7.5
        assert slider.valtext.get_fontsize() == 7.5
        label_bboxes[key] = slider.label.get_window_extent(renderer)
        slider_track_bboxes[key] = slider.ax.get_window_extent(renderer)
        valtext_bboxes[key] = slider.valtext.get_window_extent(renderer)

    button_bboxes = {
        "Export STLs": gui.btn.ax.get_window_extent(renderer),
        "Reset": gui.btn_reset.ax.get_window_extent(renderer),
        "3D View": gui.btn_3d.ax.get_window_extent(renderer),
    }
    fixed_control_bboxes = {
        "class preset controls": gui.class_radio.ax.get_window_extent(renderer),
        "status axes": gui.ax_status.get_window_extent(renderer),
        "metrics axes": gui.ax_metrics.get_window_extent(renderer),
    }
    plot_bboxes = {
        "cross-section plot": gui.ax_section.get_window_extent(renderer),
        "sheer plan plot": gui.ax_profile.get_window_extent(renderer),
        "plan-view plot": gui.ax_plan.get_window_extent(renderer),
    }

    for key, label_bbox in label_bboxes.items():
        label_text = gui.sliders[key].label.get_text()
        _assert_inside(label_bbox, fig_bbox, label=label_text)
        assert not _area_overlap(
            label_bbox, slider_track_bboxes[key]
        ), f"{label_text} overlaps its slider track"
        assert not _area_overlap(
            label_bbox, valtext_bboxes[key]
        ), f"{label_text} overlaps its value text"

        for other_key, other_bbox in label_bboxes.items():
            if other_key == key:
                continue
            assert not _area_overlap(
                label_bbox, other_bbox
            ), f"{label_text} overlaps label {gui.sliders[other_key].label.get_text()}"

        for other_key, track_bbox in slider_track_bboxes.items():
            if other_key == key:
                continue
            assert not _area_overlap(
                label_bbox, track_bbox
            ), f"{label_text} overlaps slider track for {other_key}"

        for other_key, value_bbox in valtext_bboxes.items():
            if other_key == key:
                continue
            assert not _area_overlap(
                label_bbox, value_bbox
            ), f"{label_text} overlaps value text for {other_key}"

        obstacles = {**button_bboxes, **fixed_control_bboxes, **plot_bboxes}
        for name, bbox in obstacles.items():
            assert not _area_overlap(
                label_bbox, bbox
            ), f"{label_text} overlaps {name}"

    for key, value_bbox in valtext_bboxes.items():
        value_text = f"{key} value text"
        _assert_inside(value_bbox, fig_bbox, label=value_text)
        assert not _area_overlap(
            value_bbox, slider_track_bboxes[key]
        ), f"{value_text} overlaps its slider track"
        for other_key, track_bbox in slider_track_bboxes.items():
            if other_key == key:
                continue
            assert not _area_overlap(
                value_bbox, track_bbox
            ), f"{value_text} overlaps slider track for {other_key}"
        for other_key, label_bbox in label_bboxes.items():
            assert not _area_overlap(
                value_bbox, label_bbox
            ), f"{value_text} overlaps label {gui.sliders[other_key].label.get_text()}"
        for other_key, other_value_bbox in valtext_bboxes.items():
            if other_key == key:
                continue
            assert not _area_overlap(
                value_bbox, other_value_bbox
            ), f"{value_text} overlaps value text for {other_key}"

    plt.close(gui.fig)


def test_desktop_status_segments_carry_rfc_0043_stage4_high_angle_line(
    monkeypatch,
) -> None:
    """RFC 0043 stage 4 desktop indicator (per D021 intentionally minimal):
    the status block carries a single `high_angle_gz: ...` segment that
    points at the staged opt-in CLI/sweep/comparison/web surfaces and
    preserves the unvalidated_hydrostatic_comparison wording. No safety,
    seaworthiness, calibration, or validation copy on the desktop."""
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)

    from kayakgen.ui.desktop import STATUS_SEGMENTS, KayakGUI

    gui = KayakGUI()
    try:
        block = gui._status_segments_block()
        assert "high_angle_gz" in block
        assert "unvalidated_hydrostatic_comparison" in block
        assert "cli_only" in block
        # Forbidden-copy regression on the desktop status surface. Strip
        # the explicit negated forms before the substring check so the
        # `unvalidated_hydrostatic_comparison` marker doesn't trip the
        # `validated` refusal.
        scrubbed = (
            block.replace("unvalidated_hydrostatic_comparison", "")
                 .replace("uncalibrated_comparative", "")
        )
        for forbidden in (
            "safe",
            "seaworthy",
            "validated",
            "calibrated",
            "final prediction",
            "design fitness",
        ):
            assert forbidden not in scrubbed, (
                f"desktop status must not advertise {forbidden!r}"
            )
        assert any("high_angle_gz" in seg for seg in STATUS_SEGMENTS)
    finally:
        plt.close(gui.fig)
