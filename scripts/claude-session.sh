#!/bin/bash
# Claude Session Management - Unified Tool
# Consolidates all session functionality into one comprehensive script

SESSION_DIR="$HOME/.claude/sessions"
KNOWLEDGE_BASE="$HOME/.claude/knowledge-base"
MEMENTO_CMD="npx -y @gannonh/memento-mcp"

# Ensure directories exist
mkdir -p "$SESSION_DIR" "$KNOWLEDGE_BASE"

# Main session command dispatcher
claude-session() {
    local cmd="${1:-help}"
    shift
    
    case "$cmd" in
        save|s)      session_save "$@" ;;
        load|l)      session_load "$@" ;;
        list|ls)     session_list "$@" ;;
        search)      session_search "$@" ;;
        view|v)      session_view "$@" ;;
        init|i)      session_init "$@" ;;
        checkpoint|cp) session_checkpoint "$@" ;;
        end|e)       session_end "$@" ;;
        current|c)   session_current ;;
        index)       session_index ;;
        help|h)      session_help ;;
        *)           echo "Unknown command: $cmd"; session_help ;;
    esac
}

# Initialize new session with context
session_init() {
    local topic="${1:-general}"
    
    echo "🧠 Initializing intelligent session: $topic"
    
    # Query relevant past knowledge
    echo "📚 Relevant knowledge:"
    $MEMENTO_CMD semantic_search "{\"query\": \"$topic\", \"limit\": 3}" 2>/dev/null | \
        grep -E "(problem|solution|insight)" || echo "  No prior knowledge found"
    
    # Check for similar past sessions
    echo -e "\n🕒 Similar past sessions:"
    find "$SESSION_DIR" -name "info.txt" -exec grep -l "$topic" {} \; | head -3 | while read f; do
        echo "  - $(basename $(dirname $f)): $(grep Topic: $f)"
    done
    
    # Create new session
    local session_id="session_$(date +%Y%m%d_%H%M%S)_${topic// /_}"
    mkdir -p "$SESSION_DIR/$session_id"
    
    cat > "$SESSION_DIR/$session_id/info.txt" << EOF
Topic: $topic
Created: $(date)
Status: active
Context: $(pwd)
PID: $$
EOF
    
    # Set environment
    export CLAUDE_SESSION_ID=$session_id
    export CLAUDE_SESSION_TOPIC=$topic
    echo "$session_id" > "$SESSION_DIR/.current"
    
    echo -e "\n✅ Session initialized: $session_id"
}

# Save current session or conversation
session_save() {
    local topic="${1:-$(echo $CLAUDE_SESSION_TOPIC)}"
    local session_id="${CLAUDE_SESSION_ID:-session_$(date +%Y%m%d_%H%M%S)}"
    
    if [ -z "$topic" ]; then
        echo "Usage: claude-session save <topic>"
        return 1
    fi
    
    # Create session directory
    mkdir -p "$SESSION_DIR/$session_id"
    
    # Save session info
    cat > "$SESSION_DIR/$session_id/info.txt" << EOF
Topic: $topic
Created: $(date)
Context: $(pwd)
Status: saved
EOF
    
    # Extract and save to Memento
    echo "💾 Saving to knowledge graph..."
    $MEMENTO_CMD create_entities "{\"entities\": [{
        \"name\": \"$topic\",
        \"entityType\": \"session\",
        \"observations\": [
            \"Session saved on $(date)\",
            \"Working directory: $(pwd)\",
            \"Topic: $topic\"
        ]
    }]}" 2>/dev/null
    
    # Create index entry
    echo "$(date +%Y-%m-%d): $topic - $session_id" >> "$SESSION_DIR/.index"
    
    echo "✅ Session saved: $session_id"
}

# List recent sessions
session_list() {
    local limit="${1:-10}"
    
    echo "📋 Recent sessions:"
    find "$SESSION_DIR" -name "info.txt" -printf "%T@ %p\n" | \
        sort -rn | head -$limit | while read ts path; do
        local dir=$(dirname "$path")
        local id=$(basename "$dir")
        echo -e "\n🔹 $id"
        cat "$path" | grep -E "^(Topic|Created|Status):" | sed 's/^/  /'
    done
}

# Search sessions by content
session_search() {
    local query="$1"
    
    if [ -z "$query" ]; then
        echo "Usage: claude-session search <query>"
        return 1
    fi
    
    echo "🔍 Searching sessions for: $query"
    
    # Search in session files
    grep -r "$query" "$SESSION_DIR" --include="*.txt" | while IFS=: read file line; do
        local session=$(basename $(dirname "$file"))
        echo "  📁 $session: $line"
    done | head -20
    
    # Search in Memento
    echo -e "\n🧠 Knowledge graph results:"
    $MEMENTO_CMD search_nodes "{\"query\": \"$query\"}" 2>/dev/null | \
        jq -r '.entities[]? | "  • \(.name): \(.observations[0] // "")"' | head -10
}

# View specific session details
session_view() {
    local session_id="${1:-$CLAUDE_SESSION_ID}"
    
    if [ -z "$session_id" ]; then
        echo "Usage: claude-session view <session_id>"
        return 1
    fi
    
    local session_path="$SESSION_DIR/$session_id"
    if [ ! -d "$session_path" ]; then
        echo "❌ Session not found: $session_id"
        return 1
    fi
    
    echo "📄 Session: $session_id"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$session_path/info.txt"
    
    if [ -f "$session_path/commands.log" ]; then
        echo -e "\n📝 Commands executed:"
        cat "$session_path/commands.log"
    fi
}

# Load/resume a session
session_load() {
    local session_id="$1"
    
    if [ -z "$session_id" ]; then
        # Show recent sessions to choose from
        session_list 5
        echo -e "\nEnter session ID to load: "
        read session_id
    fi
    
    local session_path="$SESSION_DIR/$session_id"
    if [ ! -d "$session_path" ]; then
        echo "❌ Session not found: $session_id"
        return 1
    fi
    
    # Load session environment
    export CLAUDE_SESSION_ID=$session_id
    export CLAUDE_SESSION_TOPIC=$(grep "Topic:" "$session_path/info.txt" | cut -d: -f2- | xargs)
    echo "$session_id" > "$SESSION_DIR/.current"
    
    # Update status
    sed -i 's/Status: .*/Status: resumed/' "$session_path/info.txt"
    echo "Resumed: $(date)" >> "$session_path/info.txt"
    
    # Change to session context if available
    local context=$(grep "Context:" "$session_path/info.txt" | cut -d: -f2- | xargs)
    if [ -d "$context" ]; then
        cd "$context"
    fi
    
    echo "✅ Session loaded: $session_id"
    echo "📍 Topic: $CLAUDE_SESSION_TOPIC"
    echo "📂 Context: $context"
}

# Get current session info
session_current() {
    if [ -z "$CLAUDE_SESSION_ID" ]; then
        echo "❌ No active session"
        return 1
    fi
    
    echo "📍 Current session: $CLAUDE_SESSION_ID"
    echo "🏷️  Topic: $CLAUDE_SESSION_TOPIC"
    session_view "$CLAUDE_SESSION_ID"
}

# Create checkpoint in current session
session_checkpoint() {
    local name="${1:-checkpoint_$(date +%H%M%S)}"
    
    if [ -z "$CLAUDE_SESSION_ID" ]; then
        echo "❌ No active session"
        return 1
    fi
    
    local checkpoint_file="$SESSION_DIR/$CLAUDE_SESSION_ID/checkpoint_$name.txt"
    
    cat > "$checkpoint_file" << EOF
Checkpoint: $name
Time: $(date)
Working Directory: $(pwd)
Git Status: $(git status --short 2>/dev/null | head -5)
EOF
    
    echo "✅ Checkpoint created: $name"
}

# End current session
session_end() {
    if [ -z "$CLAUDE_SESSION_ID" ]; then
        echo "❌ No active session"
        return 1
    fi
    
    # Update status
    sed -i 's/Status: .*/Status: completed/' "$SESSION_DIR/$CLAUDE_SESSION_ID/info.txt"
    echo "Completed: $(date)" >> "$SESSION_DIR/$CLAUDE_SESSION_ID/info.txt"
    
    # Clear environment
    local topic="$CLAUDE_SESSION_TOPIC"
    unset CLAUDE_SESSION_ID
    unset CLAUDE_SESSION_TOPIC
    rm -f "$SESSION_DIR/.current"
    
    echo "✅ Session ended: $topic"
}

# Index all sessions for faster search
session_index() {
    echo "🔄 Indexing sessions..."
    
    > "$SESSION_DIR/.index"
    
    find "$SESSION_DIR" -name "info.txt" | while read info_file; do
        local session_id=$(basename $(dirname "$info_file"))
        local topic=$(grep "Topic:" "$info_file" | cut -d: -f2- | xargs)
        local created=$(grep "Created:" "$info_file" | cut -d: -f2- | xargs)
        echo "$created|$session_id|$topic" >> "$SESSION_DIR/.index"
    done
    
    local count=$(wc -l < "$SESSION_DIR/.index")
    echo "✅ Indexed $count sessions"
}

# Help text
session_help() {
    cat << EOF
Claude Session Management - Unified Tool

Usage: claude-session <command> [options]

Commands:
  init <topic>      Initialize new session with context
  save <topic>      Save current work as session
  load [id]         Load/resume a session
  list [n]          List recent sessions (default: 10)
  search <query>    Search sessions by content
  view [id]         View session details
  current           Show current session info
  checkpoint [name] Create checkpoint in current session
  end               End current session
  index             Rebuild session index
  help              Show this help

Shortcuts:
  claude-session s  = save
  claude-session l  = load
  claude-session ls = list
  claude-session c  = current
  
Environment Variables:
  CLAUDE_SESSION_ID    Current session ID
  CLAUDE_SESSION_TOPIC Current session topic

Examples:
  claude-session init "refactoring auth system"
  claude-session save "completed oauth implementation"
  claude-session search "database migration"
  claude-session load session_20250622_140000_auth

EOF
}

# Quick aliases
alias cs='claude-session'
alias qsave='claude-session save'
alias cresume='claude-session load'
alias clast='claude-session list 5'

# Export main function
export -f claude-session

# Auto-load current session on shell start
if [ -f "$SESSION_DIR/.current" ]; then
    current_id=$(cat "$SESSION_DIR/.current")
    if [ -d "$SESSION_DIR/$current_id" ]; then
        export CLAUDE_SESSION_ID=$current_id
        export CLAUDE_SESSION_TOPIC=$(grep "Topic:" "$SESSION_DIR/$current_id/info.txt" | cut -d: -f2- | xargs)
    fi
fi