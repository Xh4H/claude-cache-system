#!/bin/bash
# Enhanced Claude Session Management with Context Bridge
# Wraps the original claude-session.sh with context preservation

# Source the original session script
source "$HOME/.claude/scripts/claude-session.sh"

# Python executable
PYTHON="${PYTHON:-python3}"

# Session bridge script
SESSION_BRIDGE="$HOME/.claude/cache/session_bridge.py"

# Override the session_save function to include context bridging
original_session_save=$(declare -f session_save)
session_save() {
    local topic="${1:-$(echo $CLAUDE_SESSION_TOPIC)}"
    local session_id="${CLAUDE_SESSION_ID:-session_$(date +%Y%m%d_%H%M%S)}"
    
    # Call original save function
    eval "${original_session_save#*\{}"
    
    # Save context patterns
    echo "🌉 Saving context patterns..."
    $PYTHON "$SESSION_BRIDGE" save "$session_id" "$topic" 2>/dev/null || true
}

# Override the session_load function to include context warming
original_session_load=$(declare -f session_load)
session_load() {
    local session_id="$1"
    
    # Call original load function
    eval "${original_session_load#*\{}"
    
    # Load context patterns
    if [ -n "$session_id" ]; then
        echo "🌉 Loading context patterns..."
        $PYTHON "$SESSION_BRIDGE" load "$session_id" 2>/dev/null || true
    fi
}

# New function: Get context-aware file suggestions
session_suggest() {
    local query="$*"
    
    if [ -z "$query" ]; then
        echo "Usage: claude-session suggest <query>"
        return 1
    fi
    
    $PYTHON "$SESSION_BRIDGE" suggest "$query"
}

# New function: Analyze cross-session patterns
session_analyze() {
    echo "📊 Analyzing cross-session patterns..."
    $PYTHON "$SESSION_BRIDGE" analyze
}

# New function: Pre-warm context for a topic
session_warm() {
    local topic="$1"
    
    if [ -z "$topic" ]; then
        echo "Usage: claude-session warm <topic>"
        return 1
    fi
    
    echo "🔥 Pre-warming context for topic: $topic"
    
    # Find recent sessions with similar topics
    local similar_sessions=$(find "$SESSION_DIR" -name "info.txt" -exec grep -l "$topic" {} \; | head -3)
    
    if [ -n "$similar_sessions" ]; then
        for info_file in $similar_sessions; do
            local session_id=$(basename $(dirname "$info_file"))
            echo "  Loading patterns from: $session_id"
            $PYTHON "$SESSION_BRIDGE" load "$session_id" 2>/dev/null || true
        done
    else
        echo "  No similar sessions found"
    fi
}

# Enhanced main dispatcher
claude_session() {
    local cmd="${1:-help}"
    shift
    
    case "$cmd" in
        save|s)      session_save "$@" ;;
        load|l)      session_load "$@" ;;
        suggest)     session_suggest "$@" ;;
        analyze)     session_analyze ;;
        warm|w)      session_warm "$@" ;;
        *)           # Fall back to original dispatcher
                     source "$HOME/.claude/scripts/claude-session.sh"
                     claude-session "$cmd" "$@" ;;
    esac
}

# Enhanced help text
session_help() {
    # Call original help
    source "$HOME/.claude/scripts/claude-session.sh"
    session_help
    
    cat << EOF

Enhanced Commands (with Context Bridge):
  suggest <query>   Get file suggestions based on patterns
  analyze           Analyze cross-session patterns  
  warm <topic>      Pre-warm context from similar sessions
  
Context Bridge Features:
  - Automatic context preservation on save
  - Intelligent cache warming on load
  - Cross-session file pattern learning
  - Priority-based file pre-loading
  
Examples:
  claude-session suggest "database migration"
  claude-session warm "refactoring"
  claude-session analyze
  
EOF
}

# Export enhanced function
export -f claude_session
export -f session_save
export -f session_load
export -f session_suggest
export -f session_analyze
export -f session_warm