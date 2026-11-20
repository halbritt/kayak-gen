#!/usr/bin/env bash
# install-hooks.sh — install scripts/fast-gate.sh as the repo pre-push hook.
#
# The hook refuses a push when the fast gate fails. Pre-merge checks
# include the full release gate described in docs/RELEASE_DISCIPLINE.md.
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
# Installed by scripts/install-hooks.sh.
# Runs scripts/fast-gate.sh; a non-zero exit refuses the push.
exec "$(git rev-parse --show-toplevel)/scripts/fast-gate.sh"
HOOK
chmod +x "$HOOKS_DIR/pre-push"
echo "installed: $HOOKS_DIR/pre-push -> scripts/fast-gate.sh"
