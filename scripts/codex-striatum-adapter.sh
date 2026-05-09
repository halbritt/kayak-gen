#!/usr/bin/env bash
# Striatum process-adapter wrapper for codex exec.
#
# Invoked by:
#   striatum adapter run --session-id SESS --lease-id LEASE \
#       --stdin packet --inherit-stdio
#
# Striatum sets these env vars before spawning this script:
#   STRIATUM_REPO, STRIATUM_SESSION_ID, STRIATUM_JOB_ID, STRIATUM_LEASE_ID
#
# The work packet JSON is piped to stdin.

set -euo pipefail

REPO="${STRIATUM_REPO:?STRIATUM_REPO not set}"
SESSION="${STRIATUM_SESSION_ID:?STRIATUM_SESSION_ID not set}"
JOB="${STRIATUM_JOB_ID:?STRIATUM_JOB_ID not set}"
LEASE="${STRIATUM_LEASE_ID:?STRIATUM_LEASE_ID not set}"

cd "$REPO"

# Read the work packet from stdin
PACKET=$(cat)

# Extract the task prompt path and read it
PROMPT_PATH=$(echo "$PACKET" | jq -r '.task_prompt.path')
FULL_PROMPT="$(cat "$PROMPT_PATH")"

# Append each context doc as a labelled section
while IFS= read -r doc; do
    [[ -z "$doc" ]] && continue
    [[ -f "$doc" ]] || continue
    FULL_PROMPT+=$'\n\n---\n'"# Context: $doc"$'\n\n'"$(cat "$doc")"
done < <(echo "$PACKET" | jq -r '.context.docs[]? // empty' 2>/dev/null || true)

# Run codex exec non-interactively with full workspace write access
echo "$FULL_PROMPT" | codex exec \
    --dangerously-bypass-approvals-and-sandbox \
    -C "$REPO" \
    -

# Publish each expected artifact that was produced
while IFS= read -r artifact; do
    [[ -z "$artifact" ]] && continue
    LOGICAL_NAME=$(echo "$artifact" | jq -r '.logical_name')
    KIND=$(echo "$artifact"         | jq -r '.kind')
    ART_PATH=$(echo "$artifact"     | jq -r '.path')

    if [[ -f "$REPO/$ART_PATH" ]]; then
        striatum --repo "$REPO" publish-artifact \
            --session-id "$SESSION" \
            --job-id     "$JOB"     \
            --lease-id   "$LEASE"   \
            --kind         "$KIND"        \
            --logical-name "$LOGICAL_NAME" \
            --path         "$ART_PATH"
    else
        echo "WARNING: expected artifact not found: $ART_PATH" >&2
    fi
done < <(echo "$PACKET" | jq -c '.expected_artifacts[]? // empty' 2>/dev/null || true)

# Complete the job
striatum --repo "$REPO" complete \
    --session-id "$SESSION" \
    --job-id     "$JOB"     \
    --lease-id   "$LEASE"
