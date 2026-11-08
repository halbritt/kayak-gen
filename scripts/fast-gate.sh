#!/usr/bin/env bash
# The pre-push convenience gate retains its fixed Ruff/pytest subset and skip pin.
# It shares renderer admission with the complete release gate.
# KAYAKGEN_PY keeps worktrees usable with the primary checkout's interpreter.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "[fast-gate] error: not inside a git worktree" >&2
  exit 1
fi
cd "$repo_root"
PY="${KAYAKGEN_PY:-.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "[fast-gate] error: $PY not found; create .venv or set KAYAKGEN_PY" >&2
  exit 1
fi
exec "$PY" -m kayakgen.operations.fast_gate "$@"
