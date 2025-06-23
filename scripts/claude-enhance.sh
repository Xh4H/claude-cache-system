#!/bin/bash
# Claude Enhancement Script - Incremental improvements to existing setup
# PURPOSE: Add abstractions and organization to current implementation

echo "🔧 Enhancing Claude configuration..."

# 1. Organize scattered files
echo "📁 Organizing files..."

# Move statsig telemetry
if [ -d ~/.claude/statsig ]; then
    mkdir -p ~/.claude/data/telemetry
    mv ~/.claude/statsig ~/.claude/data/telemetry/ 2>/dev/null
    echo "  ✓ Moved telemetry files"
fi

# Archive old backups
mkdir -p ~/.claude/backups/archive
for backup in ~/.claude/settings.local.json.mcp-backup.*; do
    [ -f "$backup" ] && mv "$backup" ~/.claude/backups/archive/
done
echo "  ✓ Archived old backups"

# 2. Create unified config loader
echo "🔧 Creating unified config system..."
cat > ~/.claude/scripts/config.sh << 'EOF'
#!/bin/bash
# Unified configuration management

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

# Load all configurations in order
load_config() {
    # System defaults
    [ -f "$CLAUDE_HOME/config/defaults.conf" ] && source "$CLAUDE_HOME/config/defaults.conf"
    
    # User settings  
    [ -f "$CLAUDE_HOME/config/settings.conf" ] && source "$CLAUDE_HOME/config/settings.conf"
    
    # Environment overrides (highest priority)
    return 0
}

# Get config value
get_config() {
    load_config
    echo "${!1:-$2}"
}

# Set config value
set_config() {
    local key="$1"
    local value="$2"
    local file="$CLAUDE_HOME/config/settings.conf"
    
    mkdir -p "$(dirname "$file")"
    
    if grep -q "^export $key=" "$file" 2>/dev/null; then
        sed -i "s|^export $key=.*|export $key=\"$value\"|" "$file"
    else
        echo "export $key=\"$value\"" >> "$file"
    fi
    echo "✓ Set $key=$value"
}

# Execute based on arguments
case "$1" in
    get) get_config "$2" "$3" ;;
    set) set_config "$2" "$3" ;;
    load) load_config ;;
    *) echo "Usage: $0 {get|set|load}" ;;
esac
EOF
chmod +x ~/.claude/scripts/config.sh

# 3. Create service wrapper for existing scripts
echo "🎯 Creating service abstractions..."
cat > ~/.claude/scripts/service.sh << 'EOF'
#!/bin/bash
# Service wrapper for Claude components

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

case "$1" in
    credentials)
        shift
        "$CLAUDE_HOME/scripts/secure-credentials.sh" "$@"
        ;;
    health)
        "$CLAUDE_HOME/scripts/health-check.sh"
        ;;
    performance)
        "$CLAUDE_HOME/scripts/performance-monitor.sh" "${2:-report}"
        ;;
    session)
        shift
        "$CLAUDE_HOME/scripts/session-manager.sh" "$@"
        ;;
    knowledge)
        shift
        "$CLAUDE_HOME/scripts/knowledge-extractor.sh" "$@"
        ;;
    *)
        echo "Available services:"
        echo "  credentials - Secure credential management"
        echo "  health      - System health check"
        echo "  performance - Performance monitoring"
        echo "  session     - Session management"
        echo "  knowledge   - Knowledge extraction"
        ;;
esac
EOF
chmod +x ~/.claude/scripts/service.sh

# 4. Create simple logger
echo "📝 Adding logging abstraction..."
cat > ~/.claude/scripts/log.sh << 'EOF'
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
EOF
chmod +x ~/.claude/scripts/log.sh

# 5. Update bashrc with new abstractions
echo "🔗 Updating shell integration..."
cat >> ~/.bashrc << 'EOF'

# Claude Enhanced Commands
alias claude-config='~/.claude/scripts/config.sh'
alias claude-service='~/.claude/scripts/service.sh'
alias claude-log='~/.claude/scripts/log.sh'

# Quick access
cs() { claude-service "$@"; }
cc() { claude-config "$@"; }
cl() { claude-log "$@"; }
EOF

# 6. Create quick status command
cat > ~/.claude/scripts/status.sh << 'EOF'
#!/bin/bash
# Quick status overview

echo "=== Claude Status ==="
echo ""
echo "📁 Storage:"
du -sh ~/.claude/* 2>/dev/null | grep -E "(sessions|logs|cache|data)" | head -5

echo ""
echo "🔐 Credentials:"
~/.claude/scripts/secure-credentials.sh list 2>/dev/null | wc -l | xargs -I{} echo "  {} stored"

echo ""
echo "📊 Recent Activity:"
find ~/.claude/sessions -type f -mtime -1 2>/dev/null | wc -l | xargs -I{} echo "  {} sessions today"
find ~/.claude/logs -type f -mtime -1 2>/dev/null | wc -l | xargs -I{} echo "  {} log files updated"

echo ""
echo "🔧 Services:"
for svc in credentials health performance; do
    echo -n "  $svc: "
    ~/.claude/scripts/service.sh $svc status 2>&1 | grep -q "Active\|OK" && echo "✓" || echo "✗"
done
EOF
chmod +x ~/.claude/scripts/status.sh

echo ""
echo "✅ Enhancement complete!"
echo ""
echo "🎯 New commands available:"
echo "  claude-config get/set   - Manage configuration"
echo "  claude-service <name>   - Control services"
echo "  claude-log <message>    - Log messages"
echo "  ~/.claude/scripts/status.sh - Quick status"
echo ""
echo "💡 Reload shell to use new aliases: source ~/.bashrc"