#!/bin/bash
# Setup script for session bridge integration

echo "🌉 Setting up Claude Session Context Bridge..."

# Backup original bashrc
cp ~/.bashrc ~/.bashrc.backup-session-bridge-$(date +%Y%m%d-%H%M%S)

# Update bashrc to use enhanced session management
cat >> ~/.bashrc << 'EOF'

# ================== Session Context Bridge ==================
# Enhanced session management with context preservation
if [ -f ~/.claude/scripts/claude-session-enhanced.sh ]; then
    source ~/.claude/scripts/claude-session-enhanced.sh
    
    # Override aliases to use enhanced version
    alias cs='claude_session'
    alias qsave='claude_session save'
    alias qlist='claude_session list'
    alias qload='claude_session load'
    alias cresume='claude_session load'
    alias clast='claude_session list 5'
    
    # New context-aware aliases
    alias csuggest='claude_session suggest'
    alias canalyze='claude_session analyze'
    alias cwarm='claude_session warm'
    
    # Context bridge commands
    alias context-save='python3 ~/.claude/cache/session_bridge.py save'
    alias context-load='python3 ~/.claude/cache/session_bridge.py load'
    alias context-analyze='python3 ~/.claude/cache/session_bridge.py analyze'
fi

# Auto-save context on shell exit
trap 'claude_session checkpoint "shell-exit" 2>/dev/null' EXIT

# Context-aware cd function
cd() {
    builtin cd "$@"
    # Suggest files when entering a project directory
    if [[ "$PWD" =~ /(PROJECTS|SEARXNG|AI-TOOLS|THESIS)/ ]] && [ -z "$CLAUDE_NO_AUTO_SUGGEST" ]; then
        local project=$(basename "$PWD")
        local suggestions=$(claude_session suggest "$project" 2>/dev/null | head -5)
        if [ -n "$suggestions" ]; then
            echo "💡 Recent files in similar contexts:"
            echo "$suggestions"
        fi
    fi
}

# Quick context status
context-status() {
    echo "📊 Context Bridge Status:"
    if [ -n "$CLAUDE_SESSION_ID" ]; then
        echo "  • Active Session: $CLAUDE_SESSION_ID"
        echo "  • Topic: $CLAUDE_SESSION_TOPIC"
    else
        echo "  • No active session"
    fi
    
    local cache_size=$(du -sh ~/.claude/cache 2>/dev/null | cut -f1)
    echo "  • Cache Size: ${cache_size:-unknown}"
    
    local db_size=$(du -h ~/.claude/cache/session_bridge.db 2>/dev/null | cut -f1)
    echo "  • Context DB: ${db_size:-not found}"
}

# ================== End Session Context Bridge ==================
EOF

# Create a cron job for periodic context saving
echo "Setting up periodic context saving..."
(crontab -l 2>/dev/null; echo "*/30 * * * * /home/mik/.claude/scripts/context-bridge-service.sh >/dev/null 2>&1") | crontab -

# Initialize the context database
echo "Initializing context database..."
python3 ~/.claude/cache/session_bridge.py analyze >/dev/null 2>&1

# Create integration test
cat > ~/.claude/scripts/test-session-bridge.sh << 'EOF'
#!/bin/bash
# Test session bridge functionality

echo "🧪 Testing Session Context Bridge..."

# Test 1: Save context
echo -e "\nTest 1: Saving context..."
export CLAUDE_SESSION_ID="test_session_$(date +%s)"
export CLAUDE_SESSION_TOPIC="test_integration"
python3 ~/.claude/cache/session_bridge.py save

# Test 2: Load context
echo -e "\nTest 2: Loading context..."
python3 ~/.claude/cache/session_bridge.py load "$CLAUDE_SESSION_ID"

# Test 3: Get suggestions
echo -e "\nTest 3: Getting suggestions..."
python3 ~/.claude/cache/session_bridge.py suggest "test"

# Test 4: Analyze patterns
echo -e "\nTest 4: Analyzing patterns..."
python3 ~/.claude/cache/session_bridge.py analyze | head -10

echo -e "\n✅ Session bridge tests complete!"
EOF

chmod +x ~/.claude/scripts/test-session-bridge.sh

echo "✅ Session Context Bridge setup complete!"
echo ""
echo "To activate the new features, run:"
echo "  source ~/.bashrc"
echo ""
echo "New commands available:"
echo "  csuggest <query>  - Get context-aware file suggestions"
echo "  canalyze          - Analyze cross-session patterns"
echo "  cwarm <topic>     - Pre-warm context for a topic"
echo "  context-status    - Check context bridge status"
echo ""
echo "To test the integration:"
echo "  ~/.claude/scripts/test-session-bridge.sh"