#!/bin/bash
# Claude Cleanup - Unified maintenance and cleanup tool
# Consolidates all cleanup functionality with safe, incremental operations

CLAUDE_DIR="$HOME/.claude"
BACKUP_DIR="$CLAUDE_DIR/backups"
LOG_FILE="$CLAUDE_DIR/logs/cleanup.log"

# Ensure directories exist
mkdir -p "$BACKUP_DIR" "$CLAUDE_DIR/logs"

# Main cleanup command dispatcher
claude-cleanup() {
    local cmd="${1:-help}"
    shift
    
    case "$cmd" in
        quick|q)     cleanup_quick "$@" ;;
        deep|d)      cleanup_deep "$@" ;;
        cache|c)     cleanup_cache "$@" ;;
        logs|l)      cleanup_logs "$@" ;;
        sessions|s)  cleanup_sessions "$@" ;;
        duplicates)  cleanup_duplicates "$@" ;;
        empty)       cleanup_empty_dirs "$@" ;;
        backup|b)    cleanup_backup "$@" ;;
        status)      cleanup_status ;;
        auto)        cleanup_auto "$@" ;;
        help|h)      cleanup_help ;;
        *)           echo "Unknown command: $cmd"; cleanup_help ;;
    esac
}

# Quick daily cleanup
cleanup_quick() {
    echo "🧹 Quick cleanup starting..."
    log_action "Quick cleanup started"
    
    # Clear old cache files
    echo "  📦 Clearing cache older than 7 days..."
    find "$CLAUDE_DIR/.cache" -type f -mtime +7 -delete 2>/dev/null
    
    # Rotate logs
    echo "  📄 Rotating logs..."
    cleanup_logs quiet
    
    # Remove temp files
    echo "  🗑️  Removing temp files..."
    find "$CLAUDE_DIR" -name "*.tmp" -o -name "*.swp" -o -name "*~" -delete 2>/dev/null
    
    # Clean empty directories
    echo "  📂 Removing empty directories..."
    cleanup_empty_dirs quiet
    
    log_action "Quick cleanup completed"
    echo "✅ Quick cleanup complete"
}

# Deep cleanup with analysis
cleanup_deep() {
    echo "🔍 Deep cleanup and analysis..."
    log_action "Deep cleanup started"
    
    # Create backup first
    if [ "${1:-}" != "--no-backup" ]; then
        cleanup_backup
    fi
    
    # Analyze duplicates
    echo -e "\n📊 Analyzing duplicates..."
    cleanup_duplicates analyze
    
    # Check for large files
    echo -e "\n💾 Large files (>10MB):"
    find "$CLAUDE_DIR" -type f -size +10M -exec ls -lh {} \; | \
        awk '{print "  " $9 " (" $5 ")"}'
    
    # Old sessions
    echo -e "\n📅 Sessions older than 30 days:"
    local old_sessions=$(find "$CLAUDE_DIR/sessions" -name "*.jsonl" -mtime +30 2>/dev/null | wc -l)
    echo "  Found $old_sessions old sessions"
    
    # Offer to clean
    read -p "Proceed with deep cleanup? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_duplicates remove
        cleanup_sessions compress
        cleanup_cache all
        cleanup_logs compress
    fi
    
    log_action "Deep cleanup completed"
    echo "✅ Deep cleanup complete"
}

# Cache cleanup
cleanup_cache() {
    local mode="${1:-week}"
    
    case "$mode" in
        all)
            echo "🗑️  Clearing all cache..."
            rm -rf "$CLAUDE_DIR/.cache"/*
            ;;
        week)
            echo "📦 Clearing cache older than 7 days..."
            find "$CLAUDE_DIR/.cache" -type f -mtime +7 -delete 2>/dev/null
            ;;
        month)
            echo "📦 Clearing cache older than 30 days..."
            find "$CLAUDE_DIR/.cache" -type f -mtime +30 -delete 2>/dev/null
            ;;
    esac
    
    local remaining=$(du -sh "$CLAUDE_DIR/.cache" 2>/dev/null | cut -f1)
    echo "✅ Cache cleaned. Remaining: $remaining"
}

# Log cleanup and rotation
cleanup_logs() {
    local quiet="${1:-}"
    
    [ -z "$quiet" ] && echo "📄 Managing logs..."
    
    # Rotate large logs
    find "$CLAUDE_DIR/logs" -name "*.log" -size +10M | while read log; do
        gzip "$log"
        > "$log"
        [ -z "$quiet" ] && echo "  Rotated: $(basename $log)"
    done
    
    # Archive old logs
    find "$CLAUDE_DIR/logs" -name "*.log.gz" -mtime +30 -exec mv {} "$BACKUP_DIR/" \; 2>/dev/null
    
    # Clean very old archives
    find "$BACKUP_DIR" -name "*.log.gz" -mtime +90 -delete 2>/dev/null
}

# Session management
cleanup_sessions() {
    local action="${1:-list}"
    
    case "$action" in
        list)
            local total=$(find "$CLAUDE_DIR/sessions" -type f 2>/dev/null | wc -l)
            local old=$(find "$CLAUDE_DIR/sessions" -type f -mtime +30 2>/dev/null | wc -l)
            echo "📊 Sessions: $total total, $old older than 30 days"
            ;;
        compress)
            echo "🗜️  Compressing old sessions..."
            local archive="$BACKUP_DIR/sessions-$(date +%Y%m%d).tar.gz"
            find "$CLAUDE_DIR/sessions" -type f -mtime +30 -print0 | \
                tar -czf "$archive" --null -T - --remove-files 2>/dev/null
            echo "✅ Compressed to: $archive"
            ;;
        clean)
            echo "🗑️  Removing sessions older than 90 days..."
            find "$CLAUDE_DIR/sessions" -type f -mtime +90 -delete 2>/dev/null
            ;;
    esac
}

# Find and handle duplicates
cleanup_duplicates() {
    local action="${1:-analyze}"
    
    echo "🔍 Checking for duplicates..."
    
    # Find duplicate scripts
    local dup_scripts=$(find "$CLAUDE_DIR/scripts" -name "*.sh" -exec basename {} \; | \
        sort | uniq -d)
    
    if [ -n "$dup_scripts" ]; then
        echo "📜 Duplicate scripts found:"
        echo "$dup_scripts" | while read script; do
            echo "  - $script:"
            find "$CLAUDE_DIR/scripts" -name "$script" -type f | sed 's/^/    /'
        done
    fi
    
    # Find duplicate config files
    local configs=$(find "$CLAUDE_DIR" -name "*.json" -o -name "*.conf" | \
        grep -E "(settings|config)" | wc -l)
    if [ $configs -gt 3 ]; then
        echo "⚙️  Multiple config files found ($configs total)"
    fi
    
    if [ "$action" = "remove" ] && [ -n "$dup_scripts" ]; then
        echo "🗑️  Archiving duplicates..."
        mkdir -p "$CLAUDE_DIR/archived/duplicates"
        # Archive older duplicates, keep newest
        echo "$dup_scripts" | while read script; do
            find "$CLAUDE_DIR/scripts" -name "$script" -type f -printf "%T@ %p\n" | \
                sort -n | head -n -1 | cut -d' ' -f2- | \
                xargs -I{} mv {} "$CLAUDE_DIR/archived/duplicates/"
        done
    fi
}

# Remove empty directories
cleanup_empty_dirs() {
    local quiet="${1:-}"
    
    local count=$(find "$CLAUDE_DIR" -type d -empty -not -path "*/.git/*" 2>/dev/null | wc -l)
    
    if [ $count -gt 0 ]; then
        [ -z "$quiet" ] && echo "📂 Removing $count empty directories..."
        find "$CLAUDE_DIR" -type d -empty -not -path "*/.git/*" -delete 2>/dev/null
    fi
}

# Create backup
cleanup_backup() {
    echo "💾 Creating backup..."
    local backup_file="$HOME/claude-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar --exclude='.git' --exclude='*.tar.gz' --exclude='.cache' \
        -czf "$backup_file" -C "$HOME" .claude/
    
    echo "✅ Backup created: $backup_file"
    echo "   Size: $(ls -lh $backup_file | awk '{print $5}')"
}

# Show cleanup status
cleanup_status() {
    echo "📊 Claude Directory Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Directory size
    echo "💾 Total size: $(du -sh $CLAUDE_DIR 2>/dev/null | cut -f1)"
    
    # Component sizes
    echo -e "\n📁 Component sizes:"
    for dir in scripts sessions knowledge logs .cache backups; do
        if [ -d "$CLAUDE_DIR/$dir" ]; then
            size=$(du -sh "$CLAUDE_DIR/$dir" 2>/dev/null | cut -f1)
            count=$(find "$CLAUDE_DIR/$dir" -type f 2>/dev/null | wc -l)
            printf "  %-12s %6s (%d files)\n" "$dir:" "$size" "$count"
        fi
    done
    
    # Check for issues
    echo -e "\n⚠️  Potential issues:"
    
    # Large logs
    local large_logs=$(find "$CLAUDE_DIR/logs" -name "*.log" -size +10M 2>/dev/null | wc -l)
    [ $large_logs -gt 0 ] && echo "  - $large_logs large log files (>10MB)"
    
    # Old sessions
    local old_sessions=$(find "$CLAUDE_DIR/sessions" -type f -mtime +30 2>/dev/null | wc -l)
    [ $old_sessions -gt 20 ] && echo "  - $old_sessions sessions older than 30 days"
    
    # Duplicate scripts
    local dup_count=$(find "$CLAUDE_DIR/scripts" -name "*.sh" -exec basename {} \; | \
        sort | uniq -d | wc -l)
    [ $dup_count -gt 0 ] && echo "  - $dup_count duplicate script names"
    
    # Empty directories
    local empty_dirs=$(find "$CLAUDE_DIR" -type d -empty -not -path "*/.git/*" 2>/dev/null | wc -l)
    [ $empty_dirs -gt 5 ] && echo "  - $empty_dirs empty directories"
}

# Automated cleanup (for cron)
cleanup_auto() {
    log_action "Automated cleanup started"
    
    # Quick cleanup
    cleanup_quick > /dev/null 2>&1
    
    # Weekly deep clean on Sundays
    if [ $(date +%w) -eq 0 ]; then
        cleanup_cache month > /dev/null 2>&1
        cleanup_sessions compress > /dev/null 2>&1
    fi
    
    # Monthly cleanup on 1st
    if [ $(date +%d) -eq 01 ]; then
        cleanup_deep --no-backup > /dev/null 2>&1
    fi
    
    log_action "Automated cleanup completed"
}

# Logging helper
log_action() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Help text
cleanup_help() {
    cat << EOF
Claude Cleanup - Unified Maintenance Tool

Usage: claude-cleanup <command> [options]

Commands:
  quick           Fast daily cleanup (cache, temp files, empty dirs)
  deep            Comprehensive cleanup with analysis
  cache [mode]    Clean cache (all|week|month)
  logs [action]   Manage logs (rotate, compress, archive)
  sessions [act]  Manage sessions (list|compress|clean)
  duplicates      Find and handle duplicate files
  empty           Remove empty directories
  backup          Create full backup before cleanup
  status          Show directory status and issues
  auto            Automated cleanup (for cron)
  help            Show this help

Examples:
  claude-cleanup quick           # Daily maintenance
  claude-cleanup deep            # Full cleanup with prompts
  claude-cleanup cache all       # Clear entire cache
  claude-cleanup sessions compress # Archive old sessions
  claude-cleanup status          # Check for issues

Shortcuts:
  ccq = claude-cleanup quick
  ccd = claude-cleanup deep
  ccs = claude-cleanup status

Cron Setup:
  # Add to crontab for daily cleanup at 3 AM:
  0 3 * * * $HOME/.claude/scripts/claude-cleanup.sh auto

EOF
}

# Aliases for quick access
alias ccq='claude-cleanup quick'
alias ccd='claude-cleanup deep'
alias ccs='claude-cleanup status'

# Export main function
export -f claude-cleanup

# If called directly, run the command
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    claude-cleanup "$@"
fi