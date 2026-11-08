"""Versioned physical identity must distinguish v2 shapes and legacy evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.distribution_v2 import DistributionV2Spec, PolynomialDistribution, UniformDistribution
from kayakgen.model.hull import Hull


def v2_hull() -> Hull:
    return Hull(
        geometry_kind="distribution_v2",
        distribution_v2=DistributionV2Spec(
            waterline_half_breadth=PolynomialDistribution(coefficients=[0.24, 0, -0.24]),
            draft_profile=UniformDistribution(value=0.11),
            section_area_curve=UniformDistribution(value=0.035),
            deck_freeboard=UniformDistribution(value=0.16),
            rocker=UniformDistribution(value=0),
        ),
    )


def test_distinct_v2_geometry_has_distinct_versioned_identity() -> None:
    hull = v2_hull()
    changed = hull.model_dump(mode="json")
    changed["distribution_v2"]["waterline_half_breadth"]["coefficients"] = [0.22, 0, -0.22]
    narrower = Hull.model_validate(changed)

    assert evaluate(hull).displaced_volume_m3 != evaluate(narrower).displaced_volume_m3
    assert hull.design_hash() != narrower.design_hash()
    assert hull.design_hash().startswith("distribution_v2_v2:")


def test_v2_identity_ignores_cosmetic_and_legacy_reporting_inputs() -> None:
    hull = v2_hull()
    renamed = hull.model_copy(update={"name": "owner design", "hull_class": "sea_kayak"})
    legacy_draft = hull.model_copy(update={"draft_m": 0.19, "beam_oa_m": 0.60})
    assert hull.design_hash() == renamed.design_hash() == legacy_draft.design_hash()
    assert hull.record_hash() != renamed.record_hash()
    assert hull.legacy_design_hash() != legacy_draft.legacy_design_hash()


def test_lofted_and_record_hashes_remain_byte_stable() -> None:
    hull = Hull()
    assert hull.design_hash() == "4f3de0c94b242c01377e4264e3d9021b8ad9e6af0a5a179ae0496ae24ae5e84e"
    assert hull.legacy_design_hash() == hull.design_hash()
    assert hull.record_hash() == "12cbd22742eb682e21dea282163b65f77d878324240e4d5696e3838f89084285"


def test_v2_identity_is_canonical_across_serialization_and_cannot_equal_legacy() -> None:
    import json

    hull = v2_hull()
    reordered = dict(reversed(list(hull.model_dump(mode="json").items())))
    assert Hull.model_validate_json(json.dumps(reordered)).design_hash() == hull.design_hash()
    assert hull.legacy_design_hash() == "77db17848bcbbdcbc9dd217f89b3067db657b227a5672e6ce7b9c6eeb860477d"
    assert hull.design_hash() != hull.legacy_design_hash()


def test_each_v2_distribution_or_family_is_part_of_identity() -> None:
    from kayakgen.model.distribution_v2 import KeyPointsDistribution

    hull = v2_hull()
    replacements = {
        "waterline_half_breadth": KeyPointsDistribution(knots=[(-1, 0), (0, 0.23), (1, 0)]),
        "draft_profile": UniformDistribution(value=0.115),
        "section_area_curve": UniformDistribution(value=0.04),
        "deck_freeboard": UniformDistribution(value=0.15),
        "rocker": UniformDistribution(value=0.01),
        "cross_section_family": "shallow_v",
        "deadrise_deg": KeyPointsDistribution(knots=[(-1, 4), (1, 8)]),
        "chine_radius_m": 0.01,
        "bow_flare_deg": 4,
        "multi_chine_count": 3,
        "rocker_bow_m": 0.01,
        "rocker_stern_m": 0.01,
        "lcb_target_frac": 0.52,
        "max_beam_position_frac": 0.52,
    }
    for name, value in replacements.items():
        spec = hull.distribution_v2.model_copy(update={name: value})
        changed = hull.model_copy(update={"distribution_v2": spec})
        assert changed.design_hash() != hull.design_hash(), name
    assert hull.model_copy(update={"length_m": 5.0}).design_hash() != hull.design_hash()


def test_keypoint_knots_are_part_of_v2_identity() -> None:
    from kayakgen.model.distribution_v2 import KeyPointsDistribution

    hull = v2_hull()
    spec = hull.distribution_v2.model_copy(update={
        "waterline_half_breadth": KeyPointsDistribution(knots=[(-1, 0), (0, 0.24), (1, 0)]),
    })
    first = hull.model_copy(update={"distribution_v2": spec})
    changed = first.model_dump(mode="json")
    changed["distribution_v2"]["waterline_half_breadth"]["knots"][1][0] = 0.1
    assert Hull.model_validate(changed).design_hash() != first.design_hash()


def test_index_and_verified_reindex_preserve_versioned_v2_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from typer.testing import CliRunner

    from kayakgen.cli.main import app
    from kayakgen.search.sweep import SweepSpec, run_sweep
    from kayakgen.services.artifact_store import SqliteIndex, load_run_manifest, reindex_run

    monkeypatch.setenv("KAYAKGEN_INDEX_DB", str(tmp_path / "index.sqlite"))
    hull = v2_hull()
    out = tmp_path / "run"
    run = run_sweep(SweepSpec.model_validate({
        "name": "versioned-identity",
        "base_hull": hull.model_dump(mode="json"),
        "variables": {"Cp": {"kind": "values", "values": [hull.Cp]}},
    }), out)
    manifest = load_run_manifest(out)
    before = manifest.model_dump(mode="json")
    index = SqliteIndex()
    rows = index.candidates_for_run(manifest.run_id)
    assert rows[0].hull_design_hash == hull.design_hash()
    response = CliRunner().invoke(app, [
        "runs", "query", manifest.run_id,
        "--filter", "hull_design_hash:" + hull.design_hash(),
    ])
    assert response.exit_code == 0, response.output
    assert hull.design_hash() in response.output
    legacy_lookup = CliRunner().invoke(app, [
        "runs", "query", manifest.run_id,
        "--filter", "hull_design_hash:" + hull.legacy_design_hash(),
    ])
    assert legacy_lookup.exit_code == 0
    assert "no candidates" in legacy_lookup.output
    # An old projection remains a historical lookup until explicitly rebuilt
    # from the run's verified complete input; no durable evidence is rewritten.
    index.upsert_candidate(
        run_id=manifest.run_id, candidate_key=run.candidates[0].candidate_key,
        status="complete", hull_design_hash=hull.legacy_design_hash(),
        hull_record_hash=hull.record_hash(),
    )
    assert index.candidates_for_run(manifest.run_id)[0].hull_design_hash == hull.legacy_design_hash()
    reindex_run(out, index=index)
    assert index.candidates_for_run(manifest.run_id)[0].hull_design_hash == hull.design_hash()
    assert load_run_manifest(out).model_dump(mode="json") == before
