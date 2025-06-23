#!/bin/bash
# Claude Init - Main initialization script
# Sources all consolidated Claude tools

CLAUDE_DIR="$HOME/.claude"
SCRIPTS_DIR="$CLAUDE_DIR/scripts"

# Load environment variables
if [ -f "$CLAUDE_DIR/.env" ]; then
    source "$CLAUDE_DIR/.env"
fi

# Load main configuration
if [ -f "$CLAUDE_DIR/config/claude.conf" ]; then
    export CLAUDE_CONFIG="$CLAUDE_DIR/config/claude.conf"
fi

# Source consolidated tools
TOOLS=(
    "claude-session.sh"    # Session management
    "claude-monitor.sh"    # Performance monitoring
    "claude-cleanup.sh"    # Maintenance and cleanup
    "claude-backup.sh"     # Backup operations (if exists)
    "claude-health.sh"     # Health checks (if exists)
)

for tool in "${TOOLS[@]}"; do
    if [ -f "$SCRIPTS_DIR/$tool" ]; then
        source "$SCRIPTS_DIR/$tool"
    fi
done

# Load project-specific settings if in a project directory
load_project_settings() {
    local current_dir="$PWD"
    
    # Check known project paths
    case "$current_dir" in
        */THESIS*)
            export CLAUDE_PROJECT_MODE="academic"
            export CLAUDE_EXTENDED_THINKING="true"
            ;;
        */SEARXNG*)
            export CLAUDE_PROJECT_MODE="development"
            export CLAUDE_TEST_COMMANDS="pytest;curl localhost:8888"
            ;;
        */AI-TOOLS*)
            export CLAUDE_PROJECT_MODE="ml_development"
            export CLAUDE_GPU_MONITORING="true"
            ;;
    esac
    
    # Check for local .claude config
    if [ -f ".claude/config.json" ]; then
        export CLAUDE_LOCAL_CONFIG=".claude/config.json"
    fi
}

# Set up aliases (consolidated list)
alias cs='claude-session'
alias cm='claude-monitor'
alias cc='claude-cleanup'
alias ch='claude-health'
alias cb='claude-backup'

# Session shortcuts
alias qsave='claude-session save'
alias cresume='claude-session load'
alias clast='claude-session list 5'

# Monitoring shortcuts
alias cms='claude-monitor status'
alias cml='claude-monitor live'
alias cmh='claude-monitor health'

# Cleanup shortcuts
alias ccq='claude-cleanup quick'
alias ccd='claude-cleanup deep'
alias ccs='claude-cleanup status'

# Initialize on shell start
if [ -n "$BASH_VERSION" ]; then
    # Load project settings
    load_project_settings
    
    # Show current session if exists
    if [ -n "$CLAUDE_SESSION_ID" ]; then
        echo "📍 Active session: $CLAUDE_SESSION_TOPIC"
    fi
fi

# Export initialization function
export -f load_project_settings

echo "✅ Claude environment initialized (consolidated)"