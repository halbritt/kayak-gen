"""Load equilibrium on a fixed canonical hull body and operating pose."""

from __future__ import annotations

from dataclasses import dataclass
import math

from kayakgen.eval.contract import LoadCase, StabilityResult
from kayakgen.eval.hydrostatics import Hydrostatics
from kayakgen.eval.immersed_geometry import ImmersedGeometry, evaluate_immersed, immersed_geometry
from kayakgen.model.hull import Hull
from kayakgen.model.operating_state import OperatingPose


@dataclass(frozen=True)
class OperatingEquilibriumOptions:
    tolerance_kg: float = 1.0
    moment_tolerance_kg_m: float | None = None
    max_iterations: int = 60
    max_trim_angle_deg: float = 8.0
    stations: int | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.tolerance_kg) or self.tolerance_kg <= 0:
            raise ValueError("equilibrium tolerance must be finite and positive")
        if self.moment_tolerance_kg_m is not None and (
            not math.isfinite(self.moment_tolerance_kg_m) or self.moment_tolerance_kg_m <= 0
        ):
            raise ValueError("moment tolerance must be finite and positive")
        if self.max_iterations < 1 or not 0 < self.max_trim_angle_deg < 90:
            raise ValueError("equilibrium iterations/trim bounds are invalid")
        if self.stations is not None and (not isinstance(self.stations, int) or self.stations < 3):
            raise ValueError("equilibrium stations must be an integer of at least three")


@dataclass(frozen=True)
class _Problem:
    hull: Hull
    load: LoadCase
    options: OperatingEquilibriumOptions
    body: ImmersedGeometry

    @property
    def moment_tolerance(self) -> float:
        explicit = self.options.moment_tolerance_kg_m
        return explicit if explicit is not None else max(.1, self.options.tolerance_kg * self.hull.length_m * .05)


@dataclass(frozen=True)
class _SinkageState:
    sinkage_m: float
    hydro: Hydrostatics
    converged: bool
    iterations: int


@dataclass(frozen=True)
class _Solution:
    state: _SinkageState
    trim_deg: float
    converged: bool
    iterations: int
    moment_bracketed: bool = True


def _solve_sinkage(problem: _Problem, trim: float) -> _SinkageState:
    vertices = problem.body.body_vertices
    relative_z = vertices[:, 2] - vertices[:, 0] * math.tan(math.radians(trim))
    low, high = float(relative_z.min()) - 1e-9, float(relative_z.max()) + 1e-9
    target = problem.load.total_mass_kg
    def hydro_at(sinkage: float) -> Hydrostatics:
        return evaluate_immersed(problem.hull, OperatingPose(sinkage, trim),
                                 stations=problem.options.stations,
                                 density_kg_m3=problem.load.seawater_density_kg_m3)

    hydro = hydro_at(high)
    if not 0 < target < hydro.displaced_mass_kg:
        return _SinkageState(high, hydro, False, 0)
    for iteration in range(1, problem.options.max_iterations + 1):
        sinkage = (low + high) / 2.0
        hydro = hydro_at(sinkage)
        if abs(hydro.displaced_mass_kg - target) <= problem.options.tolerance_kg and high - low < 1e-8:
            return _SinkageState(sinkage, hydro, hydro.waterplane_area_m2 > 0, iteration)
        if hydro.displaced_mass_kg < target:
            low = sinkage
        else:
            high = sinkage
    return _SinkageState(sinkage, hydro, False, iteration)


def _load_geometry(problem: _Problem, trim: float, state: _SinkageState) -> tuple[float, float, float]:
    reference = problem.body.reference_draft_m()
    draft = max(reference + state.sinkage_m, 1e-12)
    kg = problem.load.load_kg_above_keel_m_for_draft(draft)
    lcg = problem.load.load_lcg_m_for_draft(draft)
    angle = math.radians(trim)
    world_x = lcg * math.cos(angle) + (kg - reference - state.sinkage_m) * math.sin(angle)
    return kg, lcg, world_x


def _moment(problem: _Problem, trim: float, state: _SinkageState) -> float:
    _kg, _lcg, world_load_x = _load_geometry(problem, trim, state)
    cb_x = (state.hydro.LCB_frac - .5) * problem.hull.length_m
    return state.hydro.displaced_mass_kg * cb_x - problem.load.total_mass_kg * world_load_x


def _solve_trim(problem: _Problem, initial: _SinkageState) -> _Solution:
    low, high = -problem.options.max_trim_angle_deg, problem.options.max_trim_angle_deg
    low_state, high_state = _solve_sinkage(problem, low), _solve_sinkage(problem, high)
    low_moment, high_moment = _moment(problem, low, low_state), _moment(problem, high, high_state)
    if low_moment * high_moment > 0:
        return _Solution(initial, 0., False, 0, moment_bracketed=False)
    for iteration in range(1, problem.options.max_iterations + 1):
        trim = (low + high) / 2.0
        state = _solve_sinkage(problem, trim)
        residual = _moment(problem, trim, state)
        if state.converged and abs(residual) <= problem.moment_tolerance:
            return _Solution(state, trim, True, iteration)
        if low_moment * residual <= 0:
            high = trim
        else:
            low, low_moment = trim, residual
    return _Solution(state, trim, False, iteration)


def _result(problem: _Problem, solution: _Solution, solve_trim: bool) -> StabilityResult:
    state, trim = solution.state, solution.trim_deg
    warnings = ["fixed_body_operating_pose_v1", "operating_world_frame_centroids", "high_angle_gz_not_implemented"]
    if not solve_trim:
        warnings.append("trim_assumed_zero_no_moment_balance" if problem.load.uses_longitudinal_components
                        else "trim_assumed_zero_centered_load")
    if solution.converged:
        warnings.append("equilibrium_trim_solved" if solve_trim else "equilibrium_sinkage_solved")
    else:
        warnings.append("equilibrium_not_converged")
        if not solution.moment_bracketed:
            warnings.append("equilibrium_moment_out_of_bracket")
        if not state.converged:
            warnings.append("equilibrium_mass_out_of_bracket" if state.iterations == 0 else "max_iterations_exceeded")
        elif solve_trim and solution.moment_bracketed:
            warnings.append("max_iterations_exceeded")
    draft = problem.body.reference_draft_m() + state.sinkage_m
    pose_available = state.iterations > 0
    kg, lcg, world_lcg = _load_geometry(problem, trim, state)
    angle = math.radians(trim)
    gm = None if state.hydro.GM0_m is None else state.hydro.GM0_m + (.25 - kg) * math.cos(angle) + lcg * math.sin(angle)
    return StabilityResult(
        load_case=problem.load, method="equilibrium_trim" if solve_trim else "equilibrium_sinkage",
        status="converged" if solution.converged else "not_converged", initial_GM0_m=gm,
        load_mass_kg=problem.load.total_mass_kg, displaced_mass_kg=state.hydro.displaced_mass_kg,
        displacement_error_kg=state.hydro.displaced_mass_kg - problem.load.total_mass_kg,
        draft_at_midship_m=draft if pose_available and draft > 0 else None,
        equilibrium_draft_m=draft if pose_available and draft > 0 else None,
        sinkage_m=state.sinkage_m if pose_available else None, trim_angle_deg=trim if pose_available else None,
        load_lcg_m=world_lcg, buoyancy_lcb_m=(state.hydro.LCB_frac - .5) * problem.hull.length_m,
        moment_error_kg_m=_moment(problem, trim, state) if solve_trim else None,
        equilibrium_tolerance_kg=problem.options.tolerance_kg, moment_tolerance_kg_m=problem.moment_tolerance,
        equilibrium_iterations=solution.iterations, equilibrium_max_iterations=problem.options.max_iterations,
        warnings=warnings,
    )


def evaluate_fixed_body_equilibrium(
    hull: Hull,
    load_case: LoadCase,
    *,
    solve_trim: bool = False,
    options: OperatingEquilibriumOptions | None = None,
) -> StabilityResult:
    """Solve sinkage and optional trim without editing the physical hull."""
    if load_case.total_mass_kg <= 0:
        raise ValueError("load case total mass must be positive")
    options = options or OperatingEquilibriumOptions()
    problem = _Problem(hull, load_case, options,
                       immersed_geometry(hull, OperatingPose(), stations=options.stations))
    initial = _solve_sinkage(problem, 0.)
    solution = _solve_trim(problem, initial) if solve_trim and initial.converged else _Solution(initial, 0., initial.converged, initial.iterations)
    return _result(problem, solution, solve_trim)
