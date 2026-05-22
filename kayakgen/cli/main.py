"""``kayakgen`` console script."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import typer

from kayakgen.cli.design_report_cli import design_report_command
from kayakgen.cli.high_angle_gz import build_high_angle_gz_block, parse_heel_grid_deg
from kayakgen.cli.migrate_geometry_cli import migrate_geometry_command
from kayakgen.cli.runs_cli import runs_app
from kayakgen.cli.sensitivity_cli import sensitivity_command
from kayakgen.cli.stability_cli import stability_app
from kayakgen.eval.contract import EvaluationResult
from kayakgen.eval.contract import LoadCase
from kayakgen.eval.hydrostatics import evaluate as evaluate_hydrostatics
from kayakgen.eval.resistance import resistance_curve
from kayakgen.eval.stability import evaluate_equilibrium_stability, evaluate_initial_stability
from kayakgen.eval.turning import evaluate_turning_metrics
from kayakgen.eval.mesh_package import (
    open_wetted_surface_profile,
    watertight_solid_profile,
    write_mesh_package,
)
from kayakgen.eval.cfd.jobs import (
    CFD_FIXTURE_RESULTS_WARNING,
    CFD_RAW_RESULTS_WARNING,
    CfdDispatchError,
    CfdRunRecord,
    load_cfd_run_record,
    prepare_cfd_job,
    run_cfd_job,
    solver_profile_names,
)
from kayakgen.io.json import load_hull, save_evaluation, save_hull
from kayakgen.io.stl import write_stl
from kayakgen.model.geometry import PartType
from kayakgen.model.hull import Hull
from kayakgen.model.validity import evaluate_design_validity
from kayakgen.search.compare import parse_objective, write_comparison_report

app = typer.Typer(no_args_is_help=True, add_completion=False, help="kayakgen pipeline CLI")
cfd_app = typer.Typer(no_args_is_help=True, help="Local CFD dispatch jobs")
app.add_typer(cfd_app, name="cfd")
calibration_app = typer.Typer(
    no_args_is_help=True,
    help="Calibration-campaign ingest, acceptance, and artifact writers (RFC 0054).",
)
app.add_typer(calibration_app, name="calibration")
app.add_typer(runs_app, name="runs")
app.add_typer(stability_app, name="stability")
app.command("sensitivity")(sensitivity_command)
app.command("design-report")(design_report_command)
app.command("migrate-geometry")(migrate_geometry_command)


@app.command()
def init(
    out: Path = typer.Argument(..., help="Where to write the default Hull JSON."),
) -> None:
    """Write a default-parameter Hull JSON to ``out``."""
    save_hull(Hull(), out)
    typer.echo(f"wrote {out}")


@app.command()
def generate(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    stl_out: Path | None = typer.Option(None, "--stl-out", help="Output prefix; writes <prefix>_hull.stl and <prefix>_deck.stl."),
) -> None:
    """Generate hull and deck STL files from a Hull JSON."""
    hull = load_hull(hull_path)
    prefix = stl_out if stl_out is not None else hull_path.with_suffix("")
    hull_path_out = prefix.with_name(prefix.name + "_hull.stl")
    deck_path_out = prefix.with_name(prefix.name + "_deck.stl")
    write_stl(hull, "hull", hull_path_out)
    write_stl(hull, "deck", deck_path_out)
    typer.echo(f"wrote {hull_path_out}")
    typer.echo(f"wrote {deck_path_out}")


@app.command()
def evaluate(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(None, "--out", help="Where to write the EvaluationResult JSON; default is <hull>.eval.json."),
    skip_resistance: bool = typer.Option(False, "--skip-resistance", help="Skip the Michell+ITTC sweep (faster)."),
    turning: bool = typer.Option(
        False,
        "--turning",
        help=(
            "Opt-in (RFC 0053): compute the TurningMetrics block and attach "
            "it to the EvaluationResult. Default output is unchanged."
        ),
    ),
    turning_heel_deg: float = typer.Option(
        8.0,
        "--turning-heel-deg",
        help="Heel angle (deg) for --turning; ignored without --turning.",
    ),
) -> None:
    """Run all available evaluators on a hull and write the EvaluationResult."""
    hull = load_hull(hull_path)
    hydrostatics = evaluate_hydrostatics(hull)
    resistance = None if skip_resistance else resistance_curve(hull)
    design_validity = evaluate_design_validity(
        hull,
        cp=hydrostatics.Cp_actual,
        displaced_mass_kg=hydrostatics.displaced_mass_kg,
        surface=("cli",),
    )
    turning_block = None
    if turning:
        try:
            turning_block = evaluate_turning_metrics(hull, heel_deg=turning_heel_deg)
        except ValueError as exc:
            typer.echo(f"evaluate --turning failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    result = EvaluationResult(
        hull_hash=hull.hash(),
        hydrostatics=hydrostatics,
        resistance=resistance,
        design_validity=design_validity,
        turning_metrics=turning_block,
    )
    out_path = out if out is not None else hull_path.with_suffix(".eval.json")
    save_evaluation(result, out_path)
    typer.echo(f"wrote {out_path}")
    if resistance is not None:
        typer.echo("Resistance is uncalibrated/comparative only; see metadata.")


@app.command("mesh-check")
def mesh_check(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(
        None,
        "--out",
        help="Where to write mesh diagnostics JSON.",
    ),
    part: str = typer.Option("hull", "--part", help="Mesh part to diagnose: hull or deck."),
) -> None:
    """Diagnose generated surface mesh quality without promoting CFD readiness."""
    from kayakgen.eval.mesh_diagnostics import diagnose_mesh

    if part not in ("hull", "deck"):
        typer.echo("--part must be hull or deck", err=True)
        raise typer.Exit(code=1)
    diagnostics = diagnose_mesh(load_hull(hull_path), part=cast(PartType, part))
    out_path = out if out is not None else hull_path.with_suffix(f".{part}.mesh.json")
    out_path.write_text(diagnostics.model_dump_json(indent=2))
    typer.echo(f"wrote {out_path}")


@app.command("mesh-package")
def mesh_package(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the mesh package.",
    ),
    solver_profile: str = typer.Option(
        "open-wetted-surface",
        "--solver-profile",
        help="Mesh solver profile: open-wetted-surface or watertight-solid.",
    ),
    bind_evidence: Path | None = typer.Option(
        None,
        "--bind-evidence",
        exists=True,
        dir_okay=False,
        help=(
            "RFC 0045: attach a previously-recorded snappyHexMesh evidence "
            "JSON. Triggers hash-binding gates and promotes the manifest to "
            "cfd_ready when the bound diagnostic satisfies the watertight "
            "handoff. Without this flag, output is byte-identical to today."
        ),
    ),
) -> None:
    """Write manifest, quality reports, and STL surfaces for a Hull."""
    from kayakgen.eval.snappy_hex_mesh import (
        MeshEvidenceBindError,
        SnappyHexMeshEvidence,
        bind_evidence_to_mesh_package,
        closed_body_content_sha256,
    )
    from kayakgen.eval.closed_volume import generated_hull_plus_deck_body

    try:
        profile = _mesh_solver_profile(solver_profile)
        hull = load_hull(hull_path)
        bound_diagnostic = None
        if bind_evidence is not None:
            evidence = SnappyHexMeshEvidence.model_validate_json(
                bind_evidence.read_text()
            )
            polymesh_dir = bind_evidence.parent / "polyMesh"
            body = generated_hull_plus_deck_body(hull)
            closed_hash = closed_body_content_sha256(body)
            bound_diagnostic = bind_evidence_to_mesh_package(
                evidence,
                closed_body_hash=closed_hash,
                polymesh_dir=polymesh_dir if polymesh_dir.is_dir() else None,
            )
        manifest = write_mesh_package(
            hull,
            out,
            solver_profile=profile,
            bound_volume_mesh_diagnostic=bound_diagnostic,
        )
    except MeshEvidenceBindError as exc:
        typer.echo(f"binding_code: {exc.code}", err=True)
        typer.echo(f"mesh-package failed: {exc.message}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"mesh-package failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {out / 'manifest.json'} ({manifest.readiness.level})")
    typer.echo(f"readiness: {manifest.readiness.level}")
    for blocker in _mesh_readiness_blockers(manifest):
        typer.echo(f"readiness_blocker: {blocker}")
    for reason in manifest.readiness.reasons:
        typer.echo(f"readiness_reason: {reason}")


@app.command("mesh-evidence")
def mesh_evidence(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the snappyHexMesh evidence artifacts.",
    ),
    stations: int = typer.Option(
        12,
        "--stations",
        help="Number of stations to use when constructing the closed body.",
    ),
) -> None:
    """Run the meshing stage and write a SnappyHexMeshEvidence record.

    Refuses without ``KAYAKGEN_OPENFOAM_LOCAL_RUN=1`` and an actual
    OpenFOAM-v2512 toolchain on PATH. Produces ``evidence.json``,
    ``polyMesh/``, and ``provenance.json`` under ``--out``.
    """
    import os
    import shutil

    from kayakgen.eval.cfd.jobs import (
        OPENFOAM_LOCAL_RUN_ENV_VAR,
        probe_openfoam_provenance,
    )
    from kayakgen.eval.cfd.openfoam_v2512_interfoam.case_render import (
        OpenFoamCaseSpec,
        domain_bounds_from_stl,
        render_case,
    )
    from kayakgen.eval.cfd.openfoam_v2512_interfoam.evidence import (
        build_snappy_hex_mesh_evidence_from_case,
    )
    from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
        OpenFoamProbeBashrcRunner,
        is_openfoam_available,
        probe_commands_for_bashrc_runner,
        run_meshing_stage,
    )
    from kayakgen.eval.closed_volume import generated_hull_plus_deck_body
    from kayakgen.eval.snappy_hex_mesh import closed_body_content_sha256

    if os.environ.get(OPENFOAM_LOCAL_RUN_ENV_VAR) != "1":
        typer.echo(
            "binding_code: openfoam_local_run_env_required",
            err=True,
        )
        typer.echo(
            "mesh-evidence refuses to run: set "
            f"{OPENFOAM_LOCAL_RUN_ENV_VAR}=1 and ensure the OpenFOAM-v2512 "
            "bashrc is sourceable with interFoam on PATH",
            err=True,
        )
        typer.echo(
            "Alternatively, the RFC 0046 profile flag "
            "(kayakgen cfd prepare --allow-real-solver-execution) or a "
            "persistent setting in ~/.config/kayakgen/cfd.json can opt in; "
            "mesh-evidence currently honors only the env-knob mechanism. "
            "See docs/USER_GUIDE.md '### cfd run' for precedence.",
            err=True,
        )
        raise typer.Exit(code=1)
    if not is_openfoam_available():
        typer.echo("binding_code: openfoam_toolchain_unavailable", err=True)
        typer.echo(
            "mesh-evidence refuses to run: OpenFOAM-v2512 toolchain "
            "(sourceable bashrc + interFoam on PATH) was not detected",
            err=True,
        )
        raise typer.Exit(code=1)

    out.mkdir(parents=True, exist_ok=True)
    hull = load_hull(hull_path)
    body = generated_hull_plus_deck_body(hull, stations=stations)
    closed_hash = closed_body_content_sha256(body)

    # Write the closed-body STL into a case directory and render the case.
    case_dir = out / "case"
    case_dir.mkdir(parents=True, exist_ok=True)
    closed_body_stl = out / "closed_body.stl"
    _write_closed_body_stl(body, closed_body_stl)
    bounds = domain_bounds_from_stl(closed_body_stl)
    spec = OpenFoamCaseSpec(hull_stl_path=closed_body_stl, domain_bounds=bounds)
    render_case(spec, case_dir, stage="meshing")

    meshing = run_meshing_stage(case_dir)
    if not meshing.succeeded:
        typer.echo(
            f"mesh-evidence failed: meshing stage did not succeed "
            f"({meshing.failure_reason})",
            err=True,
        )
        raise typer.Exit(code=1)

    provenance = probe_openfoam_provenance(
        commands=probe_commands_for_bashrc_runner(),
        runner=OpenFoamProbeBashrcRunner(),
    )
    evidence = build_snappy_hex_mesh_evidence_from_case(
        case_dir,
        spec,
        meshing,
        provenance,
        body_ref_hash=closed_hash,
    )

    evidence_path = out / "evidence.json"
    evidence_path.write_text(evidence.model_dump_json(indent=2) + "\n")

    poly_src = case_dir / "constant" / "polyMesh"
    poly_dst = out / "polyMesh"
    if poly_dst.exists():
        shutil.rmtree(poly_dst)
    shutil.copytree(poly_src, poly_dst)

    provenance_path = out / "provenance.json"
    provenance_path.write_text(provenance.model_dump_json(indent=2) + "\n")

    typer.echo(f"wrote {evidence_path}")
    typer.echo(f"wrote {poly_dst}")
    typer.echo(f"wrote {provenance_path}")
    typer.echo(f"dispatch_state: {evidence.dispatch_state}")


def _write_closed_body_stl(body, path: Path) -> None:
    """Write a binary STL of ``body`` to ``path``."""

    import numpy as np
    from stl import mesh as stl_mesh

    triangles: list[tuple[tuple[float, float, float], ...]] = []
    for part in body.parts:
        vertices = [list(v) for v in part.vertices]
        for face in part.faces:
            triangles.append(tuple(tuple(vertices[idx]) for idx in face))
    data = np.zeros(len(triangles), dtype=stl_mesh.Mesh.dtype)
    obj = stl_mesh.Mesh(data)
    for i, tri in enumerate(triangles):
        for j in range(3):
            obj.vectors[i][j] = tri[j]
    obj.save(str(path))


def _mesh_solver_profile(name: str):
    if name == "open-wetted-surface":
        return open_wetted_surface_profile()
    if name == "watertight-solid":
        return watertight_solid_profile()
    raise ValueError("--solver-profile must be open-wetted-surface or watertight-solid")


def _mesh_readiness_blockers(manifest) -> list[str]:
    blockers: list[str] = []
    if manifest.solver_profile.requires_watertight:
        if not manifest.volume_mesh_diagnostic:
            blockers.append("missing_volume_mesh")
        if manifest.readiness.level != "cfd_ready":
            blockers.append("readiness_below_cfd_ready")
    else:
        blockers.append("not_watertight_profile")
    if any("separate open surfaces" in reason for reason in manifest.readiness.reasons):
        blockers.append("open_surface_package")
    return list(dict.fromkeys(blockers))


@cfd_app.command("prepare")
def cfd_prepare(
    mesh_package: Path = typer.Option(
        ...,
        "--mesh-package",
        exists=True,
        file_okay=False,
        help="Mesh package directory containing manifest.json.",
    ),
    out: Path = typer.Option(..., "--out", help="Output directory for local CFD jobs."),
    solver_profile: str = typer.Option(
        "unavailable-open-wetted-surface",
        "--solver-profile",
        help="CFD solver profile name.",
    ),
    speed_mps: float = typer.Option(..., "--speed-mps", help="Flow speed in m/s."),
    seawater_density_kg_m3: float = typer.Option(
        1025.0,
        "--seawater-density-kg-m3",
        help="Seawater density used by the solver job.",
    ),
    kinematic_viscosity_m2_s: float = typer.Option(
        1.19e-6,
        "--kinematic-viscosity-m2-s",
        help="Kinematic viscosity used by the solver job.",
    ),
    allow_real_solver_execution: bool = typer.Option(
        False,
        "--allow-real-solver-execution",
        help=(
            "Write allow_real_solver_execution=true into profile.json so a "
            "subsequent cfd run admits the OpenFOAM real-solver succeeded path "
            "without setting the env knob (RFC 0046)."
        ),
    ),
) -> None:
    """Prepare a deterministic local CFD job without running a real solver."""
    try:
        paths = prepare_cfd_job(
            mesh_package,
            out,
            solver_profile_name=solver_profile,
            speed_mps=speed_mps,
            seawater_density_kg_m3=seawater_density_kg_m3,
            kinematic_viscosity_m2_s=kinematic_viscosity_m2_s,
            allow_real_solver_execution=allow_real_solver_execution,
        )
    except CfdDispatchError as exc:
        typer.echo(f"blocker_class: {exc.code}", err=True)
        typer.echo(f"cfd prepare failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {paths.job_dir}")
    typer.echo(f"status: {paths.run.status}")
    typer.echo(CFD_RAW_RESULTS_WARNING)
    typer.echo(
        f"Next: kayakgen cfd run {paths.job_dir}. The real-solver path "
        "requires an RFC 0046 opt-in (--allow-real-solver-execution, "
        "~/.config/kayakgen/cfd.json, or KAYAKGEN_OPENFOAM_LOCAL_RUN=1)."
    )


@cfd_app.command("status")
def cfd_status(
    job_dir: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        help="Local CFD job directory.",
    ),
) -> None:
    """Show the current local CFD job state."""
    try:
        run = load_cfd_run_record(job_dir)
    except CfdDispatchError as exc:
        typer.echo(f"cfd status failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"job_id: {run.job_id}")
    typer.echo(f"status: {run.status}")
    typer.echo(f"solver_profile: {run.solver_profile}")
    if run.error_kind:
        typer.echo(f"error_kind: {run.error_kind}")
    if run.error_message:
        typer.echo(f"error_message: {run.error_message}")
    _echo_cfd_warnings(run)


@cfd_app.command("run")
def cfd_run(
    job_dir: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        help="Local CFD job directory.",
    ),
) -> None:
    """Run or mark the selected local CFD adapter state."""
    try:
        run = run_cfd_job(job_dir)
    except CfdDispatchError as exc:
        typer.echo(f"cfd run failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"status: {run.status}")
    if run.error_kind:
        typer.echo(f"error_kind: {run.error_kind}")
    if run.error_message:
        typer.echo(f"error_message: {run.error_message}")
    _echo_cfd_warnings(run)


@cfd_app.command("profiles")
def cfd_profiles() -> None:
    """List local CFD solver profiles."""
    for name in solver_profile_names():
        typer.echo(name)


def _echo_cfd_warnings(run: CfdRunRecord) -> None:
    typer.echo(CFD_RAW_RESULTS_WARNING)
    if CFD_FIXTURE_RESULTS_WARNING in run.warnings:
        typer.echo(CFD_FIXTURE_RESULTS_WARNING)


@stability_app.command("legacy", hidden=True)
def stability(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path | None = typer.Option(None, "--out", help="Where to write stability JSON."),
    load_case: Path | None = typer.Option(
        None,
        "--load-case",
        exists=True,
        dir_okay=False,
    ),
    equilibrium: bool = typer.Option(
        False,
        "--equilibrium",
        help="Solve load-case sinkage equilibrium before reporting initial stability.",
    ),
    tolerance_kg: float = typer.Option(
        1.0,
        "--tolerance-kg",
        help="Mass tolerance for equilibrium convergence.",
    ),
    moment_tolerance_kg_m: float | None = typer.Option(
        None,
        "--moment-tolerance-kg-m",
        help="Moment tolerance for trim equilibrium convergence; defaults from hull length.",
    ),
    max_iterations: int = typer.Option(
        60,
        "--max-iterations",
        help="Maximum equilibrium bisection iterations.",
    ),
    high_angle_gz: bool = typer.Option(
        False,
        "--high-angle-gz",
        help=(
            "Opt-in: append an unvalidated_hydrostatic_comparison high-angle GZ "
            "block to the stability JSON. Default output is unchanged."
        ),
    ),
    heel_grid_deg: str | None = typer.Option(
        None,
        "--heel-grid-deg",
        help=(
            "Comma-separated, strictly-increasing heel angles in degrees "
            "(0..90). Only used with --high-angle-gz."
        ),
    ),
) -> None:
    """Evaluate initial stability for a load case."""
    load = (
        LoadCase.model_validate_json(load_case.read_text())
        if load_case is not None
        else LoadCase()
    )
    hull = load_hull(hull_path)
    if equilibrium:
        result = evaluate_equilibrium_stability(
            hull,
            load,
            tolerance_kg=tolerance_kg,
            moment_tolerance_kg_m=moment_tolerance_kg_m,
            max_iterations=max_iterations,
        )
    else:
        result = evaluate_initial_stability(hull, load)
    out_path = out if out is not None else hull_path.with_suffix(".stability.json")
    if high_angle_gz:
        try:
            grid = parse_heel_grid_deg(heel_grid_deg)
        except ValueError as exc:
            typer.echo(f"stability --high-angle-gz failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        payload = json.loads(result.model_dump_json())
        payload["high_angle_gz"] = build_high_angle_gz_block(
            hull,
            load,
            heel_grid_deg=grid,
        )
        out_path.write_text(json.dumps(payload, indent=2))
    else:
        if heel_grid_deg is not None:
            typer.echo(
                "stability: --heel-grid-deg requires --high-angle-gz",
                err=True,
            )
            raise typer.Exit(code=1)
        out_path.write_text(result.model_dump_json(indent=2))
    typer.echo(f"wrote {out_path}")


@app.command()
def view(
    hull_path: Path | None = typer.Argument(
        None,
        help="Optional Hull JSON to load; defaults to the same defaults as `python gui.py`.",
    ),
) -> None:
    """Open the desktop GUI."""
    try:
        from kayakgen.ui.desktop import KayakGUI
    except ImportError as exc:
        typer.echo(f"desktop GUI extras not installed: {exc}", err=True)
        raise typer.Exit(code=1)

    if hull_path is not None:
        hull = load_hull(hull_path)
        KayakGUI(hull=hull)
    else:
        KayakGUI()


@app.command()
def serve(
    hull_path: Path | None = typer.Argument(
        None,
        help="Optional Hull JSON to seed initial state; defaults to Hull().",
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(8080, "--port", help="Bind port."),
    jobs_in_process: bool = typer.Option(
        False,
        "--jobs-in-process",
        help=(
            "RFC 0057 stage 4: opt out of the subprocess generative-job "
            "manager and run jobs in threads inside the web process. The "
            "default is detached subprocesses for crash survival."
        ),
    ),
) -> None:
    """Run the Trame web frontend (RFC 0008) locally."""
    try:
        from kayakgen.ui.web.app import create_app
    except ImportError as exc:
        typer.echo(f"web extras not installed (pip install 'kayakgen[web]'): {exc}", err=True)
        raise typer.Exit(code=1)

    from kayakgen.services.generative_jobs import (
        InProcessGenerativeJobManager,
        SubprocessGenerativeJobManager,
    )
    from kayakgen.ui.web.app import _default_generative_jobs_root_for_app

    jobs_root = _default_generative_jobs_root_for_app()
    if jobs_in_process:
        generative_manager = InProcessGenerativeJobManager(jobs_root=jobs_root)
        typer.echo(
            "serve: generative jobs will run as in-process threads "
            f"(jobs_root={generative_manager.jobs_root})"
        )
    else:
        generative_manager = SubprocessGenerativeJobManager(jobs_root=jobs_root)
        typer.echo(
            "serve: generative jobs will run as detached subprocesses "
            f"(jobs_root={generative_manager.jobs_root})"
        )

    initial_hull = load_hull(hull_path) if hull_path is not None else None
    web = create_app(initial_hull=initial_hull, generative_manager=generative_manager)
    web.server.start(host=host, port=port)


@app.command()
def sweep(
    sweep_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for generated candidates.",
    ),
    resume: bool = typer.Option(False, "--resume", help="Skip completed candidate records."),
) -> None:
    """Run a deterministic JSON sweep and write candidate records."""
    from kayakgen.search.sweep import load_sweep_spec, run_sweep

    try:
        run = run_sweep(load_sweep_spec(sweep_path), out, resume=resume)
    except Exception as exc:
        typer.echo(f"sweep failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(
        f"wrote {out} ({run.completed_count} complete, {run.failed_count} failed, "
        f"{run.skipped_count} skipped, {run.pending_count} pending)"
    )


@app.command()
def search(
    spec_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="Active-search spec JSON (RFC 0044).",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the search run (will be created if missing).",
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume from a previously persisted state.json checkpoint.",
    ),
) -> None:
    """Run an opt-in NSGA-II active hull-design search (RFC 0044)."""
    from kayakgen.search.active.runner import load_search_spec, resolve_objectives, run_search

    try:
        spec = load_search_spec(spec_path)
        objectives = resolve_objectives(spec)
        typer.echo(f"search: {spec.name} (seed={spec.algorithm.seed})")
        objective_line = ", ".join(f"{o.metric}:{o.direction}" for o in objectives)
        typer.echo(f"objectives: {objective_line}")
        if spec.objectives_explicit_exploratory:
            typer.echo(
                "exploratory: search_class=exploratory; frontier rows are tagged "
                "exploratory and remain frontier-ineligible under the conservative view"
            )
        if spec.budget.max_evaluations is not None:
            typer.echo(f"budget_max_evaluations: {spec.budget.max_evaluations}")
        if spec.budget.wall_clock_seconds is not None:
            typer.echo(f"budget_wall_clock_seconds: {spec.budget.wall_clock_seconds}")
        result = run_search(spec_path, out, resume=resume)
    except Exception as exc:
        typer.echo(f"search failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(
        f"wrote {result.run_dir} ({result.completed_count} complete, "
        f"{result.failed_count} failed, {result.constraint_failed_count} "
        f"constraint_failed, {result.pending_count} pending; "
        f"realized_evaluations={result.search_metadata.realized_evaluations}, "
        f"termination_reason={result.search_metadata.termination_reason})"
    )


@app.command()
def compare(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Sweep run directory."),
    out: Path = typer.Option(..., "--out", help="Where to write comparison report JSON."),
    objective: list[str] | None = typer.Option(
        None,
        "--objective",
        "-o",
        help="Objective as metric:min or metric:max. May be repeated.",
    ),
) -> None:
    """Compare a sweep run and write a Pareto frontier report."""
    try:
        objectives = [parse_objective(item) for item in objective] if objective else None
        report = write_comparison_report(run_dir, out, objectives=objectives)
    except Exception as exc:
        typer.echo(f"compare failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {out} ({len(report.pareto_front_keys)} pareto candidates)")


@app.command("build-export")
def build_export(
    hull_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(..., "--out", help="Output directory for builder artifacts."),
    n_stations: int = typer.Option(
        32,
        "--n-stations",
        help="Number of evenly-spaced section cuts to sample (RFC 0051).",
    ),
) -> None:
    """Write builder-oriented artifacts (offsets CSV, DXF, SVG) for a hull (RFC 0051)."""
    try:
        from kayakgen.services.build_export import BuildExportSpec, write_build_export
    except ImportError as exc:
        typer.echo(
            f"builder extras not installed (pip install 'kayakgen[builder]'): {exc}",
            err=True,
        )
        raise typer.Exit(code=1)
    try:
        manifest_path = write_build_export(
            load_hull(hull_path),
            out,
            spec=BuildExportSpec(n_stations=n_stations),
        )
    except ImportError as exc:
        typer.echo(
            f"builder extras not installed (pip install 'kayakgen[builder]'): {exc}",
            err=True,
        )
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"build-export failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {manifest_path}")


@calibration_app.command("ingest-tank-test")
def calibration_ingest_tank_test(
    csv_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="Tank-test CSV (see TankTestRun for the required columns).",
    ),
    hull: Path = typer.Option(
        ...,
        "--hull",
        exists=True,
        dir_okay=False,
        help="Hull JSON used to bind hull_design_hash.",
    ),
    rights: Path = typer.Option(
        ...,
        "--rights",
        exists=True,
        dir_okay=False,
        help="RightsChecklist JSON describing license / attribution.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the campaign artifact.",
    ),
    source_id: str = typer.Option(
        ...,
        "--source-id",
        help="Campaign source_id (must match the value carried on rows).",
    ),
    uncertainty_method: str = typer.Option(
        "Type_A_repeatability",
        "--uncertainty-method",
        help=(
            "One of Type_A_repeatability, Type_B_uncertainty_budget, "
            "documented_caveat."
        ),
    ),
) -> None:
    """Ingest a tank-test CSV into a TankTestCampaign JSON artifact."""
    from kayakgen.eval.calibration.campaigns import (
        GeometryReference,
        tank_test_campaign_from_csv,
    )
    from kayakgen.eval.calibration.rights import RightsChecklist

    try:
        hull_obj = load_hull(hull)
        rights_obj = RightsChecklist.model_validate_json(rights.read_text())
        # Until RFC 0049 lands Hull.design_hash(), use Hull.hash() as the
        # placeholder per the RFC 0054 deferred decision.
        geometry = GeometryReference(
            geometry_path=str(hull),
            hull_design_hash=hull_obj.hash(),
        )
        campaign = tank_test_campaign_from_csv(
            csv_path,
            source_id=source_id,
            hull_design_hash=hull_obj.hash(),
            rights_checklist=rights_obj,
            geometry_reference=geometry,
            uncertainty_method=uncertainty_method,  # type: ignore[arg-type]
        )
    except Exception as exc:
        typer.echo(f"calibration ingest-tank-test failed: {exc}", err=True)
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{source_id}.campaign.json"
    out_path.write_text(campaign.model_dump_json(indent=2) + "\n")
    typer.echo(f"wrote {out_path} ({len(campaign.rows)} rows)")


@calibration_app.command("ingest-inclining-test")
def calibration_ingest_inclining_test(
    csv_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="Inclining-test CSV (see IncliningTestRun for the required columns).",
    ),
    hull: Path = typer.Option(
        ...,
        "--hull",
        exists=True,
        dir_okay=False,
        help="Hull JSON used to bind hull_design_hash.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the campaign artifact.",
    ),
    source_id: str = typer.Option(
        ...,
        "--source-id",
        help="Campaign source_id (must match the value carried on rows).",
    ),
    rights: Path | None = typer.Option(
        None,
        "--rights",
        exists=True,
        dir_okay=False,
        help=(
            "Optional RightsChecklist JSON; if omitted a documented-caveat "
            "placeholder is written. Real campaigns SHOULD supply this."
        ),
    ),
) -> None:
    """Ingest an inclining-test CSV into an IncliningTestCampaign JSON artifact."""
    from kayakgen.eval.calibration.campaigns import (
        GeometryReference,
        inclining_test_campaign_from_csv,
    )
    from kayakgen.eval.calibration.rights import RightsChecklist

    try:
        hull_obj = load_hull(hull)
        if rights is not None:
            rights_obj = RightsChecklist.model_validate_json(rights.read_text())
        else:
            rights_obj = RightsChecklist(
                license_identifier="unspecified",
                attribution="unspecified",
                source_locator=str(csv_path),
                redistribution_authorized=False,
                attribution_required=True,
                notes=["rights checklist not supplied at ingest time"],
            )
        geometry = GeometryReference(
            geometry_path=str(hull),
            hull_design_hash=hull_obj.hash(),
        )
        campaign = inclining_test_campaign_from_csv(
            csv_path,
            source_id=source_id,
            hull_design_hash=hull_obj.hash(),
            rights_checklist=rights_obj,
            geometry_reference=geometry,
        )
    except Exception as exc:
        typer.echo(f"calibration ingest-inclining-test failed: {exc}", err=True)
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{source_id}.campaign.json"
    out_path.write_text(campaign.model_dump_json(indent=2) + "\n")
    typer.echo(f"wrote {out_path} ({len(campaign.rows)} rows)")


@calibration_app.command("accept-fit")
def calibration_accept_fit(
    fixture_id: str = typer.Argument(
        ...,
        help="The fixture id this accepted fit belongs to (for human cross-ref).",
    ),
    fit: Path = typer.Option(
        ...,
        "--fit",
        exists=True,
        dir_okay=False,
        help="AcceptedFitRecord JSON to evaluate and persist.",
    ),
    rmse_threshold: float = typer.Option(
        5.0,
        "--rmse-threshold",
        help=(
            "Acceptance threshold percent. Interpreted per fit_metric: "
            "for RMSE, the ceiling is rmse_threshold % of holdout_rms_n; "
            "for MAPE, the maximum admissible MAPE; for R2, the minimum "
            "admissible R2."
        ),
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output directory for the accepted-fit artifact.",
    ),
) -> None:
    """Validate an AcceptedFitRecord against the threshold and persist it."""
    from kayakgen.eval.calibration.campaigns import (
        AcceptedFitRecord,
        AcceptedFitRejection,
        evaluate_fit_against_threshold,
    )

    try:
        record = AcceptedFitRecord.model_validate_json(fit.read_text())
        evaluate_fit_against_threshold(
            record,
            measured_baseline=record.holdout_rms_n,
            threshold_pct=rmse_threshold,
        )
    except AcceptedFitRejection as exc:
        typer.echo(f"accept-fit refused: {exc.reason}: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"accept-fit failed: {exc}", err=True)
        raise typer.Exit(code=1)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{record.fit_id}.accepted_fit.json"
    out_path.write_text(record.model_dump_json(indent=2) + "\n")
    typer.echo(f"wrote {out_path} (fixture_id={fixture_id})")


@calibration_app.command("residual-plot")
def calibration_residual_plot(
    accepted_fit_json: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        help="AcceptedFitRecord JSON file to plot.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output SVG file path.",
    ),
) -> None:
    """Write a residual-stem SVG plot for an AcceptedFitRecord."""
    from kayakgen.eval.calibration.campaigns import AcceptedFitRecord
    from kayakgen.services.calibration_artifacts import write_residual_plot

    try:
        record = AcceptedFitRecord.model_validate_json(accepted_fit_json.read_text())
        write_residual_plot(record, out)
    except Exception as exc:
        typer.echo(f"residual-plot failed: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"wrote {out}")


from kayakgen.cli.target_workflows import target_draft_command, target_trim_command  # noqa: E402

app.command("target-draft")(target_draft_command)
app.command("target-trim")(target_trim_command)


if __name__ == "__main__":
    app()
