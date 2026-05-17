"""Calibration-artifact writers (RFC 0054).

Pure-Python SVG residual-plot writer. No matplotlib / no numpy. The
writer renders one stem per ``(operating_point, residual)`` pair, a
horizontal zero-line, and an mm-aligned grid. The output is a valid
standalone SVG document parseable by ``xml.etree.ElementTree``.
"""

from __future__ import annotations

from pathlib import Path

from kayakgen.eval.calibration.campaigns import AcceptedFitRecord

# Canvas geometry, in user units (which the SVG declares as mm).
_CANVAS_WIDTH_MM = 200.0
_CANVAS_HEIGHT_MM = 120.0
_PLOT_LEFT_MM = 20.0
_PLOT_RIGHT_MM = 190.0
_PLOT_TOP_MM = 15.0
_PLOT_BOTTOM_MM = 100.0
_GRID_SPACING_MM = 10.0


def _domain_bounds(residuals: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Return ``(x_min, x_max, y_min, y_max)`` with safe fallbacks."""
    if not residuals:
        return (0.0, 1.0, -1.0, 1.0)
    xs = [pt[0] for pt in residuals]
    ys = [pt[1] for pt in residuals]
    x_min = min(xs)
    x_max = max(xs)
    if x_min == x_max:
        x_min -= 0.5
        x_max += 0.5
    y_abs = max(abs(min(ys)), abs(max(ys)), 1e-9)
    return (x_min, x_max, -y_abs, y_abs)


def _project(
    x: float,
    y: float,
    *,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[float, float]:
    plot_width = _PLOT_RIGHT_MM - _PLOT_LEFT_MM
    plot_height = _PLOT_BOTTOM_MM - _PLOT_TOP_MM
    x_frac = (x - x_min) / (x_max - x_min) if x_max != x_min else 0.5
    y_frac = (y - y_min) / (y_max - y_min) if y_max != y_min else 0.5
    px = _PLOT_LEFT_MM + x_frac * plot_width
    # SVG y axis grows downward; invert so positive residuals sit above the line.
    py = _PLOT_BOTTOM_MM - y_frac * plot_height
    return (px, py)


def _format_mm(value: float) -> str:
    """SVG numeric formatter that avoids locale-specific output."""
    return f"{value:.3f}"


def _grid_lines() -> list[str]:
    out: list[str] = []
    x = _PLOT_LEFT_MM
    while x <= _PLOT_RIGHT_MM + 1e-6:
        out.append(
            f'<line x1="{_format_mm(x)}" y1="{_format_mm(_PLOT_TOP_MM)}" '
            f'x2="{_format_mm(x)}" y2="{_format_mm(_PLOT_BOTTOM_MM)}" '
            'stroke="#dddddd" stroke-width="0.2"/>'
        )
        x += _GRID_SPACING_MM
    y = _PLOT_TOP_MM
    while y <= _PLOT_BOTTOM_MM + 1e-6:
        out.append(
            f'<line x1="{_format_mm(_PLOT_LEFT_MM)}" y1="{_format_mm(y)}" '
            f'x2="{_format_mm(_PLOT_RIGHT_MM)}" y2="{_format_mm(y)}" '
            'stroke="#dddddd" stroke-width="0.2"/>'
        )
        y += _GRID_SPACING_MM
    return out


def write_residual_plot(accepted_fit: AcceptedFitRecord, out: Path) -> Path:
    """Write an SVG residual plot for ``accepted_fit`` to ``out``.

    The plot is deterministic for a given input record. Output bytes
    only change when the residual list changes.
    """
    x_min, x_max, y_min, y_max = _domain_bounds(accepted_fit.residuals)
    zero_y = _project(
        0.0,
        0.0,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )[1]

    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{_format_mm(_CANVAS_WIDTH_MM)}mm" '
        f'height="{_format_mm(_CANVAS_HEIGHT_MM)}mm" '
        f'viewBox="0 0 {_format_mm(_CANVAS_WIDTH_MM)} '
        f'{_format_mm(_CANVAS_HEIGHT_MM)}">'
    )
    parts.append(
        f'<title>Residuals for {accepted_fit.fit_id} '
        f'(model {accepted_fit.model_version})</title>'
    )
    parts.append(
        f'<desc>fit_metric={accepted_fit.fit_metric} '
        f'fit_value={accepted_fit.fit_value} '
        f'holdout_rms_n={accepted_fit.holdout_rms_n}</desc>'
    )

    # Grid + plot frame.
    parts.append('<g id="grid">')
    parts.extend(_grid_lines())
    parts.append('</g>')
    parts.append(
        f'<rect x="{_format_mm(_PLOT_LEFT_MM)}" y="{_format_mm(_PLOT_TOP_MM)}" '
        f'width="{_format_mm(_PLOT_RIGHT_MM - _PLOT_LEFT_MM)}" '
        f'height="{_format_mm(_PLOT_BOTTOM_MM - _PLOT_TOP_MM)}" '
        'fill="none" stroke="#000000" stroke-width="0.3"/>'
    )

    # Zero line.
    parts.append(
        f'<line id="zero-line" x1="{_format_mm(_PLOT_LEFT_MM)}" '
        f'y1="{_format_mm(zero_y)}" x2="{_format_mm(_PLOT_RIGHT_MM)}" '
        f'y2="{_format_mm(zero_y)}" '
        'stroke="#444444" stroke-width="0.5" stroke-dasharray="2 2"/>'
    )

    # Stems + dots.
    parts.append('<g id="residual-stems">')
    for op, resid in accepted_fit.residuals:
        x_proj, y_proj = _project(
            op,
            resid,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )
        parts.append(
            f'<line x1="{_format_mm(x_proj)}" y1="{_format_mm(zero_y)}" '
            f'x2="{_format_mm(x_proj)}" y2="{_format_mm(y_proj)}" '
            'stroke="#1f6feb" stroke-width="0.6"/>'
        )
        parts.append(
            f'<circle cx="{_format_mm(x_proj)}" cy="{_format_mm(y_proj)}" '
            'r="0.8" fill="#1f6feb"/>'
        )
    parts.append('</g>')

    parts.append(
        f'<text x="{_format_mm(_PLOT_LEFT_MM)}" '
        f'y="{_format_mm(_PLOT_TOP_MM - 4.0)}" '
        'font-family="sans-serif" font-size="3.5" fill="#222222">'
        f'fit_id={accepted_fit.fit_id} | metric={accepted_fit.fit_metric} '
        f'| value={accepted_fit.fit_value}'
        '</text>'
    )

    parts.append('</svg>')

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n")
    return out
