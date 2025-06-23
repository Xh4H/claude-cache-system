#!/bin/bash
# Claude Data Organization - Clean up scattered files
# PURPOSE: Move data files to proper locations
# DEPENDENCIES: claude-core-lib.sh

source "$(dirname "$0")/claude-core-lib.sh" || exit 1

organize_statsig() {
    claude_log "Organizing statsig telemetry files..."
    
    # Create telemetry directory
    mkdir -p "$CLAUDE_DATA/telemetry/statsig"
    
    # Move statsig files
    local count=0
    for file in "$CLAUDE_HOME"/statsig/*; do
        if [ -f "$file" ]; then
            mv "$file" "$CLAUDE_DATA/telemetry/statsig/"
            ((count++))
        fi
    done
    
    # Remove empty directory
    rmdir "$CLAUDE_HOME/statsig" 2>/dev/null
    
    claude_log "Moved $count statsig files" SUCCESS
}

organize_configs() {
    claude_log "Organizing configuration files..."
    
    # Move configs to proper locations
    if [ -f "$CLAUDE_HOME/config.json" ]; then
        mv "$CLAUDE_HOME/config.json" "$CLAUDE_CONFIG/user/legacy-config.json"
        claude_log "Moved legacy config.json"
    fi
    
    # Archive old settings backups
    mkdir -p "$CLAUDE_HOME/backups/settings"
    for backup in "$CLAUDE_HOME"/*.mcp-backup.*; do
        if [ -f "$backup" ]; then
            mv "$backup" "$CLAUDE_HOME/backups/settings/"
        fi
    done
}

organize_scripts() {
    claude_log "Categorizing scripts by function..."
    
    # Create category directories
    mkdir -p "$CLAUDE_SCRIPTS"/{core,services,tools,legacy}
    
    # Define script categories
    declare -A categories=(
        ["claude-core-lib.sh"]="core"
        ["config-loader.sh"]="core"
        ["secure-credentials.sh"]="core"
        ["claude-svc-credentials.sh"]="services"
        ["health-check.sh"]="services"
        ["performance-monitor.sh"]="services"
        ["session-manager.sh"]="tools"
        ["knowledge-extract.sh"]="tools"
        ["cleanup.sh"]="tools"
        ["claude-reorg.sh"]="tools"
        ["feedback-loop.sh"]="tools"
        ["smart-session.sh"]="tools"
    )
    
    # Create symlinks for categorized access
    for script in "${!categories[@]}"; do
        local category="${categories[$script]}"
        if [ -f "$CLAUDE_SCRIPTS/$script" ]; then
            ln -sf "../$script" "$CLAUDE_SCRIPTS/$category/$script" 2>/dev/null
        fi
    done
    
    claude_log "Scripts categorized with symlinks" SUCCESS
}

create_unified_cli() {
    claude_log "Creating unified CLI interface..."
    
    cat > "$CLAUDE_SCRIPTS/claude" << 'EOF'
#!/bin/bash
# Claude Unified CLI - Single entry point for all operations
# Usage: claude <command> [args]

source "$(dirname "$0")/claude-core-lib.sh" || exit 1

case "${1:-help}" in
    # Core commands
    config)
        shift
        claude_config "$@"
        ;;
        
    service|svc)
        shift
        claude_service "$@"
        ;;
        
    # Credential operations
    cred|credential)
        shift
        "$CLAUDE_SCRIPTS/claude-svc-credentials.sh" "$@"
        ;;
        
    # System operations
    health)
        "$CLAUDE_SCRIPTS/health-check.sh"
        ;;
        
    perf|performance)
        "$CLAUDE_SCRIPTS/performance-monitor.sh" "${2:-report}"
        ;;
        
    cleanup)
        "$CLAUDE_SCRIPTS/cleanup.sh" "${2:-standard}"
        ;;
        
    # Session operations
    session)
        shift
        "$CLAUDE_SCRIPTS/session-manager.sh" "$@"
        ;;
        
    save)
        "$CLAUDE_SCRIPTS/session-save.sh" "$2"
        ;;
        
    # Knowledge operations
    knowledge|kb)
        shift
        "$CLAUDE_SCRIPTS/knowledge-extract.sh" "$@"
        ;;
        
    # Development tools
    lint)
        "$CLAUDE_SCRIPTS/claude-lint.sh"
        ;;
        
    organize)
        "$CLAUDE_SCRIPTS/claude-organize-data.sh"
        ;;
        
    # Help
    help|--help|-h)
        cat << 'HELP'
Claude Unified CLI

Usage: claude <command> [args]

Core Commands:
  config get/set/list     Configuration management
  service <name> <action> Service control (start/stop/status)
  
Credentials:
  cred init              Initialize credential storage
  cred set <name> <val>  Store encrypted credential
  cred get <name>        Retrieve credential
  cred list              List stored credentials
  
System:
  health                 System health check
  perf [report]          Performance monitoring
  cleanup [mode]         Clean temporary files
  
Sessions:
  session save <desc>    Save current session
  session list           List saved sessions
  save <desc>            Quick save alias
  
Knowledge:
  knowledge extract      Extract from sessions
  knowledge search       Search knowledge base
  
Development:
  lint                   Check configuration
  organize               Organize scattered files

Examples:
  claude config set CLAUDE_DEBUG 1
  claude cred set github_token "ghp_..."
  claude service credentials status
  claude health
HELP
        ;;
        
    *)
        echo "Unknown command: $1"
        echo "Try: claude help"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$CLAUDE_SCRIPTS/claude"
    claude_log "Unified CLI created" SUCCESS
}

# Main execution
claude_log "Starting data organization..."

organize_statsig
organize_configs
organize_scripts
create_unified_cli

# Create directory map
cat > "$CLAUDE_HOME/DIRECTORY_STRUCTURE.md" << 'EOF'
# Claude Directory Structure

## Core Directories

```
~/.claude/
├── config/           # Configuration files
│   ├── system/      # System defaults (read-only)
│   ├── user/        # User settings
│   └── project/     # Project-specific configs
│
├── scripts/         # Executable scripts
│   ├── core/        # Core libraries (symlinks)
│   ├── services/    # Service scripts (symlinks)
│   ├── tools/       # User tools (symlinks)
│   └── legacy/      # Old scripts for reference
│
├── data/            # Application data
│   ├── sessions/    # Session recordings
│   ├── knowledge/   # Knowledge base
│   ├── telemetry/   # Usage statistics
│   └── state/       # Persistent state
│
├── runtime/         # Runtime files
│   └── *.lock       # Lock files
│
├── logs/            # Log files
├── backups/         # Backup files
├── .credentials/    # Encrypted credentials
└── cache/           # Temporary cache
```

## Key Files

- `scripts/claude` - Unified CLI entry point
- `scripts/claude-core-lib.sh` - Core library
- `config/system/defaults.conf` - System defaults
- `config/user/settings.conf` - User settings
- `data/state/claude.state` - Persistent state

## Usage

All operations through unified CLI:
```bash
claude help              # Show all commands
claude config list       # Show configuration
claude health            # Check system health
```
EOF

claude_log "Organization complete! Use 'claude help' for unified interface" SUCCESS