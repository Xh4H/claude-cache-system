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
