"""Exercise the release entry point with real pytest/Ruff in a tiny Git fixture."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import time
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "candidate"
    (repo / "scripts").mkdir(parents=True)
    (repo / "kayakgen").mkdir()
    (repo / "tests").mkdir()
    (repo / "kayakgen/__init__.py").write_text("")
    operations = ROOT / "kayakgen/operations"
    if operations.exists():
        shutil.copytree(
            operations, repo / "kayakgen/operations", ignore=shutil.ignore_patterns("__pycache__")
        )
    shutil.copyfile(ROOT / "scripts/full-gate.sh", repo / "scripts/full-gate.sh")
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n.ruff_cache/\n")
    (repo / "tests/test_fixture.py").write_text(
        "import os\nimport pytest\n\n"
        "@pytest.mark.parametrize('case', range(4))\n"
        "@pytest.mark.skipif(not (os.getenv('KAYAKGEN_OPENFOAM_SMOKE') == '1' and "
        "os.getenv('KAYAKGEN_OPENFOAM_LOCAL_RUN') == '1'), reason='documented opt-in')\n"
        "def test_opt_in(case):\n    assert case >= 0\n\n"
        "def test_basic():\n    assert 2 + 2 == 4\n"
    )
    git(repo, "init", "-q")
    git(repo, "add", ".")
    git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-qm",
        "fixture",
    )
    return repo


def git(repo: Path, *argv: str) -> str:
    return subprocess.check_output(["git", *argv], cwd=repo, text=True).strip()


def gate_env(repo: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "KAYAKGEN_OPENFOAM_SMOKE",
        "KAYAKGEN_OPENFOAM_LOCAL_RUN",
        "KAYAKGEN_GATE_RECEIPT",
        "PYTEST_ADDOPTS",
    ):
        env.pop(key, None)
    env.update(KAYAKGEN_PY=sys.executable, PYTHONPATH=str(repo))
    return env


def run_gate(repo: Path, receipt: Path, **env_updates: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/full-gate.sh", "--receipt", str(receipt)],
        cwd=repo,
        env={**gate_env(repo), **env_updates},
        capture_output=True,
        text=True,
        timeout=45,
    )


def test_full_gate_runs_pytest_then_ruff_and_binds_uncommitted_candidate(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    (repo / "kayakgen/new_candidate.py").write_text("NAME = 'frozen candidate'\n")
    git(repo, "add", "kayakgen/new_candidate.py")
    (repo / "untracked-ø.txt").write_text("frozen untracked input\n")
    index_before = (repo / ".git/index").read_bytes()
    receipt = tmp_path / "full.json"
    completed = run_gate(repo, receipt)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    record = json.loads(receipt.read_text())
    assert record["status"] == "passed"
    assert record["exit_code"] == 0
    assert [step["name"] for step in record["commands"]] == ["pytest", "ruff"]
    assert all(step["status"] == "passed" and step["exit_code"] == 0 for step in record["commands"])
    assert record["commands"][0]["finished_at"] <= record["commands"][1]["started_at"]
    assert record["expected_skips"] == record["observed_skips"] == 4
    assert record["source_unchanged"] is True
    assert (
        record["source_before"]["fingerprint_sha256"]
        == record["source_after"]["fingerprint_sha256"]
    )
    assert (repo / ".git/index").read_bytes() == index_before
    tree = record["source_before"]["tree_sha"]
    assert tree != git(repo, "rev-parse", "HEAD^{tree}")
    assert record["source_before"]["dirty"] is True
    git(repo, "add", "--all")
    git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-qm",
        "accepted unchanged candidate",
    )
    assert tree == git(repo, "rev-parse", "HEAD^{tree}")
    assert Path(record["interpreter"]["executable"]).resolve() == Path(sys.executable).resolve()


def test_explicit_openfoam_configuration_requires_zero_skips(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    receipt = tmp_path / "opt-in.json"
    completed = run_gate(
        repo, receipt, KAYAKGEN_OPENFOAM_SMOKE="1", KAYAKGEN_OPENFOAM_LOCAL_RUN="1"
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    record = json.loads(receipt.read_text())
    assert record["status"] == "passed"
    assert record["expected_skips"] == record["observed_skips"] == 0


def test_inherited_pytest_selection_cannot_hide_a_failure(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with (repo / "tests/test_fixture.py").open("a") as stream:
        stream.write(
            "\ndef test_must_not_be_hidden():\n    assert False, 'mandatory failing case'\n"
        )
    receipt = tmp_path / "selection.json"
    completed = run_gate(repo, receipt, PYTEST_ADDOPTS="-k 'opt_in or basic'")
    assert completed.returncode != 0, completed.stdout + completed.stderr
    record = json.loads(receipt.read_text())
    assert record["status"] == "failed"
    assert record["commands"][0]["exit_code"] == 1
    assert record["commands"][1]["status"] == "not_run"
    assert record["environment_policy"]["pytest_addopts"] == "cleared_for_full_gate"
    assert "mandatory failing case" in completed.stdout


def test_ruff_failure_is_retained_after_successful_pytest(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    (repo / "kayakgen/bad_lint.py").write_text("import os\n")
    receipt = tmp_path / "lint.json"
    completed = run_gate(repo, receipt)
    record = json.loads(receipt.read_text())
    assert completed.returncode != 0
    assert record["status"] == "failed"
    assert [step["exit_code"] for step in record["commands"]] == [0, 1]
    assert record["failure_reasons"] == ["ruff_failed"]
    assert record["source_unchanged"] is True


def test_changed_source_refuses_even_when_both_commands_pass(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with (repo / "tests/test_fixture.py").open("a") as stream:
        stream.write(
            "\ndef test_changes_input():\n    from pathlib import Path\n"
            "    Path('changed-input.txt').write_text('changed during pytest')\n"
        )
    receipt = tmp_path / "changed.json"
    completed = run_gate(repo, receipt)
    record = json.loads(receipt.read_text())
    assert completed.returncode == 1
    assert all(step["exit_code"] == 0 for step in record["commands"])
    assert record["source_unchanged"] is False
    assert record["status"] == "failed"
    assert record["failure_reasons"] == ["source_changed"]


def test_ruff_observes_files_created_by_the_preceding_test_run(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with (repo / "tests/test_fixture.py").open("a") as stream:
        stream.write(
            "\ndef test_creates_lint_error():\n    from pathlib import Path\n"
            "    Path('kayakgen/generated.py').write_text('import os\\n')\n"
        )
    receipt = tmp_path / "order.json"
    completed = run_gate(repo, receipt)
    record = json.loads(receipt.read_text())
    assert completed.returncode == 1
    assert [step["exit_code"] for step in record["commands"]] == [0, 1]
    assert "ruff_failed" in record["failure_reasons"]
    assert "source_changed" in record["failure_reasons"]
    assert "generated.py" in completed.stdout


def test_wrong_skip_count_is_not_full_gate_acceptance(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    tests = repo / "tests/test_fixture.py"
    tests.write_text(tests.read_text().replace("range(4)", "range(3)"))
    receipt = tmp_path / "skips.json"
    completed = run_gate(repo, receipt)
    record = json.loads(receipt.read_text())
    assert completed.returncode == 1
    assert record["status"] == "failed"
    assert record["commands"][0]["exit_code"] == 0
    assert record["commands"][1]["status"] == "not_run"
    assert record["observed_skips"] == 3 and record["expected_skips"] == 4
    assert record["failure_reasons"] == ["skip_count_mismatch"]


def test_existing_receipt_and_nonignored_source_outputs_are_not_overwritten(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    receipt = tmp_path / "prior.json"
    receipt.write_text("prior accepted bytes\n")
    completed = run_gate(repo, receipt)
    assert completed.returncode != 0
    assert receipt.read_text() == "prior accepted bytes\n"
    assert "[full-gate] pytest" not in completed.stdout
    target = repo / "unexpected-receipt.json"
    completed = run_gate(repo, target)
    assert completed.returncode != 0
    assert not target.exists()
    assert "outside source or in a Git-ignored directory" in completed.stderr
    with (repo / ".gitignore").open("a") as stream:
        stream.write("individual.json\n")
    completed = run_gate(repo, repo / "individual.json")
    assert completed.returncode != 0
    assert not (repo / "individual.json").exists()


def test_ignored_output_and_environment_receipt_path_are_allowed(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with (repo / ".gitignore").open("a") as stream:
        stream.write("evidence/\n")
    receipt = repo / "evidence/full.json"
    completed = subprocess.run(
        ["bash", "scripts/full-gate.sh"],
        cwd=repo,
        env={**gate_env(repo), "KAYAKGEN_GATE_RECEIPT": str(receipt)},
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    record = json.loads(receipt.read_text())
    assert record["status"] == "passed" and record["source_unchanged"] is True


def test_deleted_tracked_file_inside_ignored_directory_is_not_recreated(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with (repo / ".gitignore").open("a") as stream:
        stream.write("evidence/\n")
    receipt = repo / "evidence/deleted.json"
    receipt.parent.mkdir()
    receipt.write_text("tracked source\n")
    git(repo, "add", "-f", "evidence/deleted.json")
    receipt.unlink()
    completed = run_gate(repo, receipt)
    assert completed.returncode != 0
    assert not receipt.exists(), "receipt request recreated a deleted tracked source file"


def test_signal_during_final_source_check_is_retained_as_interruption(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    receipt = tmp_path / "finalization-signal.json"
    # Inject a real signal at the final source-check boundary, after actual
    # pytest and Ruff. The production CLI has no fixture or command override.
    script = (
        "import os, signal, sys\nfrom pathlib import Path\n"
        "from kayakgen.operations import gate\n"
        "original = gate._finish_source\n"
        "def interrupted_finish(root, receipt):\n"
        "    os.kill(os.getpid(), signal.SIGTERM)\n"
        "    original(root, receipt)\n"
        "gate._finish_source = interrupted_finish\n"
        "sys.exit(gate.run_gate(Path(sys.argv[1])))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(receipt)],
        cwd=repo,
        env=gate_env(repo),
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 143, completed.stdout + completed.stderr
    record = json.loads(receipt.read_text())
    assert record["status"] == "interrupted"
    assert all(step["exit_code"] == 0 for step in record["commands"])
    assert record["source_unchanged"] is True


def _is_running(pid: int) -> bool:
    try:
        status = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError):
        return False
    return status.rpartition(")")[2].split()[0] != "Z"


def test_terminated_gate_reaps_its_command_and_retains_interruption(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with (repo / "tests/test_fixture.py").open("a") as stream:
        stream.write(
            "\ndef test_slow():\n    import time\n    from pathlib import Path\n"
            "    Path(os.environ['GATE_TEST_STARTED']).write_text(str(os.getpid()))\n"
            "    time.sleep(60)\n"
        )
    marker = tmp_path / "pytest.pid"
    receipt = tmp_path / "interrupted.json"
    process = subprocess.Popen(
        ["bash", "scripts/full-gate.sh", "--receipt", str(receipt)],
        cwd=repo,
        env={**gate_env(repo), "GATE_TEST_STARTED": str(marker)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    command_pid = None
    try:
        deadline = time.monotonic() + 15
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.025)
        assert marker.exists(), "fixture pytest did not reach its live command"
        command_pid = int(marker.read_text())
        assert _is_running(command_pid)
        process.send_signal(signal.SIGTERM)
        output, _ = process.communicate(timeout=15)
        record = json.loads(receipt.read_text())
        assert process.returncode == 143, output
        assert record["status"] == "interrupted" and record["exit_code"] == 143
        assert record["commands"][0]["status"] == "interrupted"
        assert record["commands"][1]["status"] == "not_run"
        assert "interrupted_signal_15" in record["failure_reasons"]
        assert not _is_running(command_pid)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if command_pid is not None and _is_running(command_pid):
            if Path(f"/proc/{command_pid}/cwd").resolve() == repo:
                os.killpg(command_pid, signal.SIGKILL)
