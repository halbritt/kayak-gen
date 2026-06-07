#!/usr/bin/env bash
# full-gate.sh — the release gate, mechanical form (workflow 0066, G1-SKIP-PIN).
#
# Runs the two pre-merge requirements from docs/RELEASE_DISCIPLINE.md in
# order: `ruff check kayakgen tests`, then the FULL pytest suite with the
# skip-count pin — 0 failed, exactly EXPECTED_SKIPS skips (the documented
# OpenFOAM opt-ins unless the OpenFOAM smoke opts are set). This is the
# slice-completion / pre-merge gate that
# striatum workflow review/apply jobs run; scripts/fast-gate.sh is only
# the pre-push convenience net between these gates.
#
# Skip-count pin (audit G1, 2026-06-06; workflow 0067 gate-altitude
# hardening): the script and the in-suite pytest hook both fail unless the
# pytest summary reports exactly EXPECTED_SKIPS skips. EXPECTED_SKIPS is
# derived from the OpenFOAM env knobs.

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "[full-gate] error: not inside a git worktree" >&2
  exit 1
fi
cd "$repo_root"

# KAYAKGEN_PY overrides the interpreter (e.g. striatum worktrees, where the
# venv lives in the primary checkout). Default is the repo convention.
PY="${KAYAKGEN_PY:-.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "[full-gate] error: $PY not found; create .venv or set KAYAKGEN_PY" >&2
  exit 1
fi

echo "[full-gate] ruff check kayakgen tests"
"$PY" -m ruff check kayakgen tests

# Expected skip count: the 4 documented OpenFOAM opt-ins unless the explicit
# OpenFOAM smoke+local-run knobs are both set, in which case those tests must
# pass rather than skip.
if [ "${KAYAKGEN_OPENFOAM_SMOKE:-}" = "1" ] && \
   [ "${KAYAKGEN_OPENFOAM_LOCAL_RUN:-}" = "1" ]; then
  EXPECTED_SKIPS=0
else
  EXPECTED_SKIPS=4
fi
export KAYAKGEN_ENFORCE_SKIP_PIN=1
export KAYAKGEN_EXPECTED_SKIPS="$EXPECTED_SKIPS"

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
summary_line="$(grep -E '^[0-9]+ .+ in [0-9]' "$summary_file" | tail -n 1 || true)"
skipped="$(printf '%s\n' "$summary_line" | grep -Eo '(^|, )[0-9]+ skipped' | grep -Eo '[0-9]+' || true)"
skipped="${skipped:-0}"
case "$skipped" in
  ''|*[!0-9]*)
    echo "[full-gate] FAIL: could not parse numeric skip count from pytest summary: $summary_line" >&2
    exit 1
    ;;
esac
if [ "$skipped" -ne "$EXPECTED_SKIPS" ]; then
  echo "[full-gate] FAIL: $skipped skipped, expected exactly $EXPECTED_SKIPS" \
    "(documented OpenFOAM opt-ins — docs/RELEASE_DISCIPLINE.md)." >&2
  echo "[full-gate] A different count means this environment is missing" \
    "extras (or has OpenFOAM knobs set); the run does not count as a gate." >&2
  exit 1
fi

echo "[full-gate] OK ($skipped skipped == expected $EXPECTED_SKIPS)"
