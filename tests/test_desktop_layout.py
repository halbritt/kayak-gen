"""Rendered desktop layout checks for slider-label visibility."""

from __future__ import annotations

import pytest

pytest.importorskip("matplotlib", reason="kayakgen[desktop] is not installed")
pytest.importorskip("PyQt6", reason="kayakgen[desktop] is not installed")

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

from kayakgen.ui.desktop import KayakGUI


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
        assert slider.label.get_text() == expected_label
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
