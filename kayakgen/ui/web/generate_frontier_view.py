"""Pareto-frontier view module for the kayakgen Generate panel (RFC 0057).

This module implements the read-only view-model and Trame render hook
that replaces the monospace text list in the Generate tab with a 2D
scatter + sortable table + candidate-handoff affordance. It is
import-safe on cold start: the Trame widget imports are deferred into
the render function so importing :func:`build_frontier_view_model` does
not transitively require ``trame`` or ``matplotlib``.

Per RFC 0057 stage 4 decisions D-6 / D-7 / D-8:

- D-6: 2D scatter synced with a sortable table; color by ``claim_state``,
  marker shape by ``ConvergenceFlag`` (RFC 0052).
- D-7: when three objectives are present, the third surfaces as a
  colour-mapped axis on the points and as a column in the table.
- D-8: clicking a row loads the candidate into the single-hull view with
  a one-click undo toast.

This module deliberately never surfaces gated high-angle stability
display-only metrics. Those are owned by the dedicated comparison
surface, which does its own provenance + warning rendering. The
view-model helpers drop those keys defensively even if a payload's
``summary`` dict carries them.
"""

from __future__ import annotations

import html
from typing import Any, Iterable, Mapping

from kayakgen.eval.stability.high_angle_contracts import (
    resolve_analytical_claim_label,
)
from kayakgen.ui import theme
from kayakgen.ui.web.state import HULL_STATE_FIELDS


def _loaded_fit_registry() -> object:
    """Lazy, mtime-memoized accessor for the accepted-fit registry (RFC 0043 §C.4).

    Mirrors :func:`kayakgen.eval.stability.evaluator._loaded_fit_registry`. The
    underlying :func:`load_stability_fit_registry` memoizes by fits-dir mtime
    so a Trame session that mid-flight runs ``promote-fixture`` / ``accept-fit``
    sees the new registry on the next frontier-view refresh without a process
    restart. Imported lazily to keep this module's cold-start surface tight.
    """

    from kayakgen.eval.stability.registry import load_stability_fit_registry

    return load_stability_fit_registry()


# ---------------------------------------------------------------------------
# Forbidden tokens — kept in lock-step with tests/test_web_layout.py and the
# RFC 0057 stage 4 task brief. Any metric whose key contains one of these
# strings is treated as display-only and dropped from the view-model.
# ---------------------------------------------------------------------------

FORBIDDEN_METRIC_TOKENS: tuple[str, ...] = (
    "max_gz_m",  # noqa: kg-orphan-color
    "heel_at_max_gz_deg",  # noqa: kg-orphan-color
    "range_positive_stability_deg",  # noqa: kg-orphan-color
    "area_under_positive_gz_m_deg",  # noqa: kg-orphan-color
    "righting_moment_nm",  # noqa: kg-orphan-color
    "gz_m",  # noqa: kg-orphan-color
)
"""Substrings that mark a summary key as high-angle GZ display-only.

The Pareto-frontier surface MUST NOT promote these to objectives or color
axes; they live behind the comparison-panel provenance contract.

The ``# noqa: kg-orphan-color`` annotations are intentional and narrow:
these literals are RFC 0043 metric-token *names* (e.g. ``max_gz_m``,
``heel_at_max_gz_deg``), not color values. The orphan-color linter in
``tests/test_ui_theme.py`` walks for hex literals, named CSS colors, and
grayscale numerics; none of those patterns match these strings, so the
suppressions are precautionary rather than load-bearing. They document
the intent that this module remain hex-literal-free without coupling the
linter rule to the metric-token identity.
"""


# Color-token <-> CSS-class mapping. The CSS class lookup keeps render-time
# strings free of hex literals so the orphan-color scan continues to pass.
_CLAIM_STATE_COLOR_TOKENS: Mapping[str, str] = {
    "raw_unvalidated": "state-raw",
    "uncalibrated_comparative": "state-raw",
    "validation_fixture": "state-info",
    "calibration_fixture_candidate": "state-advisory",
    "calibration_fixture": "state-success",
    "calibrated_model": "state-success",
    "invalid": "state-error",
    "unknown": "text-muted",
}

_CONVERGENCE_MARKERS: Mapping[str, str] = {
    "converged": "o",
    "not_converged": "x",
    "iteration_cap": "s",
    "unknown": "D",
}


# RFC 0058 stage 3 / D-13: analytical-claim label → CSS class name. The class
# names below are wired to existing theme tokens by :func:`frontier_view_css`;
# no new theme token is introduced.
_ANALYTICAL_CLAIM_LABEL_CSS_CLASS: Mapping[str, str] = {
    "validated_hydrostatic_comparison": "kg-state-validated",
    "unvalidated_hydrostatic_comparison": "kg-state-raw",
}

# CSS-class name → existing theme token used to fill the swatch.
_ANALYTICAL_CSS_CLASS_THEME_TOKEN: Mapping[str, str] = {
    "kg-state-validated": "state-success",
    "kg-state-raw": "state-raw",
}


def _claim_state_color_class(claim_state: str) -> str:
    """Return a CSS class name for a claim_state — never a raw hex literal."""

    safe = claim_state.replace("_", "-")
    return f"kg-frontier-point--{safe}"


def _convergence_marker(flag: str) -> str:
    return _CONVERGENCE_MARKERS.get(flag, _CONVERGENCE_MARKERS["unknown"])


def _color_for_claim_state(claim_state: str, *, dark: bool = False) -> str:
    """Resolve a claim_state to a hex color via :mod:`kayakgen.ui.theme`.

    Importing the value through ``theme.COLORS_LIGHT`` / ``COLORS_DARK``
    keeps this module hex-literal-free for the orphan-color scan.
    """

    token = _CLAIM_STATE_COLOR_TOKENS.get(claim_state, _CLAIM_STATE_COLOR_TOKENS["unknown"])
    palette = theme.COLORS_DARK if dark else theme.COLORS_LIGHT
    return palette[token]


def _z_color_ratio(
    value: float | None,
    low: float | None,
    high: float | None,
) -> float | None:
    """Normalize the third objective for the browser-side color axis."""

    if value is None or low is None or high is None:
        return None
    span = high - low
    if span <= 0:
        return 0.5
    return max(0.0, min(1.0, (value - low) / span))


# ---------------------------------------------------------------------------
# Public view-model
# ---------------------------------------------------------------------------


def _is_forbidden_metric_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in FORBIDDEN_METRIC_TOKENS)


def _sanitize_summary(summary: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(summary, Mapping):
        return {}
    return {k: v for k, v in summary.items() if not _is_forbidden_metric_key(str(k))}


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN guard
        return None
    return result


def _claim_state_for(row: Mapping[str, Any]) -> str:
    """Return the conservative claim_state used for color mapping.

    The frontier payload from :func:`generative_job_frontier_payload`
    does not currently surface ``claim_state`` directly — the per-row
    ``summary`` may carry one, otherwise we fall back to the RFC 0057
    stage 2 conservative posture ``raw_unvalidated``.
    """

    summary = row.get("summary") if isinstance(row, Mapping) else None
    if isinstance(summary, Mapping):
        candidate = summary.get("claim_state")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    explicit = row.get("claim_state") if isinstance(row, Mapping) else None
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return "raw_unvalidated"


def _convergence_flag_for(row: Mapping[str, Any]) -> str:
    """Return the convergence-flag label used for marker-shape mapping."""

    summary = row.get("summary") if isinstance(row, Mapping) else None
    if isinstance(summary, Mapping):
        flag = summary.get("convergence_flag") or summary.get("convergence")
        if isinstance(flag, Mapping):
            flag = flag.get("status")
        if isinstance(flag, str) and flag.strip():
            return flag.strip()
    explicit = row.get("convergence_flag") if isinstance(row, Mapping) else None
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return "unknown"


def _objective_label(metric: str) -> str:
    """Render an axis label without leaking forbidden display-only metrics."""

    if _is_forbidden_metric_key(metric):
        # Defensive: callers are not supposed to pick a forbidden metric, but
        # if they somehow do we collapse the label to a neutral placeholder.
        return "(display-only metric hidden)"
    return metric


def _resolve_claim_label_color_token(
    row: Mapping[str, Any],
    fit_registry: Iterable[Any],
) -> str | None:
    """Compute the RFC 0058 analytical-claim CSS-class for a frontier row.

    Returns ``"kg-state-validated"`` when the row carries a hull whose
    family is covered by an accepted fit in ``fit_registry``, otherwise
    ``"kg-state-raw"`` when a hull is present but no covering fit, and
    ``None`` when the row has no hull reference (preserves the prior
    scatter-point shape for hull-less payloads).
    """

    hull = row.get("hull") if isinstance(row, Mapping) else None
    if hull is None:
        return None
    label = resolve_analytical_claim_label(hull, fit_registry)
    return _ANALYTICAL_CLAIM_LABEL_CSS_CLASS.get(label)


def build_frontier_view_model(
    frontier_payload: Mapping[str, Any],
    *,
    x_metric: str,
    y_metric: str,
    z_metric: str | None = None,
    fit_registry: Iterable[Any] = (),
) -> dict[str, Any]:
    """Project a frontier payload onto the scatter/table view-model.

    Returns a dict with keys ``rows``, ``scatter_points``, ``axis_labels``,
    ``available``, ``x_metric``, ``y_metric``, ``z_metric``. ``rows`` is
    deterministically ordered by ``candidate_key``. ``scatter_points`` are
    in the same order, ready to feed a 2D scatter widget. Forbidden
    high-angle GZ metric keys are stripped from every row's parameters
    and from the third-objective column.
    """

    if _is_forbidden_metric_key(x_metric) or _is_forbidden_metric_key(y_metric):
        return {
            "available": False,
            "rows": [],
            "scatter_points": [],
            "axis_labels": {"x": _objective_label(x_metric), "y": _objective_label(y_metric), "z": None},
            "x_metric": x_metric,
            "y_metric": y_metric,
            "z_metric": None,
            "note": "objective metric is gated as display-only",
        }

    if z_metric is not None and _is_forbidden_metric_key(z_metric):
        z_metric = None

    raw_rows = list(frontier_payload.get("frontier") or [])
    sorted_rows = sorted(
        (r for r in raw_rows if isinstance(r, Mapping)),
        key=lambda r: str(r.get("candidate_key") or ""),
    )

    z_values: list[float] = []
    if z_metric is not None:
        for row in sorted_rows:
            summary = _sanitize_summary(row.get("summary"))
            z_value = _coerce_float(summary.get(z_metric))
            if z_value is not None:
                z_values.append(z_value)
    z_low = min(z_values) if z_values else None
    z_high = max(z_values) if z_values else None

    rows: list[dict[str, Any]] = []
    scatter_points: list[dict[str, Any]] = []

    for row in sorted_rows:
        candidate_key = str(row.get("candidate_key") or "")
        summary = _sanitize_summary(row.get("summary"))
        params = {
            k: v
            for k, v in (row.get("parameters") or {}).items()
            if not _is_forbidden_metric_key(str(k))
        }
        claim_state = _claim_state_for(row)
        convergence_flag = _convergence_flag_for(row)
        claim_label_color_token = _resolve_claim_label_color_token(row, fit_registry)
        x_value = _coerce_float(summary.get(x_metric))
        y_value = _coerce_float(summary.get(y_metric))
        z_value: float | None = None
        if z_metric is not None:
            z_value = _coerce_float(summary.get(z_metric))

        rows.append(
            {
                "candidate_key": candidate_key,
                "claim_state": claim_state,
                "convergence_flag": convergence_flag,
                "status": str(row.get("status") or ""),
                "x": x_value,
                "y": y_value,
                "z": z_value,
                "z_color_ratio": _z_color_ratio(z_value, z_low, z_high),
                "parameters": params,
                "claim_label_color_token": claim_label_color_token,
            }
        )

        if x_value is None or y_value is None:
            continue
        scatter_points.append(
            {
                "x": x_value,
                "y": y_value,
                "z": z_value,
                "color": _color_for_claim_state(claim_state),
                "color_class": _claim_state_color_class(claim_state),
                "color_token": _CLAIM_STATE_COLOR_TOKENS.get(
                    claim_state, _CLAIM_STATE_COLOR_TOKENS["unknown"]
                ),
                "z_color_ratio": _z_color_ratio(z_value, z_low, z_high),
                "marker": _convergence_marker(convergence_flag),
                "label": candidate_key,
                "claim_state": claim_state,
                "convergence_flag": convergence_flag,
                "claim_label_color_token": claim_label_color_token,
            }
        )

    return {
        "available": bool(rows),
        "rows": rows,
        "scatter_points": scatter_points,
        "axis_labels": {
            "x": _objective_label(x_metric),
            "y": _objective_label(y_metric),
            "z": _objective_label(z_metric) if z_metric else None,
        },
        "color_axis": {
            "metric": z_metric,
            "label": _objective_label(z_metric) if z_metric else None,
            "min": z_low,
            "max": z_high,
        },
        "x_metric": x_metric,
        "y_metric": y_metric,
        "z_metric": z_metric,
    }


# ---------------------------------------------------------------------------
# State + controller helpers
# ---------------------------------------------------------------------------


def _candidate_metric_choices(payload: Mapping[str, Any]) -> list[str]:
    """Return sorted, deduplicated, scrubbed metric keys from a payload."""

    seen: set[str] = set()
    for row in payload.get("frontier") or []:
        if not isinstance(row, Mapping):
            continue
        summary = row.get("summary") or {}
        if not isinstance(summary, Mapping):
            continue
        for key, value in summary.items():
            key_str = str(key)
            if _is_forbidden_metric_key(key_str):
                continue
            if _coerce_float(value) is None:
                continue
            seen.add(key_str)
    return sorted(seen)


def _scatter_svg_fallback(view_model: Mapping[str, Any]) -> str:
    """Tiny precomputed SVG used when the trame-matplotlib widget is absent.

    Renders only structure (point positions + color tokens); detailed
    rendering is the matplotlib widget's job. Embedding HTML lets the
    test surface assert presence of the data without requiring a
    browser.
    """

    points = list(view_model.get("scatter_points") or [])
    if not points:
        return ""
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    width = max(x_max - x_min, 1e-9)
    height = max(y_max - y_min, 1e-9)

    def _px_x(value: float) -> float:
        return 30.0 + 240.0 * (value - x_min) / width

    def _px_y(value: float) -> float:
        return 170.0 - 140.0 * (value - y_min) / height

    parts: list[str] = [
        '<svg class="kg-frontier-scatter-svg" '
        'data-testid="frontier-scatter-svg" '
        'viewBox="0 0 300 200" '
        'role="img" aria-label="Pareto frontier scatter">'
    ]
    for point in points:
        cx = _px_x(float(point["x"]))
        cy = _px_y(float(point["y"]))
        label = html.escape(str(point.get("label") or ""))
        css_class = html.escape(str(point.get("color_class") or "kg-frontier-point"))
        parts.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="4" '
            f'class="{css_class} kg-frontier-point" '
            f'data-candidate-key="{label}" '
            f'data-claim-state="{html.escape(str(point.get("claim_state") or ""))}" '
            f'data-convergence="{html.escape(str(point.get("convergence_flag") or ""))}" '
            f'data-z-ratio="{html.escape(str(point.get("z_color_ratio") or ""))}" '
            "></circle>"
        )
    parts.append("</svg>")
    return "".join(parts)


def _frontier_state_keys() -> tuple[str, ...]:
    return (
        "generative_frontier_view_available",
        "generative_frontier_x_metric",
        "generative_frontier_y_metric",
        "generative_frontier_z_metric",
        "generative_frontier_metric_options",
        "generative_frontier_table_rows",
        "generative_frontier_axis_labels",
        "generative_frontier_scatter_points",
        "generative_frontier_scatter_svg",
        "generative_frontier_handoff_toast",
        "generative_handoff_toast",
        "generative_handoff_prior",
    )


def _candidate_row_for(view_model: Mapping[str, Any], index: int) -> Mapping[str, Any] | None:
    rows = view_model.get("rows") or []
    if index < 0 or index >= len(rows):
        return None
    return rows[index]


# ---------------------------------------------------------------------------
# Public app-state helpers
# ---------------------------------------------------------------------------


def apply_candidate_to_hull(app: Any, candidate_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Load a frontier candidate's parameters into the single-hull view.

    Captures the prior hull-state snapshot into
    ``app.state.generative_handoff_prior`` so the undo toast callback
    can restore it byte-for-byte. Returns the captured prior snapshot.
    """

    state = app.state
    prior_snapshot: dict[str, Any] = {field: getattr(state, field, None) for field in HULL_STATE_FIELDS}
    state.generative_handoff_prior = prior_snapshot

    parameters = candidate_payload.get("parameters") if isinstance(candidate_payload, Mapping) else None
    if not isinstance(parameters, Mapping):
        return prior_snapshot

    updates: dict[str, Any] = {}
    for key, value in parameters.items():
        key_str = str(key)
        if key_str in HULL_STATE_FIELDS and not _is_forbidden_metric_key(key_str):
            updates[key_str] = value
    if updates:
        state.update(updates)
        candidate_key = str(candidate_payload.get("candidate_key") or "").strip()
        state.generative_handoff_toast = (
            f"Loaded {candidate_key}; undo available."
            if candidate_key
            else "Loaded candidate; undo available."
        )
        refresh = getattr(app, "_refresh_current_hull_surface", None)
        if callable(refresh):
            try:
                refresh()
            except Exception:  # pragma: no cover - defensive guard
                pass
    return prior_snapshot


def undo_candidate_handoff(app: Any) -> bool:
    """Restore the pre-handoff hull state captured by :func:`apply_candidate_to_hull`."""

    prior = getattr(app.state, "generative_handoff_prior", None)
    if not isinstance(prior, Mapping) or not prior:
        return False
    updates = {k: v for k, v in prior.items() if k in HULL_STATE_FIELDS and v is not None}
    if updates:
        app.state.update(updates)
        refresh = getattr(app, "_refresh_current_hull_surface", None)
        if callable(refresh):
            try:
                refresh()
            except Exception:  # pragma: no cover
                pass
    app.state.generative_handoff_prior = {}
    app.state.generative_handoff_toast = ""
    return True


def refresh_frontier_view(app: Any, job_id: str) -> dict[str, Any]:
    """Pull a fresh frontier payload and update ``app.state.generative_frontier_*``.

    The caller (controller / route handler) is responsible for choosing
    when to call this. Returns the resolved view-model for tests.
    """

    # Local import to keep this module importable without the services layer
    # being initialized (e.g., on cold-import in test collection).
    from kayakgen.services.generative_jobs import generative_job_frontier_payload

    manager = getattr(app, "_generative_manager", None)
    if manager is None:
        app.state.generative_frontier_view_available = False
        app.state.generative_frontier_rendered = False
        return {"available": False, "rows": [], "scatter_points": [], "axis_labels": {"x": "", "y": "", "z": None}}

    try:
        payload = generative_job_frontier_payload(manager, job_id)
    except Exception:  # noqa: BLE001 - defensive at the boundary
        app.state.generative_frontier_view_available = False
        app.state.generative_frontier_rendered = False
        return {"available": False, "rows": [], "scatter_points": [], "axis_labels": {"x": "", "y": "", "z": None}}

    metric_options = _candidate_metric_choices(payload)
    x_metric = str(getattr(app.state, "generative_frontier_x_metric", "") or "")
    y_metric = str(getattr(app.state, "generative_frontier_y_metric", "") or "")
    z_metric_raw = getattr(app.state, "generative_frontier_z_metric", None)
    z_metric: str | None = str(z_metric_raw) if z_metric_raw else None

    if not x_metric and metric_options:
        x_metric = metric_options[0]
    if not y_metric and len(metric_options) >= 2:
        y_metric = metric_options[1]
    elif not y_metric and metric_options:
        y_metric = metric_options[0]
    if z_metric and z_metric not in metric_options:
        z_metric = None
    if len(metric_options) <= 2:
        z_metric = None

    view_model = build_frontier_view_model(
        payload,
        x_metric=x_metric,
        y_metric=y_metric,
        z_metric=z_metric,
        fit_registry=_loaded_fit_registry(),
    )

    app.state.generative_frontier_view_available = bool(view_model.get("available"))
    app.state.generative_frontier_rendered = bool(view_model.get("available"))
    app.state.generative_frontier_x_metric = x_metric
    app.state.generative_frontier_y_metric = y_metric
    app.state.generative_frontier_z_metric = z_metric or ""
    app.state.generative_frontier_metric_options = list(metric_options)
    app.state.generative_frontier_table_rows = list(view_model.get("rows") or [])
    app.state.generative_frontier_axis_labels = dict(view_model.get("axis_labels") or {})
    app.state.generative_frontier_scatter_points = list(view_model.get("scatter_points") or [])
    app.state.generative_frontier_scatter_svg = _scatter_svg_fallback(view_model)

    return view_model


# ---------------------------------------------------------------------------
# CSS for the scatter+table block (kept hex-literal-free via CSS var references)
# ---------------------------------------------------------------------------


def frontier_view_css() -> str:
    """Return the CSS for the frontier view; references theme CSS variables only."""

    parts: list[str] = [
        ".kg-frontier-section { "
        f"display: flex; flex-direction: column; gap: {theme.SPACING['space-3']}; "
        "}",
        ".kg-frontier-scatter-svg { background: var(--surface-panel); "
        f"border: {theme.BORDERS['border-width-thin']} solid var(--surface-border); "
        f"border-radius: {theme.RADII['radius-sm']}; width: 100%; "
        f"max-width: {theme.DENSITY['frontier-max-width']}; "
        "}",
        ".kg-frontier-point { stroke: var(--surface-border); stroke-width: 1; }",
    ]
    for claim_state, token in _CLAIM_STATE_COLOR_TOKENS.items():
        css_class = _claim_state_color_class(claim_state)
        parts.append(
            f".{css_class} {{ fill: var(--{token}); }}"
        )
    for css_class, token in _ANALYTICAL_CSS_CLASS_THEME_TOKEN.items():
        parts.append(
            f".{css_class} {{ fill: var(--{token}); }}"
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Render hook
# ---------------------------------------------------------------------------


def render_frontier_view_section(app: Any) -> None:
    """Render the frontier scatter + table inside an active Trame layout context.

    Must be called inside an active ``v3.VCard`` / ``v3.VWindowItem``
    parent so the widgets attach to the live layout tree. Imports
    Trame symbols lazily so the module remains import-safe when the
    ``[web]`` extras are not installed.
    """

    # Lazy imports keep the module importable on cold start without trame.
    from trame.widgets import html as html_widgets  # type: ignore[import-not-found]
    from trame.widgets import vuetify3 as v3  # type: ignore[import-not-found]

    html_widgets.Style(frontier_view_css())

    with v3.VCard(
        classes="kg-frontier-section kg-generate-pick",
        **{"data-testid": "frontier-view-section"},
    ):
        v3.VCardSubtitle("Pareto frontier", classes="kg-frontier-heading")

        v3.VCardText(
            "Loading Pareto frontier.",
            v_if=("generative_frontier_loading",),
            classes="kg-state-panel kg-state-panel--running kg-frontier-loading",
            **{"data-testid": "frontier-view-loading"},
        )

        # Empty-state hint.
        v3.VCardText(
            "Submit and complete a search job to populate the Pareto frontier.",
            v_if=("!generative_frontier_loading && !generative_frontier_view_available",),
            classes="kg-state-panel kg-frontier-empty",
            **{"data-testid": "frontier-view-empty"},
        )

        v3.VCardText(
            "Pareto frontier rendered.",
            v_if=("generative_frontier_rendered",),
            classes="kg-state-panel kg-state-panel--rendered kg-frontier-rendered",
            **{"data-testid": "frontier-view-rendered"},
        )

        with html_widgets.Div(
            v_if=("generative_frontier_view_available",),
            classes="kg-frontier-controls",
        ):
            v3.VSelect(
                v_model=("generative_frontier_x_metric",),
                items=("generative_frontier_metric_options",),
                label="X objective",
                density="compact",
                hide_details=True,
                **{"data-testid": "frontier-x-metric-select"},
            )
            v3.VSelect(
                v_model=("generative_frontier_y_metric",),
                items=("generative_frontier_metric_options",),
                label="Y objective",
                density="compact",
                hide_details=True,
                **{"data-testid": "frontier-y-metric-select"},
            )
            v3.VSelect(
                v_model=("generative_frontier_z_metric",),
                items=("generative_frontier_metric_options",),
                label="Third objective (color)",
                density="compact",
                hide_details=True,
                clearable=True,
                v_if=("generative_frontier_metric_options.length > 2",),
                **{"data-testid": "frontier-z-metric-select"},
            )

        # Scatter: prefer trame.widgets.matplotlib; fall back to the precomputed SVG.
        try:
            from trame.widgets import matplotlib as trame_matplotlib  # type: ignore[import-not-found]

            with html_widgets.Div(
                v_if=("generative_frontier_view_available",),
                classes="kg-frontier-scatter",
                **{"data-testid": "frontier-scatter"},
            ):
                trame_matplotlib.Figure(
                    style=(
                        "width: 100%; "
                        f"max-width: {theme.DENSITY['frontier-max-width']}; "
                        f"height: {theme.DENSITY['frontier-scatter-height']};"
                    ),
                )
        except Exception:  # pragma: no cover - widget optional
            html_widgets.Div(
                "{{ generative_frontier_scatter_svg }}",
                v_if=("generative_frontier_view_available",),
                classes="kg-frontier-scatter-fallback",
                html=True,
                **{"data-testid": "frontier-scatter-fallback"},
            )

        # Sortable table of frontier rows + per-row Load button.
        v3.VDataTable(
            v_if=("generative_frontier_view_available",),
            headers=(
                "[{title: 'Candidate', key: 'candidate_key', sortable: true},"
                " {title: 'Claim state', key: 'claim_state', sortable: true},"
                " {title: 'Convergence', key: 'convergence_flag', sortable: true},"
                " {title: 'X', key: 'x', sortable: true},"
                " {title: 'Y', key: 'y', sortable: true},"
                " {title: 'Third objective', key: 'z', sortable: true}]"
            ),
            items=("generative_frontier_table_rows",),
            item_value="candidate_key",
            density="compact",
            click_row=(app.ctrl.load_generative_candidate, "[$event.item.raw]"),
            **{"data-testid": "frontier-data-table"},
        )

        # Handoff toast: cleared by the undo controller callback.
        with v3.VSnackbar(
            "{{ generative_handoff_toast }}",
            v_model=("generative_handoff_toast",),
            timeout=6000,
            location="bottom right",
            classes="kg-frontier-handoff-toast",
            **{"data-testid": "frontier-handoff-toast"},
        ):
            v3.VBtn(
                "Undo",
                click=app.ctrl.undo_generative_handoff,
                density="compact",
                variant="text",
                **{"data-testid": "frontier-handoff-undo"},
            )


__all__ = (
    "FORBIDDEN_METRIC_TOKENS",
    "apply_candidate_to_hull",
    "build_frontier_view_model",
    "frontier_view_css",
    "refresh_frontier_view",
    "render_frontier_view_section",
    "undo_candidate_handoff",
)
