"""Centralised metric-registry helpers (objectives admissibility)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from kayakgen.search.objectives import (
    OBJECTIVE_REJECTION_CLAIM_GATED,
    OBJECTIVE_REJECTION_DISPLAY_ONLY,
    OBJECTIVE_REJECTION_UNKNOWN_METRIC,
    OBJECTIVE_METADATA,
    ObjectiveMetadata,
    is_objective_metric_admissible,
    register_objective_metadata,
)
from kayakgen.search.pareto import (
    HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN,
    HighAngleGzObjectiveRefusedError,
    Objective,
    UnknownSearchObjectiveError,
    ensure_objectives_claim_admissible_for_search,
)
from kayakgen.search.sweep import SweepSpec, run_sweep
from kayakgen.ui.web.read_models import _format_metric


@pytest.fixture
def restore_registry():
    """Snapshot/restore the module-level OBJECTIVE_METADATA after each test."""

    original = dict(OBJECTIVE_METADATA)
    yield OBJECTIVE_METADATA
    OBJECTIVE_METADATA.clear()
    OBJECTIVE_METADATA.update(original)


def test_objective_metadata_has_new_admissibility_fields() -> None:
    metadata = OBJECTIVE_METADATA["GM0_m"]
    assert metadata.display_format == "{value:.3f}"
    assert "hydrostatics_evaluated" in metadata.availability_conditions
    assert metadata.default_objective_eligible is True

    mesh = OBJECTIVE_METADATA["mesh_problem_count"]
    assert mesh.display_format == "{value:.0f}"
    assert mesh.default_objective_eligible is True


def test_register_objective_metadata_adds_entry(restore_registry) -> None:
    entry = ObjectiveMetadata(
        metric="__synth_metric_a",
        label="Synthetic A",
        unit="N",
        direction="min",
        source_evaluator="synthetic",
        availability_rule="present when synthetic evaluator runs",
        role="default_conservative",
        display_format="{value:.2f}",
        availability_conditions=["synthetic_evaluator_ran"],
        default_objective_eligible=False,
    )
    register_objective_metadata(entry)
    assert OBJECTIVE_METADATA["__synth_metric_a"].label == "Synthetic A"


def test_register_objective_metadata_refuses_duplicate(restore_registry) -> None:
    entry = ObjectiveMetadata(
        metric="GM0_m",  # already registered
        label="Duplicate",
        unit="m",
        direction="max",
        source_evaluator="hydrostatics",
        availability_rule="duplicate fixture",
        role="default_conservative",
    )
    with pytest.raises(ValueError, match="already registered"):
        register_objective_metadata(entry)


def test_is_objective_metric_admissible_default_passes() -> None:
    admissible, reason = is_objective_metric_admissible(
        "GM0_m", explicit_exploratory=False
    )
    assert admissible is True
    assert reason is None


def test_is_objective_metric_admissible_unknown_refused() -> None:
    admissible, reason = is_objective_metric_admissible(
        "not_a_metric", explicit_exploratory=False
    )
    assert admissible is False
    assert reason is not None
    assert reason["code"] == OBJECTIVE_REJECTION_UNKNOWN_METRIC


def test_is_objective_metric_admissible_unknown_allowed_under_exploratory() -> None:
    admissible, reason = is_objective_metric_admissible(
        "not_a_metric", explicit_exploratory=True
    )
    assert admissible is True
    assert reason is None


def test_is_objective_metric_admissible_display_only_always_refused() -> None:
    for flag in (False, True):
        admissible, reason = is_objective_metric_admissible(
            "max_gz_m", explicit_exploratory=flag
        )
        assert admissible is False
        assert reason is not None
        assert reason["code"] == OBJECTIVE_REJECTION_DISPLAY_ONLY
        assert reason["token"] == HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN


def test_is_objective_metric_admissible_claim_gated_role_refused() -> None:
    admissible, reason = is_objective_metric_admissible(
        "Rt_N_last", explicit_exploratory=False
    )
    assert admissible is False
    assert reason is not None
    assert reason["code"] == OBJECTIVE_REJECTION_CLAIM_GATED
    assert reason["role"] == "explicit_exploratory"


def test_is_objective_metric_admissible_claim_gated_allowed_under_exploratory() -> None:
    admissible, reason = is_objective_metric_admissible(
        "Rt_N_last", explicit_exploratory=True
    )
    assert admissible is True
    assert reason is None


def test_high_angle_gz_metrics_registered_with_display_only_role() -> None:
    for metric in (
        "max_gz_m",
        "heel_at_max_gz_deg",
        "range_positive_stability_deg",
    ):
        metadata = OBJECTIVE_METADATA[metric]
        assert metadata.role == "display_only"
        assert metadata.default_objective_eligible is False


def test_ensure_objectives_claim_admissible_for_search_rejects_unknown() -> None:
    with pytest.raises(UnknownSearchObjectiveError) as exc:
        ensure_objectives_claim_admissible_for_search(
            [Objective(metric="not_a_metric", direction="min")],
            explicit_exploratory=False,
        )
    assert exc.value.metric == "not_a_metric"
    assert exc.value.reason["code"] == OBJECTIVE_REJECTION_UNKNOWN_METRIC


def test_ensure_objectives_claim_admissible_for_search_allows_unknown_exploratory() -> None:
    # Should not raise — exploratory mode lets unknown metrics through so the
    # downstream evaluator's claim layer remains authoritative.
    ensure_objectives_claim_admissible_for_search(
        [Objective(metric="not_a_metric", direction="min")],
        explicit_exploratory=True,
    )


def test_ensure_objectives_claim_admissible_for_search_display_only_token_wins() -> None:
    # Even under exploratory mode the high-angle-GZ display-only refusal wins.
    with pytest.raises(HighAngleGzObjectiveRefusedError) as exc:
        ensure_objectives_claim_admissible_for_search(
            [Objective(metric="max_gz_m", direction="max")],
            explicit_exploratory=True,
        )
    assert exc.value.reason["token"] == HIGH_ANGLE_GZ_DISPLAY_ONLY_TOKEN


def test_format_metric_consults_registry_display_format() -> None:
    # mesh_problem_count is registered as "{value:.0f}" so the helper renders
    # it without decimal places. Default fallback stays "{value:.3f}".
    assert _format_metric(3.0, metric="mesh_problem_count") == "3"
    assert _format_metric(0.123456, metric="GM0_m") == "0.123"
    assert _format_metric(0.123456, metric="not_registered") == "0.123"
    # Implicit fallback (no metric name) stays byte-stable with the historical
    # ``{value:.3f}`` rendering used by the high-angle GZ display path.
    assert _format_metric(0.123456) == "0.123"
    assert _format_metric(None) == "unavailable"


def test_sweep_summary_includes_newly_registered_metric(
    tmp_path: Path, restore_registry
) -> None:
    """Registering a new metric must surface it as a summary.csv column.

    The synthetic evaluator merges a value into every candidate record's
    ``summary`` dict so the registry-driven column writer picks it up.
    """

    spec = SweepSpec(
        name="registry-extension",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50, 0.55]}},
    )

    register_objective_metadata(
        ObjectiveMetadata(
            metric="__synthetic_drag_index",
            label="Synthetic drag index",
            unit="dimensionless",
            direction="min",
            source_evaluator="synthetic_test_evaluator",
            availability_rule="injected by test fixture",
            role="default_conservative",
            display_format="{value:.4f}",
            availability_conditions=["synthetic_test_evaluator_ran"],
            default_objective_eligible=False,
        )
    )

    run = run_sweep(spec, tmp_path)
    # Force the synthetic metric onto each completed candidate's summary so the
    # registry-driven column writer has reason to surface it.
    for index, record in enumerate(run.candidates):
        record.summary["__synthetic_drag_index"] = 0.5 + index

    # Re-write summary.csv with the patched records via the same code path.
    from kayakgen.search.sweep import _write_summary

    _write_summary(tmp_path / "summary.csv", run.candidates)

    with (tmp_path / "summary.csv").open() as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)

    assert "__synthetic_drag_index" in header
    # Existing baseline columns are still present and in their historical
    # position so registry extensions are strictly additive.
    for legacy in ("displaced_mass_kg", "GM0_m", "Cp_actual"):
        assert legacy in header
    assert rows[0]["__synthetic_drag_index"] == "0.5"
    assert rows[1]["__synthetic_drag_index"] == "1.5"


def test_sweep_summary_omits_high_angle_display_only_metrics_even_if_present(
    tmp_path: Path,
) -> None:
    """Display-only high-angle metrics never leak into summary.csv columns.

    Even when a candidate's summary dict has a high-angle key (which it
    normally would not), the registry-driven column writer filters it out so
    the RFC 0043 stage 3 contract holds.
    """

    spec = SweepSpec(
        name="display-only-filter",
        base_hull={"beam_oa_m": 0.60},
        variables={"beam_wl_m": {"kind": "values", "values": [0.50]}},
    )
    run = run_sweep(spec, tmp_path)
    # Force a display-only key onto the summary dict.
    run.candidates[0].summary["max_gz_m"] = 0.42

    from kayakgen.search.sweep import _write_summary

    _write_summary(tmp_path / "summary.csv", run.candidates)

    header = (tmp_path / "summary.csv").read_text().splitlines()[0]
    assert "max_gz_m" not in header
    assert "heel_at_max_gz_deg" not in header
    assert "range_positive_stability_deg" not in header
