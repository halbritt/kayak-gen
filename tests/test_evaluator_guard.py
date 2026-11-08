"""Order-sensitive regressions for the evaluator no-rerun guard (KAYGEN-22, E16).

A parser guard must refuse evaluator calls inside its window and leave no stub
alias behind. These cases reuse the saved-result payload from
``test_recorded_method_binding.py`` and the real operating-equilibrium
regressions from ``test_evaluation_context.py``; they do not re-check the
repaired numerical method.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path

import numpy as np
import pytest
import test_evaluation_context as operating_context
import test_recorded_method_binding as method_binding
from evaluator_guard import forbid_evaluator_calls
from pydantic import BaseModel, ValidationError, field_validator

import kayakgen.eval.immersed_geometry as immersed_module
from kayakgen.eval.contract import EvaluationResult
from kayakgen.model.hull import Hull

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
IMMERSED = {"kayakgen.eval.immersed_geometry": ["immersed_geometry"]}
OPERATING_EQUILIBRIUM = "kayakgen.eval.stability.operating_equilibrium"
# The real consumers that failed in E16 after the guard file ran first.
REAL_OPERATING_CASES = tuple(
    "tests/test_evaluation_context.py::" + name
    for name in (
        "test_real_v2_load_and_fluid_share_one_operating_pose",
        "test_explicit_load_origin_and_target_draft_preserve_components",
        "test_equilibrium_and_saved_hydro_use_the_requested_mesh_resolution",
    )
)
IMMERSED_LEAK = ".immersed_geometry -> kayakgen.eval.immersed_geometry.immersed_geometry"


def _saved_result_json() -> str:
    return json.dumps(
        method_binding.payload("michell_linear_depth_v2", "michell_linear_depth_v2", assessed=True)
    )


def _parse_under_parser_guard() -> EvaluationResult:
    with forbid_evaluator_calls(
        method_binding.PARSER_FORBIDDEN_EVALUATORS,
        consumers=method_binding.PARSER_GUARD_CONSUMERS,
    ) as guard:
        result = EvaluationResult.model_validate_json(_saved_result_json())
    assert guard.calls == []
    assert guard.leaks == []
    return result


def _child_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), str(TESTS_DIR)])
    # The child is a focused run, not a gate: no skip pin, no inherited selectors.
    for name in ("KAYAKGEN_ENFORCE_SKIP_PIN", "PYTEST_ADDOPTS", "KAYAKGEN_GATE_RECEIPT"):
        env.pop(name, None)
    return env


def test_guard_records_evaluator_calls_even_when_the_parser_wraps_them():
    class Parsed(BaseModel):
        value: int

        @field_validator("value")
        @classmethod
        def rerun(cls, value):
            immersed_module.immersed_geometry(None, None)
            return value

    with forbid_evaluator_calls(IMMERSED) as guard:
        # pydantic converts the stub's AssertionError into a ValidationError, so
        # only the recorded call proves the parser ran an evaluator.
        with pytest.raises(ValidationError, match="parser reran evaluator"):
            Parsed(value=1)
    assert guard.calls == ["kayakgen.eval.immersed_geometry.immersed_geometry"]
    assert guard.leaks == []


def test_strict_parser_guard_still_refuses_a_saved_result_rerun():
    with forbid_evaluator_calls(
        method_binding.PARSER_FORBIDDEN_EVALUATORS,
        consumers=method_binding.PARSER_GUARD_CONSUMERS,
    ) as guard:
        from kayakgen.services.evaluation import evaluate_with_context

        result = EvaluationResult.model_validate_json(_saved_result_json())
        with pytest.raises(AssertionError, match="parser reran evaluator"):
            evaluate_with_context(Hull(), result.context)
    assert guard.calls == ["kayakgen.services.evaluation.evaluate_with_context"]
    assert guard.leaks == []


def test_deliberately_captured_alias_is_detected_and_legitimate_imports_are_not(
    tmp_path, monkeypatch
):
    token = uuid.uuid4().hex
    leaky = "leaky_consumer_" + token
    legit = "legit_consumer_" + token
    (tmp_path / (leaky + ".py")).write_text(
        "from kayakgen.eval.immersed_geometry import immersed_geometry\n"
    )
    (tmp_path / (legit + ".py")).write_text(
        textwrap.dedent(
            """
            import kayakgen.eval.immersed_geometry as immersed
            from kayakgen.eval.immersed_geometry import ImmersedGeometry


            def run(hull, pose):
                return immersed.immersed_geometry(hull, pose, stations=20)
            """
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    real = immersed_module.immersed_geometry
    try:
        with pytest.raises(AssertionError, match="leaked stub aliases") as excinfo:
            with forbid_evaluator_calls(IMMERSED) as guard:
                leaky_module = __import__(leaky)
                legit_module = __import__(legit)
        message = str(excinfo.value)
        assert leaky + IMMERSED_LEAK in message
        assert legit not in message
        assert guard.leaks == [leaky + IMMERSED_LEAK]
        assert guard.calls == []
        # The guard repaired the captured alias and restored the source module.
        assert leaky_module.immersed_geometry is real
        assert immersed_module.immersed_geometry is real
        # Ordinary later evaluator calls through either consumer are allowed.
        from kayakgen.model.operating_state import OperatingPose

        hull = Hull()
        via_legit = legit_module.run(hull, OperatingPose())
        via_leaky = leaky_module.immersed_geometry(hull, OperatingPose(), stations=20)
        assert isinstance(via_legit, legit_module.ImmersedGeometry)
        assert via_legit.body_faces.size > 0
        assert np.array_equal(via_leaky.body_vertices, via_legit.body_vertices)
    finally:
        for name in (leaky, legit):
            sys.modules.pop(name, None)


def test_guard_then_real_operating_consumer():
    _parse_under_parser_guard()
    operating_context.test_equilibrium_and_saved_hydro_use_the_requested_mesh_resolution()
    operating_context.test_explicit_load_origin_and_target_draft_preserve_components()


def test_real_operating_consumer_then_guard_then_real_again():
    operating_context.test_equilibrium_and_saved_hydro_use_the_requested_mesh_resolution()
    _parse_under_parser_guard()
    operating_context.test_equilibrium_and_saved_hydro_use_the_requested_mesh_resolution()
    operating_context.test_explicit_load_origin_and_target_draft_preserve_components()


_COLD_IMPORT_PROBE = textwrap.dedent(
    """
    import json, sys
    from evaluator_guard import forbid_evaluator_calls

    assert "kayakgen.eval.stability.operating_equilibrium" not in sys.modules
    consumers = tuple(sys.argv[1:])
    report = {"consumers": list(consumers)}
    try:
        with forbid_evaluator_calls(
            {"kayakgen.eval.immersed_geometry": ["immersed_geometry"]}, consumers=consumers
        ) as guard:
            import kayakgen.eval.stability.operating_equilibrium  # noqa: F401
    except AssertionError as exc:
        report["error"] = str(exc)
    report["leaks"] = guard.leaks
    import test_evaluation_context as cases
    cases.test_equilibrium_and_saved_hydro_use_the_requested_mesh_resolution()
    report["real_consumer"] = "passed"
    print(json.dumps(report))
    """
)


@pytest.mark.parametrize("preload", [False, True])
def test_cold_import_of_real_consumer_under_guard(preload):
    """E16 shape in a fresh interpreter: the consumer is first imported mid-guard."""
    args = [OPERATING_EQUILIBRIUM] if preload else []
    completed = subprocess.run(
        [sys.executable, "-c", _COLD_IMPORT_PROBE, *args],
        cwd=REPO_ROOT,
        env=_child_env(),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(completed.stdout.strip().splitlines()[-1])
    assert report["real_consumer"] == "passed"
    if preload:
        assert report["leaks"] == []
        assert "error" not in report
    else:
        leak = OPERATING_EQUILIBRIUM + IMMERSED_LEAK
        assert report["leaks"] == [leak]
        assert leak in report["error"]


@pytest.mark.parametrize("guard_first", [True, False], ids=["guard-first", "consumer-first"])
def test_guard_file_and_real_consumers_pass_in_both_file_orders(guard_first):
    """The E16 failure was file-order dependent; run both orders for real."""
    guard_files = ["tests/test_recorded_method_binding.py"]
    selected = (
        [*guard_files, *REAL_OPERATING_CASES]
        if guard_first
        else [*REAL_OPERATING_CASES, *guard_files]
    )
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *selected],
        cwd=REPO_ROOT,
        env=_child_env(),
        capture_output=True,
        text=True,
        timeout=600,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    summary = output.strip().splitlines()[-1]
    assert re.fullmatch(r"=* ?12 passed in [0-9.]+s.*", summary), output
