#!/usr/bin/env bash
# The full release gate executes pytest and its skip pin, then Ruff.
# KAYAKGEN_PY keeps worktrees usable with the primary checkout's interpreter.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "[full-gate] error: not inside a git worktree" >&2
  exit 1
fi
cd "$repo_root"
PY="${KAYAKGEN_PY:-.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "[full-gate] error: $PY not found; create .venv or set KAYAKGEN_PY" >&2
  exit 1
fi
exec "$PY" -m kayakgen.operations.gate "$@"
