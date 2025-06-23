#!/bin/bash
# Context Bridge Background Service
# Periodically saves context patterns and cleans old data

CACHE_DIR="$HOME/.claude/cache"
SESSION_BRIDGE="$CACHE_DIR/session_bridge.py"
LOG_FILE="$CACHE_DIR/context-bridge.log"
PYTHON="${PYTHON:-python3}"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Auto-save current session context every 30 minutes
auto_save_context() {
    if [ -n "$CLAUDE_SESSION_ID" ]; then
        log "Auto-saving context for session: $CLAUDE_SESSION_ID"
        $PYTHON "$SESSION_BRIDGE" save "$CLAUDE_SESSION_ID" "$CLAUDE_SESSION_TOPIC" 2>&1 | tee -a "$LOG_FILE"
    fi
}

# Clean old session data (older than 30 days)
clean_old_data() {
    log "Cleaning old session data..."
    
    # Clean old session directories
    find "$HOME/.claude/sessions" -type d -name "session_*" -mtime +30 -exec rm -rf {} \; 2>/dev/null
    
    # Clean old cache files
    find "$CACHE_DIR" -name "*.cache" -mtime +7 -delete 2>/dev/null
    
    # Vacuum SQLite database
    if [ -f "$CACHE_DIR/session_bridge.db" ]; then
        sqlite3 "$CACHE_DIR/session_bridge.db" "VACUUM;" 2>/dev/null
    fi
}

# Optimize context cache
optimize_cache() {
    log "Optimizing context cache..."
    $PYTHON -c "
from session_bridge import SessionBridge
bridge = SessionBridge()
# Trigger cache cleanup in optimizer
bridge.optimizer._clean_old_patterns()
" 2>&1 | tee -a "$LOG_FILE"
}

# Main service loop
main() {
    log "Context Bridge Service started"
    
    while true; do
        # Auto-save every 30 minutes
        auto_save_context
        
        # Clean old data once per day
        if [ "$(date +%H)" == "03" ]; then
            clean_old_data
            optimize_cache
        fi
        
        # Sleep for 30 minutes
        sleep 1800
    done
}

# Handle signals gracefully
trap 'log "Service stopping..."; exit 0' SIGTERM SIGINT

# Check if we should run as daemon
if [ "$1" == "daemon" ]; then
    main
else
    # Run once
    auto_save_context
    if [ "$1" == "clean" ]; then
        clean_old_data
        optimize_cache
    fi
fi