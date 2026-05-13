"""Structured design-validity metadata for hull-design guidance.

The records in this module are advisory metadata. They do not loosen
``Hull`` validation, prove design fitness, or promote any geometry/solver
readiness state.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kayakgen.model.classes import CLASSES
from kayakgen.model.hull import Hull

DesignValidityLevel = Literal["enforced", "advisory", "unsupported"]
DesignValiditySeverity = Literal["error", "warning", "info"]

SOURCE_L_BWL = "docs/design/kayak_hull_design_constraints.md section 4"
SOURCE_DISPLACEMENT = "docs/design/kayak_hull_design_constraints.md section 7"
SOURCE_CP = "docs/design/kayak_hull_design_constraints.md section 8"
SOURCE_CLASS = "docs/design/kayak_hull_design_constraints.md sections 3, 4, and 9"
SOURCE_UNSUPPORTED = (
    "docs/rfcs/0031-design-constraint-surfacing-revision.md section 3; "
    "kayakgen/model/hull.py reserved fields"
)

CODE_L_BWL_LOW = "design_l_bwl_below_touring_guidance"
CODE_L_BWL_HIGH = "design_l_bwl_beyond_elite_surfski_guidance"
CODE_CP_LOW = "design_cp_below_recommended_range"
CODE_CP_HIGH = "design_cp_above_recommended_range"
CODE_DISPLACEMENT_LOW = "design_displacement_below_single_paddler_load"
CODE_DISPLACEMENT_HIGH = "design_displacement_above_single_paddler_load"
CODE_SELECTED_CLASS_DRIFT = "design_selected_class_drift"
CODE_LCB_UNSUPPORTED = "unsupported_lcb_frac"
CODE_ROCKER_BOW_UNSUPPORTED = "unsupported_rocker_bow_m"
CODE_ROCKER_STERN_UNSUPPORTED = "unsupported_rocker_stern_m"

MESSAGE_L_BWL_LOW = "L/B_wl below touring guidance"
MESSAGE_L_BWL_HIGH = "L/B_wl beyond elite surfski guidance"
MESSAGE_CP_LOW = "Cp below recommended kayak range"
MESSAGE_CP_HIGH = "Cp above recommended kayak range"
MESSAGE_DISPLACEMENT_LOW = "displacement below typical single-paddler load"
MESSAGE_DISPLACEMENT_HIGH = "displacement above typical single-paddler load"
MESSAGE_SELECTED_CLASS_DRIFT = "Hull is outside the selected class envelope"
MESSAGE_LCB_UNSUPPORTED = "LCB_frac is stored but not yet honored by the loft"
MESSAGE_ROCKER_BOW_UNSUPPORTED = (
    "rocker_bow_m is stored but not yet a full geometry control"
)
MESSAGE_ROCKER_STERN_UNSUPPORTED = (
    "rocker_stern_m is stored but not yet a full geometry control"
)


class DesignValidityFinding(BaseModel):
    """One structured finding about the design parameter state.

    The model intentionally allows future optional fields so new producers can
    add details without breaking existing consumers.
    """

    model_config = ConfigDict(extra="allow")

    code: str
    level: DesignValidityLevel
    severity: DesignValiditySeverity
    message: str
    source: str
    parameters: tuple[str, ...] = Field(default_factory=tuple)


class DesignValidityReport(BaseModel):
    """Additive report carried by evaluation, sweep, and comparison JSON."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1"] = "1"
    findings: list[DesignValidityFinding] = Field(default_factory=list)
    advisory_count: int = 0
    warning_count: int = 0
    unsupported_count: int = 0
    error_count: int = 0

    @model_validator(mode="after")
    def _sync_counts(self) -> "DesignValidityReport":
        self.advisory_count = sum(
            1 for finding in self.findings if finding.level == "advisory"
        )
        self.warning_count = sum(
            1 for finding in self.findings if finding.severity == "warning"
        )
        self.unsupported_count = sum(
            1 for finding in self.findings if finding.level == "unsupported"
        )
        self.error_count = sum(1 for finding in self.findings if finding.severity == "error")
        return self

    def messages(
        self,
        *,
        levels: Iterable[DesignValidityLevel] | None = None,
        severities: Iterable[DesignValiditySeverity] | None = None,
    ) -> tuple[str, ...]:
        level_filter = set(levels) if levels is not None else None
        severity_filter = set(severities) if severities is not None else None
        return tuple(
            finding.message
            for finding in self.findings
            if (level_filter is None or finding.level in level_filter)
            and (severity_filter is None or finding.severity in severity_filter)
        )

    def codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


def evaluate_design_validity(
    hull: Hull,
    *,
    cp: float | None = None,
    displaced_mass_kg: float | None = None,
    selected_class: str | None = None,
    surface: Iterable[str] | None = None,
) -> DesignValidityReport:
    """Return structured non-blocking design guidance for a valid hull."""

    beam_wl = hull.beam_wl_m or hull.beam_oa_m
    l_over_bwl = hull.length_m / beam_wl
    cp_value = hull.Cp if cp is None else cp
    findings: list[DesignValidityFinding] = []

    if l_over_bwl < 8.0:
        findings.append(
            _finding(
                code=CODE_L_BWL_LOW,
                level="advisory",
                severity="warning",
                message=MESSAGE_L_BWL_LOW,
                source=SOURCE_L_BWL,
                parameters=("length_m", "beam_wl_m"),
                value=l_over_bwl,
                bounds={"min": 8.0, "max": 15.5},
                surface=surface,
            )
        )
    elif l_over_bwl > 15.5:
        findings.append(
            _finding(
                code=CODE_L_BWL_HIGH,
                level="advisory",
                severity="warning",
                message=MESSAGE_L_BWL_HIGH,
                source=SOURCE_L_BWL,
                parameters=("length_m", "beam_wl_m"),
                value=l_over_bwl,
                bounds={"min": 8.0, "max": 15.5},
                surface=surface,
            )
        )

    if cp_value < 0.50:
        findings.append(
            _finding(
                code=CODE_CP_LOW,
                level="advisory",
                severity="warning",
                message=MESSAGE_CP_LOW,
                source=SOURCE_CP,
                parameters=("Cp",),
                value=cp_value,
                bounds={"min": 0.50, "max": 0.65},
                surface=surface,
            )
        )
    elif cp_value > 0.65:
        findings.append(
            _finding(
                code=CODE_CP_HIGH,
                level="advisory",
                severity="warning",
                message=MESSAGE_CP_HIGH,
                source=SOURCE_CP,
                parameters=("Cp",),
                value=cp_value,
                bounds={"min": 0.50, "max": 0.65},
                surface=surface,
            )
        )

    if displaced_mass_kg is not None:
        lower_mass = 0.075 * 1025.0
        upper_mass = 0.180 * 1025.0
        if displaced_mass_kg < lower_mass:
            findings.append(
                _finding(
                    code=CODE_DISPLACEMENT_LOW,
                    level="advisory",
                    severity="warning",
                    message=MESSAGE_DISPLACEMENT_LOW,
                    source=SOURCE_DISPLACEMENT,
                    parameters=("draft_m", "beam_wl_m", "length_m"),
                    value=displaced_mass_kg,
                    bounds={"min_kg": lower_mass, "max_kg": upper_mass},
                    surface=surface,
                )
            )
        elif displaced_mass_kg > upper_mass:
            findings.append(
                _finding(
                    code=CODE_DISPLACEMENT_HIGH,
                    level="advisory",
                    severity="warning",
                    message=MESSAGE_DISPLACEMENT_HIGH,
                    source=SOURCE_DISPLACEMENT,
                    parameters=("draft_m", "beam_wl_m", "length_m"),
                    value=displaced_mass_kg,
                    bounds={"min_kg": lower_mass, "max_kg": upper_mass},
                    surface=surface,
                )
            )

    findings.extend(_selected_class_findings(hull, selected_class, surface=surface))
    findings.extend(_unsupported_findings(hull, surface=surface))
    return DesignValidityReport(findings=findings)


def design_warning_messages(report: DesignValidityReport) -> tuple[str, ...]:
    """Return visible warning text for design advisories only."""

    return report.messages(levels=("advisory",), severities=("warning",))


def _finding(
    *,
    code: str,
    level: DesignValidityLevel,
    severity: DesignValiditySeverity,
    message: str,
    source: str,
    parameters: tuple[str, ...],
    surface: Iterable[str] | None = None,
    **extra: Any,
) -> DesignValidityFinding:
    payload: dict[str, Any] = {
        "code": code,
        "level": level,
        "severity": severity,
        "message": message,
        "source": source,
        "parameters": parameters,
    }
    payload.update(extra)
    if surface is not None:
        payload["surface"] = tuple(surface)
    return DesignValidityFinding.model_validate(payload)


def _selected_class_findings(
    hull: Hull,
    selected_class: str | None,
    *,
    surface: Iterable[str] | None = None,
) -> list[DesignValidityFinding]:
    if (
        selected_class is None
        or selected_class == "custom"
        or selected_class not in CLASSES
    ):
        return []
    kayak_class = CLASSES[selected_class]
    values = {
        "length_m": hull.length_m,
        "beam_oa_m": hull.beam_oa_m,
        "beam_wl_m": hull.beam_wl_m or hull.beam_oa_m,
        "draft_m": hull.draft_m,
        "Cp": hull.Cp,
    }
    ranges = {
        "length_m": kayak_class.length_m,
        "beam_oa_m": kayak_class.beam_oa_m,
        "beam_wl_m": kayak_class.beam_wl_m,
        "draft_m": kayak_class.draft_m,
        "Cp": kayak_class.Cp,
    }
    outside = tuple(
        name
        for name, value in values.items()
        if value < ranges[name].min or value > ranges[name].max
    )
    if not outside:
        return []
    return [
        _finding(
            code=CODE_SELECTED_CLASS_DRIFT,
            level="advisory",
            severity="warning",
            message=MESSAGE_SELECTED_CLASS_DRIFT,
            source=SOURCE_CLASS,
            parameters=outside,
            selected_class=selected_class,
            value={name: values[name] for name in outside},
            bounds={
                name: {"min": ranges[name].min, "max": ranges[name].max}
                for name in outside
            },
            surface=surface,
        )
    ]


def _unsupported_findings(
    hull: Hull,
    *,
    surface: Iterable[str] | None = None,
) -> list[DesignValidityFinding]:
    findings: list[DesignValidityFinding] = []
    if not math.isclose(hull.LCB_frac, 0.50, rel_tol=0.0, abs_tol=1e-12):
        findings.append(
            _finding(
                code=CODE_LCB_UNSUPPORTED,
                level="unsupported",
                severity="info",
                message=MESSAGE_LCB_UNSUPPORTED,
                source=SOURCE_UNSUPPORTED,
                parameters=("LCB_frac",),
                value=hull.LCB_frac,
                neutral_value=0.50,
                surface=surface,
            )
        )
    if not math.isclose(hull.rocker_bow_m, 0.0, rel_tol=0.0, abs_tol=1e-12):
        findings.append(
            _finding(
                code=CODE_ROCKER_BOW_UNSUPPORTED,
                level="unsupported",
                severity="info",
                message=MESSAGE_ROCKER_BOW_UNSUPPORTED,
                source=SOURCE_UNSUPPORTED,
                parameters=("rocker_bow_m",),
                value=hull.rocker_bow_m,
                neutral_value=0.0,
                surface=surface,
            )
        )
    if not math.isclose(hull.rocker_stern_m, 0.0, rel_tol=0.0, abs_tol=1e-12):
        findings.append(
            _finding(
                code=CODE_ROCKER_STERN_UNSUPPORTED,
                level="unsupported",
                severity="info",
                message=MESSAGE_ROCKER_STERN_UNSUPPORTED,
                source=SOURCE_UNSUPPORTED,
                parameters=("rocker_stern_m",),
                value=hull.rocker_stern_m,
                neutral_value=0.0,
                surface=surface,
            )
        )
    return findings
