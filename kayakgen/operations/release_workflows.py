"""Actual installed analytical/report and builder workflows for release acceptance."""
from __future__ import annotations

from contextlib import ExitStack
import csv
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from kayakgen.operations.release_manifest import file_sha256, require, write_json


REPORT_GUARDS = {
    'kayakgen.services.design_report': ('evaluate_hydrostatics', 'resistance_curve',
        'evaluate_equilibrium_stability', 'evaluate_initial_stability', 'diagnose_mesh',
        'build_high_angle_gz_block', 'build_comparison_report'),
    'kayakgen.eval.hydrostatics': ('evaluate',),
    'kayakgen.eval.mesh_diagnostics': ('diagnose_mesh',),
    'kayakgen.eval.numerical_resistance': ('assess_resistance',),
    'kayakgen.eval.michell_quadrature': ('wave_from_grid', 'integrate_linear_depth'),
    'kayakgen.eval.resistance': ('resistance_curve', 'evaluate_resistance',
        'wave_resistance_michell', 'wetted_surface'),
    'kayakgen.eval.stability': ('evaluate_equilibrium_stability', 'evaluate_initial_stability'),
    'kayakgen.eval.immersed_geometry': ('evaluate_immersed',),
    'kayakgen.eval.stability.operating_equilibrium': ('evaluate_fixed_body_equilibrium',),
    'kayakgen.services.evaluation': ('evaluate_with_context',),
}


def generated_control(out: Path) -> tuple[Path, Path]:
    from kayakgen.eval.contract import EvaluationContext
    from kayakgen.model.hull import Hull
    def polynomial(*coefficients):
        return {'kind': 'polynomial', 'coefficients': coefficients}

    # Smooth generated geometry avoids the legacy control's sharp box transitions.
    hull = Hull(name='release-verification-generated-smoke-control', length_m=5.,
        beam_oa_m=.52, draft_m=.12, geometry_kind='distribution_v2', distribution_v2={
            'waterline_half_breadth': polynomial(.26, 0., -.26),
            'draft_profile': polynomial(.12, 0., -.06),
            'section_area_curve': polynomial(.049, 0., -.0735, 0., .0245),
            'deck_freeboard': polynomial(.2), 'rocker': polynomial(0.)})
    # This declared smoke budget is not an application default or physical accuracy claim.
    context = EvaluationContext.for_hull(
        hull, equilibrium=True, equilibrium_tolerance_kg=.01, hydrostatic_stations=150,
        speeds_knots=(5.,), n_stations=400, n_depths=25, n_theta=40,
        numerical_relative_tolerance=.01,
    )
    hull_path, context_path = out / 'control-hull.json', out / 'control-context.json'
    hull_path.write_text(hull.model_dump_json(indent=2))
    context_path.write_text(context.model_dump_json(indent=2))
    return hull_path, context_path


def verify_realized_context(requested, realized) -> None:
    solved_fields = {'sinkage_m', 'trim_angle_deg'} if requested.equilibrium else set()
    require(requested.model_dump(mode='json', exclude=solved_fields)
            == realized.model_dump(mode='json', exclude=solved_fields),
            'Realized evaluation changed requested settings beyond the solved operating pose')


def verify_evaluation(hull, requested, evaluated) -> None:
    require(evaluated.context is not None and evaluated.hull_hash == hull.record_hash(),
            'Evaluation source identity is missing or differs')
    verify_realized_context(requested, evaluated.context)
    require(evaluated.resistance.V_knots == list(requested.speeds_knots),
            'Evaluation changed the exact requested speed grid')
    constants = evaluated.resistance.metadata.constants
    require(constants['seawater_density_kg_m3'] == requested.load_case.seawater_density_kg_m3,
            'Evaluation changed the requested density')
    require(constants['seawater_kinematic_viscosity_m2_s'] == requested.kinematic_viscosity_m2_s,
            'Evaluation changed the requested viscosity')
    if requested.equilibrium:
        require(evaluated.stability.status == 'converged', 'Requested equilibrium did not converge')
        error = abs(evaluated.hydrostatics.displaced_mass_kg - requested.load_case.total_mass_kg)
        require(error <= requested.equilibrium_tolerance_kg, 'Hydrostatics do not match target load')
    if requested.numerical_relative_tolerance is not None:
        require(evaluated.resistance.metadata.numerical_quality.status == 'converged',
                'Declared numerical budget was not met; raw diagnostics are not acceptance')
    metadata = evaluated.resistance.metadata
    require(metadata.claim_state == 'uncalibrated_comparative'
            and metadata.accepted_uses == ['comparative_filter'] and metadata.model_version is None,
            'Analytical physical claim ceiling changed')


def verify_selected_report(out: Path, hull, evaluation, source: Path) -> dict:
    import kayakgen.services.design_report as reports
    calls = []
    modules = {name: importlib.import_module(name) for name in REPORT_GUARDS}

    def forbidden(name):
        def fail(*args, **kwargs):
            calls.append(name)
            raise RuntimeError('Selected report attempted evaluator execution: ' + name)
        return fail

    with ExitStack() as stack:
        for module_name, names in REPORT_GUARDS.items():
            for name in names:
                stack.enter_context(patch.object(modules[module_name], name,
                                                side_effect=forbidden(module_name + '.' + name)))
        rendered = reports.render_design_report(
            hull, html_out=out / 'report.html', hull_source_path=source, evaluation=evaluation)
    require(not calls, 'Selected report called a numerical evaluator')
    text = rendered.html_path.read_text()
    require(evaluation.context_hash in text and hull.record_hash() in text,
            'Report omitted selected evaluation identity')
    return {'report_sha256': file_sha256(rendered.html_path), 'report_recompute_calls': calls,
            'guarded_evaluators': [module + '.' + name for module, names in REPORT_GUARDS.items()
                                   for name in names],
            'forbidden_copy_clean': rendered.forbidden_copy_clean}


def analytical_workflow(out: Path, inputs: dict) -> tuple[dict, object, Path]:
    from kayakgen.eval.contract import EvaluationContext, EvaluationResult
    from kayakgen.io.json import load_hull, save_evaluation
    from kayakgen.services.evaluation import evaluate_with_context
    out.mkdir()
    if inputs['hull'] is None:
        source, context_path = generated_control(out)
        origin = 'generated smoke control with explicitly declared 1% numerical budget'
    else:
        source, context_path = Path(inputs['hull']), Path(inputs['context'])
        origin = 'supplied hull and evaluation context'
    hull = load_hull(source)
    requested = EvaluationContext.model_validate_json(context_path.read_text())
    original = hull.model_dump_json()
    evaluated = evaluate_with_context(hull, requested)
    evaluated_path = out / 'evaluation.json'
    save_evaluation(evaluated, evaluated_path)
    require(hull.model_dump_json() == original, 'Evaluation mutated the physical Hull record')
    verify_evaluation(hull, requested, evaluated)
    loaded = EvaluationResult.model_validate_json(evaluated_path.read_text())
    require(loaded.model_dump(mode='json') == evaluated.model_dump(mode='json'),
            'Persist/reload changed the selected evaluation')
    record = {'input_kind': origin, 'hull_record_hash': hull.record_hash(),
              'context_hash': loaded.context_hash, 'requested_context': requested.model_dump(mode='json'),
              'realized_context': loaded.context.model_dump(mode='json'),
              'displaced_mass_kg': loaded.hydrostatics.displaced_mass_kg,
              'numerical_quality': loaded.resistance.metadata.numerical_quality.model_dump(mode='json'),
              'evaluation_sha256': file_sha256(evaluated_path),
              **verify_selected_report(out, hull, loaded, source)}
    write_json(out / 'analytical-workflow.json', record)
    return record, hull, source


def cli_command(out: Path, label: str, arguments: list[str], *, success: bool = True) -> dict:
    command = [sys.executable, '-I', '-B', '-c', 'from kayakgen.cli.main import app; app()', *arguments]
    completed = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=90)
    (out / (label + '.stdout.txt')).write_text(completed.stdout)
    (out / (label + '.stderr.txt')).write_text(completed.stderr)
    require((completed.returncode == 0) == success,
            f'{label} unexpected exit {completed.returncode}; inspect {label}.stderr.txt')
    return {'argv': command, 'returncode': completed.returncode}


def surface_exports(out: Path, hull, source: Path) -> dict:
    import numpy as np
    from stl import mesh as stl_mesh
    command = cli_command(out, 'generate', ['generate', str(source), '--stl-out', str(out / 'surface')])
    surfaces = {}
    for part in ('hull', 'deck'):
        path = out / f'surface_{part}.stl'
        header = path.read_bytes()[:80].decode('ascii').rstrip()
        require(header == f'sha256:{hull.record_hash()} m {part}', 'STL source/units header differs')
        mesh = stl_mesh.Mesh.from_file(str(path))
        vertices, faces = hull.to_geometry().mesh(part)
        np.testing.assert_allclose(mesh.vectors, vertices[faces], rtol=1e-6, atol=1e-7)
        require(math.isclose(float(np.ptp(mesh.x)), hull.length_m, rel_tol=1e-6),
                'STL metre span differs')
        require(float(mesh.x.min()) < 0 < float(mesh.x.max()), 'STL longitudinal frame differs')
        surfaces[part] = {'sha256': file_sha256(path), 'header': header,
                          'triangles': len(mesh.vectors), 'semantics': 'open inspection surface'}
    return {'command': command, 'surfaces': surfaces}


def builder_exports(out: Path, hull, source: Path) -> dict:
    import ezdxf
    import numpy as np
    bundle = out / 'builder'
    commands = [cli_command(out, 'builder', ['build-export', str(source), '--out', str(bundle),
                                           '--n-stations', '5'])]
    manifest = json.loads((bundle / 'manifest.json').read_text())
    require(manifest['hull_sha256'] == hull.record_hash(), 'Builder source identity differs')
    for entry in manifest['artifacts']:
        path = (bundle / entry['path']).resolve()
        require(path.is_relative_to(bundle.resolve()), 'Builder artifact escapes output')
        require(file_sha256(path) == entry['sha256'], 'Builder artifact hash differs')
    with (bundle / 'offsets.csv').open() as stream:
        rows = list(csv.DictReader(line for line in stream if not line.startswith('#')))
    document = ezdxf.readfile(bundle / 'sections.dxf')
    require(document.header['$INSUNITS'] == 4, 'DXF millimetre unit flag differs')
    sections = list(document.modelspace().query('LWPOLYLINE'))
    require(len(rows) == len(sections) == 5, 'Builder section count differs')
    for x, row, section in zip(np.linspace(-hull.length_m / 2, hull.length_m / 2, 5),
                               rows, sections, strict=True):
        require(math.isclose(float(row['X']), float(x), abs_tol=1e-9), 'CSV metre frame differs')
        yz = np.array(list(section.get_points('xy'))) / 1000.
        np.testing.assert_allclose(yz, hull.to_geometry().section_for_closed_body(float(row['X']), 'hull'),
                                   atol=1e-9)
    before = {p.name: file_sha256(p) for p in bundle.iterdir() if p.is_file()}
    commands.append(cli_command(out, 'builder-repeat', ['build-export', str(source),
                                                      '--out', str(bundle)], success=False))
    require(before == {p.name: file_sha256(p) for p in bundle.iterdir() if p.is_file()},
            'Refused builder repeat changed the prior bundle')
    return {'commands': commands, 'manifest': manifest, 'repeat_refused_unchanged': True}
