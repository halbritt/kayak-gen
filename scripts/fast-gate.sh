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
# Deselect list (measured on the operator workstation 2026-06-06;
# full suite: 1309 passed + 4 skipped in 8:36):
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
# Measured fast-subset runtime (2026-06-06): 2m57s wall — pytest 175.4s
# (1052 passed / 4 skipped / 2 deselected) + ruff + interpreter startup.
# Budget: <= ~3 minutes. The 4 skips are the documented OpenFOAM opt-ins.

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
  --deselect "tests/test_web.py::test_cfd_routes_fixture_command_success_remains_raw_unvalidated"

echo "[fast-gate] OK"
