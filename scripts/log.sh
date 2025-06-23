#!/bin/bash
# Simple logging for Claude scripts

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
LOG_FILE="$CLAUDE_HOME/logs/claude.log"

log() {
    local level="${2:-INFO}"
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$timestamp] [$level] $msg" >> "$LOG_FILE"
    
    case "$level" in
        ERROR)   echo "❌ $msg" >&2 ;;
        WARN)    echo "⚠️  $msg" ;;
        SUCCESS) echo "✅ $msg" ;;
        DEBUG)   [ "${DEBUG:-0}" = "1" ] && echo "🔍 $msg" ;;
        *)       echo "ℹ️  $msg" ;;
    esac
}

# If called directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    log "$@"
fi
