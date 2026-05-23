"""Render-verification tests for the desktop matplotlib slider labels.

Closes audit finding ``AUD-O-010`` from
``docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md``
(workflow 0035). RFC 0061 wires ``label_with_unit(key)`` into the
``KayakGUI.SLIDERS`` tuple but no existing test inspects the actual
matplotlib ``Slider(label=...)`` argument on the constructed widget.
``tests/test_desktop_layout.py`` already asserts label equality as part
of its geometry / non-overlap checks, but the audit asked for a
dedicated render-verification file traceable to AUD-O-010 — kept
separate so a future layout-test reshuffle cannot silently drop the
label-rendering coverage.

The test constructs a ``KayakGUI()`` headlessly (matplotlib Agg
backend, ``plt.show`` patched out) and reads
``gui.sliders[key].label.get_text()`` directly off each constructed
``matplotlib.widgets.Slider`` widget.
"""

from __future__ import annotations

import pytest

pytest.importorskip("matplotlib", reason="kayakgen[desktop] is not installed")
pytest.importorskip("PyQt6", reason="kayakgen[desktop] is not installed")

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from kayakgen.ui.desktop import KayakGUI  # noqa: E402
from kayakgen.ui.parameter_metadata import label_with_unit  # noqa: E402


# ---------------------------------------------------------------------------
# (a) full SLIDERS coverage — every constructed Slider.label.get_text()
#     must equal label_with_unit(key) for its row.
# ---------------------------------------------------------------------------


def test_every_kayakgui_slider_label_equals_registry_label_with_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each row in ``KayakGUI.SLIDERS`` must render the registry-sourced label.

    This is the load-bearing assertion for AUD-O-010. The test reads
    ``gui.sliders[key].label.get_text()`` directly off each matplotlib
    ``Slider`` instance — the value matplotlib renders to screen — and
    asserts it equals ``label_with_unit(key)`` from the central
    registry. A regression where the SLIDERS-construction path stops
    sourcing the second column from ``label_with_unit`` (or where the
    registry stops returning the expected string for a given key) trips
    this test.
    """

    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)

    gui = KayakGUI()
    try:
        # Iterate KayakGUI.SLIDERS directly so a future change to
        # _NON_HULL_GUI_KEYS or to the row order is followed
        # automatically — the test pins the per-row contract, not a
        # hardcoded list of keys.
        for key, slider_label, _vmin, _vmax in KayakGUI.SLIDERS:
            slider = gui.sliders[key]
            rendered = slider.label.get_text()
            expected = label_with_unit(key)

            # The SLIDERS tuple's second column is the same value we
            # expect, but assert against the registry helper directly so
            # a regression in the SLIDERS-construction path (e.g. a
            # hardcoded literal sneaks in) also trips this test.
            assert rendered == expected, (
                f"KayakGUI slider for {key!r} rendered label "
                f"{rendered!r}, expected {expected!r} from "
                f"label_with_unit({key!r}). AUD-O-010 regression: the "
                "registry-sourced label wiring no longer reaches the "
                "matplotlib Slider widget."
            )
            # Cross-check the SLIDERS-tuple second column too: if it
            # ever drifts from the registry, the dedicated assertion
            # above already fails, but this catches the related case
            # where the tuple value is constructed from a stale source.
            assert rendered == slider_label, (
                f"KayakGUI.SLIDERS[{key!r}] second column is "
                f"{slider_label!r} but the constructed widget rendered "
                f"{rendered!r}; the SLIDERS tuple and the Slider widget "
                "have drifted."
            )
    finally:
        plt.close(gui.fig)


# ---------------------------------------------------------------------------
# (b) named spot checks — three stable, easy-to-read fixtures the audit
#     explicitly calls out. These catch a registry-side label rename or
#     a wiring drop without requiring a test rerun to inspect the diff.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "expected_label"),
    [
        # `Cp` carries `unit=None`; label_with_unit returns the bare label
        # (no trailing parens). The audit named this row explicitly.
        ("Cp", "Prismatic coefficient (Cp)"),
        # `length_m` is the canonical dimensional Hull field; its rendered
        # label must round-trip through the registry, not the raw key.
        ("length_m", "Length (m)"),
        # `target_speed_kt` is the sole view-only parameter (lives in
        # VIEW_PARAMETER_METADATA, not HULL_PARAMETER_METADATA). Pinning
        # it here catches the two-registry fall-back drift case.
        ("target_speed_kt", "Target speed (kt)"),
    ],
)
def test_named_slider_label_spot_checks(
    monkeypatch: pytest.MonkeyPatch, key: str, expected_label: str
) -> None:
    """Three named spot checks on the matplotlib Slider rendered label.

    The bare-string assertion is the finger-test that catches a
    registry-side label rename without requiring a test rerun to read
    the diff — if the registry label changes intentionally, this
    assertion must be updated in lockstep with
    ``kayakgen/ui/parameter_metadata.py``.
    """

    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)

    gui = KayakGUI()
    try:
        assert key in gui.sliders, (
            f"KayakGUI did not construct a Slider for {key!r}; "
            f"available slider keys: {sorted(gui.sliders)}"
        )
        slider = gui.sliders[key]
        rendered = slider.label.get_text()

        # Round-trip through label_with_unit — the registry helper is
        # the source of truth for the rendered string.
        assert rendered == label_with_unit(key), (
            f"Slider {key!r} rendered label {rendered!r} does not equal "
            f"label_with_unit({key!r})={label_with_unit(key)!r}; the "
            "registry-sourced label wiring on the desktop has drifted."
        )

        # Bare-string finger-test — independent of label_with_unit's
        # behaviour. If the registry intentionally renames a label, this
        # is the assertion the change must update.
        assert rendered == expected_label, (
            f"Slider {key!r} rendered label {rendered!r} does not match "
            f"the spot-check fixture {expected_label!r}; either the "
            "registry label was renamed (update this fixture in lockstep "
            "with kayakgen/ui/parameter_metadata.py) or the wiring on "
            "the desktop slider construction is broken."
        )
    finally:
        plt.close(gui.fig)
