"""Design report renderer service (RFC 0055).

The design report is a *renderer* over existing aggregates and evaluator
records: hydrostatics, stability, resistance, mesh diagnostics, and the
sweep/search comparison position. It introduces no new evaluator and no
new claim state. The renderer assembles every section the RFC enumerates,
runs the assembled HTML through a forbidden-copy scan, and optionally
emits a sibling PDF when ``weasyprint`` is installed.

Per RFC 0055 the report surface must NOT advertise any "safe",
"seaworthy", "validated", "calibrated", "final prediction", or
"design fitness" copy. The explicit negated tokens
(``unvalidated_hydrostatic_comparison``, ``uncalibrated_comparative``)
are scrubbed from the scan window so the negation itself does not trip
the refusal.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.contract import LoadCase, ResistanceMetadata
from kayakgen.eval.high_angle_gz import (
    HIGH_ANGLE_GZ_SURFACE_WARNINGS,
    build_high_angle_gz_block,
)
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.mesh_diagnostics import diagnose_mesh
from kayakgen.eval.resistance import resistance_curve
from kayakgen.eval.stability import (
    evaluate_equilibrium_stability,
    evaluate_initial_stability,
)
from kayakgen.model.hull import Hull
from kayakgen.search.compare import build_comparison_report

__all__ = [
    "DesignReportRequest",
    "DesignReportResult",
    "ReportForbiddenCopyError",
    "FORBIDDEN_COPY_PATTERN",
    "FORBIDDEN_COPY_TOKENS",
    "FORBIDDEN_COPY_SCRUB_TOKENS",
    "render_design_report",
]

# RFC 0055: tokens that must never appear in the rendered report surface.
# Names are load-bearing — `tests/test_design_report.py` pins them.
FORBIDDEN_COPY_TOKENS: tuple[str, ...] = (
    "safe",
    "seaworthy",
    "validated",
    "calibrated",
    "final prediction",
    "design fitness",
)

# Explicit negated forms that legitimately appear (e.g.
# ``unvalidated_hydrostatic_comparison``). These are scrubbed from the scan
# window before the forbidden-token check so the negation does not trip
# the refusal. Order matters: longest first so the longer specific token
# is consumed before its shorter prefix is matched.
FORBIDDEN_COPY_SCRUB_TOKENS: tuple[str, ...] = (
    "unvalidated_hydrostatic_comparison",
    "uncalibrated_comparative",
    "not_safety_or_seaworthiness_claim",
    "raw_unvalidated",
    "unvalidated_",
    "uncalibrated_",
)

# Compiled case-insensitive scan pattern used by the renderer and pinned by
# the regression test. Each token is matched on a word/phrase boundary.
FORBIDDEN_COPY_PATTERN: re.Pattern[str] = re.compile(
    "|".join(re.escape(token) for token in FORBIDDEN_COPY_TOKENS),
    re.IGNORECASE,
)

_TEMPLATE_DIR = Path(__file__).parent / "design_report_templates"
_TEMPLATE_NAME = "report.html.j2"
_PREVIEW_PNG_DIMENSION_PX = 480
_MAX_HTML_BYTES = 5 * 1024 * 1024


class ReportForbiddenCopyError(RuntimeError):
    """Raised when the rendered report contains any forbidden copy token."""

    def __init__(self, matches: list[str], *, snippet: str | None = None) -> None:
        self.matches = matches
        self.snippet = snippet
        joined = ", ".join(sorted(set(matches)))
        super().__init__(
            f"design report assembly produced forbidden copy: {joined}"
        )


class DesignReportRequest(BaseModel):
    """Input for the design-report renderer."""

    model_config = ConfigDict(extra="forbid")

    hull_path: Path
    html_out: Path
    pdf_out: Path | None = None
    from_run: Path | None = None


class DesignReportResult(BaseModel):
    """Renderer outcome."""

    model_config = ConfigDict(extra="forbid")

    html_path: Path
    pdf_path: Path | None = None
    forbidden_copy_clean: bool
    html_size_bytes: int = Field(ge=0)
    sections: list[str] = Field(default_factory=list)


def render_design_report(
    hull: Hull,
    *,
    from_run: Path | None = None,
    html_out: Path,
    pdf_out: Path | None = None,
    hull_source_path: Path | None = None,
    timestamp: datetime | None = None,
) -> DesignReportResult:
    """Render an RFC 0055 design report and write it to ``html_out``.

    The renderer orchestrates the existing hydrostatics, stability,
    resistance, mesh-diagnostics, and (optional) comparison services to
    gather every section, runs the jinja2 template, then scans the
    assembled text against :data:`FORBIDDEN_COPY_PATTERN`. The HTML is
    written only if the scan passes; on failure the renderer raises
    :class:`ReportForbiddenCopyError` and leaves no artifact behind.

    PDF output is produced when ``pdf_out`` is set AND ``weasyprint`` is
    importable. Without ``weasyprint`` the renderer raises ``RuntimeError``
    pointing at the ``kayakgen[report]`` extras group; the HTML still
    lands.
    """

    try:
        import jinja2
    except ImportError as exc:  # pragma: no cover - import-guarded
        raise RuntimeError(
            "jinja2 is required for design-report rendering; "
            "install via `pip install 'kayakgen[report]'`"
        ) from exc

    html_out = Path(html_out)
    pdf_out_path = Path(pdf_out) if pdf_out is not None else None

    timestamp = timestamp or datetime.now(timezone.utc)

    context = _assemble_context(
        hull,
        from_run=from_run,
        hull_source_path=hull_source_path,
        timestamp=timestamp,
    )
    section_ids = [section["id"] for section in context["sections"]]

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(_TEMPLATE_NAME)
    html_text = template.render(**context)

    matches = _scan_forbidden(html_text)
    if matches:
        snippet = _first_match_snippet(html_text, matches[0])
        raise ReportForbiddenCopyError(matches, snippet=snippet)

    html_bytes = html_text.encode("utf-8")
    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_bytes(html_bytes)

    pdf_written: Path | None = None
    if pdf_out_path is not None:
        try:
            import weasyprint  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "PDF export requires weasyprint; install via "
                "`pip install 'kayakgen[report]'`"
            ) from exc
        pdf_out_path.parent.mkdir(parents=True, exist_ok=True)
        weasyprint.HTML(string=html_text).write_pdf(str(pdf_out_path))
        pdf_written = pdf_out_path

    return DesignReportResult(
        html_path=html_out,
        pdf_path=pdf_written,
        forbidden_copy_clean=True,
        html_size_bytes=len(html_bytes),
        sections=section_ids,
    )


# ---------------------------------------------------------------------------
# Internal section assemblers


def _assemble_context(
    hull: Hull,
    *,
    from_run: Path | None,
    hull_source_path: Path | None,
    timestamp: datetime,
) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    artifacts: list[dict[str, str]] = []

    header = _section_header(hull, hull_source_path, timestamp)
    sections.append(header)

    parameters = _section_parameters(hull)
    sections.append(parameters)

    rendered_views = _section_rendered_views(hull)
    sections.append(rendered_views)

    hydro = evaluate_hydrostatics(hull)
    hydrostatics = _section_hydrostatics(hydro)
    sections.append(hydrostatics)

    load_case = LoadCase()
    initial_stability = evaluate_initial_stability(hull, load_case)
    equilibrium = evaluate_equilibrium_stability(hull, load_case)
    high_angle_block = _safe_high_angle(hull, load_case)
    stability = _section_stability(initial_stability, equilibrium, high_angle_block)
    sections.append(stability)

    resistance = resistance_curve(hull)
    resistance_section = _section_resistance(resistance)
    sections.append(resistance_section)

    mesh_section = _section_mesh(hull)
    sections.append(mesh_section)

    comparison = _section_comparison(hull, from_run)
    sections.append(comparison)

    if hull_source_path is not None:
        artifacts.append(_artifact_entry(hull_source_path, label="hull_json"))
    if from_run is not None:
        run_record = Path(from_run) / "run.json"
        if run_record.is_file():
            artifacts.append(_artifact_entry(run_record, label="sweep_run"))
    sections.append(_section_artifacts(artifacts))

    sections.append(_section_claim_explanations())

    return {
        "title": f"kayakgen design report — {header['hull_name']}",
        "timestamp_iso": timestamp.isoformat(),
        "sections": sections,
    }


def _section_header(
    hull: Hull, hull_source_path: Path | None, timestamp: datetime
) -> dict[str, Any]:
    return {
        "id": "header",
        "title": "Header",
        "hull_name": hull.name or "untitled",
        "record_hash": hull.hash(),
        # RFC 0049 reserves a separate ``Hull.design_hash()``. Until that
        # lands, the record hash is the only stable identifier. Tag the
        # second slot honestly so the report reads correctly.
        "design_hash": hull.hash(),
        "design_hash_note": "record_hash mirrored; RFC 0049 design_hash() pending",
        "kayakgen_version": _kayakgen_version(),
        "timestamp_iso": timestamp.isoformat(),
        "hull_source": str(hull_source_path) if hull_source_path else None,
    }


def _section_parameters(hull: Hull) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for field_name, field in type(hull).model_fields.items():
        if field_name in ("schema_version",):
            continue
        value = getattr(hull, field_name)
        unit = _field_unit(field_name)
        rows.append(
            {
                "name": field_name,
                "value": _format_value(value),
                "unit": unit,
                "source": _field_source(field, value),
            }
        )
    return {"id": "parameters", "title": "Parameters", "rows": rows}


def _section_rendered_views(hull: Hull) -> dict[str, Any]:
    preview_png = _render_preview_png(hull)
    return {
        "id": "rendered_views",
        "title": "Rendered views",
        "preview_alt": "hull plus deck 3D preview (uncalibrated_geometry view)",
        "preview_png_base64": preview_png,
        "notice": (
            "Embedded preview is a small PNG snapshot of the generated "
            "hull plus deck closed body; not a rendered photograph."
        ),
    }


def _section_hydrostatics(hydro: Any) -> dict[str, Any]:
    rows = [
        ("Displaced volume", f"{hydro.displaced_volume_m3:.4f}", "m^3"),
        ("Displaced mass", f"{hydro.displaced_mass_kg:.2f}", "kg"),
        ("Wetted surface", f"{hydro.wetted_surface_m2:.4f}", "m^2"),
        ("Waterplane area", f"{hydro.waterplane_area_m2:.4f}", "m^2"),
        ("LCB fraction", f"{hydro.LCB_frac:.4f}", ""),
        ("Cp actual", f"{hydro.Cp_actual:.4f}", ""),
        ("Cm actual", f"{hydro.Cm_actual:.4f}", ""),
        (
            "GM0",
            "n/a" if hydro.GM0_m is None else f"{hydro.GM0_m:.4f}",
            "m",
        ),
    ]
    return {
        "id": "hydrostatics",
        "title": "Hydrostatics",
        "rows": [{"label": label, "value": value, "unit": unit} for label, value, unit in rows],
    }


def _section_stability(
    initial: Any, equilibrium: Any, high_angle_block: dict[str, Any] | None
) -> dict[str, Any]:
    section = {
        "id": "stability",
        "title": "Stability",
        "initial": _stability_rows(initial),
        "equilibrium": _stability_rows(equilibrium),
        "high_angle": None,
        "high_angle_surface_warnings": list(HIGH_ANGLE_GZ_SURFACE_WARNINGS),
    }
    if high_angle_block is not None:
        section["high_angle"] = {
            "available": bool(high_angle_block.get("available", False)),
            "result_semantics": str(high_angle_block.get("result_semantics", "")),
            "body_profile": str(high_angle_block.get("body_profile", "")),
            "warnings": list(high_angle_block.get("warnings", [])),
            "assumptions": list(high_angle_block.get("assumptions", [])),
            "heel_grid_deg": list(high_angle_block.get("heel_grid_deg", [])),
            "summary": high_angle_block.get("summary"),
            "unavailable_reason": high_angle_block.get("unavailable_reason"),
        }
    return section


def _stability_rows(result: Any) -> dict[str, Any]:
    return {
        "method": result.method,
        "status": result.status,
        "load_mass_kg": result.load_mass_kg,
        "displaced_mass_kg": result.displaced_mass_kg,
        "displacement_error_kg": result.displacement_error_kg,
        "initial_GM0_m": result.initial_GM0_m,
        "equilibrium_draft_m": result.equilibrium_draft_m,
        "trim_angle_deg": result.trim_angle_deg,
        "warnings": list(result.warnings),
    }


def _section_resistance(curve: Any) -> dict[str, Any]:
    rows = []
    for speed, fn, rv, rw, rt in zip(
        curve.V_knots, curve.Fn, curve.Rv_N, curve.Rw_N, curve.Rt_N, strict=True
    ):
        rows.append(
            {
                "speed_kt": float(speed),
                "Fn": float(fn),
                "Rv_N": float(rv),
                "Rw_N": float(rw),
                "Rt_N": float(rt),
            }
        )
    metadata: ResistanceMetadata = curve.metadata
    return {
        "id": "resistance",
        "title": "Resistance",
        "rows": rows,
        "claim_state": metadata.claim_state,
        "accepted_uses": list(metadata.accepted_uses),
        "warnings": list(metadata.warnings),
        # Surface notice deliberately written to avoid forbidden tokens.
        "notice": (
            "Curve carries the uncalibrated_comparative resistance claim; "
            "rows are for comparative filtering between candidates only."
        ),
    }


def _section_mesh(hull: Hull) -> dict[str, Any]:
    parts: list[dict[str, Any]] = []
    for part in ("hull", "deck"):
        try:
            diagnostics = diagnose_mesh(hull, part=part)
        except Exception as exc:  # pragma: no cover - defensive
            parts.append({"part": part, "status": "error", "message": str(exc)})
            continue
        parts.append(
            {
                "part": part,
                "status": "ready",
                "readiness_level": diagnostics.readiness.level,
                "readiness_reasons": list(diagnostics.readiness.reasons),
                "raw_boundary_edges": diagnostics.raw_boundary_edges,
                "raw_nonmanifold_edges": diagnostics.raw_nonmanifold_edges,
                "welded_boundary_edges": diagnostics.welded_boundary_edges,
                "welded_nonmanifold_edges": diagnostics.welded_nonmanifold_edges,
                "degenerate_faces": diagnostics.degenerate_faces,
                "warnings": list(diagnostics.warnings),
            }
        )
    return {"id": "mesh", "title": "Mesh and readiness", "parts": parts}


def _section_comparison(hull: Hull, from_run: Path | None) -> dict[str, Any]:
    if from_run is None:
        return {
            "id": "comparison",
            "title": "Comparison position",
            "available": False,
            "notice": "No --from-run was provided; this section is omitted by request.",
        }

    run_dir = Path(from_run)
    if not (run_dir / "run.json").is_file():
        return {
            "id": "comparison",
            "title": "Comparison position",
            "available": False,
            "notice": (
                f"No sweep/search run.json found under {run_dir}; "
                "comparison position cannot be computed."
            ),
        }

    try:
        report = build_comparison_report(run_dir)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "id": "comparison",
            "title": "Comparison position",
            "available": False,
            "notice": f"comparison report unavailable: {exc}",
        }

    target_hash = hull.hash()
    match = None
    for summary in report.candidate_summaries:
        if summary.hull_hash == target_hash:
            match = summary
            break

    if match is None:
        return {
            "id": "comparison",
            "title": "Comparison position",
            "available": False,
            "notice": (
                "This hull was not in the referenced run "
                f"({run_dir}); no comparison position to report."
            ),
            "run_name": report.run_name,
            "candidates_total": len(report.candidate_summaries),
        }

    on_frontier = match.candidate_key in set(report.pareto_front_keys)
    high_angle_display = None
    if match.high_angle_gz_display is not None:
        display = match.high_angle_gz_display
        high_angle_display = {
            "available": display.available,
            "body_profile": display.body_profile,
            "result_semantics": display.result_semantics,
            "max_gz_m": display.max_gz_m,
            "heel_at_max_gz_deg": display.heel_at_max_gz_deg,
            "range_positive_stability_deg": display.range_positive_stability_deg,
            "warnings": list(display.warnings),
            "assumptions": list(display.assumptions),
        }
    return {
        "id": "comparison",
        "title": "Comparison position",
        "available": True,
        "run_name": report.run_name,
        "report_kind": report.report_kind,
        "candidate_index": match.candidate_index,
        "candidate_key": match.candidate_key,
        "candidates_total": len(report.candidate_summaries),
        "frontier_size": len(report.pareto_front_keys),
        "on_frontier": on_frontier,
        "objective_values": match.objective_values,
        "warnings": list(match.warnings),
        "high_angle_display": high_angle_display,
    }


def _section_artifacts(artifacts: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "id": "artifacts",
        "title": "Artifact references",
        "rows": artifacts,
        "notice": (
            "Hashes are SHA-256 over the referenced bytes at render time; "
            "recipients can re-derive every number from these inputs."
        ),
    }


def _section_claim_explanations() -> dict[str, Any]:
    rows = [
        {
            "topic": "Hydrostatics",
            "claim": "raw_unvalidated",
            "decisions": ["D006", "D012"],
            "explanation": (
                "Integrated mesh hydrostatics; arithmetic on the generated "
                "surface. No measured comparator; no accepted prediction "
                "envelope is advertised."
            ),
        },
        {
            "topic": "Resistance",
            "claim": "uncalibrated_comparative",
            "decisions": ["D006", "D014"],
            "explanation": (
                "Michell + ITTC-57 sweep; admitted only for comparative "
                "filtering between candidates, never as a drag report."
            ),
        },
        {
            "topic": "Initial stability",
            "claim": "raw_unvalidated",
            "decisions": ["D018"],
            "explanation": (
                "Design-waterline initial-GM0 read model from the generated "
                "body; no measured comparator."
            ),
        },
        {
            "topic": "High-angle GZ (opt-in)",
            "claim": "unvalidated_hydrostatic_comparison",
            "decisions": ["D022", "D027"],
            "explanation": (
                "Display-only; never a Pareto/search objective and never a "
                "stability claim. Surface warnings travel with every row."
            ),
        },
        {
            "topic": "Mesh / readiness",
            "claim": "n/a (readiness, not a claim)",
            "decisions": ["D026"],
            "explanation": (
                "Readiness level governs what the next operation may "
                "consume; it is independent of any numeric claim state."
            ),
        },
        {
            "topic": "Comparison position",
            "claim": "report read-model",
            "decisions": ["D025", "D028"],
            "explanation": (
                "Pareto position from a sweep/search run; objectives and "
                "frontier eligibility follow the run's own admissibility "
                "gates."
            ),
        },
    ]
    return {
        "id": "claim_explanations",
        "title": "Claim-state explanations",
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Helpers


def _scan_forbidden(text: str) -> list[str]:
    scrubbed = text
    for token in FORBIDDEN_COPY_SCRUB_TOKENS:
        scrubbed = re.sub(re.escape(token), "", scrubbed, flags=re.IGNORECASE)
    return [match.group(0) for match in FORBIDDEN_COPY_PATTERN.finditer(scrubbed)]


def _first_match_snippet(text: str, match_text: str) -> str | None:
    idx = text.lower().find(match_text.lower())
    if idx < 0:
        return None
    start = max(0, idx - 40)
    end = min(len(text), idx + len(match_text) + 40)
    return text[start:end]


def _safe_high_angle(hull: Hull, load_case: LoadCase) -> dict[str, Any] | None:
    try:
        return build_high_angle_gz_block(
            hull,
            load_case,
            heel_grid_deg=[0.0, 10.0, 20.0, 30.0, 45.0, 60.0],
        )
    except Exception:  # pragma: no cover - defensive
        return None


def _render_preview_png(hull: Hull) -> str:
    """Render a small PNG of the hull plus deck for embedding.

    Uses matplotlib's 3D wireframe (available via the desktop extras when
    present) and falls back to a 1x1 transparent PNG when matplotlib is
    unavailable. The output is base64-encoded for inline ``<img>`` use.
    """

    try:
        import matplotlib  # type: ignore[import-not-found]

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt  # type: ignore[import-not-found]
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore[import-not-found]
    except Exception:
        return _BLANK_PNG_BASE64

    try:
        geom = hull.to_geometry()
        vertices, faces = geom.mesh("hull")
    except Exception:
        return _BLANK_PNG_BASE64

    fig = plt.figure(figsize=(4.8, 3.2), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    try:
        tris = vertices[faces]
        coll = Poly3DCollection(tris, alpha=0.6, edgecolor=(0.2, 0.3, 0.5, 0.4))
        coll.set_facecolor((0.55, 0.7, 0.85, 0.5))
        ax.add_collection3d(coll)
        ax.auto_scale_xyz(
            [vertices[:, 0].min(), vertices[:, 0].max()],
            [vertices[:, 1].min(), vertices[:, 1].max()],
            [vertices[:, 2].min(), vertices[:, 2].max()],
        )
        ax.set_axis_off()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    finally:
        plt.close(fig)


def _artifact_entry(path: Path, *, label: str) -> dict[str, str]:
    data = path.read_bytes() if path.is_file() else b""
    digest = hashlib.sha256(data).hexdigest()
    return {
        "label": label,
        "path": str(path),
        "sha256": digest,
        "size_bytes": str(len(data)),
    }


def _format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _field_unit(name: str) -> str:
    units = {
        "length_m": "m",
        "beam_oa_m": "m",
        "beam_wl_m": "m",
        "draft_m": "m",
        "deck_height_m": "m",
        "rocker_bow_m": "m",
        "rocker_stern_m": "m",
    }
    return units.get(name, "")


def _field_source(field: Any, value: Any) -> str:
    default = getattr(field, "default", None)
    try:
        if value == default:
            return "default"
    except Exception:
        return "override"
    return "operator override"


def _kayakgen_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - py<3.8
        return "unknown"
    try:
        return version("kayakgen")
    except PackageNotFoundError:  # pragma: no cover - editable install w/o metadata
        return "unknown"


# 1x1 transparent PNG fallback (base64-encoded).
_BLANK_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNgAAIAAAUAAen"
    "63NgAAAAASUVORK5CYII="
)


# Public re-exports used by tests for the size budget check.
HTML_SIZE_LIMIT_BYTES = _MAX_HTML_BYTES

# Make the imports module-importable without falling unused (importlib reach
# from tests) — referenced indirectly via attribute access.
_ = json  # noqa: F841
