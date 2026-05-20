# Shared helpers for striatum supervised wrappers.
#
# Three sibling wrappers (codex/claude/gemini) source this file. Each
# wrapper supplies a `run_model_with_prompt "$prompt"` shell function
# that invokes its model CLI; the rest of the claim-loop lives here.
#
# Usage in a wrapper:
#
#   #!/usr/bin/env bash
#   set -uo pipefail
#   LIB="$(dirname "$0")/striatum-wrapper-lib.sh"
#   . "$LIB"
#
#   run_model_with_prompt() {
#       printf '%s' "$1" | claude --model opus -p ...
#   }
#
#   wrapper_main "claude" "$@"
#
# Environment variables read by the library:
#   STRIATUM_REPO                          (default: $PWD)
#   STRIATUM_HEARTBEAT_SECONDS             (default: 300)
#
# The wrapper-supplied function MUST be named `run_model_with_prompt`
# and MUST return the exit code of the underlying model CLI.

# shellcheck shell=bash

REPO="${STRIATUM_REPO:-$PWD}"
HEARTBEAT_INTERVAL="${STRIATUM_HEARTBEAT_SECONDS:-300}"
HEARTBEAT_PID=""
WRAPPER_LABEL="${WRAPPER_LABEL:-striatum-wrapper}"

log() { printf '[%s %(%Y-%m-%dT%H:%M:%SZ)T] %s\n' "$WRAPPER_LABEL" -1 "$*" >&2; }

require() {
    command -v "$1" >/dev/null 2>&1 || {
        log "fatal: required binary missing: $1"
        exit 127
    }
}

# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

start_heartbeat() {
    local session_id="$1"
    local lease_id="$2"
    # Spawn the heartbeat in a detached subshell. setsid + disown make
    # the subshell survive even if the parent wrapper loses its
    # controlling terminal or the supervisor SIGTERMs the wrapper group.
    # We track the PID so stop_heartbeat can kill it explicitly on the
    # success path.
    setsid bash -c "
        while :; do
            sleep $HEARTBEAT_INTERVAL
            striatum --repo $REPO heartbeat \
                --session-id $session_id \
                --lease-id $lease_id \
                >/dev/null 2>&1 || true
        done
    " >/dev/null 2>&1 &
    HEARTBEAT_PID=$!
    disown $HEARTBEAT_PID 2>/dev/null || true
}

stop_heartbeat() {
    if [[ -n "$HEARTBEAT_PID" ]] && kill -0 "$HEARTBEAT_PID" 2>/dev/null; then
        # setsid put it in its own process group; kill the group so the
        # while-loop subshell + sleep child both die.
        kill -- -"$HEARTBEAT_PID" 2>/dev/null || kill "$HEARTBEAT_PID" 2>/dev/null || true
    fi
    HEARTBEAT_PID=""
}

cleanup_and_exit() {
    local code="${1:-0}"
    stop_heartbeat
    exit "$code"
}

# ---------------------------------------------------------------------------
# Prompt composition
# ---------------------------------------------------------------------------

build_prompt() {
    local packet="$1"
    local prompt=""

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

    local objective
    objective=$(printf '%s' "$packet" | jq -r '.job.objective // empty')
    if [[ -n "$objective" ]]; then
        prompt+="# Objective"$'\n\n'"$objective"$'\n\n'
    fi

    prompt+="# Write scope (allowed paths only)"$'\n\n'
    while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        prompt+="- $path"$'\n'
    done < <(printf '%s' "$packet" | jq -r '.write_scope.allowed_paths[]? // empty')
    prompt+=$'\n'

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

    prompt+="# Required context (read these before editing)"$'\n\n'
    while IFS= read -r doc; do
        [[ -z "$doc" ]] && continue
        prompt+="- $doc"$'\n'
    done < <(printf '%s' "$packet" | jq -r '.context.docs[]?.path // empty')
    prompt+=$'\n'

    printf '%s' "$prompt"
}

# ---------------------------------------------------------------------------
# Claim loop
# ---------------------------------------------------------------------------

process_packet() {
    local packet="$1"

    local session_id lease_id message_id job_id packet_id
    session_id=$(printf '%s' "$packet" | jq -r '.session.session_id // .session.id // empty')
    lease_id=$(printf '%s' "$packet" | jq -r '.lease.lease_id // .lease.id // empty')
    message_id=$(printf '%s' "$packet" | jq -r '.lease.message_id // empty')
    job_id=$(printf '%s' "$packet" | jq -r '.job.job_id // .job.id // empty')
    packet_id=$(printf '%s' "$packet" | jq -r '.packet_id // empty')

    if [[ -z "$session_id" || -z "$lease_id" || -z "$job_id" ]]; then
        log "fatal: malformed packet (missing session/lease/job ids)"
        return 1
    fi

    if [[ -z "$message_id" ]]; then
        local ack_cmd
        ack_cmd=$(printf '%s' "$packet" | jq -r '.commands.ack // empty')
        message_id=$(printf '%s' "$ack_cmd" | grep -oE -- '--message-id msg_[0-9a-f]+' | awk '{print $2}')
    fi

    log "packet_id=$packet_id job=$job_id session=$session_id lease=$lease_id"

    striatum --repo "$REPO" ack \
        --session-id "$session_id" \
        --message-id "$message_id" \
        --lease-id "$lease_id" >/dev/null 2>&1 \
        || log "warn: ack failed for packet $packet_id (job=$job_id)"

    start_heartbeat "$session_id" "$lease_id"

    local prompt
    prompt=$(build_prompt "$packet")

    local model_exit=0
    if ! run_model_with_prompt "$prompt"; then
        model_exit=$?
        log "model CLI exited $model_exit for job=$job_id"
    fi

    stop_heartbeat

    local all_artifacts_present=1
    while IFS= read -r artifact; do
        [[ -z "$artifact" ]] && continue
        local name kind path required full
        name=$(printf '%s' "$artifact" | jq -r '.logical_name')
        kind=$(printf '%s' "$artifact" | jq -r '.kind')
        path=$(printf '%s' "$artifact" | jq -r '.path')
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
                || log "warn: publish-artifact failed for $path"
        elif [[ "$required" == "true" ]]; then
            all_artifacts_present=0
            log "missing required artifact: $path (logical_name=$name)"
        fi
    done < <(printf '%s' "$packet" | jq -c '.expected_artifacts[]? // empty')

    if [[ "$model_exit" -eq 0 && "$all_artifacts_present" -eq 1 ]]; then
        # Review jobs require submit-review (records a verdict); synthesis
        # jobs use complete. The daemon's "accepted review" edges into
        # downstream jobs (e.g. findings_ledger) fire on a verdict event,
        # not on plain completion — calling `complete` on a review leaves
        # those edges unsatisfied.
        local job_type
        job_type=$(printf '%s' "$packet" | jq -r '.job.job_type // empty')
        if [[ "$job_type" == "review" ]]; then
            local first_path first_kind first_name
            first_path=$(printf '%s' "$packet" | jq -r '.expected_artifacts[0].path // empty')
            first_kind=$(printf '%s' "$packet" | jq -r '.expected_artifacts[0].kind // "finding"')
            first_name=$(printf '%s' "$packet" | jq -r '.expected_artifacts[0].logical_name // "review"')
            if [[ -z "$first_path" || ! -f "$REPO/$first_path" ]]; then
                log "warn: review job=$job_id missing finding artifact for submit-review"
                return 1
            fi
            local verdict="${STRIATUM_WRAPPER_DEFAULT_VERDICT:-accept_with_findings}"
            striatum --repo "$REPO" submit-review \
                --session-id "$session_id" \
                --job-id "$job_id" \
                --lease-id "$lease_id" \
                --kind "$first_kind" \
                --logical-name "$first_name" \
                --path "$first_path" \
                --verdict "$verdict" >/dev/null 2>&1 \
                || { log "warn: submit-review failed for job=$job_id"; return 1; }
            log "submitted review job=$job_id verdict=$verdict"
            return 0
        fi
        striatum --repo "$REPO" complete \
            --session-id "$session_id" \
            --job-id "$job_id" \
            --lease-id "$lease_id" >/dev/null 2>&1 \
            || { log "warn: complete failed for job=$job_id"; return 1; }
        log "completed job=$job_id"
        return 0
    fi

    local block_kind block_description
    if [[ "$model_exit" -ne 0 ]]; then
        block_kind="model_exec_nonzero"
        block_description="model CLI exited $model_exit"
    else
        block_kind="missing_required_artifact"
        block_description="required artifact missing after model run; see wrapper log"
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

wrapper_main() {
    WRAPPER_LABEL="${1:-striatum-wrapper}"
    trap 'cleanup_and_exit 143' SIGTERM
    trap 'cleanup_and_exit 130' SIGINT

    log "ready repo=$REPO heartbeat=${HEARTBEAT_INTERVAL}s"

    require jq
    require striatum

    while IFS= read -r LINE; do
        [[ -z "$LINE" ]] && continue
        process_packet "$LINE" || true
    done

    log "stdin closed; exiting"
    exit 0
}
