"""RFC 0058 stage 2: CFD-in-loop evaluator graduation status."""

from __future__ import annotations

from types import SimpleNamespace

from kayakgen.eval.stability.accepted_fit import HullFamilyScope
from kayakgen.services.generative_jobs import cfd_in_loop_evaluator_status


def _scope(
    hull_class: str = "sea kayak",
    design_hash_envelope: list[str] | None = None,
) -> HullFamilyScope:
    return HullFamilyScope(
        hull_class=hull_class,
        design_hash_envelope=design_hash_envelope or ["design-hash-001"],
    )


def _record(
    kind: str,
    *,
    acceptance_verdict: str = "accepted",
    hull_family_scope: HullFamilyScope | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        kind=kind,
        acceptance_verdict=acceptance_verdict,
        hull_family_scope=hull_family_scope or _scope(),
    )


def test_empty_registry_defaults_to_opt_in_only() -> None:
    assert (
        cfd_in_loop_evaluator_status(registry=(), hull_scope=_scope())
        == "opt_in_only"
    )


def test_analytical_only_registry_stays_opt_in_only() -> None:
    registry = [_record("analytical")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_cfd_in_loop_only_registry_stays_opt_in_only() -> None:
    registry = [_record("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_both_accepted_covering_fits_promote_to_first_class() -> None:
    registry = [_record("analytical"), _record("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "first_class"
    )


def test_non_covering_fit_does_not_promote() -> None:
    registry = [
        _record("analytical"),
        _record(
            "cfd_in_loop",
            hull_family_scope=_scope(design_hash_envelope=["other-design-hash"]),
        ),
    ]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_rejected_fit_does_not_promote() -> None:
    registry = [
        _record("analytical"),
        _record("cfd_in_loop", acceptance_verdict="rejected"),
    ]

    assert (
        cfd_in_loop_evaluator_status(registry=registry, hull_scope=_scope())
        == "opt_in_only"
    )


def test_persistent_opt_out_wins_over_graduation() -> None:
    registry = [_record("analytical"), _record("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(
            registry=registry,
            hull_scope=_scope(),
            persistent_opt_in=False,
        )
        == "opt_in_only"
    )


def test_persistent_opt_in_does_not_block_graduation() -> None:
    registry = [_record("analytical"), _record("cfd_in_loop")]

    assert (
        cfd_in_loop_evaluator_status(
            registry=registry,
            hull_scope=_scope(),
            persistent_opt_in=True,
        )
        == "first_class"
    )
