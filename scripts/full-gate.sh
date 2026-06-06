#!/usr/bin/env bash
# full-gate.sh — the release gate, mechanical form (workflow 0066, G1-SKIP-PIN).
#
# Runs the two pre-merge requirements from docs/RELEASE_DISCIPLINE.md in
# order: `ruff check kayakgen tests`, then the FULL pytest suite with the
# skip-count pin — 0 failed, exactly EXPECTED_SKIPS skips (the documented
# OpenFOAM opt-ins). This is the slice-completion / pre-merge gate that
# striatum workflow review/apply jobs run; scripts/fast-gate.sh is only
# the pre-push convenience net between these gates.
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
  echo "[full-gate] error: $PY not found; create .venv or set KAYAKGEN_PY" >&2
  exit 1
fi

echo "[full-gate] ruff check kayakgen tests"
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

echo "[full-gate] pytest full suite (this is the release gate)"
"$PY" -m pytest -q 2>&1 | tee "$summary_file"

# Skip-count pin (audit G1): a green exit code with the wrong skip count
# means env-gated tests silently skipped; refuse the gate.
skipped="$(grep -Eo '[0-9]+ skipped' "$summary_file" | tail -n 1 | grep -Eo '[0-9]+' || true)"
skipped="${skipped:-0}"
if [ "$skipped" -ne "$EXPECTED_SKIPS" ]; then
  echo "[full-gate] FAIL: $skipped skipped, expected exactly $EXPECTED_SKIPS" \
    "(documented OpenFOAM opt-ins — docs/RELEASE_DISCIPLINE.md)." >&2
  echo "[full-gate] A different count means this environment is missing" \
    "extras (or has OpenFOAM knobs set); the run does not count as a gate." >&2
  exit 1
fi

echo "[full-gate] OK ($skipped skipped == expected $EXPECTED_SKIPS)"
