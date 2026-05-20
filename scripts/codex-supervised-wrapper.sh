#!/usr/bin/env bash
# Striatum supervised wrapper for codex.
#
# Lane.command: ["bash", "scripts/codex-supervised-wrapper.sh"]
#
# Reads newline-terminated JSON packets from stdin (delivered by
# `striatum supervise send --packet-id <pkt>`), drives the full claim-loop
# per packet via the shared library in striatum-wrapper-lib.sh.

set -uo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/striatum-wrapper-lib.sh
. "$HERE/striatum-wrapper-lib.sh"

CODEX_BIN="${STRIATUM_CODEX_BIN:-codex}"
CODEX_MODEL="${STRIATUM_CODEX_MODEL:-gpt-5.5}"
require "$CODEX_BIN"

run_model_with_prompt() {
    local prompt="$1"
    printf '%s' "$prompt" | "$CODEX_BIN" exec \
        --model "$CODEX_MODEL" \
        --dangerously-bypass-approvals-and-sandbox \
        -C "$REPO" \
        - >/dev/null 2>&1
}

wrapper_main "codex-wrapper" "$@"
