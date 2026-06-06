#!/usr/bin/env bash
# fast-gate.sh — pre-push convenience gate (workflow 0062, P0-GATE-ENFORCE).
#
# Runs `ruff check kayakgen tests`, then the FAST pytest subset. This is
# NOT the release gate: the slice-completion / pre-merge gate is the FULL
# suite — `.venv/bin/python -m pytest -q` -> 0 failed, exactly the 4
# documented OpenFOAM opt-in skips (docs/RELEASE_DISCIPLINE.md). Striatum
# workflow review/apply jobs run the full suite; this script only keeps
# red from reaching the remote between those gates.
#
# Install as .git/hooks/pre-push via scripts/install-hooks.sh.
#
# Deselect list (re-measured 2026-06-06 after workflow 0066, in a
# striatum per-job worktree with KAYAKGEN_PY -> the primary venv;
# full suite: 1347 passed + 4 skipped in 10:49):
#
#  Named sets (workflow 0062 / remediation plan Q3):
#   tests/test_web_browser.py                      34.3s  browser/visual (Playwright)
#   tests/test_generative_jobs_subprocess.py       10.9s  subprocess lifecycle
#   tests/test_cfd_jobs.py                         29.7s  CFD jobs integration, incl.
#                                                         every fixture-command test
#   tests/test_cli.py::test_cfd_fixture_run_and_status_keep_raw_warning_visible (1.1s)
#   tests/test_web.py::test_cfd_routes_fixture_command_success_remains_raw_unvalidated (0.7s)
#
#  Runtime-dominant integration files (junitxml per-file totals, 2026-06-06;
#  the named sets alone cut only ~51s of a 516s suite, nowhere near the
#  <= ~3 minute budget, so the measured dominators are deselected too):
#   tests/test_generated_closed_body_hardening.py  58.8s
#   tests/test_design_report.py                    36.4s
#   tests/test_generated_closed_body.py            34.8s
#   tests/test_sweep.py                            32.6s
#   tests/test_active_search_nested_keys.py        29.4s
#   tests/test_web_layout.py                       22.8s
#   tests/test_generative_jobs_manager.py          19.4s
#   tests/test_compare.py                          18.6s
#
#  Kept on purpose (protection-critical, cheap): import/services boundary
#  tests, forbidden-copy regressions (test_web_read_models.py,
#  test_desktop_layout.py), claims promotion chain, artifact-store +
#  index-isolation regression, registry/metadata pins.
#
# Measured fast-subset runtime (2026-06-06, post-workflow-0066): 3m42s
# wall — pytest 220.6s (1087 passed / 4 skipped / 2 deselected) + ruff +
# interpreter startup. Budget: <= ~3 minutes — this measurement runs
# slightly over; revisit the deselect list if the subset keeps growing.
# The 4 skips are the documented OpenFOAM opt-ins.
#
# Skip-count pin (audit G1, 2026-06-06): the run fails unless the pytest
# summary reports exactly EXPECTED_SKIPS skips. The pin assumes the
# OpenFOAM env knobs (KAYAKGEN_OPENFOAM_SMOKE, KAYAKGEN_OPENFOAM_LOCAL_RUN)
# are UNSET; a solver-equipped host running the smoke uses the explicit
# opt-in command from docs/RELEASE_DISCIPLINE.md, not this gate.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# KAYAKGEN_PY overrides the interpreter (e.g. striatum worktrees, where the
# venv lives in the primary checkout). Default is the repo convention.
PY="${KAYAKGEN_PY:-.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "[fast-gate] error: $PY not found; create .venv or set KAYAKGEN_PY" >&2
  exit 1
fi

echo "[fast-gate] ruff check kayakgen tests"
"$PY" -m ruff check kayakgen tests

# Expected skip count: the 4 documented OpenFOAM opt-ins
# (docs/RELEASE_DISCIPLINE.md "Pre-merge requirements"). Any other count
# means the environment is missing extras and the run does not count.
EXPECTED_SKIPS=4

# Stream pytest output to the operator while capturing it for the skip-pin
# parse. Under `set -euo pipefail` a red pytest fails the `| tee` pipeline
# and exits the script here, which is the desired gate behavior; the pin
# below only ever sees green runs.
summary_file="$(mktemp)"
trap 'rm -f "$summary_file"' EXIT

echo "[fast-gate] pytest fast subset (full suite remains the release gate)"
"$PY" -m pytest -q \
  --ignore=tests/test_web_browser.py \
  --ignore=tests/test_generative_jobs_subprocess.py \
  --ignore=tests/test_cfd_jobs.py \
  --ignore=tests/test_generated_closed_body_hardening.py \
  --ignore=tests/test_design_report.py \
  --ignore=tests/test_generated_closed_body.py \
  --ignore=tests/test_sweep.py \
  --ignore=tests/test_active_search_nested_keys.py \
  --ignore=tests/test_web_layout.py \
  --ignore=tests/test_generative_jobs_manager.py \
  --ignore=tests/test_compare.py \
  --deselect "tests/test_cli.py::test_cfd_fixture_run_and_status_keep_raw_warning_visible" \
  --deselect "tests/test_web.py::test_cfd_routes_fixture_command_success_remains_raw_unvalidated" \
  2>&1 | tee "$summary_file"

# Skip-count pin (audit G1): a green exit code with the wrong skip count
# means env-gated tests silently skipped; refuse the gate.
skipped="$(grep -Eo '[0-9]+ skipped' "$summary_file" | tail -n 1 | grep -Eo '[0-9]+' || true)"
skipped="${skipped:-0}"
if [ "$skipped" -ne "$EXPECTED_SKIPS" ]; then
  echo "[fast-gate] FAIL: $skipped skipped, expected exactly $EXPECTED_SKIPS" \
    "(documented OpenFOAM opt-ins — docs/RELEASE_DISCIPLINE.md)." >&2
  echo "[fast-gate] A different count means this environment is missing" \
    "extras (or has OpenFOAM knobs set); the run does not count as a gate." >&2
  exit 1
fi

echo "[fast-gate] OK ($skipped skipped == expected $EXPECTED_SKIPS)"
