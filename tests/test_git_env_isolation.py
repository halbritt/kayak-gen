"""Git hook environment must not reach fixture repositories."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from kayakgen.operations.git_env import GIT_LOCAL_ENV_VARS, scrub_git_local_env

ROOT = Path(__file__).resolve().parents[1]


def _git(*arguments: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=cwd, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_fixed_list_covers_this_git() -> None:
    reported = set(_git("rev-parse", "--local-env-vars", cwd=ROOT).split())
    assert reported <= set(GIT_LOCAL_ENV_VARS)


def test_scrub_removes_only_repository_local_variables() -> None:
    environ = {
        "GIT_DIR": "/x/.git",
        "GIT_INDEX_FILE": "/x/.git/index",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.bare",
        "GIT_CONFIG_VALUE_0": "true",
        "GIT_AUTHOR_NAME": "kept",
        "PATH": "/usr/bin",
    }
    removed = scrub_git_local_env(environ)
    assert set(removed) == {
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0",
    }
    assert environ == {"GIT_AUTHOR_NAME": "kept", "PATH": "/usr/bin"}


def test_test_session_has_no_repository_local_git_variables() -> None:
    assert not [name for name in GIT_LOCAL_ENV_VARS if name in os.environ]


def _sentinel(tmp_path: Path) -> tuple[Path, str, dict[str, str]]:
    sentinel = tmp_path / "sentinel"
    sentinel.mkdir()
    _git("init", "-q", cwd=sentinel)
    (sentinel / "kept.txt").write_text("kept")
    _git("add", ".", cwd=sentinel)
    _git("-c", "user.name=S", "-c", "user.email=s@example.invalid", "-c", "commit.gpgsign=false",
         "-c", "core.hooksPath=/dev/null", "commit", "-qm", "sentinel", cwd=sentinel)
    head = _git("rev-parse", "HEAD", cwd=sentinel)
    hook_env = {
        **os.environ,
        "GIT_DIR": str(sentinel / ".git"),
        "GIT_INDEX_FILE": str(sentinel / ".git" / "index"),
    }
    return sentinel, head, hook_env


FIXTURE_COMMIT = (
    "import subprocess, sys\n"
    "repo = sys.argv[1]\n"
    "{prelude}"
    "subprocess.run(['git', 'init', '-q', repo], check=True)\n"
    "open(repo + '/a.txt', 'w').write('a')\n"
    "subprocess.run(['git', '-C', repo, 'add', '.'], check=True)\n"
    "subprocess.run(['git', '-C', repo, '-c', 'user.name=F', '-c', 'user.email=f@example.invalid',"
    " '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture'],"
    " check=True)\n"
)


def test_hook_environment_would_redirect_a_fixture_commit(tmp_path: Path) -> None:
    """The hazard itself: without the scrub the fixture commit lands in the sentinel."""

    sentinel, head, hook_env = _sentinel(tmp_path)
    fixture = tmp_path / "fixture-unscrubbed"
    fixture.mkdir()
    subprocess.run(
        [sys.executable, "-c", FIXTURE_COMMIT.format(prelude=""), str(fixture)],
        env=hook_env, cwd=tmp_path, check=False, capture_output=True,
    )
    assert _git("rev-parse", "HEAD", cwd=sentinel) != head


def test_scrubbed_process_leaves_the_hook_repository_alone(tmp_path: Path) -> None:
    sentinel, head, hook_env = _sentinel(tmp_path)
    config_before = (sentinel / ".git" / "config").read_bytes()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    prelude = (
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "from kayakgen.operations.git_env import scrub_git_local_env\n"
        "scrub_git_local_env()\n"
    )
    subprocess.run(
        [sys.executable, "-c", FIXTURE_COMMIT.format(prelude=prelude), str(fixture)],
        env=hook_env, cwd=tmp_path, check=True, capture_output=True,
    )
    assert _git("rev-parse", "HEAD", cwd=sentinel) == head
    assert (sentinel / ".git" / "config").read_bytes() == config_before
    assert _git("log", "--format=%s", cwd=fixture) == "fixture"


def test_gate_entry_scrubs_before_running_checks(tmp_path: Path, monkeypatch) -> None:
    from kayakgen.operations import gate

    seen: dict[str, object] = {}

    def fake_run_gate(*_args: object, **_kwargs: object) -> int:
        seen["leaked"] = [name for name in GIT_LOCAL_ENV_VARS if name in os.environ]
        return 0

    monkeypatch.setenv("GIT_DIR", str(tmp_path / "nowhere.git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "nowhere.index"))
    monkeypatch.setattr(gate, "run_gate", fake_run_gate)
    monkeypatch.setattr(sys, "argv", ["gate"])
    assert gate.gate_entry("fast", "description") == 0
    assert seen["leaked"] == []
