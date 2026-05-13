"""KayakClass presets and beam_wl semantics — RFC 0006."""

from __future__ import annotations

from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.advisory import design_advisory
from kayakgen.model.classes import CLASSES, get_class, list_classes
from kayakgen.model.hull import Hull
from kayakgen.model.validity import CODE_CP_HIGH, CODE_L_BWL_LOW


def test_canonical_classes_present() -> None:
    assert set(CLASSES) == {"touring", "performance", "surfski_int", "surfski_elite"}


def test_touring_acceptance_defaults() -> None:
    h = get_class("touring").default_hull()
    assert h.length_m == 5.0
    assert h.beam_oa_m == 0.58
    assert abs(h.beam_wl_m - 0.53) < 1e-9
    assert h.draft_m == 0.12
    assert h.Cp == 0.54


def test_elite_surfski_acceptance_defaults() -> None:
    h = get_class("surfski_elite").default_hull()
    assert h.length_m == 6.1
    assert h.beam_oa_m == 0.43
    assert abs(h.beam_wl_m - 0.40) < 1e-9
    assert h.draft_m == 0.11
    assert h.Cp == 0.58


def test_preset_round_trip_through_pydantic() -> None:
    for kc in list_classes():
        hull = kc.default_hull()
        loaded = Hull.model_validate_json(hull.model_dump_json())
        assert loaded == hull


def test_beam_wl_monotonicity_volume() -> None:
    # Narrowing the waterline beam shrinks displaced volume monotonically;
    # the deck (above-water) widens are kept by beam_oa unchanged.
    base = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.60))
    narrow = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.50))
    narrower = evaluate(Hull(beam_oa_m=0.60, beam_wl_m=0.40))
    assert base.displaced_volume_m3 > narrow.displaced_volume_m3
    assert narrow.displaced_volume_m3 > narrower.displaced_volume_m3


def test_beam_wl_default_falls_back_to_beam_oa() -> None:
    # Hull with beam_wl_m=None must reproduce the legacy hull volume.
    legacy_like = evaluate(Hull(beam_wl_m=None))
    explicit = evaluate(Hull(beam_wl_m=Hull().beam_oa_m))
    assert abs(legacy_like.displaced_volume_m3 - explicit.displaced_volume_m3) < 1e-12


def test_explicit_beam_wl_must_be_positive_and_not_exceed_overall() -> None:
    import pytest

    with pytest.raises(ValueError):
        Hull(beam_wl_m=-0.1)
    with pytest.raises(ValueError):
        Hull(beam_oa_m=0.55, beam_wl_m=0.60)


def test_preset_volumes_in_paddler_envelope() -> None:
    # Constraints doc §6 places paddler-only displacement at ~75-180 L.
    for kc in list_classes():
        h = evaluate(kc.default_hull())
        v_litres = h.displaced_volume_m3 * 1000
        assert 60 < v_litres < 200, f"{kc.name}: {v_litres:.1f} L"


def test_design_advisory_reports_shared_warning_bands() -> None:
    broad = design_advisory(Hull(length_m=4.0, beam_oa_m=0.70, beam_wl_m=0.65))
    assert broad.l_over_bwl < 8
    assert "L/B_wl below touring guidance" in broad.warnings
    assert CODE_L_BWL_LOW in broad.design_validity.codes()

    full_ends = design_advisory(Hull(Cp=0.66))
    assert "Cp above recommended kayak range" in full_ends.warnings
    assert CODE_CP_HIGH in full_ends.design_validity.codes()

    overloaded = design_advisory(Hull(), displaced_mass_kg=190.0)
    assert "displacement above typical single-paddler load" in overloaded.warnings
    assert overloaded.warnings == tuple(
        finding.message
        for finding in overloaded.design_validity.findings
        if finding.level == "advisory" and finding.severity == "warning"
    )


def test_design_advisory_keeps_class_defaults_quiet() -> None:
    for kc in list_classes():
        hull = kc.default_hull()
        hydro = evaluate(hull)
        assert design_advisory(
            hull,
            cp=hydro.Cp_actual,
            displaced_mass_kg=hydro.displaced_mass_kg,
        ).warnings == ()


def test_class_lookup() -> None:
    import pytest

    assert get_class("touring").name == "touring"
    with pytest.raises(KeyError):
        get_class("does-not-exist")
