#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/ai_employee.log"

# ── Helpers ──────────────────────────────────────────────────────
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

# ── Load .env ────────────────────────────────────────────────────
ENV_FILE="${PROJECT_ROOT}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log "FATAL: .env not found at ${ENV_FILE}"
    exit 1
fi

VAULT_PATH=$(grep '^VAULT_PATH=' "$ENV_FILE" | cut -d'=' -f2-)
if [[ -z "$VAULT_PATH" ]]; then
    log "FATAL: VAULT_PATH not set in .env"
    exit 1
fi
export VAULT_PATH
log "VAULT_PATH=${VAULT_PATH}"

# ── Component definitions ────────────────────────────────────────
NAMES=("gmail_watcher" "orchestrator" "mcp_trigger" "whatsapp_watcher")
SCRIPTS=(
    "${PROJECT_ROOT}/watchers/gmail_watcher.py"
    "${PROJECT_ROOT}/orchestrator.py"
    "${PROJECT_ROOT}/mcp_trigger.py"
    "${PROJECT_ROOT}/watchers/whatsapp_watcher.py"
)
PIDS=(0 0 0 0)

# ── Start / restart a single component by index ─────────────────
start_component() {
    local i=$1
    local name="${NAMES[$i]}"
    local script="${SCRIPTS[$i]}"

    if [[ ! -f "$script" ]]; then
        log "ERROR: ${name} script not found at ${script}"
        return 1
    fi

    uv run python "$script" >> "$LOG_FILE" 2>&1 &
    local pid=$!

    # Give the process a moment to fail on import errors etc.
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        PIDS[$i]=$pid
        log "STARTED: ${name} (PID ${pid})"
        return 0
    else
        PIDS[$i]=0
        log "FAILED:  ${name} could not start"
        return 1
    fi
}

# ── Cleanup on Ctrl+C / exit ────────────────────────────────────
cleanup() {
    log "Shutting down all components..."
    for i in "${!NAMES[@]}"; do
        local pid=${PIDS[$i]}
        if [[ $pid -ne 0 ]] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            wait "$pid" 2>/dev/null
            log "STOPPED: ${NAMES[$i]} (PID ${pid})"
        fi
    done
    log "All components stopped. Goodbye."
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Initial startup ─────────────────────────────────────────────
log "=========================================="
log "  AI Employee - Starting all components"
log "=========================================="

for i in "${!NAMES[@]}"; do
    start_component "$i"
done

# Print summary
echo ""
log "── Startup Summary ──"
running=0
for i in "${!NAMES[@]}"; do
    if [[ ${PIDS[$i]} -ne 0 ]]; then
        log "  [OK]   ${NAMES[$i]}  PID ${PIDS[$i]}"
        ((running++))
    else
        log "  [FAIL] ${NAMES[$i]}"
    fi
done
log "${running}/${#NAMES[@]} components running"
echo ""

if [[ $running -eq 0 ]]; then
    log "FATAL: No components started. Exiting."
    exit 1
fi

# ── Monitor loop – restart crashed processes ─────────────────────
log "Monitoring processes (Ctrl+C to stop all)..."

while true; do
    for i in "${!NAMES[@]}"; do
        local_pid=${PIDS[$i]}
        # Skip components that never started
        [[ $local_pid -eq 0 ]] && continue

        if ! kill -0 "$local_pid" 2>/dev/null; then
            log "CRASH: ${NAMES[$i]} (PID ${local_pid}) is no longer running. Restarting..."
            start_component "$i"
        fi
    done
    sleep 5
done
