#!/bin/bash
# Quick setup for Claude improvements

set -e

echo "🚀 Claude Configuration Improvements - Quick Setup"
echo "================================================"

# 1. Create essential directories
echo "📁 Creating directory structure..."
mkdir -p ~/.claude/{scripts,logs,templates,workflows,dashboard,knowledge-base,venvs,backups,.cache,.credentials}
chmod 700 ~/.claude/.credentials

# 2. Backup existing config
if [ -f ~/.claude.json ]; then
    echo "💾 Backing up existing configuration..."
    cp ~/.claude.json ~/.claude.json.backup-20250622-173816 2>/dev/null || true
fi

# 3. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user croniter pyyaml crontab aiohttp psutil jsonschema 2>/dev/null || echo "Some packages may need manual installation"

# 4. Create security script
echo "🔐 Setting up security..."
cat > ~/.claude/scripts/secure-credentials.sh << 'SECURITY'
#!/bin/bash
CRED_DIR="/home/mik/.claude/.credentials"
mkdir -p "" && chmod 700 ""

init() {
    if [ ! -f "/.master_key" ]; then
        openssl rand -base64 32 > "/.master_key"
        chmod 600 "/.master_key"
        echo "✅ Master key created"
    fi
}

set_cred() {
    init
    echo "" | openssl enc -aes-256-cbc -a -salt -pass file:"/.master_key" -out "/.enc"
    chmod 600 "/.enc"
    echo "✅ Credential  saved"
}

get_cred() {
    [ -f "/.enc" ] && openssl enc -aes-256-cbc -d -a -pass file:"/.master_key" -in "/.enc"
}

case "" in
    init) init ;;
    set) set_cred "" "" ;;
    get) get_cred "" ;;
    *) echo "Usage: /bin/bash {init|set|get}" ;;
esac
SECURITY

chmod +x ~/.claude/scripts/secure-credentials.sh

# 5. Initialize security
~/.claude/scripts/secure-credentials.sh init

# 6. Create performance monitoring script
echo "📊 Setting up performance monitoring..."
cat > ~/.claude/scripts/simple-monitor.sh << 'MONITOR'
#!/bin/bash
echo "=== Claude System Status ==="
echo "Sessions: 0"
echo "Memory: "
echo "Disk: "
echo "MCP Servers: 67 running"
MONITOR

chmod +x ~/.claude/scripts/simple-monitor.sh

# 7. Create session manager
echo "📝 Setting up session management..."
cat > ~/.claude/scripts/session-save.sh << 'SESSION'
#!/bin/bash
SESSION_ID="session_20250622_173816"
SESSION_DIR="/home/mik/.claude/sessions/"
mkdir -p ""

echo "# Session: " > "/summary.md"
echo "Created: Sun Jun 22 17:38:16 CEST 2025" >> "/summary.md"
pwd > "/working_dir.txt"

echo "✅ Session saved: "
SESSION

chmod +x ~/.claude/scripts/session-save.sh

# 8. Add aliases to bashrc
echo "🔧 Adding aliases..."
if ! grep -q "claude-secure" ~/.bashrc; then
    cat >> ~/.bashrc << 'ALIASES'

# Claude Improvements Aliases
alias claude-secure='~/.claude/scripts/secure-credentials.sh'
alias claude-monitor='~/.claude/scripts/simple-monitor.sh'
alias claude-save='~/.claude/scripts/session-save.sh'
alias claude-logs='tail -f ~/.claude/logs/*.log 2>/dev/null || echo "No logs yet"'
ALIASES
fi

echo ""
echo "✅ Basic setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up credentials: claude-secure set neo4j_password YOUR_PASSWORD"
echo "2. Check status: claude-monitor"
echo "3. Save session: claude-save 'topic name'"
echo "4. Source bashrc: source ~/.bashrc"

