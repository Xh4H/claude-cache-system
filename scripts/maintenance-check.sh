#!/bin/bash
# Automated maintenance check for Claude directory
# Run via cron to ensure structure compliance

LOG_FILE="$HOME/.claude/logs/maintenance.log"
CLAUDE_DIR="$HOME/.claude"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log_issue() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Start check
log_issue "=== Maintenance check started ==="

# Run validation
VALIDATION_OUTPUT=$("$CLAUDE_DIR/scripts/validate-structure.sh" 2>&1)
VALIDATION_EXIT=$?

if [ $VALIDATION_EXIT -ne 0 ]; then
    log_issue "Structure validation failed with $VALIDATION_EXIT issues"
    echo "$VALIDATION_OUTPUT" | grep -E "^(❌|⚠️)" | while read line; do
        log_issue "$line"
    done
    
    # Auto-fix safe issues
    log_issue "Attempting auto-fixes..."
    
    # Fix permissions
    find "$CLAUDE_DIR/scripts" -name "*.sh" -exec chmod +x {} \;
    
    # Remove empty directories
    find "$CLAUDE_DIR" -type d -empty -not -path "*/.git/*" -delete 2>/dev/null
    
    # Quick cleanup
    "$CLAUDE_DIR/scripts/claude-cleanup.sh" quick > /dev/null 2>&1
    
    log_issue "Auto-fixes completed"
fi

# Check disk usage
DISK_USAGE=$(du -sh "$CLAUDE_DIR" 2>/dev/null | cut -f1)
log_issue "Directory size: $DISK_USAGE"

# Alert if too large
SIZE_MB=$(du -sm "$CLAUDE_DIR" 2>/dev/null | cut -f1)
if [ $SIZE_MB -gt 500 ]; then
    log_issue "WARNING: Directory exceeds 500MB ($SIZE_MB MB)"
fi

log_issue "=== Maintenance check completed ==="

# Keep log file size in check
tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"