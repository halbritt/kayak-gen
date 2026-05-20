#!/usr/bin/env bash
# Striatum supervised wrapper for Claude Code (Anthropic).
#
# Lane.command: ["bash", "scripts/claude-supervised-wrapper.sh"]
#
# Reads newline-terminated JSON packets from stdin (delivered by
# `striatum supervise send --packet-id <pkt>`), drives the full claim-loop
# per packet via the shared library in striatum-wrapper-lib.sh.

set -uo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/striatum-wrapper-lib.sh
. "$HERE/striatum-wrapper-lib.sh"

CLAUDE_BIN="${STRIATUM_CLAUDE_BIN:-claude}"
CLAUDE_MODEL="${STRIATUM_CLAUDE_MODEL:-opus}"
require "$CLAUDE_BIN"

run_model_with_prompt() {
    local prompt="$1"
    printf '%s' "$prompt" | "$CLAUDE_BIN" \
        --model "$CLAUDE_MODEL" \
        -p \
        --dangerously-skip-permissions \
        --output-format text \
        --add-dir "$REPO" \
        >/dev/null 2>&1
}

wrapper_main "claude-wrapper" "$@"
