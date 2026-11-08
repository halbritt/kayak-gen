"""Semantic preflight selects the existing contract oracles before a full gate."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from kayakgen.operations.semantic_preflight import preflight_plan


def test_shared_context_change_selects_cross_consumer_contracts():
    packet = preflight_plan(["kayakgen/eval/contract.py"], [])
    assert {contract["id"] for contract in packet["contracts"]} == {
        "operating-inputs", "recorded-methods", "numerical-admission", "presentation"
    }
    assert "tests/test_recorded_method_binding.py" in packet["pytest_targets"]
    assert packet["operating_oracle_required"]
    assert packet["full_release_gate_required"]
    operating = next(c for c in packet["contracts"] if c["id"] == "operating-inputs")
    assert {"load and CG", "fluid", "exact speeds", "budget forwarding"}.issubset(
        operating["shared_inputs"]
    )
    assert "kayakgen/services/evaluation.py" in operating["producers"]
    assert "kayakgen/search/compare.py" in operating["consumers"]


def test_presentation_change_does_not_select_full_numerical_matrix():
    packet = preflight_plan(["docs/README.md"], ["presentation"])
    assert [contract["id"] for contract in packet["contracts"]] == ["presentation"]
    assert packet["unmapped_paths"] == ["docs/README.md"]
    assert not packet["operating_oracle_required"]
    assert "tests/test_evaluation_context.py" in packet["pytest_targets"]


@pytest.mark.parametrize("path", ["kayakgen/ui/web/handlers.py", "kayakgen/ui/desktop.py",
                                 "kayakgen/ui/web/state.py"])
def test_physical_context_adapters_select_operating_and_presentation(path):
    packet = preflight_plan([path], [])
    assert {contract["id"] for contract in packet["contracts"]} == {
        "operating-inputs", "presentation"
    }
    assert packet["operating_oracle_required"]


@pytest.mark.parametrize("path", ["kayakgen/io/json.py", "kayakgen/services/design_report.py",
                                 "kayakgen/eval/immersed_geometry.py"])
def test_persistence_report_and_pose_consumers_select_operating_contract(path):
    packet = preflight_plan([path], [])
    assert "operating-inputs" in {contract["id"] for contract in packet["contracts"]}
    assert packet["operating_oracle_required"]


def test_changing_the_matrix_caller_selects_all_its_contracts():
    packet = preflight_plan(["kayakgen/operations/semantic_preflight.py"], [])
    assert len(packet["contracts"]) == 4


@pytest.mark.parametrize("path", ["", ".", "../outside.py", "/absolute.py", "bad\0path"])
def test_invalid_changed_paths_do_not_hide_behind_no_selected_checks(path):
    with pytest.raises(ValueError, match="repository-relative"):
        preflight_plan([path], [])


def test_unrelated_caller_emits_explicit_partial_source_bound_nonacceptance(tmp_path):
    out = tmp_path / "preflight"
    command = [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
               "--changed-path", "docs/海.md", "--out", str(out)]
    completed = subprocess.run(command, cwd=Path(__file__).resolve().parents[1],
                               capture_output=True, text=True, timeout=15)
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == "not_applicable"
    assert receipt["evidence_scope"] == "semantic_preflight"
    assert receipt["release_acceptance"] is False
    assert receipt["full_release_gate_required"] is True
    assert receipt["commands"] == []
    assert receipt["unmapped_paths"] == ["docs/海.md"]
    assert receipt["source_before"]["tree_sha"] == receipt["source_after"]["tree_sha"]


def test_selected_real_method_cases_run_despite_inherited_subset_and_full_pin(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k no_such_case")
    monkeypatch.setenv("KAYAKGEN_ENFORCE_SKIP_PIN", "1")
    monkeypatch.setenv("KAYAKGEN_EXPECTED_SKIPS", "4")
    out = tmp_path / "preflight"
    completed = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
         "--contract", "recorded-methods", "--out", str(out)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == "passed"
    assert receipt["pytest_targets"] == ["tests/test_recorded_method_binding.py"]
    assert receipt["pytest_result"]["executed_cases"] >= 8
    assert receipt["pytest_result"]["skipped"] == 0
    assert [command["name"] for command in receipt["commands"]] == ["pytest"]
    assert receipt["source_unchanged"]
    assert receipt["release_acceptance"] is False


def isolated_checkout(tmp_path, body):
    """Actual maintained caller, Git capture and pytest; controlled contract case."""
    repo = tmp_path / "repo"
    operations = repo / "kayakgen/operations"
    operations.mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "kayakgen/__init__.py").touch()
    (operations / "__init__.py").touch()
    source = Path(__file__).resolve().parents[1] / "kayakgen/operations"
    shutil.copytree(source, operations, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n*.pyc\n")
    (repo / "tracked.txt").write_text("unchanged")
    (repo / "tests/test_recorded_method_binding.py").write_text(body)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Preflight fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)
    return repo


@pytest.mark.parametrize("body,reason", [
    ("def test_contract():\n    assert False, 'controlled contradiction'\n", "pytest command failed"),
    ("import pytest\ndef test_contract():\n    pytest.skip('required check unavailable')\n", "skipped"),
    ("from pathlib import Path\ndef test_contract():\n    Path('tracked.txt').write_text('changed')\n",
     "source changed"),
])
def test_real_failing_skipped_and_source_changing_checks_are_nonacceptance(tmp_path, body, reason):
    repo = isolated_checkout(tmp_path, body)
    out = tmp_path / "attempt"
    completed = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
         "--contract", "recorded-methods", "--out", str(out)],
        cwd=repo, env={**os.environ, "PYTHONPATH": str(repo)},
        capture_output=True, text=True, timeout=30)
    assert completed.returncode == 1, completed.stdout + completed.stderr
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == "failed"
    assert receipt["release_acceptance"] is False
    assert any(reason in failure for failure in receipt["failure_reasons"])
    assert (out / "pytest.log").is_file()


def test_warning_text_does_not_count_as_deselected_cases(tmp_path):
    repo = isolated_checkout(tmp_path, "import warnings\ndef test_contract():\n"
        "    warnings.warn('historical metadata named deselected remains readable')\n")
    out = tmp_path / "attempt"
    completed = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
         "--contract", "recorded-methods", "--out", str(out)],
        cwd=repo, env={**os.environ, "PYTHONPATH": str(repo)},
        capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == "passed"
    assert receipt["pytest_result"]["executed_cases"] == 1


def test_interrupt_retains_terminal_receipt_and_reaps_owned_check(tmp_path):
    marker = tmp_path / "owned-pytest-pid"
    repo = isolated_checkout(tmp_path, "import os, time\nfrom pathlib import Path\n"
        f"def test_contract():\n    Path({str(marker)!r}).write_text(str(os.getpid()))\n"
        "    time.sleep(60)\n")
    out = tmp_path / "attempt"
    with subprocess.Popen(
        [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
         "--contract", "recorded-methods", "--out", str(out)],
        cwd=repo, env={**os.environ, "PYTHONPATH": str(repo)},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as preflight:
        try:
            deadline = time.monotonic() + 10
            while not marker.exists() and preflight.poll() is None and time.monotonic() < deadline:
                time.sleep(.05)
            assert marker.exists(), "owned pytest did not reach its controlled wait"
            preflight.terminate()
            stdout, stderr = preflight.communicate(timeout=10)
            assert preflight.returncode == 143, stdout + stderr
        finally:
            if preflight.poll() is None:
                preflight.terminate()
                preflight.wait(timeout=10)
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == "interrupted"
    assert receipt["exit_code"] == 143
    assert receipt["release_acceptance"] is False
    with pytest.raises(ProcessLookupError):
        os.kill(int(marker.read_text()), 0)


def test_existing_attempt_refuses_reuse_without_rewriting_evidence(tmp_path):
    repo = isolated_checkout(tmp_path, "def test_contract():\n    assert True\n")
    out = tmp_path / "attempt"
    command = [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
               "--changed-path", "README.md", "--out", str(out)]
    environment = {**os.environ, "PYTHONPATH": str(repo)}
    first = subprocess.run(command, cwd=repo, env=environment,
                           capture_output=True, text=True, timeout=15)
    assert first.returncode == 0, first.stderr
    before = (out / "receipt.json").read_bytes()
    repeated = subprocess.run(command, cwd=repo, env=environment,
                              capture_output=True, text=True, timeout=15)
    assert repeated.returncode == 1
    assert "prior attempts are retained" in repeated.stderr
    assert (out / "receipt.json").read_bytes() == before


def test_receipt_output_cannot_modify_candidate_source(tmp_path):
    repo = isolated_checkout(tmp_path, "def test_contract():\n    assert True\n")
    out = repo / "attempt"
    completed = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.semantic_preflight",
         "--changed-path", "README.md", "--out", str(out)],
        cwd=repo, env={**os.environ, "PYTHONPATH": str(repo)},
        capture_output=True, text=True, timeout=15)
    assert completed.returncode == 1
    assert "outside a source checkout" in completed.stderr
    assert not out.exists()
    assert subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"]) == b""
