"""Wired-default coverage for the high-angle GZ evaluator.

The :func:`evaluate_gz_curve` call site now sources
``GeneratedBodyGZCurve.result_semantics`` via
:func:`resolve_analytical_claim_label` (RFC 0058 stage 2 / workflow 0056 D-13)
instead of relying on the field's default. With an empty registry the
resolver returns ``unvalidated_hydrostatic_comparison``, so the wired path
must remain byte-stable against the pre-wiring default.
"""

from __future__ import annotations

from kayakgen.eval.closed_volume import (
    diagnose_closed_volume_body,
    generated_hull_plus_deck_body,
)
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.stability import (
    GeneratedBodyGZCurve,
    evaluate_gz_curve,
)
from kayakgen.model.hull import Hull


def test_generated_body_result_semantics_resolved_via_empty_registry() -> None:
    hull = Hull(name="wired-default", bow_rake=0.0, stern_rake=0.0)
    body = generated_hull_plus_deck_body(hull, stations=6)
    diagnostics = diagnose_closed_volume_body(body)

    result = evaluate_gz_curve(
        hull,
        LoadCase(),
        heel_grid_deg=[0.0, 5.0, 10.0],
        body_ref=body,
        body_diagnostics=diagnostics,
    )

    assert isinstance(result, GeneratedBodyGZCurve)
    assert result.status == "computed"
    # The resolver is wired at the construction site with fit_registry=();
    # the default literal must be byte-stable against the pre-wiring path.
    assert result.result_semantics == "unvalidated_hydrostatic_comparison"
