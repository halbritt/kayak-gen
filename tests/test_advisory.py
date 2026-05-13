"""Structured advisory records for design feedback."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kayakgen.model.advisory import Advisory, design_advisory
from kayakgen.model.hull import Hull
from kayakgen.model.validity import (
    CODE_CP_HIGH,
    CODE_DISPLACEMENT_HIGH,
    CODE_L_BWL_LOW,
    design_warning_messages,
)


def warning_hull_advisory():
    return design_advisory(
        Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65, Cp=0.66),
        displaced_mass_kg=190.0,
    )


def test_design_advisory_warning_strings_remain_compatible() -> None:
    advisory = warning_hull_advisory()

    assert advisory.warnings == design_warning_messages(advisory.design_validity)
    assert advisory.warnings == (
        "L/B_wl below touring guidance",
        "Cp above recommended kayak range",
        "displacement above typical single-paddler load",
    )


def test_design_advisory_records_preserve_structured_field_refs() -> None:
    advisory = warning_hull_advisory()
    by_code = {record.code: record for record in advisory.advisories}

    assert tuple(by_code) == (CODE_L_BWL_LOW, CODE_CP_HIGH, CODE_DISPLACEMENT_HIGH)
    assert by_code[CODE_L_BWL_LOW].message == "L/B_wl below touring guidance"
    assert by_code[CODE_L_BWL_LOW].field_refs == ("length_m", "beam_wl_m")
    assert by_code[CODE_CP_HIGH].field_refs == ("Cp",)
    assert by_code[CODE_DISPLACEMENT_HIGH].field_refs == (
        "draft_m",
        "beam_wl_m",
        "length_m",
    )
    assert advisory.advisories == tuple(
        Advisory(
            code=finding.code,
            message=finding.message,
            field_refs=finding.parameters,
        )
        for finding in advisory.design_validity.findings
        if finding.level == "advisory" and finding.severity == "warning"
    )


def test_advisory_records_are_immutable() -> None:
    record = Advisory(
        code="design_cp_above_recommended_range",
        message="Cp above recommended kayak range",
        field_refs=["Cp"],
    )

    assert record.field_refs == ("Cp",)
    with pytest.raises(FrozenInstanceError):
        setattr(record, "message", "changed")
    with pytest.raises(TypeError):
        record.field_refs[0] = "length_m"


def test_advisory_records_do_not_promote_warnings_to_hard_failures() -> None:
    advisory = warning_hull_advisory()

    assert advisory.warnings
    assert advisory.advisories
    assert advisory.design_validity.error_count == 0
    assert advisory.design_validity.messages(severities=("error",)) == ()
    assert all(
        finding.level == "advisory" and finding.severity == "warning"
        for finding in advisory.design_validity.findings
    )
