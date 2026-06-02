from __future__ import annotations

import ast
import math
import re
from pathlib import Path

import pytest

from kayakgen.ui import theme


UI_ROOT = Path(__file__).resolve().parents[1] / "kayakgen" / "ui"
THEME_PATH = UI_ROOT / "theme.py"

HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?(?:[0-9A-Fa-f]{2})?\b")
DIMENSION_LITERAL_RE = re.compile(r"(?<![\w-])-?\d+(?:\.\d+)?(?:px|rem|em)\b")
CSS_PROPERTY_NAME_RE = re.compile(
    r"\b(?:border-radius|box-shadow|outline-width|outline)\s*:",
    re.IGNORECASE,
)
FOCUS_PROPERTY_NAME_RE = re.compile(r"\bfocus(?:-ring)?\s*:", re.IGNORECASE)
GRAYSCALE_COLOR_RE = re.compile(r"^(?:0(?:\.\d+)?|1(?:\.0+)?)$")
COLOR_NAME_LITERALS = frozenset(
    {
        "black",
        "blue",
        "brown",
        "crimson",
        "cyan",
        "green",
        "grey",
        "gray",
        "k",
        "magenta",
        "navy",
        "orange",
        "pink",
        "purple",
        "red",
        "royalblue",
        "seagreen",
        "slateblue",
        "steelblue",
        "teal",
        "white",
        "yellow",
    }
)


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.removeprefix("#")
    return tuple(int(value[index : index + 2], 16) / 255.0 for index in (0, 2, 4))


def _linear_channel(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    red, green, blue = (_linear_channel(channel) for channel in _hex_to_rgb(hex_color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _lab(hex_color: str) -> tuple[float, float, float]:
    red, green, blue = (_linear_channel(channel) for channel in _hex_to_rgb(hex_color))
    x = (0.4124 * red + 0.3576 * green + 0.1805 * blue) / 0.95047
    y = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    z = (0.0193 * red + 0.1192 * green + 0.9505 * blue) / 1.08883

    def pivot(value: float) -> float:
        if value > 0.008856:
            return value ** (1.0 / 3.0)
        return 7.787 * value + 16.0 / 116.0

    fx, fy, fz = pivot(x), pivot(y), pivot(z)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def _cie76_delta_e(left: str, right: str) -> float:
    lab_left = _lab(left)
    lab_right = _lab(right)
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab_left, lab_right, strict=True)))


def test_css_vuetify_and_matplotlib_helpers_use_shared_tokens() -> None:
    css = theme.css_root_block()
    assert "--surface-viewport-bg: #e7f0ec;" in css
    assert "--font-mono:" in css
    assert "--space-3: 0.75rem;" in css
    assert "--viewport-height: 520px;" in css
    assert "--radius-sm: 4px;" in css
    assert "--elevation-panel:" in css
    assert "--border-width-thin: 1px;" in css
    assert "--state-focus-ring: #005f5b;" in css
    assert "--state-focus-ring-width: 2px;" in css
    assert "--state-hover-surface:" in css
    assert theme.css_root_block(dark=True) != css

    vuetify = theme.vuetify_theme_config()
    themes = vuetify["themes"]
    assert vuetify["defaultTheme"] == "kayakgenLight"
    assert (
        themes["kayakgenLight"]["colors"]["viewport"]
        == theme.COLORS_LIGHT["surface-viewport-bg"]
    )
    assert themes["kayakgenDark"]["colors"]["viewport"] == theme.COLORS_DARK["surface-viewport-bg"]
    assert themes["kayakgenLight"]["colors"]["focus-ring"] == theme.COLORS_LIGHT[
        "state-focus-ring"
    ]
    assert themes["kayakgenDark"]["colors"]["state-hover-surface"] == theme.COLORS_DARK[
        "state-hover-surface"
    ]
    assert themes["kayakgenLight"]["variables"]["focus-ring-width"] == theme.BORDERS[
        "state-focus-ring-width"
    ]

    rc_params = theme.matplotlib_rc_params()
    assert rc_params["axes.facecolor"] == theme.COLORS_LIGHT["surface-panel"]
    assert rc_params["grid.color"] == theme.COLORS_LIGHT["surface-viewport-grid"]
    assert theme.PLOT_PALETTE["hull"] == theme.COLORS_LIGHT["data-hull"]
    assert theme.PLOT_PALETTE["deck"] == theme.COLORS_LIGHT["data-deck"]


@pytest.mark.parametrize(
    ("dark", "tokens"),
    [(False, theme.COLORS_LIGHT), (True, theme.COLORS_DARK)],
)
def test_vtk_background_rgb_matches_viewport_token(dark: bool, tokens: theme.ColorTokens) -> None:
    expected = _hex_to_rgb(tokens["surface-viewport-bg"])
    assert theme.vtk_background_rgb(dark=dark) == expected
    assert theme.vtk_background_rgb(dark=dark) != (0.10, 0.10, 0.18)
    assert all(0.0 <= channel <= 1.0 for channel in theme.vtk_background_rgb(dark=dark))


@pytest.mark.parametrize(
    ("palette_name", "tokens"),
    [("light", theme.COLORS_LIGHT), ("dark", theme.COLORS_DARK)],
)
def test_contrast_manifest_clears_thresholds(
    palette_name: str,
    tokens: theme.ColorTokens,
) -> None:
    for pair in theme.CONTRAST_MANIFEST:
        foreground = tokens[pair.foreground_token]
        background = tokens[pair.background_token]
        ratio = _contrast_ratio(foreground, background)
        assert ratio >= pair.min_ratio, (
            f"{palette_name}.{pair.name} contrast {ratio:.2f} below {pair.min_ratio:.2f}"
        )


def test_slider_label_contrast_pair_is_manifested() -> None:
    assert any(
        pair.name == "slider.label.rail"
        and pair.foreground_token == "text-secondary"
        and pair.background_token == "surface-rail"
        for pair in theme.CONTRAST_MANIFEST
    )


def test_new_visual_token_maps_are_additive_and_resolved() -> None:
    assert theme.SPACING["space-3"] == "0.75rem"
    assert theme.DENSITY["viewport-height"] == "520px"
    assert theme.DENSITY["frontier-max-width"] == "480px"
    assert theme.DENSITY["collapse-breakpoint"] == "960px"
    assert theme.RADII["radius-sm"] == "4px"
    assert theme.BORDERS["border-width-thin"] == "1px"
    assert theme.BORDERS["state-focus-ring-width"] == "2px"
    assert theme.ELEVATION["elevation-none"] == "none"

    color_bearing = {
        "state-focus-ring",
        "state-hover-surface",
        "state-hover-text",
        "state-active-surface",
        "state-active-text",
        "state-disabled-surface",
        "state-disabled-text",
    }
    assert color_bearing <= theme.COLORS_LIGHT.keys()
    assert color_bearing <= theme.COLORS_DARK.keys()


def test_new_visual_token_contrast_pairs_are_manifested() -> None:
    manifested = {pair.name for pair in theme.CONTRAST_MANIFEST}
    assert {
        "focus.ring.panel",
        "focus.ring.viewport",
        "state.hover",
        "state.active",
        "state.disabled",
    } <= manifested


@pytest.mark.parametrize(
    ("palette_name", "tokens"),
    [("light", theme.COLORS_LIGHT), ("dark", theme.COLORS_DARK)],
)
def test_advisory_yellow_and_raw_orange_are_perceptually_distinct(
    palette_name: str,
    tokens: theme.ColorTokens,
) -> None:
    delta = _cie76_delta_e(tokens["state-advisory"], tokens["state-raw"])
    assert delta >= 20.0, f"{palette_name} advisory/raw separation is only {delta:.1f}"

    text_delta = _cie76_delta_e(tokens["state-advisory-text"], tokens["state-raw-text"])
    assert text_delta >= 20.0, (
        f"{palette_name} advisory/raw text separation is only {text_delta:.1f}"
    )


def test_no_orphan_visual_literals_under_kayakgen_ui() -> None:
    offenders: list[str] = []
    for path in sorted(UI_ROOT.rglob("*.py")):
        if path == THEME_PATH or "__pycache__" in path.parts:
            continue
        offenders.extend(_visual_literal_offenders(path))

    assert offenders == [], (
        "Visual literals outside kayakgen/ui/theme.py:\n" + "\n".join(offenders)
    )


def test_visual_literal_lint_fails_on_planted_literal(tmp_path: Path) -> None:
    planted = tmp_path / "planted.py"
    planted.write_text(
        "\n".join(
            [
                "STYLE = 'padding: 12px;'",
                "RADIUS = 'border-radius: 4px;'",
                "SHADOW = 'box-shadow: 0 1px 2px rgb(0 0 0 / 0.1);'",
                "OUTLINE = 'outline-width: 2px;'",
                "FOCUS = 'focus-ring: #005f5b;'",
            ]
        ),
        encoding="utf-8",
    )

    offenders = _visual_literal_offenders(planted)
    assert len(offenders) >= 5
    assert any("12px" in offender for offender in offenders)
    assert any("border-radius" in offender for offender in offenders)
    assert any("box-shadow" in offender for offender in offenders)
    assert any("outline-width" in offender for offender in offenders)
    assert any("focus-ring" in offender for offender in offenders)


def _visual_literal_offenders(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    lines = source.splitlines()
    offenders: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.strip()
            normalized = value.lower()
            if (
                HEX_COLOR_RE.fullmatch(value)
                or normalized in COLOR_NAME_LITERALS
                or GRAYSCALE_COLOR_RE.fullmatch(normalized)
            ):
                offenders.append(_format_offender(path, node.lineno, value))
            offenders.extend(_css_visual_literal_offenders(path, node.lineno, value))

        if isinstance(node, ast.Call):
            offenders.extend(_rgb_call_offenders(path, node))

    for match in HEX_COLOR_RE.finditer(source):
        line_number = source.count("\n", 0, match.start()) + 1
        line_text = lines[line_number - 1]
        if "theme.py" not in line_text:
            offender = _format_offender(path, line_number, match.group(0))
            if offender not in offenders:
                offenders.append(offender)

    return offenders


def _css_visual_literal_offenders(path: Path, line_number: int, value: str) -> list[str]:
    offenders: list[str] = []
    for match in DIMENSION_LITERAL_RE.finditer(value):
        offenders.append(_format_offender(path, line_number, match.group(0)))
    for pattern in (CSS_PROPERTY_NAME_RE, FOCUS_PROPERTY_NAME_RE):
        for match in pattern.finditer(value):
            suffix = value[match.end() :].lstrip()
            if suffix and not suffix.startswith("var(--"):
                offenders.append(_format_offender(path, line_number, match.group(0).strip()))
    return offenders


def _rgb_call_offenders(path: Path, node: ast.Call) -> list[str]:
    call_name = _call_name(node.func)
    offenders: list[str] = []

    if call_name in {"SetBackground", "SetColor"} and len(node.args) >= 3:
        args = node.args[:3]
        if all(_is_numeric_unit_constant(arg) for arg in args):
            offenders.append(_format_offender(path, node.lineno, ast.unparse(node)))

    rgb_literal_keywords = {"color"}
    if call_name == "_theme_color":
        rgb_literal_keywords.add("fallback")

    for keyword in node.keywords:
        if keyword.arg in rgb_literal_keywords and _is_numeric_color_tuple(keyword.value):
            offenders.append(_format_offender(path, node.lineno, ast.unparse(keyword.value)))

    if call_name in {"_make_actor"}:
        for arg in node.args:
            if _is_numeric_color_tuple(arg):
                offenders.append(_format_offender(path, node.lineno, ast.unparse(arg)))

    return offenders


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _is_numeric_unit_constant(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and 0.0 <= node.value <= 1.0
    )


def _is_numeric_color_tuple(node: ast.AST) -> bool:
    if not isinstance(node, (ast.Tuple, ast.List)) or len(node.elts) not in {3, 4}:
        return False
    return all(_is_numeric_unit_constant(element) for element in node.elts)


def _format_offender(path: Path, line_number: int, literal: str) -> str:
    try:
        rel_path = path.relative_to(UI_ROOT.parents[1])
    except ValueError:
        rel_path = path
    return f"{rel_path}:{line_number}: {literal}"
