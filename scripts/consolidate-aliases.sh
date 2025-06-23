#!/bin/bash
# Script to consolidate Claude aliases and remove duplicates

echo "=== Consolidating Claude Aliases ==="

# Backup current .bashrc
cp ~/.bashrc ~/.bashrc.backup-$(date +%Y%m%d-%H%M%S)

# Create temporary file for new aliases
cat > /tmp/claude-aliases.txt << 'EOF'
# Claude Code Enhanced Aliases - Consolidated
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
EOF

echo "New aliases prepared. Review and apply manually to ~/.bashrc"
echo "Temporary file saved to: /tmp/claude-aliases.txt"