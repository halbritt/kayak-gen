"""Gate-script manifest self-checks (audit G4, workflow 0066).

The fast gate's ignore/deselect lists are load-bearing gate logic with no
other test: a renamed test file silently turns ``--ignore`` into a no-op,
and a renamed test function makes ``--deselect`` select nothing. These
tests pin the manifest against the repo so that rot fails loudly, and pin
the presence of the skip-count enforcement (audit G1) in both gate
scripts so it cannot silently regress back to claimed-but-absent.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAST_GATE = REPO_ROOT / "scripts" / "fast-gate.sh"
FULL_GATE = REPO_ROOT / "scripts" / "full-gate.sh"


def _fast_gate_text() -> str:
    return FAST_GATE.read_text(encoding="utf-8")


def _ignore_paths() -> list[str]:
    # Matches the canonical form used in the script: --ignore=tests/foo.py
    return re.findall(r"--ignore=(\S+)", _fast_gate_text())


def _deselect_nodeids() -> list[str]:
    # Matches the canonical form used in the script: --deselect "nodeid"
    return re.findall(r'--deselect "([^"]+)"', _fast_gate_text())


def test_every_ignore_path_exists_in_repo() -> None:
    paths = _ignore_paths()
    assert paths, "fast-gate.sh no longer declares any --ignore paths"
    missing = [p for p in paths if not (REPO_ROOT / p).is_file()]
    assert not missing, (
        f"fast-gate.sh --ignore paths missing from the repo: {missing}; "
        "a renamed test file makes --ignore a silent no-op (audit G4)"
    )


def test_every_deselect_nodeid_still_collects() -> None:
    nodeids = _deselect_nodeids()
    assert nodeids, "fast-gate.sh no longer declares any --deselect nodeids"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *nodeids],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    # Exit code 4 (usage error) / 5 (no tests collected) both mean a
    # nodeid rotted; either way --deselect would deselect nothing.
    assert result.returncode == 0, (
        f"pytest --collect-only failed (exit {result.returncode}) for the "
        f"fast-gate --deselect nodeids {nodeids}:\n{result.stdout}\n{result.stderr}"
    )
    for nodeid in nodeids:
        assert nodeid in result.stdout, (
            f"--deselect nodeid {nodeid!r} no longer collects; "
            "fast-gate.sh would silently run the test it means to skip"
        )


def test_both_gate_scripts_contain_the_skip_count_pin() -> None:
    # Audit G1: the skip pin was once claimed in the commit subject and
    # the release doc while nothing enforced it. Pin its presence — the
    # named expected count and the comparison that refuses the run.
    for script in (FAST_GATE, FULL_GATE):
        assert script.is_file(), f"{script.name} missing from scripts/"
        text = script.read_text(encoding="utf-8")
        assert "EXPECTED_SKIPS=4" in text, (
            f"{script.name} lost the EXPECTED_SKIPS=4 pin "
            "(docs/RELEASE_DISCIPLINE.md documents exactly 4 OpenFOAM opt-ins)"
        )
        assert re.search(r"-ne\s+\"\$EXPECTED_SKIPS\"", text), (
            f"{script.name} no longer compares the parsed skip count "
            "against EXPECTED_SKIPS; the pin is claimed but unenforced (audit G1)"
        )
