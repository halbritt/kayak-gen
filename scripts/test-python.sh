#!/usr/bin/env bash
# Print the Python interpreter the tests use.
# Order: KAYAKGEN_PY, this worktree's .venv, the primary checkout's .venv.
# A linked worktree has no .venv of its own, so the last step lets the mise
# test tasks run there without setting KAYAKGEN_PY by hand.
set -euo pipefail

if [ -n "${KAYAKGEN_PY:-}" ]; then
  printf '%s\n' "$KAYAKGEN_PY"
  exit 0
fi
root="$(git rev-parse --show-toplevel)"
if [ -x "$root/.venv/bin/python" ]; then
  printf '%s\n' "$root/.venv/bin/python"
  exit 0
fi
common="$(git rev-parse --path-format=absolute --git-common-dir)"
primary="$(dirname "$common")"
if [ -x "$primary/.venv/bin/python" ]; then
  printf '%s\n' "$primary/.venv/bin/python"
  exit 0
fi
echo "[test-python] error: no interpreter; create .venv or set KAYAKGEN_PY" >&2
exit 1
