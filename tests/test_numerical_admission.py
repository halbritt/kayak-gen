"""Numerical evidence is independent of exploratory physical-claim permission."""
import json

import pytest

from kayakgen.eval.contract import EvaluationResult, ResistanceCurve
from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.hull import Hull
from kayakgen.search.pareto import CandidatePoint, Objective, pareto_front


def test_finite_resistance_is_not_evidence_of_convergence():
    hull = Hull()
    curve = ResistanceCurve(V_knots=[4.5], Fn=[0.3], Rv_N=[20], Rw_N=[228223], Rt_N=[228243])
    joined = EvaluationResult(hull_hash=hull.hash(), hydrostatics=evaluate(hull), resistance=curve)
    assert next(flag for flag in joined.convergence if flag.stage == 'resistance').status == 'unknown'
    assert curve.metadata.numerical_quality.status == 'unknown'


def test_exploratory_point_without_numerical_evidence_cannot_join_frontier():
    point = CandidatePoint(id='diagnostic', metrics={'Rt_N_last': 228243}, provenance={})
    assert pareto_front([point], [Objective(metric='Rt_N_last', direction='min')]) == []


def test_legacy_converged_flag_does_not_supply_numerical_evidence():
    hull = Hull()
    curve = ResistanceCurve(V_knots=[4.5], Fn=[0.3], Rv_N=[20], Rw_N=[40], Rt_N=[60])
    original = EvaluationResult(hull_hash=hull.hash(), hydrostatics=evaluate(hull), resistance=curve)
    payload = original.model_dump(mode="json")
    payload['resistance']['metadata'].pop('numerical_quality')
    payload['convergence'] = [{'stage': 'resistance', 'status': 'converged', 'residual': None}]
    restored = EvaluationResult.model_validate(payload)
    assert restored.resistance.metadata.numerical_quality.status == 'unknown'


def test_comparison_retains_diagnostics_but_does_not_rank_unassessed_curve(tmp_path):
    from kayakgen.search.sweep import SweepSpec, run_sweep
    from kayakgen.search.compare import build_comparison_report
    spec = SweepSpec.model_validate({
        'name': 'numerical-check', 'base_hull': Hull().model_dump(mode='json'),
        'variables': {'Cp': {'kind': 'values', 'values': [0.55]}},
        'evaluators': {'resistance': True},
    })
    out = tmp_path / 'run'
    run_sweep(spec, out)
    report = build_comparison_report(out, objectives=[Objective(metric='Rt_N_last', direction='min')], explicit_exploratory=True)
    assert not report.pareto_front_keys
    assert report.candidate_summaries[0].metrics['Rt_N_last'] > 0
    assert any('numerical' in w for w in report.candidate_summaries[0].warnings)


@pytest.mark.parametrize('algorithm', [
    {'kind': 'nsga2', 'population_size': 2, 'generations': 1, 'seed': 1},
    {'kind': 'ehvi', 'initial_population_size': 2, 'iteration_budget': 1, 'seed': 1,
     'candidate_pool_size': 4},
])
def test_search_keeps_unassessed_resistance_out_of_final_frontier(tmp_path, algorithm):
    from kayakgen.search.active.runner import run_search
    spec = {
        'name': 'numerical-search', 'base_hull': Hull().model_dump(mode='json'),
        'search_space': {'beam_wl_m': {'kind': 'uniform', 'min': .46, 'max': .5}},
        'algorithm': algorithm,
        'objectives': [{'metric': 'Rt_N_last', 'direction': 'min'}],
        'objectives_explicit_exploratory': True,
        'evaluators': {'resistance': True}, 'budget': {'max_evaluations': 2},
    }
    path = tmp_path / 'search.json'
    path.write_text(json.dumps(spec))
    result = run_search(path, tmp_path / 'out')
    assert result.completed_count == 2
    assert not result.final_frontier_keys


def test_assessed_point_needs_complete_distinct_resolution_evidence():
    from pydantic import ValidationError
    from kayakgen.eval.contract import NumericalQuality
    evidence = {
        'status': 'converged', 'policy_version': 'test-policy-1', 'evidence': 'test-reference',
        'resolutions': [{'n': 100}, {'n': 200}, {'n': 400}],
        'relative_changes': [.001], 'relative_tolerance': .01,
    }
    quality = NumericalQuality.model_validate(evidence)
    point = CandidatePoint(id='assessed', metrics={'Rt_N_last': 60}, provenance={
        'Rt_N_last': {'numerical_quality': quality.model_dump(mode='json')},
    })
    # RFC0077: an asserted generic policy remains readable historical evidence;
    # current admission requires the supported, verified method-specific policy.
    assert quality.status == 'converged'
    assert pareto_front([point], [Objective(metric='Rt_N_last', direction='min')]) == []
    with pytest.raises(ValidationError, match='exceeds'):
        NumericalQuality.model_validate({**evidence, 'relative_changes': [.1]})
    with pytest.raises(ValidationError):
        NumericalQuality.model_validate({**evidence, 'relative_tolerance': float('inf')})
    with pytest.raises(ValidationError, match='distinct'):
        NumericalQuality.model_validate({**evidence, 'resolutions': [{'n': 100}]*3})


def test_supported_real_assessed_control_joins_frontier():
    from numerical_test_cases import assessed_curve
    curve = assessed_curve()
    point = CandidatePoint(id='measured-numerical-control', metrics={'Rt_N_last': curve.Rt_N[-1]},
                           provenance={'Rt_N_last': {'numerical_quality':
                               curve.metadata.numerical_quality.model_dump(mode='json')}})
    assert pareto_front([point], [Objective(metric='Rt_N_last', direction='min')])[0].id == point.id
