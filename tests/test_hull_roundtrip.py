"""Hull JSON round-trip and stable hash."""

from __future__ import annotations

import json

from kayakgen.model.hull import Hull


def test_default_round_trip() -> None:
    hull = Hull()
    assert hull.bow_rake == 1.0
    assert hull.stern_rake == 1.0
    blob = hull.model_dump_json()
    hull2 = Hull.model_validate_json(blob)
    assert hull == hull2


def test_named_round_trip(tmp_path) -> None:
    hull = Hull(name="performance-tour", length_m=5.2, beam_oa_m=0.50, draft_m=0.13, Cp=0.58)
    out = tmp_path / "hull.json"
    out.write_text(hull.model_dump_json(indent=2))
    loaded = Hull.model_validate_json(out.read_text())
    assert loaded.name == "performance-tour"
    assert loaded.length_m == 5.2
    assert loaded == hull


def test_hash_stable_across_dumps() -> None:
    h1 = Hull(name="a", length_m=4.5)
    h2 = Hull(name="a", length_m=4.5)
    assert h1.hash() == h2.hash()


def test_hash_reflects_changes() -> None:
    base = Hull()
    longer = base.model_copy(update={"length_m": 5.0})
    assert base.hash() != longer.hash()


def test_legacy_bow_rake_json_seeds_symmetric_stern_rake() -> None:
    blob = json.dumps({"bow_rake": 0.25})
    hull = Hull.model_validate_json(blob)

    assert hull.bow_rake == 0.25
    assert hull.stern_rake == 0.25
    assert Hull.model_validate_json(hull.model_dump_json()).stern_rake == 0.25
    assert hull == Hull(bow_rake=0.25, stern_rake=0.25)
    assert hull.hash() == Hull(bow_rake=0.25, stern_rake=0.25).hash()


def test_independent_stern_rake_round_trip() -> None:
    hull = Hull.model_validate_json(json.dumps({"bow_rake": 0.0, "stern_rake": 1.0}))

    assert hull.bow_rake == 0.0
    assert hull.stern_rake == 1.0
    assert Hull.model_validate_json(hull.model_dump_json()) == hull


def test_stern_rake_only_json_uses_default_bow_rake() -> None:
    hull = Hull.model_validate_json(json.dumps({"stern_rake": 0.0}))

    assert hull.bow_rake == 1.0
    assert hull.stern_rake == 0.0


def test_stern_rake_range_is_validated() -> None:
    import pydantic

    for value in (-0.1, 1.1):
        try:
            Hull(stern_rake=value)
        except pydantic.ValidationError:
            continue
        raise AssertionError("Hull should validate stern_rake in [0, 1]")


def test_unknown_field_rejected() -> None:
    import pydantic

    blob = json.dumps({"length_m": 4.5, "made_up_field": 1.0})
    try:
        Hull.model_validate_json(blob)
    except pydantic.ValidationError:
        return
    raise AssertionError("Hull should reject unknown fields")


def test_to_geometry_returns_lofted() -> None:
    from kayakgen.model.geometry import LoftedHullGeometry

    g = Hull().to_geometry()
    assert isinstance(g, LoftedHullGeometry)
