#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/cron.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Read VAULT_PATH from .env
ENV_FILE="${PROJECT_ROOT}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log "ERROR: .env file not found at ${ENV_FILE}"
    exit 1
fi

VAULT_PATH=$(grep '^VAULT_PATH=' "$ENV_FILE" | cut -d'=' -f2-)
if [[ -z "$VAULT_PATH" ]]; then
    log "ERROR: VAULT_PATH not set in .env"
    exit 1
fi

NEEDS_ACTION="${VAULT_PATH}/Needs_Action"

if [[ ! -d "$NEEDS_ACTION" ]]; then
    log "ERROR: Needs_Action folder does not exist at ${NEEDS_ACTION}"
    exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S%z')
DATE_TAG=$(date '+%Y%m%d')
FILENAME="WEEKLY_LINKEDIN_TRIGGER_${DATE_TAG}.md"
FILEPATH="${NEEDS_ACTION}/${FILENAME}"

cat > "$FILEPATH" <<EOF
---
type: linkedin_weekly_trigger
created: ${TIMESTAMP}
status: pending
---

## Weekly LinkedIn Post

Trigger created by cron. Use linkedin_posting_skill.md and AI_Employee_Progress.md to draft weekly progress post.
EOF

log "SUCCESS: Created trigger file ${FILENAME}"
