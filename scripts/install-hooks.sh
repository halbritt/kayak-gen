#!/usr/bin/env bash
# install-hooks.sh — install scripts/fast-gate.sh as the repo pre-push hook.
#
# Workflow 0062 (P0-GATE-ENFORCE, audit R0): the services->ui boundary
# regression sat red on main for 12 days because nothing forced a local
# test run before push. This installs a pre-push hook that runs the fast
# gate and refuses the push on failure. The FULL suite remains the
# slice-completion / pre-merge gate (docs/RELEASE_DISCIPLINE.md).
#
# Usage (once per clone):
#   scripts/install-hooks.sh
#
# Bypass (emergencies only; does not waive the full-suite pre-merge gate):
#   git push --no-verify

set -euo pipefail

HOOKS_DIR="$(git rev-parse --git-path hooks)"

mkdir -p "$HOOKS_DIR"
cat > "$HOOKS_DIR/pre-push" <<'HOOK'
#!/usr/bin/env bash
# Installed by scripts/install-hooks.sh (workflow 0062, P0-GATE-ENFORCE).
# Runs scripts/fast-gate.sh; a non-zero exit refuses the push.
exec "$(git rev-parse --show-toplevel)/scripts/fast-gate.sh"
HOOK
chmod +x "$HOOKS_DIR/pre-push"
echo "installed: $HOOKS_DIR/pre-push -> scripts/fast-gate.sh"
