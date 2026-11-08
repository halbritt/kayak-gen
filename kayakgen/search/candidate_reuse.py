"""Admit cached candidate outcomes only with their recorded artifact bytes.

Synchronous restoration requires one writer per run directory. Managed jobs
satisfy that precondition through their separate ownership protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kayakgen.eval.contract import EvaluationResult
from kayakgen.model.hull import Hull
from kayakgen.services.artifact_store import ArtifactIntegrityError

if TYPE_CHECKING:
    from kayakgen.search.sweep import CandidateRecord
    from kayakgen.services.artifact_store import ArtifactKind, FilesystemArtifactStore


class CandidateReuseUnavailable(RuntimeError):
    """Required cached evidence cannot authorize reuse of a prior outcome."""


def load_reusable_candidate(store: "FilesystemArtifactStore", key: str) -> CandidateRecord | None:
    from kayakgen.search.sweep import CandidateRecord

    relative = f"candidates/{key}.record.json"
    ref = store.manifest.artifacts.get(relative)
    if ref is None and not (store.run_dir / relative).exists():
        return None
    try:
        ref = store.ref_for_relative_path(relative, kind="candidate_record", candidate_key=key)
        if ref is None:
            raise ValueError(f"unknown historical candidate provenance: {relative}")
        prior = CandidateRecord.model_validate_json(store.restore_artifact(ref))
        if prior.candidate_key != key:
            raise ValueError("candidate identity does not match its recorded occurrence")
        if prior.status in ("complete", "constraint_failed"):
            _verify_completed_artifacts(store, prior)
        return prior
    except (ArtifactIntegrityError, OSError, ValueError) as exc:
        raise CandidateReuseUnavailable(f"candidate reuse unavailable for {key}: {exc}") from exc


def _verify_completed_artifacts(store: "FilesystemArtifactStore", prior: CandidateRecord) -> None:
    kinds: dict[str, "ArtifactKind"] = {
        "hull": "hull_json", "evaluation": "eval_result_json", "mesh_diagnostics": "mesh_quality_json",
        "stl_hull": "hull_stl", "stl_deck": "deck_stl", "high_angle_gz": "high_angle_gz_artifact",
    }
    if not {"hull", "evaluation"}.issubset(prior.artifacts):
        raise ValueError("complete candidate lacks required hull/evaluation references")
    requested_artifacts = {
        "stl": {"stl_hull", "stl_deck"}, "mesh_diagnostics": {"mesh_diagnostics"},
        "high_angle_gz": {"high_angle_gz"},
    }
    for option, roles in requested_artifacts.items():
        if prior.evaluator_settings.get(option) and not roles.issubset(prior.artifacts):
            raise ValueError(f"complete candidate lacks requested {option} artifacts")
    described = {}
    if prior.stl_artifacts is not None:
        described.update(stl_hull=prior.stl_artifacts.hull, stl_deck=prior.stl_artifacts.deck)
    if prior.high_angle_gz_artifact is not None:
        described["high_angle_gz"] = prior.high_angle_gz_artifact
    for role, artifact in described.items():
        if prior.artifacts.get(role) != artifact.path:
            raise ValueError(f"required artifact paths disagree: {role}")
    verified = {}
    for role, relative in prior.artifacts.items():
        if role not in kinds:
            raise ValueError(f"unsupported required artifact role: {role}")
        ref = store.ref_for_relative_path(relative, kind=kinds[role], candidate_key=prior.candidate_key)
        if ref is None:
            raise ValueError(f"unknown historical artifact provenance: {relative}")
        verified[role] = store.restore_artifact(ref)
        if role in described and (ref.artifact_hash != described[role].sha256
                                  or len(verified[role]) != described[role].bytes):
            raise ValueError(f"required artifact metadata disagrees with recorded content: {role}")
    hull = Hull.model_validate_json(verified["hull"])
    evaluation = EvaluationResult.model_validate_json(verified["evaluation"])
    if hull.record_hash() != prior.hull_hash or evaluation.hull_hash != prior.hull_hash:
        raise ValueError("cached hull, evaluation and candidate identities disagree")


def load_finalized_candidates(store: "FilesystemArtifactStore") -> dict[str, "CandidateRecord"]:
    """Load the manifest's finalized outcomes, including missing canonical files.

    Unbound canonical records are included in the inventory so they fail closed
    instead of silently becoming new historical proof.
    """
    prefix, suffix = "candidates/", ".record.json"
    relatives = {path for path in store.manifest.artifacts
                 if path.startswith(prefix) and path.endswith(suffix)}
    relatives.update(str(path.relative_to(store.run_dir))
                     for path in (store.run_dir / "candidates").glob("*.record.json"))
    records = {}
    for relative in sorted(relatives):
        key = relative[len(prefix):-len(suffix)]
        record = load_reusable_candidate(store, key)
        if record is not None and record.status in ("complete", "failed", "constraint_failed"):
            records[key] = record
    return records
