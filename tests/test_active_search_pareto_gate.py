"""RFC 0044 claim-admissibility gate (sibling of ensure_objectives_not_high_angle_gz)."""

from __future__ import annotations

import pytest

from kayakgen.search import objectives as objectives_module
from kayakgen.search.objectives import ObjectiveMetadata
from kayakgen.search.pareto import (
    HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
    HighAngleGzObjectiveRefusedError,
    Objective,
    SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN,
    SearchObjectiveRefusedError,
    ensure_objectives_claim_admissible_for_search,
)


@pytest.fixture
def patched_metadata(monkeypatch) -> dict[str, ObjectiveMetadata]:
    """Inject synthetic objective entries covering each gated role."""

    patched = dict(objectives_module.OBJECTIVE_METADATA)
    patched["raw_drag_demo"] = ObjectiveMetadata(
        metric="raw_drag_demo",
        label="Raw drag demo",
        unit="N",
        direction="min",
        source_evaluator="resistance",
        availability_rule="present when raw resistance runs",
        role="explicit_exploratory",
    )
    patched["uncalibrated_demo"] = ObjectiveMetadata(
        metric="uncalibrated_demo",
        label="Uncalibrated demo",
        unit="N",
        direction="min",
        source_evaluator="reserved_claim_gate",
        availability_rule="reserved gate",
        role="claim_gated_reserved",
    )
    monkeypatch.setattr(objectives_module, "OBJECTIVE_METADATA", patched)
    return patched


def test_search_objective_claim_admissibility_refuses_raw_unvalidated(
    patched_metadata,
) -> None:
    with pytest.raises(SearchObjectiveRefusedError) as exc:
        ensure_objectives_claim_admissible_for_search(
            [Objective(metric="raw_drag_demo", direction="min")],
            explicit_exploratory=False,
        )
    assert exc.value.metric == "raw_drag_demo"
    assert exc.value.claim_state == "raw_unvalidated"
    assert exc.value.reason["code"] == "search_objective_claim_not_admissible"
    assert exc.value.reason["token"] == SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY_TOKEN


def test_search_objective_claim_admissibility_refuses_uncalibrated_comparative(
    patched_metadata,
) -> None:
    with pytest.raises(SearchObjectiveRefusedError) as exc:
        ensure_objectives_claim_admissible_for_search(
            [Objective(metric="uncalibrated_demo", direction="min")],
            explicit_exploratory=False,
        )
    assert exc.value.claim_state == "uncalibrated_comparative"


def test_search_objective_claim_admissibility_allows_when_exploratory(
    patched_metadata,
) -> None:
    ensure_objectives_claim_admissible_for_search(
        [
            Objective(metric="raw_drag_demo", direction="min"),
            Objective(metric="uncalibrated_demo", direction="min"),
        ],
        explicit_exploratory=True,
    )


def test_search_high_angle_gz_objective_still_refused_in_exploratory_mode() -> None:
    with pytest.raises(HighAngleGzObjectiveRefusedError) as exc:
        ensure_objectives_claim_admissible_for_search(
            [Objective(metric="max_gz_m", direction="max")],
            explicit_exploratory=True,
        )
    assert exc.value.reason["token"] == HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN


def test_search_admissibility_passes_for_conservative_defaults() -> None:
    # GM0_m / displacement_error_kg / mesh_problem_count are default_conservative.
    ensure_objectives_claim_admissible_for_search(
        [
            Objective(metric="GM0_m", direction="max"),
            Objective(metric="displacement_error_kg", direction="min"),
            Objective(metric="mesh_problem_count", direction="min"),
        ],
        explicit_exploratory=False,
    )
