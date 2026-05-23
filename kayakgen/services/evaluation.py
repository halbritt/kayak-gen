"""Evaluation service: hydrostatics, resistance, mesh diagnostics, summaries.

These functions accept a flat state dict (as produced by the Trame UI or by
the REST request body) and return Pydantic records or plain dicts. They do
not touch any HTTP / Trame state object.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kayakgen.eval.contract import (
    EvaluationResult,
    LoadCase,
    ResistanceCurve,
    ResistanceMetadata,
    StabilityResult,
)
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.mesh_diagnostics import MeshDiagnostics, diagnose_mesh
from kayakgen.eval.mesh_package import MeshPackageManifest
from kayakgen.eval.resistance import KNOTS_TO_MS, evaluate_resistance, resistance_curve
from kayakgen.eval.stability import evaluate_equilibrium_stability
from kayakgen.eval.stability.trim_equilibrium import _evaluate_trim_equilibrium
from kayakgen.model.advisory import design_advisory
from kayakgen.model.hull import Hull
from kayakgen.model.validity import evaluate_design_validity
from kayakgen.services.design import hull_from_web_state

DISPLAY_CURVE_SPEEDS_KT: tuple[float, ...] = (2.0, 3.0, 4.0, 5.0, 6.0)
MESH_PROFILE_LABEL_TO_ID: dict[str, str] = {
    "open-wetted-surface": "open_wetted_surface_resistance_v1",
    "watertight-solid": "watertight_solid_resistance_v1",
}
MESH_PROFILE_ID_TO_LABEL: dict[str, str] = {
    profile_id: label for label, profile_id in MESH_PROFILE_LABEL_TO_ID.items()
}
WATERTIGHT_SOLID_DISABLED_TOOLTIP = (
    "Current generated packages do not satisfy watertight-solid readiness."
)

# Mirrors the Trame state aliases used by the orchestrators. Duplicated to
# keep ``kayakgen.services`` free of any ``kayakgen.ui.*`` imports.
_MESH_PACKAGE_REF_ALIASES: tuple[str, ...] = ("mesh_package_ref", "cfd_mesh_package_ref")
_CFD_STATUS_ALIASES: tuple[str, ...] = ("cfd_status", "status")
_CFD_PAYLOAD_ALIASES: tuple[str, ...] = (
    "cfd_payload",
    "cfd_job_payload",
    "cfd_last_payload",
)
_CFD_STATUS_LINE_ALIASES: tuple[str, ...] = ("cfd_status_lines",)


def metrics_from_state(state: dict[str, Any], stations: int = 60) -> dict[str, Any]:
    """Single-shot read model: hydrostatics + at-speed resistance."""
    hull = hull_from_web_state(state)
    h = evaluate_hydrostatics(hull, stations=stations)
    target_kt = float(state.get("target_speed_kt", 3.5))
    V_ms = target_kt * KNOTS_TO_MS
    r = evaluate_resistance(
        hull, V_ms, Sw=h.wetted_surface_m2, n_stations=400, n_depths=20, n_theta=30
    )
    resistance_claim = ResistanceMetadata()
    advisory = design_advisory(
        hull,
        cp=h.Cp_actual,
        displaced_mass_kg=h.displaced_mass_kg,
    )
    return {
        "displaced_mass_kg": h.displaced_mass_kg,
        "wetted_surface_m2": h.wetted_surface_m2,
        "waterplane_area_m2": h.waterplane_area_m2,
        "Cp_actual": h.Cp_actual,
        "Cm_actual": h.Cm_actual,
        "l_over_bwl": advisory.l_over_bwl,
        "Fn": r["Fn"],
        "Rv_N": r["Rv_N"],
        "Rw_N": r["Rw_N"],
        "Rt_N": r["Rt_N"],
        "resistance_claim_state": resistance_claim.claim_state,
        "resistance_accepted_uses": resistance_claim.accepted_uses,
        "resistance_warnings": resistance_claim.warnings,
        "advisory_warnings": advisory.warnings,
        "design_validity": advisory.design_validity.model_dump(mode="json"),
        "design_warning_codes": tuple(
            finding.code
            for finding in advisory.design_validity.findings
            if finding.level == "advisory" and finding.severity == "warning"
        ),
    }


def analysis_view_model(state: dict[str, Any]) -> dict[str, Any]:
    """Build unit-labeled analysis rows for the current web hull state."""
    hull = hull_from_web_state(state)
    hydro = evaluate_hydrostatics(hull, stations=60)
    resistance = resistance_curve(
        hull,
        V_knots=np.array(DISPLAY_CURVE_SPEEDS_KT, dtype=float),
        n_stations=400,
        n_depths=20,
        n_theta=30,
    )
    advisory = design_advisory(
        hull,
        cp=hydro.Cp_actual,
        displaced_mass_kg=hydro.displaced_mass_kg,
    )
    hydro_rows = [
        ("Displacement", f"{hydro.displaced_mass_kg:.1f}", "kg"),
        ("Wetted surface", f"{hydro.wetted_surface_m2:.3f}", "m^2"),
        ("Waterplane area", f"{hydro.waterplane_area_m2:.3f}", "m^2"),
        ("GM0", f"{hydro.GM0_m:.3f}", "m"),
        ("Cp actual", f"{hydro.Cp_actual:.3f}", ""),
        ("Cm actual", f"{hydro.Cm_actual:.3f}", ""),
        ("L/B wl", f"{advisory.l_over_bwl:.2f}", ""),
    ]
    resistance_rows = [
        {
            "speed_kt": speed,
            "Fn": fn,
            "Rv_N": rv,
            "Rw_N": rw,
            "Rt_N": rt,
        }
        for speed, fn, rv, rw, rt in zip(
            resistance.V_knots,
            resistance.Fn,
            resistance.Rv_N,
            resistance.Rw_N,
            resistance.Rt_N,
            strict=True,
        )
    ]
    return {
        "hydro_rows": hydro_rows,
        "resistance_rows": resistance_rows,
        "design_warnings": list(advisory.warnings),
        "design_validity": advisory.design_validity.model_dump(mode="json"),
        "resistance_warnings": list(resistance.metadata.warnings),
        "warnings": [*advisory.warnings, *resistance.metadata.warnings],
        "resistance_metadata": resistance.metadata.model_dump(mode="json"),
    }


def resistance_table_view_model(
    state: dict[str, Any],
    *,
    target_tolerance_kt: float = 0.05,
) -> dict[str, Any]:
    """Resistance table rows with a focused target-speed row.

    The fixed sweep stays at ``DISPLAY_CURVE_SPEEDS_KT``. A continuous
    ``target_speed_kt`` is inserted as a sorted extra row only when it is
    outside the configured tolerance from every fixed sweep speed.
    """
    hull = hull_from_web_state(state)
    target_speed_kt = float(state.get("target_speed_kt", 3.5))
    nearest_fixed = min(DISPLAY_CURVE_SPEEDS_KT, key=lambda speed: abs(speed - target_speed_kt))
    matches_fixed = abs(nearest_fixed - target_speed_kt) <= target_tolerance_kt + 1e-9
    focus_speed = nearest_fixed if matches_fixed else target_speed_kt
    speeds = list(DISPLAY_CURVE_SPEEDS_KT)
    if not matches_fixed:
        speeds.append(target_speed_kt)
    speeds = sorted(speeds)

    resistance = resistance_curve(
        hull,
        V_knots=np.array(speeds, dtype=float),
        n_stations=400,
        n_depths=20,
        n_theta=30,
    )
    rows = []
    for speed, fn, rv, rw, rt in zip(
        resistance.V_knots,
        resistance.Fn,
        resistance.Rv_N,
        resistance.Rw_N,
        resistance.Rt_N,
        strict=True,
    ):
        is_target = abs(float(speed) - focus_speed) <= 1e-9
        rows.append(
            {
                "speed_kt": float(speed),
                "Fn": float(fn),
                "Rv_N": float(rv),
                "Rw_N": float(rw),
                "Rt_N": float(rt),
                "is_target": is_target,
                "source": "target" if is_target and not matches_fixed else "sweep",
            }
        )

    return {
        "target_speed_kt": target_speed_kt,
        "target_tolerance_kt": target_tolerance_kt,
        "rows": rows,
        "metadata": resistance.metadata.model_dump(mode="json"),
        "caption": (
            "Uncalibrated; no accepted final-prediction validity envelope. "
            "Compare nearby candidates, do not report as drag."
        ),
    }


def evaluation_summary(state: dict[str, Any]) -> dict[str, Any]:
    """Status-bar read model for package, readiness, resistance, CFD, advisories."""
    hull = hull_from_web_state(state)
    hydro = evaluate_hydrostatics(hull, stations=60)
    advisory = design_advisory(
        hull,
        cp=hydro.Cp_actual,
        displaced_mass_kg=hydro.displaced_mass_kg,
    )
    resistance_claim = ResistanceMetadata()

    package_ref = str(_first_truthy_alias(state, _MESH_PACKAGE_REF_ALIASES) or "")
    package_model = mesh_package_view_model(package_ref) if package_ref else None
    if package_model:
        package = package_model["profile"]
        readiness = package_model["readiness"]
    else:
        package = _profile_view(MESH_PROFILE_LABEL_TO_ID["open-wetted-surface"])
        readiness = {
            "level": None,
            "display": "unavailable",
            "reasons": ["No mesh package selected."],
        }

    advisories = [
        {
            "code": finding.code,
            "message": finding.message,
            "field_refs": list(finding.parameters),
        }
        for finding in advisory.design_validity.findings
        if finding.level == "advisory" and finding.severity == "warning"
    ]

    return {
        "package": package,
        "readiness": readiness,
        "resistance_claim": {
            "claim_state": resistance_claim.claim_state,
            "accepted_uses": list(resistance_claim.accepted_uses),
            "warnings": list(resistance_claim.warnings),
        },
        "cfd_status": _cfd_status_from_state(state),
        "advisories": advisories,
    }


def mesh_diagnostics_lines_from_state(
    state: dict[str, Any],
    part: str = "hull",
) -> list[str]:
    """Text diagnostics for a generated mesh, with welded topology primary."""
    hull = hull_from_web_state(state)
    diagnostics = diagnose_mesh(hull, part=part)
    counts = _mesh_diagnostics_counts(diagnostics)
    boundary = counts["boundary_edges"]
    nonmanifold = counts["nonmanifold_edges"]
    lines = [
        f"{str(part).title()} diagnostics",
        f"Readiness: {diagnostics.readiness.level}",
        f"Boundary edges: {boundary['primary']} (welded primary)",
        f"Non-manifold edges: {nonmanifold['primary']} (welded primary)",
        f"Degenerate faces: {diagnostics.degenerate_faces}",
        (
            "Raw detail: "
            f"boundary edges {boundary['raw']}; "
            f"non-manifold edges {nonmanifold['raw']}; "
            f"vertices {diagnostics.profile.vertex_count}; "
            f"welded vertices {diagnostics.profile.welded_vertex_count}"
        ),
    ]
    if diagnostics.warnings:
        lines.extend(["Warnings", *[f"  {warning}" for warning in diagnostics.warnings]])
    return lines


def mesh_package_view_model(path: str | Path) -> dict[str, Any]:
    """Read a mesh package manifest and quality reports for UI display."""
    package_path = Path(path).expanduser()
    manifest_path = package_path / "manifest.json"
    base = {
        "path": str(package_path),
        "profile_options": _mesh_profile_options(),
        "parts": [],
        "diagnostics": {},
    }
    if not manifest_path.is_file():
        return {
            **base,
            "status": "missing",
            "error": "mesh_package_not_found",
            "profile": _profile_view(MESH_PROFILE_LABEL_TO_ID["open-wetted-surface"]),
            "readiness": {
                "level": None,
                "display": "unavailable",
                "reasons": ["Mesh package manifest not found."],
            },
            "warnings": ["Mesh package manifest not found."],
        }

    try:
        manifest = MeshPackageManifest.model_validate_json(manifest_path.read_text())
    except Exception as exc:
        return {
            **base,
            "status": "error",
            "error": "malformed_mesh_package",
            "message": str(exc),
            "profile": _profile_view(MESH_PROFILE_LABEL_TO_ID["open-wetted-surface"]),
            "readiness": {
                "level": None,
                "display": "unavailable",
                "reasons": ["Malformed mesh package manifest."],
            },
            "warnings": ["Malformed mesh package manifest."],
        }

    diagnostics: dict[str, Any] = {}
    warnings = list(manifest.warnings)
    artifact_errors: list[str] = []
    for label, artifact_ref in [
        ("hull_json", manifest.hull_json),
        *[
            (f"surface {part}", artifact_ref)
            for part, artifact_ref in sorted(manifest.surfaces.items())
        ],
    ]:
        try:
            resolve_package_artifact_path(package_path, artifact_ref)
        except ValueError:
            artifact_errors.append(f"{label}: artifact path outside package")
            warnings.append(f"{label}: artifact path outside package")

    for part, report_ref in sorted(manifest.quality_reports.items()):
        try:
            report_path = resolve_package_artifact_path(package_path, report_ref)
        except ValueError:
            diagnostics[part] = {
                "status": "error",
                "error": "artifact_path_outside_package",
                "path": report_ref,
            }
            artifact_errors.append(f"{part}: artifact path outside package")
            warnings.append(f"{part}: artifact path outside package")
            continue
        try:
            report = MeshDiagnostics.model_validate_json(report_path.read_text())
        except Exception:
            diagnostics[part] = {
                "status": "error",
                "error": "malformed_mesh_quality_report",
                "path": report_ref,
            }
            warnings.append(f"{part}: mesh quality report unavailable")
            continue
        diagnostics[part] = {
            "status": "ready",
            "path": report_ref,
            "readiness": report.readiness.model_dump(mode="json"),
            "counts": _mesh_diagnostics_counts(report),
            "warnings": list(report.warnings),
        }

    return {
        **base,
        "status": "ready",
        "manifest_path": str(manifest_path),
        "hull_hash": manifest.hull_hash,
        "profile": _profile_view(manifest.solver_profile.profile_name),
        "readiness": manifest.readiness.model_dump(mode="json"),
        "warnings": warnings,
        "artifact_errors": artifact_errors,
        "parts": list(manifest.parts),
        "diagnostics": diagnostics,
    }


def analysis_lines_from_state(state: dict[str, Any]) -> list[str]:
    """Text view of :func:`analysis_view_model` for the current Trame UI."""
    model = analysis_view_model(state)
    lines = ["Hydrostatics"]
    lines.extend(
        f"  {label:<16} {value:>10} {unit}".rstrip()
        for label, value, unit in model["hydro_rows"]
    )
    lines.append("")
    lines.append("Resistance curve (raw comparative filter)")
    lines.append("  kt     Fn     Rv N     Rw N     Rt N")
    lines.extend(
        f"  {row['speed_kt']:>3.1f}  {row['Fn']:>5.2f}  {row['Rv_N']:>7.1f}  "
        f"{row['Rw_N']:>7.1f}  {row['Rt_N']:>7.1f}"
        for row in model["resistance_rows"]
    )
    if model["design_warnings"]:
        lines.extend(
            ["", "Design warnings", *[f"  {warning}" for warning in model["design_warnings"]]]
        )
    if model["resistance_warnings"]:
        lines.extend(
            [
                "",
                "Resistance warnings",
                *[f"  {warning}" for warning in model["resistance_warnings"]],
            ]
        )
    return lines


def hydro_lines_from_state(state: dict[str, Any]) -> list[str]:
    """Hydrostatics-only text view for the web Hydrostatics card."""
    model = analysis_view_model(state)
    lines = ["Hydrostatics"]
    lines.extend(
        f"  {label:<16} {value:>10} {unit}".rstrip()
        for label, value, unit in model["hydro_rows"]
    )
    if model["design_warnings"]:
        lines.extend(
            ["", "Design warnings", *[f"  {warning}" for warning in model["design_warnings"]]]
        )
    return lines


def hydro_rows_from_state(state: dict[str, Any]) -> list[dict[str, str]]:
    """Return hydrostatics as a list of ``{label, value}`` dicts for table rendering.

    Each entry has ``label`` (e.g. "Displacement") and ``value`` (e.g. "18.5 kg").
    Design warnings are appended as rows with label ``"Warning"`` so the
    table surface can surface them inline without a separate ``<pre>`` block.
    """
    model = analysis_view_model(state)
    rows: list[dict[str, str]] = []
    for label, value, unit in model["hydro_rows"]:
        display_value = f"{value} {unit}".strip() if unit else str(value)
        rows.append({"label": label, "value": display_value})
    for warning in model.get("design_warnings", []):
        rows.append({"label": "Warning", "value": str(warning)})
    return rows


def mesh_diagnostics_rows_from_state(
    state: dict[str, Any],
    part: str = "hull",
) -> list[dict[str, str]]:
    """Return mesh diagnostics as a list of ``{label, value}`` dicts.

    Structured key/value pairs suitable for an HTML table or VDataTable.
    The ``part`` argument selects ``"hull"`` or ``"deck"``.
    """
    hull = hull_from_web_state(state)
    diagnostics = diagnose_mesh(hull, part=part)
    counts = _mesh_diagnostics_counts(diagnostics)
    boundary = counts["boundary_edges"]
    nonmanifold = counts["nonmanifold_edges"]
    rows: list[dict[str, str]] = [
        {"label": "Part", "value": str(part).title()},
        {"label": "Readiness", "value": diagnostics.readiness.level},
        {
            "label": "Boundary edges",
            "value": f"{boundary['primary']} (welded), {boundary['raw']} (raw)",
        },
        {
            "label": "Non-manifold edges",
            "value": f"{nonmanifold['primary']} (welded), {nonmanifold['raw']} (raw)",
        },
        {"label": "Degenerate faces", "value": str(diagnostics.degenerate_faces)},
        {"label": "Vertices", "value": str(diagnostics.profile.vertex_count)},
        {
            "label": "Welded vertices",
            "value": str(diagnostics.profile.welded_vertex_count),
        },
    ]
    for warning in diagnostics.warnings:
        rows.append({"label": "Warning", "value": str(warning)})
    return rows


def evaluation_for_state(state: dict[str, Any]) -> EvaluationResult:
    """Run all evaluators on the state — used by the REST `/api/evaluate` route."""
    hull = hull_from_web_state(state)
    h = evaluate_hydrostatics(hull)

    rc: ResistanceCurve | None
    try:
        rc = resistance_curve(hull)
    except Exception:
        rc = None
    design_validity = evaluate_design_validity(
        hull,
        cp=h.Cp_actual,
        displaced_mass_kg=h.displaced_mass_kg,
        surface=("web",),
    )
    return EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=h,
        resistance=rc,
        design_validity=design_validity,
    )


def evaluation_payload(state: dict[str, Any]) -> dict[str, Any]:
    """JSON-serializable payload for `POST /api/evaluate`."""
    return evaluation_for_state(state).model_dump(mode="json")


def resolve_package_artifact_path(package_dir: Path, artifact_ref: str) -> Path:
    """Resolve an in-package artifact reference and reject anything outside the package."""
    if "://" in artifact_ref:
        raise ValueError("mesh package artifact references must be local relative paths")
    ref_path = Path(artifact_ref)
    if ref_path.is_absolute():
        raise ValueError("mesh package artifact references must be relative")
    package_root = package_dir.resolve()
    resolved = (package_root / ref_path).resolve()
    if not _is_relative_to(resolved, package_root):
        raise ValueError("mesh package artifact reference resolves outside package")
    return resolved


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _first_truthy_alias(state: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        value = state.get(key)
        if value:
            return value
    return None


def _mesh_profile_options() -> list[dict[str, Any]]:
    return [
        {
            "label": "open-wetted-surface",
            "profile_id": MESH_PROFILE_LABEL_TO_ID["open-wetted-surface"],
            "disabled": False,
            "tooltip": "",
        },
        {
            "label": "watertight-solid",
            "profile_id": MESH_PROFILE_LABEL_TO_ID["watertight-solid"],
            "disabled": True,
            "tooltip": WATERTIGHT_SOLID_DISABLED_TOOLTIP,
        },
    ]


def _profile_view(profile_id: str) -> dict[str, str]:
    return {
        "label": MESH_PROFILE_ID_TO_LABEL.get(profile_id, profile_id),
        "profile_id": profile_id,
    }


def _mesh_diagnostics_counts(diagnostics: MeshDiagnostics) -> dict[str, dict[str, Any]]:
    return {
        "boundary_edges": {
            "primary": diagnostics.welded_boundary_edges,
            "primary_basis": "welded",
            "raw": diagnostics.raw_boundary_edges,
        },
        "nonmanifold_edges": {
            "primary": diagnostics.welded_nonmanifold_edges,
            "primary_basis": "welded",
            "raw": diagnostics.raw_nonmanifold_edges,
        },
        "degenerate_faces": {
            "primary": diagnostics.degenerate_faces,
            "primary_basis": "raw",
            "raw": diagnostics.degenerate_faces,
        },
    }


class TargetDraftMismatchReport(BaseModel):
    """Diagnostic report comparing an assumed draft against a load case.

    Returned by :func:`target_draft_load_mismatch`. Given a fixed draft for
    a hull, reports the buoyant displaced mass at that draft, the
    expected mass requested by the load case, and the signed mismatch in
    kilograms and percent of the requested load. Positive ``mismatch_kg``
    means the hull at the assumed draft displaces *more* mass than the
    load case requests (under-loaded relative to draft).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = "1"
    hull_record_hash: str
    assumed_draft_m: float = Field(gt=0)
    expected_displaced_mass_kg: float = Field(ge=0)
    actual_displaced_mass_kg: float = Field(ge=0)
    mismatch_kg: float
    mismatch_percent: float
    notes: list[str] = Field(default_factory=list)


def solve_target_draft(hull: Hull, load_case: LoadCase) -> StabilityResult:
    """Solve upright sinkage for the given load (no longitudinal trim).

    Wraps :func:`evaluate_equilibrium_stability` with a load case stripped
    of explicit longitudinal components so the centered sinkage-only
    solver path is used even if the caller supplied a component list. The
    returned :class:`StabilityResult` carries the solved equilibrium
    draft, residuals, iterations, and the buoyancy/load summary fields
    populated by the underlying solver.
    """
    upright_load = (
        load_case.model_copy(update={"components": []})
        if load_case.uses_longitudinal_components
        else load_case
    )
    return evaluate_equilibrium_stability(hull, upright_load)


def solve_target_trim(hull: Hull, load_case: LoadCase) -> StabilityResult:
    """Solve draft + trim for a load case with explicit longitudinal CG.

    Delegates to the existing fixed-body upright trim solver. When the
    supplied load case has no explicit longitudinal components, a
    placeholder paddler component is synthesized at ``x_m = 0`` so the
    trim solver receives a non-empty components list; the result will
    converge near zero trim in that case.
    """
    if load_case.uses_longitudinal_components:
        trim_load = load_case
    else:
        from kayakgen.eval.contract import LongitudinalLoadComponent

        kg_above_keel = load_case.kg_above_keel_for_draft(hull.draft_m)
        trim_load = load_case.model_copy(
            update={
                "components": [
                    LongitudinalLoadComponent(
                        name="paddler",
                        mass_kg=load_case.paddler_mass_kg,
                        x_m=0.0,
                        kg_above_keel_m=kg_above_keel,
                    ),
                    LongitudinalLoadComponent(
                        name="hull",
                        mass_kg=load_case.hull_mass_kg,
                        x_m=0.0,
                        kg_above_keel_m=kg_above_keel,
                    ),
                    LongitudinalLoadComponent(
                        name="cargo",
                        mass_kg=load_case.cargo_mass_kg,
                        x_m=0.0,
                        kg_above_keel_m=kg_above_keel,
                    ),
                ]
            }
        )
    tolerance_kg = 1.0
    moment_tolerance_kg_m = max(0.1, tolerance_kg * hull.length_m * 0.05)
    return _evaluate_trim_equilibrium(
        hull,
        trim_load,
        tolerance_kg=tolerance_kg,
        moment_tolerance_kg_m=moment_tolerance_kg_m,
        max_iterations=60,
        max_trim_angle_deg=8.0,
    )


def target_draft_load_mismatch(
    hull: Hull,
    draft_m: float,
    load_case: LoadCase,
) -> TargetDraftMismatchReport:
    """Report displacement mismatch for a fixed draft and load case.

    Recomputes the hull's hydrostatics at the assumed ``draft_m`` and
    compares the resulting displaced mass against the load case's total
    requested mass. The signed mismatch is positive when the hull
    displaces more than requested (over-buoyant at the assumed draft).
    """
    if draft_m <= 0:
        raise ValueError("draft_m must be positive")
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")

    hull_at_draft = hull.model_copy(update={"draft_m": draft_m})
    hydro = evaluate_hydrostatics(hull_at_draft)
    actual_mass = float(hydro.displaced_volume_m3 * load_case.seawater_density_kg_m3)
    expected_mass = float(load_case.total_mass_kg)
    mismatch_kg = actual_mass - expected_mass
    mismatch_percent = 100.0 * mismatch_kg / expected_mass

    notes: list[str] = ["target_draft_load_mismatch_report"]
    if abs(mismatch_kg) <= 1.0:
        notes.append("mismatch_within_one_kg")
    if mismatch_kg > 0:
        notes.append("hull_over_buoyant_at_assumed_draft")
    elif mismatch_kg < 0:
        notes.append("hull_under_buoyant_at_assumed_draft")

    return TargetDraftMismatchReport(
        hull_record_hash=hull.hash(),
        assumed_draft_m=float(draft_m),
        expected_displaced_mass_kg=expected_mass,
        actual_displaced_mass_kg=actual_mass,
        mismatch_kg=float(mismatch_kg),
        mismatch_percent=float(mismatch_percent),
        notes=notes,
    )


def _cfd_status_from_state(state: dict[str, Any]) -> str:
    for key in _CFD_STATUS_ALIASES:
        status = state.get(key)
        if status:
            return str(status)

    for key in _CFD_PAYLOAD_ALIASES:
        payload = state.get(key)
        if not isinstance(payload, dict):
            continue
        run = payload.get("run")
        if isinstance(run, dict) and run.get("status"):
            return str(run["status"])
        if payload.get("status"):
            return str(payload["status"])

    for key in _CFD_STATUS_LINE_ALIASES:
        lines = state.get(key)
        if not isinstance(lines, list):
            continue
        for line in lines:
            text = str(line)
            if text.startswith("Status:"):
                return text.split(":", 1)[1].strip() or "unavailable"
    return "unavailable"
