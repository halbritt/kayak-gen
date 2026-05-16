"""Load-case utilities and load-component math shared by stability evaluators."""

from __future__ import annotations

from kayakgen.eval.contract import LoadCase
from kayakgen.eval.hydrostatics import Hydrostatics, evaluate as evaluate_hydrostatics
from kayakgen.model.hull import Hull

COMPAT_KG_ABOVE_KEEL_M = 0.25
GRAVITY_M_S2 = 9.80665


def _gm0_for_load_case(hydro_gm0_m: float | None, kg_above_keel_m: float) -> float | None:
    if hydro_gm0_m is None:
        return None
    return hydro_gm0_m + COMPAT_KG_ABOVE_KEEL_M - kg_above_keel_m


def _mass_for_load_case(hull: Hull, load_case: LoadCase) -> tuple[Hydrostatics, float]:
    hydro = evaluate_hydrostatics(hull)
    return hydro, hydro.displaced_volume_m3 * load_case.seawater_density_kg_m3
