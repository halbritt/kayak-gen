"""RFC 0058 stage 2: CFD-in-loop evaluator graduation status.

D049 (workflow 0064, closes BUG-001): every graduation-semantics test below
exercises ``cfd_in_loop_evaluator_status`` with REAL ``StabilityFitRecord``
instances built by the shared conftest factory. The previous suite fed
``SimpleNamespace(kind=...)`` fakes while the production record had no
``kind`` field at all, so the ``first_class`` branch was unreachable with
real records and the suite stayed green (audit R1). Exactly one clearly
labeled shape-tolerance test keeps a SimpleNamespace fake.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Literal

from kayakgen.eval.stability.accepted_fit import (
    HullFamilyScope,
    StabilityFitRecord,
)
from kayakgen.services.generative_jobs import cfd_in_loop_evaluator_status

from tests.conftest import make_stability_acceptance_triple


def _scope(design_hash_envelope: list[str] | None = None) -> HullFamilyScope:
    return HullFamilyScope(
        hull_class="sea_kayak",
        design_hash_envelope=design_hash_envelope or ["deadbeef"],
    )


def _fit(
    kind: Literal["analytical", "cfd_in_loop"],
    *,
    design_hash: str = "deadbeef",
) -> StabilityFitRecord:
    """Real production fit record via the shared acceptance-triple factory."""

    return make_stability_acceptance_triple(
        kind=kind,
        design_hash=design_hash,
        fit_id=f"fit-{kind}",
        fixture_id=f"fxt-{kind}",
    ).fit


def _rejected_fit(
    kind: Literal["analytical", "cfd_in_loop"],
) -> StabilityFitRecord:
    """Real rejected record, re-validated through the production model."""

    return StabilityFitRecord.model_validate(
        _fit(kind).model_dump()
        | {
            "acceptance_verdict": "rejected",
            "accepted_at": None,
            "rejection_reasons": ["rejected_for_graduation_test"],
        }
    )


def test_kind_is_additive_legacy_fit_json_parses_as_analytical() -> None:
    """D049 additive guarantee: pre-kind fit JSON parses with the default."""

    legacy = make_stability_acceptance_triple().fit.model_dump(mode="json")
    legacy.pop("kind")

    parsed = StabilityFitRecord.model_validate(legacy)

    assert parsed.kind == "analytical"


def test_empty_registry_defaults_to_opt_in_only() -> None:
    assert (
        cfd_in_loop_evaluator_status(registry=(), hull_scope=_scope())
        == "opt_in_only"
    )


def test_analytical_only_registry_stays_opt_in_only() -> None:
    registry = [_fit("analytical")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_cfd_in_loop_only_registry_stays_opt_in_only() -> None:
    registry = [_fit("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_both_accepted_covering_fits_promote_to_first_class() -> None:
    registry = [_fit("analytical"), _fit("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "first_class"
    )


def test_non_covering_fit_does_not_promote() -> None:
    registry = [
        _fit("analytical"),
        _fit("cfd_in_loop", design_hash="0ther-design-hash"),
    ]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_rejected_fit_does_not_promote() -> None:
    registry = [_fit("analytical"), _rejected_fit("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_persistent_opt_out_wins_over_graduation() -> None:
    registry = [_fit("analytical"), _fit("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(
            registry=registry,
            hull_scope=_scope(),
            persistent_opt_in=False,
        )
        == "opt_in_only"
    )


def test_persistent_opt_in_does_not_block_graduation() -> None:
    registry = [_fit("analytical"), _fit("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(
            registry=registry,
            hull_scope=_scope(),
            persistent_opt_in=True,
        )
        == "first_class"
    )


def test_structural_registry_tolerates_duck_typed_records() -> None:
    """SHAPE-TOLERANCE: intentionally the only SimpleNamespace fake left.

    The status helper reads records structurally (``getattr``), so a
    duck-typed record carrying ``kind`` / ``acceptance_verdict`` /
    ``hull_family_scope`` still counts. Graduation semantics are pinned by
    the real-record tests above; this only pins the structural tolerance.
    """

    def fake(kind: str) -> SimpleNamespace:
        return SimpleNamespace(
            kind=kind,
            acceptance_verdict="accepted",
            hull_family_scope=_scope(),
        )

    registry = [fake("analytical"), fake("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "first_class"
    )
