"""Structured design-validity metadata — RFC 0031."""

from __future__ import annotations

from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.model.classes import list_classes
from kayakgen.model.hull import Hull
from kayakgen.model.validity import (
    CODE_CP_HIGH,
    CODE_DISPLACEMENT_LOW,
    CODE_L_BWL_LOW,
    CODE_LCB_UNSUPPORTED,
    CODE_ROCKER_BOW_UNSUPPORTED,
    CODE_ROCKER_STERN_UNSUPPORTED,
    CODE_SELECTED_CLASS_DRIFT,
    DesignValidityFinding,
    DesignValidityReport,
    design_warning_messages,
    evaluate_design_validity,
)
from kayakgen.search.compare import CandidateSummary, ComparisonReport
from kayakgen.search.sweep import CandidateRecord


def test_design_validity_records_pin_sources_and_compatible_messages() -> None:
    hull = Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65, Cp=0.66)

    report = evaluate_design_validity(hull, displaced_mass_kg=50.0)
    by_code = {finding.code: finding for finding in report.findings}

    assert by_code[CODE_L_BWL_LOW].message == "L/B_wl below touring guidance"
    assert by_code[CODE_L_BWL_LOW].source.endswith("section 4")
    assert by_code[CODE_CP_HIGH].source.endswith("section 8")
    assert by_code[CODE_DISPLACEMENT_LOW].source.endswith("section 7")
    assert design_warning_messages(report) == (
        "L/B_wl below touring guidance",
        "Cp above recommended kayak range",
        "displacement below typical single-paddler load",
    )
    assert report.warning_count == 3


def test_design_validity_models_tolerate_future_optional_fields() -> None:
    finding = DesignValidityFinding.model_validate(
        {
            "code": "future_design_hint",
            "level": "advisory",
            "severity": "warning",
            "message": "future advisory",
            "source": "future source",
            "parameters": ["length_m"],
            "future_optional": {"score": 0.25},
        }
    )
    report = DesignValidityReport.model_validate(
        {"findings": [finding.model_dump(mode="json")], "future_top_level": True}
    )

    assert report.findings[0].model_extra["future_optional"] == {"score": 0.25}
    assert report.model_extra["future_top_level"] is True
    assert report.warning_count == 1


def test_old_strict_records_load_without_design_validity_fields() -> None:
    hull = Hull()
    hydro = evaluate_hydrostatics(hull)

    evaluation = EvaluationResult.model_validate(
        {"hull_hash": hull.hash(), "hydrostatics": hydro.model_dump(mode="json")}
    )
    candidate = CandidateRecord.model_validate(
        {
            "candidate_index": 0,
            "candidate_key": "candidate-a",
            "parameters": {},
            "attempted_hull": hull.model_dump(mode="json"),
            "status": "complete",
        }
    )
    summary = CandidateSummary.model_validate(
        {
            "candidate_index": 0,
            "candidate_key": "candidate-a",
            "status": "complete",
        }
    )
    report = ComparisonReport.model_validate(
        {
            "run_name": "old",
            "spec_hash": "old",
            "report_kind": "pareto_frontier",
            "objectives": [],
            "pareto_front_keys": [],
            "candidate_summaries": [],
        }
    )

    assert evaluation.design_validity.findings == []
    assert candidate.design_validity.findings == []
    assert summary.design_validity.findings == []
    assert report.design_validity == {}


def test_class_defaults_are_quiet_with_explicit_selected_class() -> None:
    for kayak_class in list_classes():
        hull = kayak_class.default_hull()
        hydro = evaluate_hydrostatics(hull)

        report = evaluate_design_validity(
            hull,
            cp=hydro.Cp_actual,
            displaced_mass_kg=hydro.displaced_mass_kg,
            selected_class=kayak_class.name,
        )

        assert report.findings == []


def test_selected_class_drift_is_explicit_and_optional() -> None:
    hull = Hull(length_m=6.1, beam_oa_m=0.58, beam_wl_m=0.53, Cp=0.54)

    assert CODE_SELECTED_CLASS_DRIFT not in evaluate_design_validity(hull).codes()

    report = evaluate_design_validity(hull, selected_class="touring")

    assert report.codes() == (CODE_SELECTED_CLASS_DRIFT,)
    finding = report.findings[0]
    assert finding.selected_class == "touring"
    assert finding.parameters == ("length_m",)


def test_non_neutral_reserved_fields_emit_unsupported_records() -> None:
    neutral = evaluate_design_validity(Hull())
    assert not any(finding.level == "unsupported" for finding in neutral.findings)

    report = evaluate_design_validity(
        Hull(LCB_frac=0.51, rocker_bow_m=0.02, rocker_stern_m=0.01)
    )

    assert {
        CODE_LCB_UNSUPPORTED,
        CODE_ROCKER_BOW_UNSUPPORTED,
        CODE_ROCKER_STERN_UNSUPPORTED,
    }.issubset(report.codes())
    assert report.unsupported_count == 3
    assert all(finding.severity == "info" for finding in report.findings)
