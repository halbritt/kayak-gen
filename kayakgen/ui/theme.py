"""Shared UI theme tokens for the desktop and web frontends.

RFC 0033 treats this module as the single color-literal authority under
``kayakgen/ui``. Other UI modules should import semantic tokens from here rather
than spelling hex values, matplotlib named colors, or VTK RGB triples inline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

ColorTokens = Mapping[str, str]


COLORS_LIGHT: Final[dict[str, str]] = {
    "surface-bg": "#f7faf8",
    "surface-panel": "#ffffff",
    "surface-rail": "#f1f6f3",
    "surface-review": "#fbfdfb",
    "surface-viewport-bg": "#e7f0ec",
    "surface-viewport-grid": "#bfd1c8",
    "surface-border": "#c7d5ce",
    "surface-rule": "#30383c",
    "surface-muted": "#e6eee9",
    "surface-raised": "#d8dee2",
    "surface-inverse": "#2f3437",
    "surface-inverse-hover": "#414a4f",
    "text-primary": "#18221f",
    "text-secondary": "#43524d",
    "text-muted": "#596963",
    "text-inverse": "#ffffff",
    "text-on-accent": "#ffffff",
    "brand-primary": "#005f5b",
    "brand-primary-hover": "#08746d",
    "brand-secondary": "#49615b",
    "action-primary": "#126f86",
    "action-primary-hover": "#0f6573",
    "primary-button": "#126f86",
    "primary-button-hover": "#0f6573",
    "neutral-button": "#d4ded8",
    "neutral-button-hover": "#c3d0c8",
    "dark-button": "#24312d",
    "dark-button-hover": "#33433e",
    "state-success": "#1c7a3e",
    "state-success-text": "#155c35",
    "state-success-bg": "#d8f3df",
    "state-advisory": "#8f6b00",
    "state-advisory-text": "#684f00",
    "state-advisory-bg": "#fff1bd",
    "state-raw": "#b34100",
    "state-raw-text": "#7f2800",
    "state-raw-bg": "#ffe2d2",
    "state-error": "#b4372f",
    "state-error-text": "#8a1f1a",
    "state-error-bg": "#fbe0dd",
    "state-info": "#126f86",
    "state-info-bg": "#d9eff4",
    "state-focus-rail": "#087d74",
    "state-focus-row": "#dff3ee",
    "state-delta-pos": "#1c6b36",
    "state-delta-neg": "#a32f28",
    "data-hull": "#126f86",
    "data-hull-fill": "#bce1e9",
    "data-deck": "#23743a",
    "data-deck-fill": "#c9eacb",
    "data-waterline": "#5aa2b0",
    "data-viscous": "#355f8d",
    "data-wave": "#b34100",
    "data-total": "#18221f",
    "button-neutral": "#d4ded8",
    "button-neutral-hover": "#c3d0c8",
    "button-strong": "#24312d",
    "button-strong-hover": "#33433e",
}


COLORS_DARK: Final[dict[str, str]] = {
    "surface-bg": "#111815",
    "surface-panel": "#18211d",
    "surface-rail": "#141d19",
    "surface-review": "#1d2823",
    "surface-viewport-bg": "#16201b",
    "surface-viewport-grid": "#34463f",
    "surface-border": "#3a4c45",
    "surface-rule": "#7f918a",
    "surface-muted": "#24322d",
    "surface-raised": "#364842",
    "surface-inverse": "#dce7e2",
    "surface-inverse-hover": "#ffffff",
    "text-primary": "#eef5f1",
    "text-secondary": "#becac4",
    "text-muted": "#9aaba4",
    "text-inverse": "#101614",
    "text-on-accent": "#101614",
    "brand-primary": "#5dc2b6",
    "brand-primary-hover": "#77d6ca",
    "brand-secondary": "#95aaa3",
    "action-primary": "#65bdd2",
    "action-primary-hover": "#78d2e8",
    "primary-button": "#65bdd2",
    "primary-button-hover": "#78d2e8",
    "neutral-button": "#293832",
    "neutral-button-hover": "#364842",
    "dark-button": "#dce7e2",
    "dark-button-hover": "#ffffff",
    "state-success": "#78c987",
    "state-success-text": "#bfeec8",
    "state-success-bg": "#173c25",
    "state-advisory": "#ffcb45",
    "state-advisory-text": "#ffe8a0",
    "state-advisory-bg": "#3c3109",
    "state-raw": "#ff8a3d",
    "state-raw-text": "#ffd5be",
    "state-raw-bg": "#55200a",
    "state-error": "#ff766b",
    "state-error-text": "#ffc5c0",
    "state-error-bg": "#561b18",
    "state-info": "#65bdd2",
    "state-info-bg": "#173542",
    "state-focus-rail": "#58d2c6",
    "state-focus-row": "#203e38",
    "state-delta-pos": "#8fd89d",
    "state-delta-neg": "#ff9f96",
    "data-hull": "#65bdd2",
    "data-hull-fill": "#1d5662",
    "data-deck": "#78c987",
    "data-deck-fill": "#215a32",
    "data-waterline": "#84cdd7",
    "data-viscous": "#8fb1dc",
    "data-wave": "#ff8a3d",
    "data-total": "#eef5f1",
    "button-neutral": "#293832",
    "button-neutral-hover": "#364842",
    "button-strong": "#dce7e2",
    "button-strong-hover": "#ffffff",
}


TYPOGRAPHY: Final[dict[str, str]] = {
    "font-mono": (
        '"JetBrains Mono", "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace'
    ),
    "font-condensed": (
        '"Inter Tight", "IBM Plex Sans", system-ui, -apple-system, sans-serif'
    ),
    "type-display": "600 1.125rem/1.25 var(--font-condensed)",
    "type-heading": "600 0.95rem/1.25 var(--font-condensed)",
    "type-label": "600 0.78rem/1.25 var(--font-condensed)",
    "type-body": "400 0.875rem/1.45 var(--font-condensed)",
    "type-caption": "500 0.72rem/1.35 var(--font-condensed)",
    "type-metric": "500 0.78rem/1.4 var(--font-mono)",
}


PLOT_PALETTE: Final[dict[str, str]] = {
    "hull": COLORS_LIGHT["data-hull"],
    "hull_fill": COLORS_LIGHT["data-hull-fill"],
    "deck": COLORS_LIGHT["data-deck"],
    "deck_fill": COLORS_LIGHT["data-deck-fill"],
    "waterline": COLORS_LIGHT["data-waterline"],
    "station": COLORS_LIGHT["state-focus-rail"],
    "focus": COLORS_LIGHT["state-focus-rail"],
    "viscous": COLORS_LIGHT["data-viscous"],
    "wave": COLORS_LIGHT["data-wave"],
    "total": COLORS_LIGHT["data-total"],
    "axis": COLORS_LIGHT["text-secondary"],
    "grid": COLORS_LIGHT["surface-viewport-grid"],
}


@dataclass(frozen=True)
class ChipSpec:
    """Presentation contract for shared claim/readiness/status chips."""

    label: str
    css_class: str
    color_token: str
    background_token: str
    text_token: str


CHIP_SPECS: Final[dict[str, ChipSpec]] = {
    "raw_unvalidated": ChipSpec(
        "Raw/unvalidated",
        "kg-chip kg-chip--raw",
        "state-raw",
        "state-raw-bg",
        "state-raw-text",
    ),
    "uncalibrated_comparative": ChipSpec(
        "Raw comparative filter",
        "kg-chip kg-chip--raw",
        "state-raw",
        "state-raw-bg",
        "state-raw-text",
    ),
    "validation_fixture": ChipSpec(
        "Validation fixture",
        "kg-chip kg-chip--info",
        "state-info",
        "state-info-bg",
        "state-info",
    ),
    "calibration_fixture_candidate": ChipSpec(
        "Calibration candidate",
        "kg-chip kg-chip--advisory",
        "state-advisory",
        "state-advisory-bg",
        "state-advisory-text",
    ),
    "calibration_fixture": ChipSpec(
        "Calibration fixture",
        "kg-chip kg-chip--success",
        "state-success",
        "state-success-bg",
        "state-success-text",
    ),
    "calibrated_model": ChipSpec(
        "Calibrated model",
        "kg-chip kg-chip--success",
        "state-success",
        "state-success-bg",
        "state-success-text",
    ),
    "validated_design_fitness": ChipSpec(
        "Validated design fitness",
        "kg-chip kg-chip--success",
        "state-success",
        "state-success-bg",
        "state-success-text",
    ),
    "invalid": ChipSpec(
        "Invalid",
        "kg-chip kg-chip--error",
        "state-error",
        "state-error-bg",
        "state-error-text",
    ),
    "display": ChipSpec(
        "Display only",
        "kg-chip kg-chip--advisory",
        "state-advisory",
        "state-advisory-bg",
        "state-advisory-text",
    ),
    "stl_surface": ChipSpec(
        "STL surface",
        "kg-chip kg-chip--info",
        "state-info",
        "state-info-bg",
        "state-info",
    ),
    "cfd_surface_candidate": ChipSpec(
        "Open wetted-surface",
        "kg-chip kg-chip--advisory",
        "state-advisory",
        "state-advisory-bg",
        "state-advisory-text",
    ),
    "cfd_ready": ChipSpec(
        "CFD ready",
        "kg-chip kg-chip--success",
        "state-success",
        "state-success-bg",
        "state-success-text",
    ),
    "queued": ChipSpec(
        "Queued",
        "kg-chip kg-chip--info",
        "state-info",
        "state-info-bg",
        "state-info",
    ),
    "running": ChipSpec(
        "Running",
        "kg-chip kg-chip--info",
        "state-info",
        "state-info-bg",
        "state-info",
    ),
    "succeeded": ChipSpec(
        "Succeeded",
        "kg-chip kg-chip--success",
        "state-success",
        "state-success-bg",
        "state-success-text",
    ),
    "failed": ChipSpec(
        "Failed",
        "kg-chip kg-chip--error",
        "state-error",
        "state-error-bg",
        "state-error-text",
    ),
    "unavailable": ChipSpec(
        "Unavailable",
        "kg-chip kg-chip--raw",
        "state-raw",
        "state-raw-bg",
        "state-raw-text",
    ),
    "advisory": ChipSpec(
        "Advisory",
        "kg-chip kg-chip--advisory",
        "state-advisory",
        "state-advisory-bg",
        "state-advisory-text",
    ),
    "high_angle_unavailable": ChipSpec(
        "High-angle GZ unavailable",
        "kg-chip kg-chip--raw",
        "state-raw",
        "state-raw-bg",
        "state-raw-text",
    ),
}

CHIP_LABELS: Final[dict[str, str]] = {
    key: spec.label for key, spec in CHIP_SPECS.items()
}
CHIP_CLASSES: Final[dict[str, str]] = {
    key: spec.css_class for key, spec in CHIP_SPECS.items()
}


@dataclass(frozen=True)
class ContrastPair:
    """A token pair that must meet a minimum contrast ratio."""

    name: str
    foreground_token: str
    background_token: str
    min_ratio: float = 4.5


CONTRAST_MANIFEST: Final[tuple[ContrastPair, ...]] = (
    ContrastPair("text.primary", "text-primary", "surface-bg"),
    ContrastPair("text.secondary", "text-secondary", "surface-bg"),
    ContrastPair("text.muted.panel", "text-muted", "surface-panel"),
    ContrastPair("brand.primary", "brand-primary", "surface-bg"),
    ContrastPair("chip.raw", "state-raw-text", "state-raw-bg"),
    ContrastPair("chip.advisory", "state-advisory-text", "state-advisory-bg"),
    ContrastPair("chip.success", "state-success-text", "state-success-bg"),
    ContrastPair("chip.error", "state-error-text", "state-error-bg"),
    ContrastPair("focus.rail", "state-focus-rail", "surface-viewport-bg", 3.0),
    ContrastPair("data.hull", "data-hull", "surface-panel", 3.0),
    ContrastPair("data.deck", "data-deck", "surface-panel", 3.0),
    ContrastPair("delta.pos", "state-delta-pos", "surface-panel", 3.0),
    ContrastPair("delta.neg", "state-delta-neg", "surface-panel", 3.0),
)


def _tokens(dark: bool) -> ColorTokens:
    return COLORS_DARK if dark else COLORS_LIGHT


def _hex_to_rgb_tuple(value: str) -> tuple[int, int, int]:
    hex_value = value.removeprefix("#")
    if len(hex_value) != 6:
        raise ValueError(f"expected 6-digit hex color, got {value!r}")
    return tuple(int(hex_value[index : index + 2], 16) for index in (0, 2, 4))


def rgb_float(token: str, *, dark: bool = False) -> tuple[float, float, float]:
    """Return a semantic token as a VTK/PyVista-compatible RGB triple."""

    r, g, b = _hex_to_rgb_tuple(_tokens(dark)[token])
    return (r / 255.0, g / 255.0, b / 255.0)


def css_root_block(dark: bool = False) -> str:
    """Return a CSS ``:root`` block defining RFC 0033 design tokens."""

    lines = [":root {"]
    for name, value in _tokens(dark).items():
        lines.append(f"  --{name}: {value};")
    for name, value in TYPOGRAPHY.items():
        lines.append(f"  --{name}: {value};")
    lines.append("}")
    return "\n".join(lines)


def vuetify_theme_config() -> dict[str, object]:
    """Return a Vuetify 3 theme registry using the shared semantic tokens."""

    return {
        "defaultTheme": "kayakgenLight",
        "themes": {
            "kayakgenLight": _vuetify_theme("kayakgenLight", COLORS_LIGHT, dark=False),
            "kayakgenDark": _vuetify_theme("kayakgenDark", COLORS_DARK, dark=True),
        },
    }


def _vuetify_theme(name: str, colors: ColorTokens, *, dark: bool) -> dict[str, object]:
    return {
        "dark": dark,
        "colors": {
            "background": colors["surface-bg"],
            "surface": colors["surface-panel"],
            "primary": colors["brand-primary"],
            "secondary": colors["brand-secondary"],
            "success": colors["state-success"],
            "warning": colors["state-advisory"],
            "error": colors["state-error"],
            "info": colors["state-info"],
            "raw": colors["state-raw"],
            "viewport": colors["surface-viewport-bg"],
            "hull": colors["data-hull"],
            "deck": colors["data-deck"],
        },
        "variables": {
            "theme-name": name,
            "border-color": colors["surface-border"],
            "high-emphasis-opacity": 1.0,
            "medium-emphasis-opacity": 0.74,
            "disabled-opacity": 0.38,
        },
    }


def matplotlib_rc_params(dark: bool = False) -> dict[str, object]:
    """Return matplotlib rcParams for desktop plots without importing matplotlib."""

    colors = _tokens(dark)
    return {
        "figure.facecolor": colors["surface-bg"],
        "axes.facecolor": colors["surface-panel"],
        "savefig.facecolor": colors["surface-bg"],
        "axes.edgecolor": colors["surface-border"],
        "axes.labelcolor": colors["text-secondary"],
        "axes.titlecolor": colors["text-primary"],
        "xtick.color": colors["text-secondary"],
        "ytick.color": colors["text-secondary"],
        "text.color": colors["text-primary"],
        "grid.color": colors["surface-viewport-grid"],
        "legend.facecolor": colors["surface-panel"],
        "legend.edgecolor": colors["surface-border"],
        "font.family": ["Inter Tight", "IBM Plex Sans", "DejaVu Sans", "sans-serif"],
        "font.monospace": [
            "JetBrains Mono",
            "IBM Plex Mono",
            "DejaVu Sans Mono",
            "monospace",
        ],
    }


def vtk_background_rgb(dark: bool = False) -> tuple[float, float, float]:
    """Return the shared 3D viewport background as normalized RGB."""

    return rgb_float("surface-viewport-bg", dark=dark)
