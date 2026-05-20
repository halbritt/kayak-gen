#!/usr/bin/env bash
# Striatum supervised wrapper for Google Gemini CLI.
#
# Lane.command: ["bash", "scripts/gemini-supervised-wrapper.sh"]
#
# Reads newline-terminated JSON packets from stdin (delivered by
# `striatum supervise send --packet-id <pkt>`), drives the full claim-loop
# per packet via the shared library in striatum-wrapper-lib.sh.

set -uo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/striatum-wrapper-lib.sh
. "$HERE/striatum-wrapper-lib.sh"

GEMINI_BIN="${STRIATUM_GEMINI_BIN:-gemini}"
GEMINI_MODEL="${STRIATUM_GEMINI_MODEL:-gemini-3.1-pro-preview}"
require "$GEMINI_BIN"

run_model_with_prompt() {
    local prompt="$1"
    # Gemini appends stdin to the -p argument; passing an empty -p makes
    # the entire prompt arrive on stdin.
    cd "$REPO" || return 1
    printf '%s' "$prompt" | "$GEMINI_BIN" \
        --model "$GEMINI_MODEL" \
        --yolo \
        -p "" \
        >/dev/null 2>&1
}

wrapper_main "gemini-wrapper" "$@"
