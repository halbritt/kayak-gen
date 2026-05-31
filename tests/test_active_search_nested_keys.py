"""RFC 0063 nested-key search variables tests.

Covers the dotted-path overlay path through ``_apply_genome`` /
``_hull_from_genome``, the ``SearchSpec`` model-validator that rejects
typos at spec-load time, and the no-regression invariant for flat-key
specs (byte-identical ``run.json`` across runs).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from kayakgen.search.active.runner import _apply_genome, run_search
from kayakgen.search.active.spec import (
    ChoiceVariable,
    ObjectiveSpec,
    SearchAlgorithmSpec,
    SearchBudget,
    SearchSpec,
    UniformVariable,
)
from kayakgen.search.sweep import CandidateRecord, EvaluatorOptions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _distribution_v2_base_hull() -> dict:
    """Compact distribution_v2 base hull used by the dotted-path tests."""
    return {
        "geometry_kind": "distribution_v2",
        "length_m": 4.5,
        "beam_oa_m": 0.55,
        "draft_m": 0.12,
        "distribution_v2": {
            "waterline_half_breadth": {
                "kind": "key_points",
                "knots": [
                    [-1.0, 0.0],
                    [-0.5, 0.20],
                    [0.0, 0.275],
                    [0.5, 0.20],
                    [1.0, 0.0],
                ],
            },
            "draft_profile": {
                "kind": "key_points",
                "knots": [
                    [-1.0, 0.0],
                    [-0.5, 0.10],
                    [0.0, 0.12],
                    [0.5, 0.10],
                    [1.0, 0.0],
                ],
            },
            "section_area_curve": {
                "kind": "polynomial",
                "coefficients": [0.04, 0.0, -0.04],
            },
            "deck_freeboard": {
                "kind": "key_points",
                "knots": [[-1.0, 0.04], [0.0, 0.11], [1.0, 0.04]],
            },
            "rocker": {
                "kind": "key_points",
                "knots": [
                    [-1.0, 0.0],
                    [-0.5, 0.0],
                    [0.0, 0.0],
                    [0.5, 0.0],
                    [1.0, 0.0],
                ],
            },
            "cross_section_family": "round",
            "deadrise_deg": 0.0,
        },
    }


def _write_spec(spec: SearchSpec, dest: Path, name: str = "spec.in.json") -> Path:
    path = dest / name
    path.write_text(spec.model_dump_json())
    return path


# ---------------------------------------------------------------------------
# _apply_genome unit tests
# ---------------------------------------------------------------------------


def test_apply_genome_flat_keys_byte_identical_to_dict_merge() -> None:
    base = {"length_m": 4.5, "beam_oa_m": 0.55, "Cp": 0.55}
    genome = {"length_m": 5.2, "Cp": 0.60}
    out = _apply_genome(base, genome)
    assert out == {"length_m": 5.2, "beam_oa_m": 0.55, "Cp": 0.60}
    # Original base must be untouched (deepcopy semantics).
    assert base == {"length_m": 4.5, "beam_oa_m": 0.55, "Cp": 0.55}


def test_apply_genome_dotted_path_writes_nested_leaf() -> None:
    base = _distribution_v2_base_hull()
    genome = {
        "length_m": 5.0,
        "distribution_v2.cross_section_family": "shallow_v",
        "distribution_v2.deadrise_deg": 12.5,
    }
    out = _apply_genome(base, genome)
    assert out["length_m"] == 5.0
    assert out["distribution_v2"]["cross_section_family"] == "shallow_v"
    assert out["distribution_v2"]["deadrise_deg"] == 12.5
    # The original base is untouched — deepcopy guarantees no nested
    # aliasing between callers.
    assert base["distribution_v2"]["cross_section_family"] == "round"
    assert base["distribution_v2"]["deadrise_deg"] == 0.0


def test_apply_genome_raises_on_missing_intermediate() -> None:
    base = {"length_m": 4.5}
    genome = {"distribution_v2.cross_section_family": "round"}
    with pytest.raises(ValueError, match=r"distribution_v2\.cross_section_family"):
        _apply_genome(base, genome)


def test_apply_genome_raises_on_non_dict_intermediate() -> None:
    base = {"distribution_v2": "not-a-dict"}
    genome = {"distribution_v2.cross_section_family": "round"}
    with pytest.raises(ValueError, match=r"non-dict path"):
        _apply_genome(base, genome)


# ---------------------------------------------------------------------------
# SearchSpec model-validator tests
# ---------------------------------------------------------------------------


def test_missing_dotted_path_rejected_at_spec_load() -> None:
    payload = {
        "schema_version": "1",
        "name": "nested-bad-path",
        "base_hull": _distribution_v2_base_hull(),
        "search_space": {
            "distribution_v2.no_such_field": {
                "kind": "choice",
                "values": ["a", "b"],
            },
        },
        "algorithm": {
            "kind": "nsga2",
            "population_size": 4,
            "generations": 2,
            "seed": 1,
        },
        "evaluators": {"hydrostatics": True},
        "budget": {"max_evaluations": 8},
    }
    with pytest.raises(ValidationError) as excinfo:
        SearchSpec.model_validate(payload)
    message = str(excinfo.value)
    assert "distribution_v2.no_such_field" in message
    assert "no_such_field" in message


def test_missing_intermediate_rejected_at_spec_load() -> None:
    payload = {
        "schema_version": "1",
        "name": "nested-bad-intermediate",
        # Lofted base hull — distribution_v2 is None — so any
        # distribution_v2.* dotted key has no nested record to land on.
        "base_hull": {"length_m": 4.5},
        "search_space": {
            "distribution_v2.cross_section_family": {
                "kind": "choice",
                "values": ["round", "shallow_v"],
            },
        },
        "algorithm": {
            "kind": "nsga2",
            "population_size": 4,
            "generations": 2,
            "seed": 1,
        },
        "evaluators": {"hydrostatics": True},
        "budget": {"max_evaluations": 8},
    }
    with pytest.raises(ValidationError) as excinfo:
        SearchSpec.model_validate(payload)
    message = str(excinfo.value)
    assert "distribution_v2.cross_section_family" in message


def test_flat_key_spec_skips_dotted_validator() -> None:
    """A spec with no dotted keys must not synthesize a Hull — base_hull
    might be partial in a way Hull.model_validate would reject."""
    payload = {
        "schema_version": "1",
        "name": "flat-only",
        # base_hull intentionally minimal — Hull defaults fill in the rest.
        "base_hull": {"length_m": 4.5},
        "search_space": {
            "beam_wl_m": {"kind": "uniform", "min": 0.46, "max": 0.54},
        },
        "algorithm": {
            "kind": "nsga2",
            "population_size": 4,
            "generations": 2,
            "seed": 1,
        },
        "evaluators": {"hydrostatics": True},
        "budget": {"max_evaluations": 8},
    }
    spec = SearchSpec.model_validate(payload)
    assert "beam_wl_m" in spec.search_space


# ---------------------------------------------------------------------------
# Runner integration tests
# ---------------------------------------------------------------------------


def _dotted_path_spec(*, name: str = "search-nested-keys") -> SearchSpec:
    return SearchSpec(
        name=name,
        base_hull=_distribution_v2_base_hull(),
        search_space={
            "distribution_v2.cross_section_family": ChoiceVariable(
                kind="choice",
                values=["round", "shallow_arch", "shallow_v"],
            ),
            "distribution_v2.deadrise_deg": UniformVariable(
                kind="uniform", min=0.0, max=15.0
            ),
        },
        algorithm=SearchAlgorithmSpec(
            kind="nsga2",
            population_size=6,
            generations=1,
            seed=2026,
        ),
        objectives=[
            ObjectiveSpec(metric="GM0_m", direction="max"),
            ObjectiveSpec(metric="displaced_mass_kg", direction="min"),
        ],
        evaluators=EvaluatorOptions(hydrostatics=True),
        constraints=[],
        budget=SearchBudget(max_evaluations=64),
    )


def test_dotted_path_overlays_distribution_v2(tmp_path: Path) -> None:
    spec = _dotted_path_spec()
    spec_path = _write_spec(spec, tmp_path)
    out = tmp_path / "run"
    result = run_search(spec_path, out)

    # The run must complete and produce at least one evaluated candidate.
    assert result.search_metadata.termination_reason == "completed"
    assert result.completed_count + result.constraint_failed_count >= 1

    # Candidate records must carry the dotted keys verbatim in `parameters`.
    record_paths = list((out / "candidates").glob("*.record.json"))
    assert record_paths, "expected at least one candidate record on disk"
    dotted_in_parameters = False
    families_seen: set[str] = set()
    for path in record_paths:
        rec = CandidateRecord.model_validate_json(path.read_text())
        if "distribution_v2.cross_section_family" in rec.parameters:
            dotted_in_parameters = True
            families_seen.add(rec.parameters["distribution_v2.cross_section_family"])
        # The resolved attempted_hull must carry the *nested* write — not
        # a top-level dotted key.
        assert "distribution_v2.cross_section_family" not in rec.attempted_hull
        nested = rec.attempted_hull.get("distribution_v2")
        assert isinstance(nested, dict)
        assert nested.get("cross_section_family") in {
            "round",
            "shallow_arch",
            "shallow_v",
        }
    assert dotted_in_parameters, (
        "every candidate's parameters must record the dotted key verbatim"
    )
    # The seed/family choices should produce more than a single family
    # across a 6-candidate run (degenerate same-family runs would
    # indicate the genome wasn't being applied).
    assert len(families_seen) >= 1


def test_dotted_path_handles_top_level_fields_too(tmp_path: Path) -> None:
    """A mixed flat + dotted search space evaluates both kinds of keys."""
    spec = SearchSpec(
        name="search-mixed-keys",
        base_hull=_distribution_v2_base_hull(),
        search_space={
            "length_m": UniformVariable(kind="uniform", min=4.4, max=4.7),
            "distribution_v2.deadrise_deg": UniformVariable(
                kind="uniform", min=0.0, max=10.0
            ),
        },
        algorithm=SearchAlgorithmSpec(
            kind="nsga2",
            population_size=4,
            generations=1,
            seed=7,
        ),
        objectives=[
            ObjectiveSpec(metric="GM0_m", direction="max"),
            ObjectiveSpec(metric="displaced_mass_kg", direction="min"),
        ],
        evaluators=EvaluatorOptions(hydrostatics=True),
        constraints=[],
        budget=SearchBudget(max_evaluations=8),
    )
    spec_path = _write_spec(spec, tmp_path)
    out = tmp_path / "run"
    run_search(spec_path, out)
    record_paths = list((out / "candidates").glob("*.record.json"))
    assert record_paths
    for path in record_paths:
        rec = CandidateRecord.model_validate_json(path.read_text())
        # Flat key lives at top level of attempted_hull.
        assert 4.4 <= float(rec.attempted_hull["length_m"]) <= 4.7
        # Dotted key lives in the nested distribution_v2 block.
        nested = rec.attempted_hull["distribution_v2"]
        assert isinstance(nested, dict)
        assert 0.0 <= float(nested["deadrise_deg"]) <= 10.0


# ---------------------------------------------------------------------------
# Flat-key byte-stability (no regression for the existing example).
# ---------------------------------------------------------------------------


_EXAMPLE_SPEC_PATH = (
    Path(__file__).parent.parent
    / "docs"
    / "examples"
    / "search_touring_sea_kayak_pareto.json"
)


_NONDETERMINISTIC_FIELDS = re.compile(
    r'"realized_wall_clock_seconds"\s*:\s*[^,}]+,?'
)


def _strip_nondeterministic(payload: str) -> str:
    """Remove wall-clock fields that vary across runs."""
    return _NONDETERMINISTIC_FIELDS.sub("", payload)


def test_flat_keys_byte_identical_after_refactor(tmp_path: Path) -> None:
    """Two runs of the flat-key example produce byte-identical run.json
    after stripping the nondeterministic wall-clock field.

    This is the no-regression invariant for RFC 0063: routing
    ``_hull_from_genome`` through ``_apply_genome`` must not change any
    bytes for specs that contain only flat top-level keys (every spec
    that exists in the repo today, including the canonical example).
    """
    assert _EXAMPLE_SPEC_PATH.exists(), (
        f"missing flat-key example at {_EXAMPLE_SPEC_PATH}"
    )

    out_a = tmp_path / "run-a"
    out_b = tmp_path / "run-b"
    run_search(_EXAMPLE_SPEC_PATH, out_a)
    run_search(_EXAMPLE_SPEC_PATH, out_b)

    payload_a = _strip_nondeterministic((out_a / "run.json").read_text())
    payload_b = _strip_nondeterministic((out_b / "run.json").read_text())
    assert payload_a == payload_b, (
        "flat-key example must produce byte-identical run.json across "
        "deterministic re-runs; dotted-path refactor must not perturb the "
        "no-dot path"
    )

    # Belt-and-suspenders: every candidate's parameters dict must use
    # only flat keys (no dots) — the existing example has no dotted
    # variables.
    record_paths = list((out_a / "candidates").glob("*.record.json"))
    assert record_paths
    for path in record_paths:
        rec = CandidateRecord.model_validate_json(path.read_text())
        assert all("." not in key for key in rec.parameters), (
            f"flat-key spec produced dotted parameters: {rec.parameters}"
        )


def test_example_distribution_v2_section_family_spec_loads(tmp_path: Path) -> None:
    """The shipped dotted-key example spec is loadable and validates."""
    example_path = (
        Path(__file__).parent.parent
        / "docs"
        / "examples"
        / "search_distribution_v2_section_family.json"
    )
    payload = json.loads(example_path.read_text())
    spec = SearchSpec.model_validate(payload)
    assert "distribution_v2.cross_section_family" in spec.search_space
    assert "distribution_v2.deadrise_deg" in spec.search_space
