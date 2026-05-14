"""Initial stability and load-case helpers.

This module exposes design-waterline initial stability, the legacy centered
sinkage-equilibrium mode, and a bounded fixed-body upright trim slice for
explicit longitudinal load components. The high-angle GZ boundary now returns
an RFC 0024 result envelope, but real kayak curves remain unavailable unless a
generated closed body passes diagnostics and a later heeled-volume solver lands.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

import numpy as np

from kayakgen.eval.closed_volume import (
    GENERATED_CLOSED_BODY_PART_NAME,
    GENERATED_CLOSED_BODY_TYPE,
    RFC0022_GENERATED_PROFILE_NAME,
    SELF_INTERSECTION_ALGORITHM,
    ClosedVolumeBody,
    ClosedVolumeDiagnostics,
    diagnose_closed_volume_body,
)
from kayakgen.eval.contract import GZCurve, LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull

COMPAT_KG_ABOVE_KEEL_M = 0.25
GRAVITY_M_S2 = 9.80665
DEFAULT_EQUILIBRIUM_TOLERANCE_KG = 1.0
DEFAULT_EQUILIBRIUM_MAX_ITERATIONS = 60
EQUILIBRIUM_DRAFT_TOLERANCE_M = 1e-9
DEFAULT_MAX_TRIM_ANGLE_DEG = 8.0
TRIM_STATIONS = 61
TRIM_DRAFT_TOLERANCE_M = 1e-5
DEFAULT_GZ_HEEL_GRID_DEG: tuple[float, ...] = tuple(float(angle) for angle in range(0, 95, 5))
GZ_UNAVAILABLE_ASSUMPTIONS: tuple[str, ...] = (
    "cg_model_fixed_to_hull_coordinates_unresolved_for_real_gz",
    "trim_policy_at_heel_unresolved_for_real_gz",
    "deck_immersion_and_flooding_not_modeled",
    "secondary_stability_metrics_hidden_until_generated_body_handoff_passes",
)
GZ_FIXTURE_ASSUMPTIONS: tuple[str, ...] = (
    "fixture_only_synthetic_righting_arm_math",
    "cg_fixed_to_hull_coordinates_fixture",
    "fixed_upright_trim_fixture",
    "not_kayak_stability_evidence",
)


class GZNotImplementedError(NotImplementedError):
    """Raised when high-angle stability is requested before its RFC lands."""


def _gm0_for_load_case(hydro_gm0_m: float | None, kg_above_keel_m: float) -> float | None:
    if hydro_gm0_m is None:
        return None
    return hydro_gm0_m + COMPAT_KG_ABOVE_KEEL_M - kg_above_keel_m


def _mass_for_load_case(hull: Hull, load_case: LoadCase) -> tuple[Hydrostatics, float]:
    hydro = evaluate_hydrostatics(hull)
    return hydro, hydro.displaced_volume_m3 * load_case.seawater_density_kg_m3


def _polygon_area(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    ys = points[:, 0]
    zs = points[:, 1]
    return float(0.5 * abs(np.sum(ys * np.roll(zs, -1) - np.roll(ys, -1) * zs)))


def _clipped_section_area(section: np.ndarray, waterline_z: float) -> float:
    """Area of ``section`` below a local waterline in body coordinates."""
    if len(section) < 3:
        return 0.0
    if waterline_z >= float(section[:, 1].max()):
        return _polygon_area(section)
    if waterline_z <= float(section[:, 1].min()):
        return 0.0

    clipped: list[np.ndarray] = []
    for i, current in enumerate(section):
        previous = section[i - 1]
        current_inside = current[1] <= waterline_z
        previous_inside = previous[1] <= waterline_z

        if current_inside != previous_inside:
            dz = current[1] - previous[1]
            if abs(dz) > 1e-12:
                ratio = (waterline_z - previous[1]) / dz
                clipped.append(previous + ratio * (current - previous))
        if current_inside:
            clipped.append(current)

    if not clipped:
        return 0.0
    return _polygon_area(np.array(clipped))


def _trim_hydrostatic_state(
    hull: Hull,
    *,
    draft_at_midship_m: float,
    trim_angle_deg: float,
    density_kg_m3: float,
    stations: int = TRIM_STATIONS,
    section_samples: list[tuple[float, np.ndarray]] | None = None,
) -> tuple[float, float]:
    """Return ``(displaced_mass_kg, signed_lcb_m)`` for fixed-body trim.

    ``trim_angle_deg > 0`` is stern-down/bow-up. Since model ``+x`` points
    sternward, the trimmed waterline rises with positive ``x`` for positive
    trim.
    """
    if section_samples is None:
        geom = hull.to_geometry()
        xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, stations)
        section_samples = [(float(x), geom.section(float(x), "hull")) for x in xs]
    else:
        xs = np.array([sample[0] for sample in section_samples], dtype=float)
    tan_trim = math.tan(math.radians(trim_angle_deg))
    area_by_station = np.zeros_like(xs)
    for i, (x, section) in enumerate(section_samples):
        waterline_z = draft_at_midship_m - hull.draft_m + x * tan_trim
        area_by_station[i] = _clipped_section_area(section, waterline_z)

    volume = float(np.trapezoid(area_by_station, xs))
    if volume <= 0:
        return 0.0, 0.0
    lcb_m = float(np.trapezoid(area_by_station * xs, xs) / volume)
    return volume * density_kg_m3, lcb_m


def _solve_midship_draft_for_trim(
    hull: Hull,
    load_case: LoadCase,
    *,
    trim_angle_deg: float,
    tolerance_kg: float,
    max_iterations: int,
    section_samples: list[tuple[float, np.ndarray]] | None = None,
) -> tuple[float | None, float, float, int, bool]:
    target_mass = load_case.total_mass_kg
    low = max(hull.draft_m * 0.01, 1e-4)
    high = hull.draft_m
    low_mass, low_lcb = _trim_hydrostatic_state(
        hull,
        draft_at_midship_m=low,
        trim_angle_deg=trim_angle_deg,
        density_kg_m3=load_case.seawater_density_kg_m3,
        section_samples=section_samples,
    )
    high_mass, high_lcb = _trim_hydrostatic_state(
        hull,
        draft_at_midship_m=high,
        trim_angle_deg=trim_angle_deg,
        density_kg_m3=load_case.seawater_density_kg_m3,
        section_samples=section_samples,
    )
    if not (low_mass <= target_mass <= high_mass):
        return None, high_mass, high_lcb, 0, False

    best_draft = high
    best_mass = high_mass
    best_lcb = high_lcb
    iterations = 0
    converged = False
    for iterations in range(1, max_iterations + 1):
        draft = (low + high) / 2.0
        mass, lcb = _trim_hydrostatic_state(
            hull,
            draft_at_midship_m=draft,
            trim_angle_deg=trim_angle_deg,
            density_kg_m3=load_case.seawater_density_kg_m3,
            section_samples=section_samples,
        )
        best_draft = draft
        best_mass = mass
        best_lcb = lcb
        error = mass - target_mass
        if abs(error) <= tolerance_kg and (high - low) <= TRIM_DRAFT_TOLERANCE_M:
            converged = True
            break
        if error < 0:
            low = draft
        else:
            high = draft
    return best_draft, best_mass, best_lcb, iterations, converged


def _evaluate_trim_equilibrium(
    hull: Hull,
    load_case: LoadCase,
    *,
    tolerance_kg: float,
    moment_tolerance_kg_m: float,
    max_iterations: int,
    max_trim_angle_deg: float,
) -> StabilityResult:
    target_mass = load_case.total_mass_kg
    load_lcg_m = load_case.load_lcg_m_for_draft(hull.draft_m)
    warnings = [
        "equilibrium_trim_attempted",
        "fixed_body_station_area_trim_model",
        "trim_sign_positive_stern_down",
        "high_angle_gz_not_implemented",
    ]

    _, full_mass = _mass_for_load_case(hull, load_case)
    if target_mass > full_mass:
        warnings.extend(["equilibrium_not_converged", "equilibrium_mass_out_of_bracket"])
        return StabilityResult(
            load_case=load_case,
            method="equilibrium_trim",
            status="not_converged",
            initial_GM0_m=None,
            load_mass_kg=target_mass,
            displaced_mass_kg=full_mass,
            displacement_error_kg=full_mass - target_mass,
            load_lcg_m=load_lcg_m,
            equilibrium_tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=moment_tolerance_kg_m,
            equilibrium_iterations=0,
            equilibrium_max_iterations=max_iterations,
            warnings=warnings,
            gz_curve=None,
        )

    geom = hull.to_geometry()
    xs = np.linspace(-hull.length_m / 2.0, hull.length_m / 2.0, TRIM_STATIONS)
    samples = [(float(x), geom.section(float(x), "hull")) for x in xs]

    def state_for_trim(trim: float) -> tuple[float | None, float, float, int, bool, float]:
        draft, mass, lcb, inner_iterations, mass_converged = _solve_midship_draft_for_trim(
            hull,
            load_case,
            trim_angle_deg=trim,
            tolerance_kg=tolerance_kg,
            max_iterations=max(30, max_iterations),
            section_samples=samples,
        )
        moment_error = mass * lcb - target_mass * load_lcg_m
        return draft, mass, lcb, inner_iterations, mass_converged, moment_error

    sampled: list[tuple[float, tuple[float | None, float, float, int, bool, float]]] = []
    for trim in np.linspace(-max_trim_angle_deg, max_trim_angle_deg, 33):
        state = state_for_trim(float(trim))
        if state[0] is not None:
            sampled.append((float(trim), state))

    bracket: tuple[
        tuple[float, tuple[float | None, float, float, int, bool, float]],
        tuple[float, tuple[float | None, float, float, int, bool, float]],
    ] | None = None
    for left, right in zip(sampled, sampled[1:], strict=False):
        left_error = left[1][5]
        right_error = right[1][5]
        if left_error == 0 or left_error * right_error <= 0:
            bracket = (left, right)
            break

    if bracket is None:
        warnings.extend(["equilibrium_not_converged", "equilibrium_moment_out_of_bracket"])
        if sampled:
            edge_trim, edge = min(sampled, key=lambda item: abs(item[1][5]))
        else:
            edge_trim, edge = 0.0, state_for_trim(0.0)
        return StabilityResult(
            load_case=load_case,
            method="equilibrium_trim",
            status="not_converged",
            initial_GM0_m=None,
            load_mass_kg=target_mass,
            displaced_mass_kg=edge[1],
            displacement_error_kg=edge[1] - target_mass,
            draft_at_midship_m=edge[0],
            equilibrium_draft_m=edge[0],
            sinkage_m=None if edge[0] is None else edge[0] - hull.draft_m,
            trim_angle_deg=edge_trim,
            load_lcg_m=load_lcg_m,
            buoyancy_lcb_m=edge[2],
            moment_error_kg_m=edge[5],
            equilibrium_tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=moment_tolerance_kg_m,
            equilibrium_iterations=0,
            equilibrium_max_iterations=max_iterations,
            warnings=warnings,
            gz_curve=None,
        )

    low_trim, low_state = bracket[0]
    high_trim, high_state = bracket[1]
    best_trim = high_trim
    best_state = high_state
    converged = False
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        trim = (low_trim + high_trim) / 2.0
        state = state_for_trim(trim)
        best_trim = trim
        best_state = state
        draft, mass, lcb, _inner, mass_converged, moment_error = state
        if (
            draft is not None
            and mass_converged
            and abs(mass - target_mass) <= tolerance_kg
            and abs(moment_error) <= moment_tolerance_kg_m
        ):
            converged = True
            break
        if moment_error < 0:
            low_trim = trim
        else:
            high_trim = trim

    draft, mass, lcb, _inner, _mass_converged, moment_error = best_state
    if converged:
        warnings.append("equilibrium_trim_solved")
    else:
        warnings.extend(["equilibrium_not_converged", "max_iterations_exceeded"])

    kg_above_keel_m = load_case.load_kg_above_keel_m_for_draft(draft or hull.draft_m)
    hydro = evaluate_hydrostatics(hull.model_copy(update={"draft_m": draft or hull.draft_m}))
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    return StabilityResult(
        load_case=load_case,
        method="equilibrium_trim",
        status="converged" if converged else "not_converged",
        initial_GM0_m=_gm0_for_load_case(hydro.GM0_m, kg_above_keel_m),
        load_mass_kg=target_mass,
        displaced_mass_kg=mass,
        displacement_error_kg=mass - target_mass,
        draft_at_midship_m=draft,
        equilibrium_draft_m=draft,
        sinkage_m=None if draft is None else draft - hull.draft_m,
        trim_angle_deg=best_trim,
        load_lcg_m=load_lcg_m,
        buoyancy_lcb_m=lcb,
        moment_error_kg_m=moment_error,
        equilibrium_tolerance_kg=tolerance_kg,
        moment_tolerance_kg_m=moment_tolerance_kg_m,
        equilibrium_iterations=iterations,
        equilibrium_max_iterations=max_iterations,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_initial_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
) -> StabilityResult:
    """Evaluate design-waterline initial GM for ``hull`` and ``load_case``."""
    load_case = load_case or LoadCase()
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    hydro = evaluate_hydrostatics(hull)
    kg_above_keel_m = (
        load_case.load_kg_above_keel_m_for_draft(hull.draft_m)
        if load_case.uses_longitudinal_components
        else load_case.kg_above_keel_for_draft(hull.draft_m)
    )
    load_lcg_m = (
        load_case.load_lcg_m_for_draft(hull.draft_m)
        if load_case.uses_longitudinal_components
        else 0.0
    )
    gm0 = _gm0_for_load_case(hydro.GM0_m, kg_above_keel_m)
    displacement_error = hydro.displaced_mass_kg - load_case.total_mass_kg
    warnings = [
        "design_waterline_initial_stability_only",
        "equilibrium_sinkage_trim_not_solved",
        "high_angle_gz_not_implemented",
    ]
    if abs(displacement_error) > 5.0:
        warnings.append("load_displacement_mismatch")
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    if load_case.uses_longitudinal_components:
        warnings.append("longitudinal_components_normalized")
    return StabilityResult(
        load_case=load_case,
        initial_GM0_m=gm0,
        load_mass_kg=load_case.total_mass_kg,
        displaced_mass_kg=hydro.displaced_mass_kg,
        displacement_error_kg=displacement_error,
        load_lcg_m=load_lcg_m,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_equilibrium_stability(
    hull: Hull,
    load_case: LoadCase | None = None,
    *,
    tolerance_kg: float = DEFAULT_EQUILIBRIUM_TOLERANCE_KG,
    moment_tolerance_kg_m: float | None = None,
    max_iterations: int = DEFAULT_EQUILIBRIUM_MAX_ITERATIONS,
    max_trim_angle_deg: float = DEFAULT_MAX_TRIM_ANGLE_DEG,
) -> StabilityResult:
    """Evaluate load-case equilibrium.

    Compact legacy load cases keep the centered sinkage-only path and report
    zero trim with an explicit warning. Load cases with explicit longitudinal
    components use the bounded fixed-body upright trim solver.
    """
    if tolerance_kg <= 0:
        raise ValueError("tolerance_kg must be positive")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    if max_trim_angle_deg <= 0:
        raise ValueError("max_trim_angle_deg must be positive")

    load_case = load_case or LoadCase()
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    effective_moment_tolerance = (
        moment_tolerance_kg_m
        if moment_tolerance_kg_m is not None
        else max(0.1, tolerance_kg * hull.length_m * 0.05)
    )
    if effective_moment_tolerance <= 0:
        raise ValueError("moment_tolerance_kg_m must be positive")
    if load_case.uses_longitudinal_components:
        return _evaluate_trim_equilibrium(
            hull,
            load_case,
            tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=effective_moment_tolerance,
            max_iterations=max_iterations,
            max_trim_angle_deg=max_trim_angle_deg,
        )

    target_mass = load_case.total_mass_kg
    lower_draft = max(min(hull.draft_m, hull.deck_height_m) * 0.01, 1e-4)
    upper_draft = max(hull.draft_m, hull.deck_height_m)

    lower_hydro, lower_mass = _mass_for_load_case(
        hull.model_copy(update={"draft_m": lower_draft}),
        load_case,
    )
    upper_hydro, upper_mass = _mass_for_load_case(
        hull.model_copy(update={"draft_m": upper_draft}),
        load_case,
    )

    hydro = upper_hydro
    displaced_mass = upper_mass
    draft: float | None = upper_draft
    kg_draft = upper_draft
    iterations = 0
    converged = False
    bracketed = lower_mass <= target_mass <= upper_mass
    warnings = [
        "equilibrium_sinkage_attempted",
        "trim_assumed_zero_centered_load",
        "generalized_trim_not_implemented",
        "high_angle_gz_not_implemented",
    ]

    if not bracketed:
        if target_mass < lower_mass:
            hydro = lower_hydro
            displaced_mass = lower_mass
            kg_draft = lower_draft
        draft = None
        warnings.extend(["equilibrium_not_converged", "equilibrium_mass_out_of_bracket"])
    else:
        low = lower_draft
        high = upper_draft
        for iterations in range(1, max_iterations + 1):
            draft = (low + high) / 2.0
            kg_draft = draft
            hydro, displaced_mass = _mass_for_load_case(
                hull.model_copy(update={"draft_m": draft}),
                load_case,
            )
            error = displaced_mass - target_mass
            if abs(error) <= tolerance_kg and (high - low) <= EQUILIBRIUM_DRAFT_TOLERANCE_M:
                converged = True
                break
            if error < 0:
                low = draft
            else:
                high = draft
        if not converged:
            warnings.extend(["equilibrium_not_converged", "max_iterations_exceeded"])
        else:
            warnings.append("equilibrium_sinkage_solved")

    kg_above_keel_m = load_case.kg_above_keel_for_draft(kg_draft)
    if load_case.kg_reference_value_m is not None and load_case.kg_reference != "keel":
        warnings.append("kg_reference_normalized_to_keel")
    displacement_error = displaced_mass - target_mass
    return StabilityResult(
        load_case=load_case,
        method="equilibrium_sinkage",
        status="converged" if converged else "not_converged",
        initial_GM0_m=_gm0_for_load_case(hydro.GM0_m, kg_above_keel_m),
        load_mass_kg=target_mass,
        displaced_mass_kg=displaced_mass,
        displacement_error_kg=displacement_error,
        draft_at_midship_m=draft,
        equilibrium_draft_m=draft,
        sinkage_m=None if draft is None else draft - hull.draft_m,
        trim_angle_deg=0.0 if bracketed else None,
        load_lcg_m=0.0 if bracketed else None,
        buoyancy_lcb_m=0.0 if bracketed else None,
        moment_error_kg_m=0.0 if bracketed else None,
        equilibrium_tolerance_kg=tolerance_kg,
        moment_tolerance_kg_m=effective_moment_tolerance,
        equilibrium_iterations=iterations,
        equilibrium_max_iterations=max_iterations,
        warnings=warnings,
        gz_curve=None,
    )


def evaluate_gz_curve(
    hull: Hull,
    load_case: LoadCase | None = None,
    heel_grid_deg: Sequence[float] | None = None,
    body_ref: object | None = None,
    body_diagnostics: object | None = None,
    *,
    fixture_only: bool = False,
) -> GZCurve:
    """Return an RFC 0024 GZ result envelope.

    Real kayak GZ values are still unavailable in this slice. Generated closed
    bodies are validated so callers get specific unavailable diagnostics, while
    synthetic explicit bodies can exercise deterministic math only when
    ``fixture_only`` is explicitly set.
    """

    load_case = load_case or LoadCase()
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    heel_grid = _normalize_heel_grid(heel_grid_deg)

    if body_ref is None:
        return _unavailable_gz_curve(
            heel_grid,
            warnings=["generated_closed_body_not_available", "body_ref_missing"],
        )

    if isinstance(body_ref, str):
        return _unavailable_gz_curve(
            heel_grid,
            body_ref=body_ref,
            body_type="unresolved",
            warnings=[
                "generated_closed_body_not_available",
                "body_ref_unresolved",
                "body_ref_must_be_generated_closed_volume_body",
            ],
        )

    try:
        body = ClosedVolumeBody.model_validate(body_ref)
    except Exception:
        return _unavailable_gz_curve(
            heel_grid,
            body_ref=str(body_ref),
            body_type="unsupported",
            warnings=[
                "generated_closed_body_not_available",
                "body_ref_not_closed_volume_body",
            ],
        )

    diagnostics, diagnostic_warnings = _diagnostics_for_body(body, body_diagnostics)
    diagnostic_ref = _body_diagnostic_ref(diagnostics) if diagnostics else None

    if body.body_type == "explicit_synthetic_triangle_mesh":
        if not fixture_only:
            return _unavailable_gz_curve(
                heel_grid,
                body_ref=body.body_id,
                body_type=body.body_type,
                body_diagnostic_ref=diagnostic_ref,
                warnings=[
                    "generated_closed_body_not_available",
                    "synthetic_body_not_allowed_for_real_gz",
                    *diagnostic_warnings,
                ],
            )
        fixture_warnings = _closed_body_fixture_warnings(body, diagnostics)
        if diagnostic_warnings or fixture_warnings:
            return _unavailable_gz_curve(
                heel_grid,
                body_ref=body.body_id,
                body_type=body.body_type,
                body_diagnostic_ref=diagnostic_ref,
                fixture_only=True,
                warnings=[
                    "fixture_only",
                    "fixture_closed_body_diagnostic_failed",
                    *diagnostic_warnings,
                    *fixture_warnings,
                ],
            )
        assert diagnostics is not None
        return _fixture_gz_curve(
            heel_grid,
            body=body,
            diagnostics=diagnostics,
            load_case=load_case,
        )

    generated_warnings = _generated_body_gz_gate_warnings(hull, body, diagnostics)
    if diagnostic_warnings or generated_warnings:
        return _unavailable_gz_curve(
            heel_grid,
            body_ref=body.body_id,
            body_type=body.body_type,
            body_diagnostic_ref=diagnostic_ref,
            warnings=[
                "generated_closed_body_not_available",
                *diagnostic_warnings,
                *generated_warnings,
            ],
        )

    return _unavailable_gz_curve(
        heel_grid,
        body_ref=body.body_id,
        body_type=body.body_type,
        body_diagnostic_ref=diagnostic_ref,
        assumptions=["generated_closed_body_diagnostic_gate_passed"],
        warnings=[
            "high_angle_gz_generated_body_solver_not_implemented",
            "secondary_stability_metrics_hidden_until_generated_body_solver_lands",
        ],
    )


def _normalize_heel_grid(heel_grid_deg: Sequence[float] | None) -> list[float]:
    grid = (
        list(DEFAULT_GZ_HEEL_GRID_DEG)
        if heel_grid_deg is None
        else [float(value) for value in heel_grid_deg]
    )
    if not grid:
        raise ValueError("heel_grid_deg must contain at least one angle")
    for value in grid:
        if not math.isfinite(value):
            raise ValueError("heel_grid_deg must contain only finite values")
    for left, right in zip(grid, grid[1:], strict=False):
        if right <= left:
            raise ValueError("heel_grid_deg must be strictly increasing")
    return grid


def _diagnostics_for_body(
    body: ClosedVolumeBody,
    body_diagnostics: object | None,
) -> tuple[ClosedVolumeDiagnostics | None, list[str]]:
    if body_diagnostics is None:
        try:
            return diagnose_closed_volume_body(body), []
        except Exception as exc:
            return None, [f"closed_volume_diagnostic_unavailable: {exc}"]
    try:
        diagnostics = ClosedVolumeDiagnostics.model_validate(body_diagnostics)
    except Exception as exc:
        return None, [f"closed_volume_diagnostic_invalid: {exc}"]
    return diagnostics, []


def _unavailable_gz_curve(
    heel_grid_deg: list[float],
    *,
    body_ref: str | None = None,
    body_type: str | None = None,
    body_diagnostic_ref: str | None = None,
    fixture_only: bool = False,
    assumptions: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> GZCurve:
    return GZCurve(
        status="unavailable",
        method="fixture_only_math" if fixture_only else "generated_body_handoff",
        fixture_only=fixture_only,
        body_ref=body_ref,
        body_type=body_type,
        body_diagnostic_ref=body_diagnostic_ref,
        heel_grid_deg=list(heel_grid_deg),
        assumptions=_dedupe([*GZ_UNAVAILABLE_ASSUMPTIONS, *assumptions]),
        warnings=_dedupe(warnings),
    )


def _body_diagnostic_ref(diagnostics: ClosedVolumeDiagnostics) -> str:
    return f"closed_volume_diagnostics:{diagnostics.body_id}:{diagnostics.profile_name}"


def _closed_body_fixture_warnings(
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics | None,
) -> list[str]:
    if diagnostics is None:
        return ["closed_volume_diagnostic_missing"]
    warnings = _closed_volume_readiness_warnings(diagnostics)
    if diagnostics.body_id != body.body_id:
        warnings.append("body_diagnostic_ref_mismatch")
    if diagnostics.body_type != body.body_type:
        warnings.append("body_diagnostic_type_mismatch")
    return warnings


def _generated_body_gz_gate_warnings(
    hull: Hull,
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics | None,
) -> list[str]:
    warnings: list[str] = []
    if body.body_type != GENERATED_CLOSED_BODY_TYPE:
        warnings.append("body_type_not_generated_hull_plus_deck_closed_body")
    if body.policy.profile_name != RFC0022_GENERATED_PROFILE_NAME:
        warnings.append("generated_body_profile_mismatch")
    if body.policy.body_type != GENERATED_CLOSED_BODY_TYPE:
        warnings.append("generated_body_policy_type_mismatch")
    if body.policy.cap_policy != "explicit_bow_stern_endpoint_ring_caps":
        warnings.append("generated_body_cap_policy_mismatch")
    if body.policy.deck_join_policy != "exact_shared_vertices_topside_sheerline_strip":
        warnings.append("generated_body_deck_join_policy_mismatch")
    if body.policy.self_intersection_policy != "required_rfc0021_conservative":
        warnings.append("generated_body_self_intersection_policy_mismatch")
    if body.policy.normal_orientation != "outward_positive_signed_volume":
        warnings.append("generated_body_normal_orientation_mismatch")
    if body.policy.waterline_semantics != "metadata_only":
        warnings.append("generated_body_waterline_semantics_mismatch")
    if len(body.parts) != 1 or body.parts[0].name != GENERATED_CLOSED_BODY_PART_NAME:
        warnings.append("generated_body_part_identity_mismatch")
    if body.source_hull_hash != hull.hash():
        warnings.append("source_hull_hash_mismatch")

    if diagnostics is None:
        warnings.append("closed_volume_diagnostic_missing")
        return warnings

    warnings.extend(_closed_volume_readiness_warnings(diagnostics))
    if diagnostics.body_id != body.body_id:
        warnings.append("body_diagnostic_ref_mismatch")
    if diagnostics.body_type != body.body_type:
        warnings.append("body_diagnostic_type_mismatch")
    if diagnostics.profile_name != body.policy.profile_name:
        warnings.append("body_diagnostic_profile_mismatch")
    if diagnostics.source_hull_hash != body.source_hull_hash:
        warnings.append("body_diagnostic_source_hull_hash_mismatch")
    if diagnostics.units != body.units:
        warnings.append("body_diagnostic_units_mismatch")
    if diagnostics.coordinate_system != body.coordinate_system:
        warnings.append("body_diagnostic_coordinate_system_mismatch")
    if diagnostics.waterline_z_m != body.waterline_z_m:
        warnings.append("body_diagnostic_waterline_mismatch")
    if diagnostics.waterline_metadata != body.waterline_metadata:
        warnings.append("body_diagnostic_waterline_metadata_mismatch")
    if diagnostics.policy != body.policy:
        warnings.append("body_diagnostic_policy_mismatch")
    if diagnostics.self_intersection_algorithm != SELF_INTERSECTION_ALGORITHM:
        warnings.append("self_intersection_algorithm_mismatch")
    if diagnostics.self_intersection_pair_count != 0:
        warnings.append("self_intersection_pairs_present")
    if diagnostics.part_diagnostics and len(diagnostics.part_diagnostics) == len(body.parts):
        for part, report in zip(body.parts, diagnostics.part_diagnostics, strict=True):
            if report.name != part.name:
                warnings.append("part_diagnostic_name_mismatch")
            if report.vertex_count != len(part.vertices):
                warnings.append("part_diagnostic_vertex_count_mismatch")
            if report.face_count != len(part.faces):
                warnings.append("part_diagnostic_face_count_mismatch")
    else:
        warnings.append("part_diagnostic_count_mismatch")
    return warnings


def _closed_volume_readiness_warnings(
    diagnostics: ClosedVolumeDiagnostics,
) -> list[str]:
    warnings: list[str] = []
    if diagnostics.readiness.level != "closed_volume":
        warnings.append("closed_volume_readiness_not_closed")
    if diagnostics.readiness.reasons:
        warnings.append("closed_volume_readiness_reasons_present")
    for field_name in (
        "raw_boundary_edges",
        "welded_boundary_edges",
        "raw_nonmanifold_edges",
        "welded_nonmanifold_edges",
        "degenerate_faces",
        "nonfinite_vertices",
        "nonfinite_faces",
        "invalid_face_indices",
    ):
        if getattr(diagnostics, field_name) != 0:
            warnings.append(f"{field_name}_nonzero")
    if (
        diagnostics.signed_volume_m3
        <= diagnostics.policy.tolerances.signed_volume_tolerance_m3
    ):
        warnings.append("signed_volume_not_positive_above_tolerance")
    if diagnostics.self_intersection_status != "passed":
        warnings.append(f"self_intersection_status_{diagnostics.self_intersection_status}")
    if diagnostics.cfd_ready is not False:
        warnings.append("closed_volume_diagnostic_must_not_claim_cfd_ready")
    return warnings


def _fixture_gz_curve(
    heel_grid_deg: list[float],
    *,
    body: ClosedVolumeBody,
    diagnostics: ClosedVolumeDiagnostics,
    load_case: LoadCase,
) -> GZCurve:
    heel_deg = list(heel_grid_deg)
    gz_m = [0.08 * math.sin(math.radians(2.0 * heel)) for heel in heel_deg]
    righting_moment_nm = [
        load_case.total_mass_kg * GRAVITY_M_S2 * gz for gz in gz_m
    ]
    summaries = _gz_summary_metrics(heel_deg, gz_m)
    return GZCurve(
        status="computed",
        method="fixture_only_math",
        fixture_only=True,
        body_ref=body.body_id,
        body_type=body.body_type,
        body_diagnostic_ref=_body_diagnostic_ref(diagnostics),
        heel_grid_deg=list(heel_grid_deg),
        heel_deg=heel_deg,
        gz_m=gz_m,
        righting_moment_nm=righting_moment_nm,
        assumptions=list(GZ_FIXTURE_ASSUMPTIONS),
        warnings=[
            "fixture_only",
            "synthetic_closed_body_not_generated_kayak",
            "not_user_facing_secondary_stability",
        ],
        **summaries,
    )


def _gz_summary_metrics(heel_deg: list[float], gz_m: list[float]) -> dict[str, float | None]:
    if not gz_m:
        return {
            "max_gz_m": None,
            "heel_at_max_gz_deg": None,
            "range_positive_stability_deg": None,
            "area_under_positive_gz_m_deg": None,
        }
    max_index = max(range(len(gz_m)), key=lambda index: gz_m[index])
    positive_indices = [index for index, value in enumerate(gz_m) if value > 1e-12]
    positive_gz = [max(value, 0.0) for value in gz_m]
    return {
        "max_gz_m": gz_m[max_index],
        "heel_at_max_gz_deg": heel_deg[max_index],
        "range_positive_stability_deg": (
            heel_deg[positive_indices[-1]] if positive_indices else None
        ),
        "area_under_positive_gz_m_deg": float(np.trapezoid(positive_gz, heel_deg)),
    }


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
