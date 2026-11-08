"""Active search must not admit cached metrics without their recorded evidence."""

from pathlib import Path

import pytest

from kayakgen.search.active.runner import SearchRunRecord, run_search
from kayakgen.search.active.spec import SearchSpec
from kayakgen.services.artifact_store import FilesystemArtifactStore


def search_spec(algorithm: str) -> SearchSpec:
    algorithm_settings = (
        {"kind": "nsga2", "population_size": 4, "generations": 1, "seed": 1234}
        if algorithm == "nsga2" else
        {"kind": "ehvi", "initial_population_size": 4, "iteration_budget": 1,
         "candidate_pool_size": 8, "seed": 1234}
    )
    return SearchSpec.model_validate({
        "name": "recovery", "base_hull": {"beam_oa_m": 0.6},
        "search_space": {"beam_wl_m": {"kind": "uniform", "min": 0.48, "max": 0.54}},
        "algorithm": algorithm_settings,
        "budget": {"max_evaluations": 50},
        "objectives": [{"metric": "displaced_mass_kg", "direction": "min"}],
    })


@pytest.mark.parametrize("algorithm", ["nsga2", "ehvi"])
def test_active_resume_restores_missing_record_and_evaluation(tmp_path: Path, algorithm: str) -> None:
    spec_path = tmp_path / "input.json"
    spec_path.write_text(search_spec(algorithm).model_dump_json())
    out = tmp_path / "run"
    first = run_search(spec_path, out)
    persisted = SearchRunRecord.model_validate_json((out / "run.json").read_bytes())
    record = next(r for r in persisted.candidates if r.status == "complete")
    paths = [out / record.artifacts["evaluation"], out / "candidates" / f"{record.candidate_key}.record.json"]
    originals = [path.read_bytes() for path in paths]
    for path in paths:
        path.unlink()
    resumed = run_search(spec_path, out, resume=True)
    assert [path.read_bytes() for path in paths] == originals
    assert resumed.final_frontier_keys == first.final_frontier_keys


@pytest.mark.parametrize("algorithm", ["nsga2", "ehvi"])
@pytest.mark.parametrize("damage", ["missing_all", "corrupt"])
def test_active_resume_refuses_unverifiable_evaluation(tmp_path: Path, algorithm: str, damage: str) -> None:
    spec_path = tmp_path / "input.json"
    spec_path.write_text(search_spec(algorithm).model_dump_json())
    out = tmp_path / "run"
    run_search(spec_path, out)
    persisted = SearchRunRecord.model_validate_json((out / "run.json").read_bytes())
    record = next(r for r in persisted.candidates if r.status == "complete")
    relative = record.artifacts["evaluation"]
    if damage == "missing_all":
        store = FilesystemArtifactStore(out)
        ref = store.ref_for_relative_path(relative)
        (out / relative).unlink()
        for blob in store.store_dir.glob(ref.artifact_hash + ".*"):
            blob.unlink()
    else:
        (out / relative).write_text("corrupt")
    before = (out / "run.json").read_bytes()
    with pytest.raises(RuntimeError, match="reuse unavailable"):
        run_search(spec_path, out, resume=True)
    assert (out / "run.json").read_bytes() == before


@pytest.mark.parametrize("algorithm", ["nsga2", "ehvi"])
def test_active_resume_preserves_unknown_legacy_namespace(tmp_path: Path, algorithm: str) -> None:
    spec_path = tmp_path / "input.json"
    spec_path.write_text(search_spec(algorithm).model_dump_json())
    out = tmp_path / "run"
    out.mkdir()
    originals = {"run.json": b'{"old-run":true}', "spec.json": b'{"old-spec":true}'}
    for name, data in originals.items():
        (out / name).write_bytes(data)
    with pytest.raises(RuntimeError, match="legacy run provenance is unknown"):
        run_search(spec_path, out, resume=True)
    assert {name: (out / name).read_bytes() for name in originals} == originals
