"""KayakClass presets and beam_wl semantics — RFC 0006."""

from __future__ import annotations

from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.classes import CLASSES, get_class, list_classes
from kayakgen.model.hull import Hull


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


def test_preset_volumes_in_paddler_envelope() -> None:
    # Constraints doc §6 places paddler-only displacement at ~75-180 L.
    for kc in list_classes():
        h = evaluate(kc.default_hull())
        v_litres = h.displaced_volume_m3 * 1000
        assert 60 < v_litres < 200, f"{kc.name}: {v_litres:.1f} L"


def test_class_lookup() -> None:
    import pytest

    assert get_class("touring").name == "touring"
    with pytest.raises(KeyError):
        get_class("does-not-exist")
