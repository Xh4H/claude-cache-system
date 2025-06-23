#!/bin/bash
# Update .bashrc with consolidated Claude aliases

# Backup current .bashrc
cp ~/.bashrc ~/.bashrc.backup-claude-$(date +%Y%m%d-%H%M%S)

# Create new .bashrc without claude aliases
grep -v "^alias claude" ~/.bashrc | grep -v "^alias qsave" | grep -v "^alias qlist" | grep -v "^alias qrestore" | grep -v "^alias cw=" | grep -v "^alias cresume" | grep -v "^alias clast" > /tmp/bashrc.new

# Add consolidated aliases
cat >> /tmp/bashrc.new << 'EOF'

# ================== Claude Code Enhanced Aliases ==================
# Consolidated configuration - Single source of truth
alias claude='~/.claude/scripts/claude-secure'  # Secure launcher with credentials
alias claude-health='~/.claude/scripts/health-check.sh'
alias claude-secure='~/.claude/scripts/secure-credentials.sh'
alias claude-session='~/.claude/scripts/claude-session.sh'
alias claude-backup='tar -czf ~/.claude/backups/claude-backup-$(date +%Y%m%d-%H%M%S).tar.gz ~/.claude/'
alias claude-clean='~/.claude/scripts/claude-cleanup.sh'
alias claude-perf='~/.claude/scripts/performance-optimizer.sh'
alias claude-monitor='~/.claude/scripts/simple-monitor.sh'
alias claude-knowledge='~/.claude/scripts/knowledge-extract.sh'
alias claude-dash='cd ~/.claude/dashboard && python3 -m http.server 8090'
alias claude-restore='tar -xzf'  # Usage: claude-restore backup-file.tar.gz

# Quick access aliases
alias qsave='~/.claude/scripts/claude-session.sh save'
alias qlist='~/.claude/scripts/claude-session.sh list'
alias qrestore='~/.claude/scripts/claude-session.sh restore'
alias cresume='claude --resume'
alias clast='claude-session list | head -5'

# Function for quick checkpoint
checkpoint() {
    local name="${1:-checkpoint-$(date +%H%M)}"
    ~/.claude/scripts/claude-session.sh save "$name"
}

# Function for knowledge search
memento_search() {
    ~/.claude/scripts/knowledge.sh search "$1"
}

# Function for quick status
claude-status() {
    echo "=== Claude Status ==="
    ~/.claude/scripts/health-check.sh
}
# ================== End Claude Aliases ==================

EOF

# Replace bashrc
mv /tmp/bashrc.new ~/.bashrc
echo "✅ Updated ~/.bashrc with consolidated aliases"
echo "Run 'source ~/.bashrc' to apply changes"