"""OpenFOAM-v2512 interFoam real-execution pipeline package.

This package implements the workflow 0052 D012 closure path: a real,
end-to-end OpenFOAM-v2512 case renderer, runner, and evidence collector
that produces ``CfdRunRecord(status="succeeded", claim_state="raw_unvalidated")``
output. The behaviour is opt-in: the default ``OpenFoamLocalAdapter``
behaviour remains byte-equal to the historical
``solver_success_blocked`` skeleton when the opt-in env knob is not set.

The package contents are:

* ``case_render`` - renders the vendored proven case dictionaries
  (``system/*``, ``constant/*``, ``0.orig/*``) into a case directory.
* ``runner`` - bashrc-sourced subprocess helper plus meshing/solver
  stage runners.
* ``evidence`` - binds meshing-stage output to the existing
  ``SnappyHexMeshEvidence`` record.

Importing this package never invokes any OpenFOAM binary.
"""

from __future__ import annotations

from kayakgen.eval.cfd.openfoam_v2512_interfoam.case_render import (
    OpenFoamCaseSpec,
    OpenFoamCaseRenderedPaths,
    render_case,
    domain_bounds_from_stl,
    stl_bounding_box,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam.runner import (
    OPENFOAM_BASHRC,
    OPENFOAM_BASHRC_ENV_VAR,
    OpenFoamCommandResult,
    OpenFoamProbeBashrcRunner,
    MeshingResult,
    SolverResult,
    bash_source_run,
    bash_source_run_streamed,
    is_openfoam_available,
    parse_check_mesh_output,
    run_meshing_stage,
    run_solver_stage,
)
from kayakgen.eval.cfd.openfoam_v2512_interfoam.evidence import (
    build_snappy_hex_mesh_evidence_from_case,
    read_poly_mesh_patches,
    sha256_of_path,
)

__all__ = [
    "OpenFoamCaseSpec",
    "OpenFoamCaseRenderedPaths",
    "render_case",
    "domain_bounds_from_stl",
    "stl_bounding_box",
    "OPENFOAM_BASHRC",
    "OPENFOAM_BASHRC_ENV_VAR",
    "OpenFoamCommandResult",
    "OpenFoamProbeBashrcRunner",
    "MeshingResult",
    "SolverResult",
    "bash_source_run",
    "bash_source_run_streamed",
    "is_openfoam_available",
    "parse_check_mesh_output",
    "run_meshing_stage",
    "run_solver_stage",
    "build_snappy_hex_mesh_evidence_from_case",
    "read_poly_mesh_patches",
    "sha256_of_path",
]
