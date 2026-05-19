#!/usr/bin/env bash
# Striatum supervised wrapper for codex.
#
# Lives at scripts/codex-supervised-wrapper.sh; intended to be the lane.command
# for codex-bound lanes that go through `striatum supervise start` (the
# long-lived agent-per-session pattern; RFC 0009 / the FIFO protocol in
# striatum docs/dogfood/049/design/codex/DESIGN.md).
#
# Invocation:
#   "command": ["bash", "scripts/codex-supervised-wrapper.sh"]
# in workflow.json under the codex lane.
#
# Behavior:
# - Reads newline-terminated JSON work packets from stdin (delivered by
#   `striatum supervise send --packet-id <pkt>`).
# - For each packet:
#     1) striatum ack
#     2) spawn a background heartbeat tick every HEARTBEAT_INTERVAL seconds
#     3) compose a codex prompt from task_prompt.path + context.docs +
#        write_scope + expected_artifacts, pipe to `codex exec ... -`
#     4) on codex success + every expected artifact present →
#        striatum publish-artifact for each + striatum complete
#     5) otherwise → striatum block with a structured error
# - Stops cleanly on stdin EOF or SIGTERM (supervise stop sends SIGTERM,
#   then SIGKILL after 5 s).
#
# All striatum CLI invocations honour --repo so the wrapper works no matter
# what CWD the supervisor launched it from. Stderr is what shows up in the
# supervisor's log file; stdout is the FIFO and must stay quiet (DEVNULL per
# the supervisor contract).

set -uo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO="${STRIATUM_REPO:-$PWD}"
HEARTBEAT_INTERVAL="${STRIATUM_CODEX_HEARTBEAT_SECONDS:-300}"  # 5 minutes
HEARTBEAT_PID=""

CODEX_BIN="${STRIATUM_CODEX_BIN:-codex}"
CODEX_MODEL="${STRIATUM_CODEX_MODEL:-gpt-5.5}"

log() { printf '[codex-wrapper %(%Y-%m-%dT%H:%M:%SZ)T] %s\n' -1 "$*" >&2; }

require() {
    command -v "$1" >/dev/null 2>&1 || {
        log "fatal: required binary missing: $1"
        exit 127
    }
}

require jq
require "$CODEX_BIN"
require striatum

# ---------------------------------------------------------------------------
# Heartbeat helpers
# ---------------------------------------------------------------------------

start_heartbeat() {
    local session_id="$1"
    local lease_id="$2"
    (
        # Tick until killed. Failures (e.g. lease expired) are non-fatal here;
        # the foreground codex exec will eventually error and the parent will
        # call striatum block.
        while :; do
            sleep "$HEARTBEAT_INTERVAL"
            striatum --repo "$REPO" heartbeat \
                --session-id "$session_id" \
                --lease-id "$lease_id" \
                >/dev/null 2>&1 || true
        done
    ) &
    HEARTBEAT_PID=$!
}

stop_heartbeat() {
    if [[ -n "$HEARTBEAT_PID" ]] && kill -0 "$HEARTBEAT_PID" 2>/dev/null; then
        kill "$HEARTBEAT_PID" 2>/dev/null || true
        wait "$HEARTBEAT_PID" 2>/dev/null || true
    fi
    HEARTBEAT_PID=""
}

cleanup_and_exit() {
    local code="${1:-0}"
    stop_heartbeat
    exit "$code"
}

trap 'cleanup_and_exit 143' SIGTERM
trap 'cleanup_and_exit 130' SIGINT

# ---------------------------------------------------------------------------
# Packet processing
# ---------------------------------------------------------------------------

build_prompt() {
    local packet="$1"
    local prompt
    prompt=""

    # 1. Task prompt body
    local task_prompt_path
    task_prompt_path=$(printf '%s' "$packet" | jq -r '.task_prompt.path // empty')
    if [[ -n "$task_prompt_path" && -f "$REPO/$task_prompt_path" ]]; then
        prompt+=$(cat "$REPO/$task_prompt_path")
        prompt+=$'\n\n'
    else
        local inline_prompt
        inline_prompt=$(printf '%s' "$packet" | jq -r '.task_prompt.content // empty')
        prompt+="$inline_prompt"
        prompt+=$'\n\n'
    fi

    # 2. Job objective (always present on the packet)
    local objective
    objective=$(printf '%s' "$packet" | jq -r '.job.objective // empty')
    if [[ -n "$objective" ]]; then
        prompt+="# Objective"$'\n\n'"$objective"$'\n\n'
    fi

    # 3. Write scope — name the files the agent may touch
    prompt+="# Write scope (allowed paths only)"$'\n\n'
    while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        prompt+="- $path"$'\n'
    done < <(printf '%s' "$packet" | jq -r '.write_scope.allowed_paths[]? // empty')
    prompt+=$'\n'

    # 4. Forbidden paths
    local forbidden
    forbidden=$(printf '%s' "$packet" | jq -r '.write_scope.forbidden_paths[]? // empty')
    if [[ -n "$forbidden" ]]; then
        prompt+="# Forbidden paths"$'\n\n'
        while IFS= read -r path; do
            [[ -z "$path" ]] && continue
            prompt+="- $path"$'\n'
        done <<<"$forbidden"
        prompt+=$'\n'
    fi

    # 5. Expected artifacts — explicit paths the agent MUST produce
    prompt+="# Required artifacts (publish these paths before exit)"$'\n\n'
    while IFS= read -r artifact; do
        [[ -z "$artifact" ]] && continue
        local name kind path
        name=$(printf '%s' "$artifact" | jq -r '.logical_name')
        kind=$(printf '%s' "$artifact" | jq -r '.kind')
        path=$(printf '%s' "$artifact" | jq -r '.path')
        prompt+="- $name ($kind) → $path"$'\n'
    done < <(printf '%s' "$packet" | jq -c '.expected_artifacts[]? // empty')
    prompt+=$'\n'

    # 6. Context docs — referenced by path so the agent can `cat` them
    prompt+="# Required context (read these before editing)"$'\n\n'
    while IFS= read -r doc; do
        [[ -z "$doc" ]] && continue
        prompt+="- $doc"$'\n'
    done < <(printf '%s' "$packet" | jq -r '.context.docs[]?.path // empty')
    prompt+=$'\n'

    printf '%s' "$prompt"
}

process_packet() {
    local packet="$1"

    local session_id lease_id message_id job_id packet_id
    session_id=$(printf '%s' "$packet" | jq -r '.session.id')
    lease_id=$(printf '%s' "$packet" | jq -r '.lease.id')
    message_id=$(printf '%s' "$packet" | jq -r '.lease.message_id // .commands.ack | tostring | capture("--message-id (?<m>msg_[0-9a-f]+)").m // empty')
    job_id=$(printf '%s' "$packet" | jq -r '.job.id')
    packet_id=$(printf '%s' "$packet" | jq -r '.packet_id')

    if [[ "$session_id" == "null" || "$lease_id" == "null" || "$job_id" == "null" ]]; then
        log "fatal: malformed packet (missing session/lease/job ids)"
        return 1
    fi

    # Fall back to grepping the ack command for the message_id if it isn't
    # present as a structured field on the packet (the supervise.send body
    # includes both).
    if [[ -z "$message_id" || "$message_id" == "null" ]]; then
        local ack_cmd
        ack_cmd=$(printf '%s' "$packet" | jq -r '.commands.ack')
        message_id=$(printf '%s' "$ack_cmd" | grep -oE -- '--message-id msg_[0-9a-f]+' | awk '{print $2}')
    fi

    log "packet_id=$packet_id job=$job_id session=$session_id lease=$lease_id"

    # 1. ack
    if ! striatum --repo "$REPO" ack \
        --session-id "$session_id" \
        --message-id "$message_id" \
        --lease-id "$lease_id" >/dev/null 2>&1; then
        log "warn: ack failed for packet $packet_id (job=$job_id); continuing"
    fi

    # 2. heartbeat
    start_heartbeat "$session_id" "$lease_id"

    # 3. compose prompt and run codex
    local prompt
    prompt=$(build_prompt "$packet")

    local codex_exit=0
    if ! printf '%s' "$prompt" | "$CODEX_BIN" exec \
        --model "$CODEX_MODEL" \
        --dangerously-bypass-approvals-and-sandbox \
        -C "$REPO" \
        - >/dev/null 2>&1; then
        codex_exit=$?
        log "codex exec exited $codex_exit for job=$job_id"
    fi

    # 4. stop heartbeat before terminal verb
    stop_heartbeat

    # 5. publish + complete or block
    local all_artifacts_present=1
    local published_any=0
    while IFS= read -r artifact; do
        [[ -z "$artifact" ]] && continue
        local name kind path full
        name=$(printf '%s' "$artifact" | jq -r '.logical_name')
        kind=$(printf '%s' "$artifact" | jq -r '.kind')
        path=$(printf '%s' "$artifact" | jq -r '.path')
        local required
        required=$(printf '%s' "$artifact" | jq -r '.required // false')
        full="$REPO/$path"
        if [[ -f "$full" ]]; then
            striatum --repo "$REPO" publish-artifact \
                --session-id "$session_id" \
                --job-id "$job_id" \
                --lease-id "$lease_id" \
                --kind "$kind" \
                --logical-name "$name" \
                --path "$path" >/dev/null 2>&1 \
                && published_any=1 \
                || log "warn: publish-artifact failed for $path"
        elif [[ "$required" == "true" ]]; then
            all_artifacts_present=0
            log "missing required artifact: $path (logical_name=$name)"
        fi
    done < <(printf '%s' "$packet" | jq -c '.expected_artifacts[]? // empty')

    if [[ "$codex_exit" -eq 0 && "$all_artifacts_present" -eq 1 ]]; then
        if ! striatum --repo "$REPO" complete \
            --session-id "$session_id" \
            --job-id "$job_id" \
            --lease-id "$lease_id" >/dev/null 2>&1; then
            log "warn: complete failed for job=$job_id"
            return 1
        fi
        log "completed job=$job_id"
        return 0
    fi

    # Failure path: record the block so the operator can inspect.
    local block_kind block_description
    if [[ "$codex_exit" -ne 0 ]]; then
        block_kind="codex_exec_nonzero"
        block_description="codex exec exited $codex_exit"
    else
        block_kind="missing_required_artifact"
        block_description="required artifact missing after codex exec; see wrapper log"
    fi
    striatum --repo "$REPO" block \
        --session-id "$session_id" \
        --job-id "$job_id" \
        --lease-id "$lease_id" \
        --kind "$block_kind" \
        --severity blocked \
        --description "$block_description" >/dev/null 2>&1 \
        || log "warn: block call failed for job=$job_id"
    log "blocked job=$job_id kind=$block_kind"
    return 1
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

log "ready repo=$REPO heartbeat=${HEARTBEAT_INTERVAL}s codex=$CODEX_BIN model=$CODEX_MODEL"

while IFS= read -r LINE; do
    [[ -z "$LINE" ]] && continue
    process_packet "$LINE" || true
done

log "stdin closed; exiting"
exit 0
