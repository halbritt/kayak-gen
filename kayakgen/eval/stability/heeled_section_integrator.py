"""Heeled-volume integration helpers for the fixed-trim generated-body solver.

Given the station rings of a generated closed body, these helpers rotate each
section by the requested heel angle, clip it against a local waterline, and
integrate to recover ``(displaced_mass, transverse_CB, longitudinal_CB)`` so
the evaluator can solve per-heel sinkage and compute GZ.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

from kayakgen.eval.closed_volume import ClosedVolumeBody
from kayakgen.eval.contract import GZHeelPointMetadata, LoadCase
from kayakgen.eval.stability.load_case import GRAVITY_M_S2
from kayakgen.eval.stability.trim_equilibrium import _clipped_section_properties
from kayakgen.model.hull import Hull

GZ_SINKAGE_TOLERANCE_KG = 1.0
GZ_SINKAGE_MAX_ITERATIONS = 60
GZ_SINKAGE_WATERLINE_TOLERANCE_M = 1e-8


def _generated_body_station_sections(
    body: ClosedVolumeBody,
) -> list[tuple[float, np.ndarray]]:
    if len(body.parts) != 1:
        raise ValueError("generated GZ v1 requires a single closed body part")
    vertices = np.asarray(body.parts[0].vertices, dtype=float)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or len(vertices) == 0:
        raise ValueError("generated GZ v1 body vertices must be Nx3")

    x_values = sorted(float(value) for value in np.unique(vertices[:, 0]))
    grouped = [
        (x, vertices[np.isclose(vertices[:, 0], x, atol=1e-10), 1:3])
        for x in x_values
    ]
    ring_counts = [len(section) for _x, section in grouped if len(section) >= 4]
    if not ring_counts:
        raise ValueError("generated GZ v1 body has no station rings")
    ring_count = min(ring_counts)

    sections: list[tuple[float, np.ndarray]] = []
    for x, section in grouped:
        if len(section) >= 4:
            # Plumb-stem endpoint cap centers share the station x-coordinate.
            # The ring vertices are emitted first; cap centers are interior
            # helper vertices and are not part of the 2-D waterline clip.
            section = section[:ring_count]
        sections.append((x, np.asarray(section, dtype=float)))
    return sections


def _heel_section(section: np.ndarray, heel_deg: float) -> np.ndarray:
    if len(section) == 0:
        return section.copy()
    radians = math.radians(heel_deg)
    cos_heel = math.cos(radians)
    sin_heel = math.sin(radians)
    y = section[:, 0] * cos_heel - section[:, 1] * sin_heel
    z = section[:, 0] * sin_heel + section[:, 1] * cos_heel
    return np.column_stack((y, z))


def _heeled_displacement_state(
    sections: list[tuple[float, np.ndarray]],
    *,
    heel_deg: float,
    sinkage_m: float,
    density_kg_m3: float,
) -> tuple[float, float, float, bool]:
    xs = np.array([sample[0] for sample in sections], dtype=float)
    area_by_station = np.zeros_like(xs)
    y_moment_by_station = np.zeros_like(xs)
    for i, (_x, section) in enumerate(sections):
        heeled = _heel_section(section, heel_deg)
        area, centroid_y, _centroid_z = _clipped_section_properties(
            heeled,
            sinkage_m,
        )
        area_by_station[i] = area
        y_moment_by_station[i] = area * centroid_y

    volume = float(np.trapezoid(area_by_station, xs))
    if volume <= 0.0:
        return 0.0, 0.0, 0.0, True
    displaced_mass_kg = volume * density_kg_m3
    cb_y_m = float(np.trapezoid(y_moment_by_station, xs) / volume)
    lcb_m = float(np.trapezoid(area_by_station * xs, xs) / volume)
    return displaced_mass_kg, cb_y_m, lcb_m, True


def _heeled_z_bounds(
    sections: list[tuple[float, np.ndarray]],
    heel_deg: float,
) -> tuple[float, float]:
    z_values: list[float] = []
    for _x, section in sections:
        if len(section) == 0:
            continue
        heeled = _heel_section(section, heel_deg)
        z_values.extend(float(value) for value in heeled[:, 1])
    if not z_values:
        raise ValueError("generated GZ v1 body has no heeled section vertices")
    return min(z_values), max(z_values)


def _load_cg_for_gz(hull: Hull, load_case: LoadCase) -> tuple[float, float]:
    if load_case.uses_longitudinal_components:
        return (
            load_case.load_lcg_m_for_draft(hull.draft_m),
            load_case.load_kg_above_keel_m_for_draft(hull.draft_m),
        )
    return 0.0, load_case.kg_above_keel_for_draft(hull.draft_m)


def _solve_generated_body_heel_point(
    sections: list[tuple[float, np.ndarray]],
    *,
    hull: Hull,
    load_case: LoadCase,
    heel_deg: float,
    tolerance_kg: float = GZ_SINKAGE_TOLERANCE_KG,
    max_iterations: int = GZ_SINKAGE_MAX_ITERATIONS,
) -> tuple[float | None, float | None, GZHeelPointMetadata]:
    target_mass_kg = load_case.total_mass_kg
    load_lcg_m, kg_above_keel_m = _load_cg_for_gz(hull, load_case)
    cg_z_m = -hull.draft_m + kg_above_keel_m
    cg_y_m = -cg_z_m * math.sin(math.radians(heel_deg))

    low_z, high_z = _heeled_z_bounds(sections, heel_deg)
    low = low_z - GZ_SINKAGE_WATERLINE_TOLERANCE_M
    high = high_z + GZ_SINKAGE_WATERLINE_TOLERANCE_M
    high_mass, _high_cb_y, _high_lcb, clipping_ok = _heeled_displacement_state(
        sections,
        heel_deg=heel_deg,
        sinkage_m=high,
        density_kg_m3=load_case.seawater_density_kg_m3,
    )
    if not clipping_ok:
        return None, None, GZHeelPointMetadata(
            heel_deg=heel_deg,
            status="skipped",
            displacement_iterations=0,
            displacement_max_iterations=max_iterations,
            clipping_status="failed",
            warnings=["waterline_clipping_failed"],
        )
    if target_mass_kg > high_mass:
        return None, None, GZHeelPointMetadata(
            heel_deg=heel_deg,
            status="skipped",
            displaced_mass_kg=high_mass,
            displacement_residual_kg=high_mass - target_mass_kg,
            displacement_iterations=0,
            displacement_max_iterations=max_iterations,
            clipping_status="computed",
            warnings=[
                "heel_point_non_converged",
                "displacement_mass_out_of_bracket",
            ],
        )

    best_sinkage = high
    best_mass = high_mass
    best_cb_y = 0.0
    best_lcb = 0.0
    converged = False
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        sinkage = (low + high) / 2.0
        mass, cb_y, lcb, clipping_ok = _heeled_displacement_state(
            sections,
            heel_deg=heel_deg,
            sinkage_m=sinkage,
            density_kg_m3=load_case.seawater_density_kg_m3,
        )
        if not clipping_ok:
            return None, None, GZHeelPointMetadata(
                heel_deg=heel_deg,
                status="skipped",
                displacement_iterations=iterations,
                displacement_max_iterations=max_iterations,
                clipping_status="failed",
                warnings=["waterline_clipping_failed"],
            )
        best_sinkage = sinkage
        best_mass = mass
        best_cb_y = cb_y
        best_lcb = lcb
        error = mass - target_mass_kg
        if abs(error) <= tolerance_kg:
            converged = True
            break
        if error < 0.0:
            low = sinkage
        else:
            high = sinkage

    residual_kg = best_mass - target_mass_kg
    moment_residual_kg_m = best_mass * best_lcb - target_mass_kg * load_lcg_m
    warnings = ["fixed_trim_longitudinal_moment_not_solved"]
    status: Literal["computed", "non_converged"] = "computed"
    if not converged:
        status = "non_converged"
        warnings.extend(["heel_point_non_converged", "max_iterations_exceeded"])
    metadata = GZHeelPointMetadata(
        heel_deg=heel_deg,
        status=status,
        sinkage_m=best_sinkage,
        displaced_mass_kg=best_mass,
        displacement_residual_kg=residual_kg,
        displacement_iterations=iterations,
        displacement_max_iterations=max_iterations,
        trim_angle_deg=0.0,
        longitudinal_moment_residual_kg_m=moment_residual_kg_m,
        clipping_status="computed",
        warnings=warnings,
    )
    if not converged:
        return None, None, metadata
    gz_m = cg_y_m - best_cb_y
    return gz_m, target_mass_kg * GRAVITY_M_S2 * gz_m, metadata
