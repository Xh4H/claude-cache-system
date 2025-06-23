#!/bin/bash
# Unified Claude Configuration Loader
# PURPOSE: Single source of truth for all configurations
# DEPENDENCIES: None
# CONFIG_USED: ~/.claude/config/*

# Load configurations in order of precedence
load_claude_config() {
    # 1. Defaults (shipped with Claude)
    [ -f ~/.claude/config/defaults/base.conf ] && source ~/.claude/config/defaults/base.conf
    
    # 2. User customizations
    [ -f ~/.claude/config/user/settings.conf ] && source ~/.claude/config/user/settings.conf
    
    # 3. Project-specific (if in a project)
    local project_config=$(find_project_config)
    [ -f "$project_config" ] && source "$project_config"
    
    # 4. Environment variables (highest precedence)
    # These override everything
    
    # 5. Load secure credentials
    [ -f ~/.claude/scripts/load-credentials.sh ] && source ~/.claude/scripts/load-credentials.sh
}

# Find project-specific config
find_project_config() {
    local dir=$(pwd)
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/.claude/config.conf" ]; then
            echo "$dir/.claude/config.conf"
            return
        fi
        dir=$(dirname "$dir")
    done
}

# Get config value with fallback
claude_config_get() {
    local key="$1"
    local default="${2:-}"
    echo "${!key:-$default}"
}

# Set config value
claude_config_set() {
    local key="$1"
    local value="$2"
    local file="${3:-$HOME/.claude/config/user/settings.conf}"
    
    # Ensure file exists
    mkdir -p $(dirname "$file")
    touch "$file"
    
    # Update or add the key
    if grep -q "^export $key=" "$file"; then
        sed -i "s|^export $key=.*|export $key=\"$value\"|" "$file"
    else
        echo "export $key=\"$value\"" >> "$file"
    fi
}

# Export functions for use in other scripts
export -f load_claude_config
export -f claude_config_get  
export -f claude_config_set

# Auto-load on source
load_claude_config
