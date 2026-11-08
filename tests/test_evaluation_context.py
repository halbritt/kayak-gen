"""Evaluation context preserves actual load, fluid and numerical inputs."""
import pytest
from pydantic import ValidationError
from kayakgen.eval.contract import EvaluationContext, LoadCase
from kayakgen.model.hull import Hull
from kayakgen.services.evaluation import evaluate_with_context


def test_context_deeply_snapshots_mutable_component_inputs():
    load = LoadCase(components=[{'name': 'paddler', 'mass_kg': 90, 'x_m': 0, 'kg_above_keel_m': .25}])
    context = EvaluationContext.for_hull(Hull(), load_case=load, input_origin='supplied')
    fingerprint = context.fingerprint()
    load.components[0].mass_kg = 100
    assert context.load_case.total_mass_kg == 90
    assert context.fingerprint() == fingerprint
    assert 'components.0.mass_kg' in context.load_supplied_fields
    assert 'hull_mass_kg' not in context.load_supplied_fields
    with pytest.raises(ValidationError):
        context.load_case.components[0].mass_kg = 110


def test_evaluation_receives_fluid_and_resolution_not_just_metadata():
    hull = Hull()
    results = []
    for density in [997, 1025]:
        context = EvaluationContext.for_hull(hull, load_case=LoadCase(paddler_mass_kg=80, seawater_density_kg_m3=density), input_origin='supplied', speeds_knots=(3.2, 4.1), n_stations=80, n_depths=12, n_theta=20)
        results.append(evaluate_with_context(hull, context))
    fresh, sea = results
    assert sea.hydrostatics.displaced_mass_kg / fresh.hydrostatics.displaced_mass_kg == pytest.approx(1025/997)
    assert sea.resistance.Rv_N[0] / fresh.resistance.Rv_N[0] == pytest.approx(1025/997)
    assert fresh.resistance.V_knots == [3.2, 4.1]
    assert fresh.resistance.metadata.quadrature == {'n_stations': 80, 'n_depths': 12, 'n_theta': 20}
    assert sea.context_hash != fresh.context_hash
    assert sea.hull_hash == fresh.hull_hash
    assert fresh.context.load_case.total_mass_kg == 98


def test_saved_result_report_does_not_recompute_numerical_evaluators(tmp_path, monkeypatch):
    from kayakgen.services import design_report
    hull = Hull()
    context = EvaluationContext.for_hull(hull, load_case=LoadCase(paddler_mass_kg=81.6466266, cargo_mass_kg=15.87573295, hull_mass_kg=18.1436948), input_origin='supplied', speeds_knots=(3.2,), n_stations=40, n_depths=8, n_theta=12)
    result = evaluate_with_context(hull, context)
    def forbidden(*args, **kwargs):
        raise AssertionError('report recomputed a numerical evaluator')
    for name in ['evaluate_hydrostatics', 'resistance_curve', 'evaluate_initial_stability', 'evaluate_equilibrium_stability', '_safe_high_angle']:
        monkeypatch.setattr(design_report, name, forbidden)
    path = tmp_path / 'report.html'
    design_report.render_design_report(hull, evaluation=result, html_out=path)
    text = path.read_text()
    assert '115.666' in text
    assert result.context_hash in text
    assert '3.20' in text


def test_report_rejects_mismatched_hull_before_output(tmp_path):
    from kayakgen.services.design_report import render_design_report
    hull = Hull()
    result = evaluate_with_context(hull, EvaluationContext.for_hull(hull), include_resistance=False)
    out = tmp_path / 'bad.html'
    with pytest.raises(ValueError, match='match'):
        render_design_report(hull.model_copy(update={'length_m': 5.0}), evaluation=result, html_out=out)
    assert not out.exists()


def test_web_evaluation_adapter_retains_exact_supplied_context():
    from kayakgen.services.evaluation import evaluation_payload
    hull = Hull()
    context = EvaluationContext.for_hull(hull, input_origin='supplied',
        load_case=LoadCase(paddler_mass_kg=83, seawater_density_kg_m3=997),
        speeds_knots=(3.2,), n_stations=60, n_depths=10, n_theta=14)
    payload = evaluation_payload({**hull.model_dump(mode='json'),
                                  'evaluation_context': context.model_dump(mode='json')})
    assert payload['context_hash'] == context.fingerprint()
    assert payload['stability']['load_mass_kg'] == 101
    assert payload['resistance']['metadata']['constants']['seawater_density_kg_m3'] == 997


def test_evaluate_cli_context_and_report_cli_share_saved_result(tmp_path):
    from typer.testing import CliRunner
    from kayakgen.cli.main import app
    from kayakgen.eval.contract import EvaluationResult
    hull = Hull()
    context = EvaluationContext.for_hull(hull, input_origin='supplied',
        load_case=LoadCase(paddler_mass_kg=95, cargo_mass_kg=5),
        speeds_knots=(3.2,), n_stations=40, n_depths=8, n_theta=12)
    h = tmp_path/'hull.json'
    h.write_text(hull.model_dump_json())
    c = tmp_path/'context.json'
    c.write_text(context.model_dump_json())
    e = tmp_path/'eval.json'
    out = tmp_path/'report.html'
    cli = CliRunner()
    evaluated = cli.invoke(app, ['evaluate',str(h),'--context',str(c),'--out',str(e)])
    assert evaluated.exit_code == 0, evaluated.output
    saved = EvaluationResult.model_validate_json(e.read_text())
    assert saved.context_hash == context.fingerprint()
    rendered = cli.invoke(app, ['design-report',str(h),'--evaluation',str(e),'--out',str(out)])
    assert rendered.exit_code == 0, rendered.output
    assert context.fingerprint() in out.read_text()
    assert '118.000000000' in out.read_text()


@pytest.mark.parametrize('mass,density', [(90,997), (115.66605435,1025)])
def test_real_v2_load_and_fluid_share_one_operating_pose(mass,density):
    from pathlib import Path
    from kayakgen.eval.hydrostatics import evaluate
    from kayakgen.model.operating_state import OperatingPose
    hull = Hull.model_validate_json((Path(__file__).parent/'fixtures/hulls/needle18-v2.json').read_text())
    physical = hull.model_dump_json()
    context = EvaluationContext.for_hull(hull, input_origin='supplied', equilibrium=True,
        load_case=LoadCase(paddler_mass_kg=mass-18, hull_mass_kg=18,
                           seawater_density_kg_m3=density),
        speeds_knots=(4.5,), n_stations=60, n_depths=12, n_theta=20)
    result = evaluate_with_context(hull, context)
    assert hull.model_dump_json() == physical
    assert result.stability.status == 'converged'
    assert abs(result.hydrostatics.displaced_mass_kg-mass) < 1.0
    pose = OperatingPose(result.context.sinkage_m, result.context.trim_angle_deg)
    direct_hydro = evaluate(hull,stations=60,pose=pose,density_kg_m3=density)
    assert result.hydrostatics == direct_hydro
    assert result.resistance.metadata.constants['seawater_density_kg_m3'] == density


@pytest.mark.parametrize('mass,density,grid', [(90,997,(40,8,12)), (115.66605435,1025,(60,12,20))])
def test_web_and_desktop_adapters_use_explicit_values(mass, density, grid):
    from types import SimpleNamespace
    from kayakgen.services.evaluation import analysis_view_model
    from kayakgen.ui.desktop import KayakGUI
    from kayakgen.ui.web.handlers import HandlersMixin
    from kayakgen.ui.web.state import state_dict_from_hull
    hull = Hull()
    context = EvaluationContext.for_hull(
        hull, input_origin='supplied',
        load_case=LoadCase(paddler_mass_kg=mass-18, hull_mass_kg=18,
                           seawater_density_kg_m3=density),
        speeds_knots=(3.2,), n_stations=grid[0], n_depths=grid[1], n_theta=grid[2],
    )
    state = {**state_dict_from_hull(hull), 'evaluation_context': context.model_dump(mode='json'),
             'target_speed_kt': 3.2}
    expected = evaluate_with_context(hull, context)
    view = analysis_view_model(state)
    assert view['resistance_rows'][0]['Rt_N'] == expected.resistance.Rt_N[0]
    class Web(HandlersMixin):
        pass
    web = Web()
    web.state = SimpleNamespace(**state)
    web._refresh_analysis()
    assert web.state.evaluation_context_hash == expected.context_hash
    assert web.state.evaluation_result['stability']['load_mass_kg'] == mass
    assert web.state.resistance_table_rows[0]['Rt_N'] == expected.resistance.Rt_N[0]
    gui = object.__new__(KayakGUI)
    gui._hull_from_params = lambda: hull
    gui._active_class_name = 'custom'
    gui.params = {'target_speed_kt': 3.2}
    gui.metrics_text = SimpleNamespace(set_text=lambda text: setattr(gui, 'metrics_output', text))
    gui.set_evaluation_context(context)
    assert gui.last_evaluation.context_hash == expected.context_hash
    assert gui.last_evaluation.resistance == expected.resistance
    assert gui.last_evaluation.hydrostatics == expected.hydrostatics
    assert 'supplied' in gui.metrics_output


def test_malformed_cli_context_refuses_without_output(tmp_path):
    from typer.testing import CliRunner
    from kayakgen.cli.main import app
    hull_path = tmp_path/'hull.json'
    hull_path.write_text(Hull().model_dump_json())
    context_path = tmp_path/'bad.json'
    context_path.write_text('{bad json')
    output = tmp_path/'bad.eval.json'
    result = CliRunner().invoke(app, ['evaluate',str(hull_path),'--context',str(context_path),'--out',str(output)])
    assert result.exit_code == 1
    assert 'evaluation input failed' in result.output
    assert not output.exists()


@pytest.mark.parametrize('part', ['speed', 'grid', 'fluid'])
def test_persisted_result_refuses_inconsistent_context(part):
    from kayakgen.eval.contract import EvaluationResult
    hull = Hull()
    context = EvaluationContext.for_hull(hull, speeds_knots=(3.2,),
                                        n_stations=40, n_depths=8, n_theta=12)
    result = evaluate_with_context(hull, context).model_dump(mode='json')
    if part == 'speed':
        result['resistance']['V_knots'] = [4.2]
    elif part == 'grid':
        result['resistance']['metadata']['quadrature']['n_stations'] = 80
    else:
        result['resistance']['metadata']['constants']['seawater_density_kg_m3'] = 997
    with pytest.raises(ValueError, match='match evaluation context'):
        EvaluationResult.model_validate(result)


def test_explicit_load_origin_and_target_draft_preserve_components():
    from kayakgen.eval.contract import LongitudinalLoadComponent
    from kayakgen.services.evaluation import solve_target_draft
    hull = Hull()
    load = LoadCase(components=[LongitudinalLoadComponent(
        name='all', mass_kg=90, x_m=.1, kg_above_keel_m=.3)])
    assert EvaluationContext.for_hull(hull, load_case=load).input_origin == 'supplied'
    result = solve_target_draft(hull, load)
    assert result.load_case == load
    assert result.load_mass_kg == 90
    assert abs(result.displaced_mass_kg-90) <= result.equilibrium_tolerance_kg
    assert 'trim_assumed_zero_no_moment_balance' in result.warnings


def test_fixed_pose_gm_applies_default_kg_once_and_renders_unavailable():
    from pathlib import Path
    from kayakgen.services.evaluation import hydrostatics_view_model
    hull = Hull.model_validate_json((Path(__file__).parent/'fixtures/hulls/needle18-v2.json').read_text())
    result = evaluate_with_context(hull, EvaluationContext.for_hull(hull), include_resistance=False)
    assert result.stability.initial_GM0_m == pytest.approx(result.hydrostatics.GM0_m)
    submerged = evaluate_with_context(hull, EvaluationContext.for_hull(hull, sinkage_m=1),
                                      include_resistance=False)
    assert submerged.hydrostatics.GM0_m is None
    model = hydrostatics_view_model(hull, hydro=submerged.hydrostatics)
    assert any(row[1] == 'unavailable' for row in model['hydro_rows'])


def test_equilibrium_and_saved_hydro_use_the_requested_mesh_resolution():
    from pathlib import Path
    hull = Hull.model_validate_json((Path(__file__).parent/'fixtures/hulls/needle18-v2.json').read_text())
    context = EvaluationContext.for_hull(hull,
        load_case=LoadCase(paddler_mass_kg=72, hull_mass_kg=18),
        equilibrium=True, hydrostatic_stations=3, equilibrium_tolerance_kg=.001)
    result = evaluate_with_context(hull, context, include_resistance=False)
    assert result.context.hydrostatic_stations == 3
    assert result.stability.status == 'converged'
    assert result.hydrostatics.displaced_mass_kg == result.stability.displaced_mass_kg
    assert abs(result.hydrostatics.displaced_mass_kg-90) <= .001


def test_sweep_density_override_retains_actual_supplied_field_origin(tmp_path):
    from kayakgen.search.sweep import SweepSpec, run_sweep
    from kayakgen.eval.contract import EvaluationResult
    spec = SweepSpec.model_validate({
        'base_hull': Hull().model_dump(mode='json'),
        'variables': {'Cp': {'kind': 'values', 'values': [.55]}},
        'evaluators': {'resistance': False, 'water_density_kg_m3': 997},
    })
    run_sweep(spec, tmp_path/'sweep')
    path = next((tmp_path/'sweep/candidates').glob('*.eval.json'))
    result = EvaluationResult.model_validate_json(path.read_text())
    assert result.context.input_origin == 'supplied'
    assert result.context.load_supplied_fields == ('seawater_density_kg_m3',)
    assert result.context.load_case.seawater_density_kg_m3 == 997


def test_persisted_stability_load_must_match_immutable_context():
    from kayakgen.eval.contract import EvaluationResult
    hull = Hull()
    result = evaluate_with_context(hull, EvaluationContext.for_hull(hull),
                                   include_resistance=False).model_dump(mode='json')
    result['stability']['load_case']['paddler_mass_kg'] = 100
    with pytest.raises(ValueError, match='stability load does not match'):
        EvaluationResult.model_validate(result)
