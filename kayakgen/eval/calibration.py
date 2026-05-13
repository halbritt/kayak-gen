"""Resistance calibration source registry.

These records describe candidate sources. They do not imply that current
resistance output is calibrated.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SourceUse = Literal["citation_only", "validation_candidate", "calibration_fixture"]


class ResistanceSourceRecord(BaseModel):
    """Citation/provenance record for a candidate resistance source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    url: str
    source_type: str
    intended_use: SourceUse
    measured_data: bool
    hull_class: str
    rights_status: str
    extraction_status: str
    notes: str
    warnings: list[str] = Field(default_factory=list)


def default_resistance_source_registry() -> tuple[ResistanceSourceRecord, ...]:
    """Return candidate sources reviewed by workflows 0012 and 0023.

    None of these records is currently accepted as a calibration fixture.
    """
    return (
        ResistanceSourceRecord(
            source_id="edinburgh_pacific_canoe_hydrodynamics",
            title="Hydrodynamics of Three Slender Models Resembling Pacific Canoe Hulls",
            url="https://datashare.ed.ac.uk/handle/10283/4772",
            source_type="open_measured_towing_tank_dataset",
            intended_use="validation_candidate",
            measured_data=True,
            hull_class="pacific_canoe_like_slender_hulls",
            rights_status="cc_by_4_0_dataset_doi_10_7488_ds_3785",
            extraction_status="no_checked_in_numeric_fixture_until_schema",
            notes=(
                "Open measured towing-tank force dataset with CAD models for "
                "three slender Pacific-canoe-like hulls. Useful for validation "
                "source tracking, but not representative enough for general "
                "sea-kayak resistance calibration."
            ),
            warnings=[
                "pacific_canoe_not_sea_kayak",
                "fixed_sink_trim",
                "validation_not_calibration",
            ],
        ),
        ResistanceSourceRecord(
            source_id="sea_kayaker_kanu_compilation",
            title="Sea Kayaker-derived sea-kayak resistance compilation",
            url="https://www.kanu.de/nuke/downloads/Resistance.pdf",
            source_type="compiled_model_results",
            intended_use="citation_only",
            measured_data=False,
            hull_class="sea_kayak",
            rights_status="copyrighted_compilation_unclear_redistribution",
            extraction_status="do_not_vendor_extracted_tables",
            notes=(
                "Broad sea-kayak coverage, but values are Sea Kayaker-derived "
                "model outputs rather than primary open measurement data."
            ),
            warnings=["model_to_model_calibration_risk", "redistribution_unclear"],
        ),
        ResistanceSourceRecord(
            source_id="gomes_2018_k1_drag_components",
            title="Effect of wetted surface area on friction, pressure, wave and total drag of a kayak",
            url="https://doi.org/10.1080/14763141.2017.1357748",
            source_type="peer_reviewed_experimental_and_decomposition",
            intended_use="validation_candidate",
            measured_data=True,
            hull_class="sprint_k1",
            rights_status="publisher_copyright_no_fixture_rights",
            extraction_status="citation_only_until_permission",
            notes=(
                "Direct kayak passive-drag data for a sprint K1 with simulated "
                "paddler weights, but too narrow for general sea-kayak calibration."
            ),
            warnings=["sprint_k1_not_sea_kayak", "redistribution_not_established"],
        ),
        ResistanceSourceRecord(
            source_id="tzabiras_k1_tow_tank",
            title="Experimental and Numerical Study of the Flow Past the Olympic Class K-1 Flat Water Racing Kayak",
            url=(
                "https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-"
                "the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/"
            ),
            source_type="tow_tank_experimental_and_numerical",
            intended_use="validation_candidate",
            measured_data=True,
            hull_class="sprint_k1",
            rights_status="article_available_no_open_fixture_license",
            extraction_status="citation_only_until_permission",
            notes=(
                "Measured K1 resistance over a useful speed band, but hull class "
                "and load case do not represent the broader sea-kayak design space."
            ),
            warnings=["sprint_k1_not_sea_kayak", "fixture_rights_not_established"],
        ),
        ResistanceSourceRecord(
            source_id="mdpi_physics_of_kayaking",
            title="On the Physics of Kayaking",
            url="https://www.mdpi.com/2076-3417/12/18/8925",
            source_type="open_access_modeling_context",
            intended_use="citation_only",
            measured_data=False,
            hull_class="kayak_general",
            rights_status="cc_by_article_context",
            extraction_status="no_primary_calibration_dataset",
            notes=(
                "Open-access literature context may be reusable with attribution, "
                "but it does not provide primary calibration fixture data."
            ),
            warnings=["not_primary_resistance_dataset"],
        ),
    )
