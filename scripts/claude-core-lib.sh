#!/bin/bash
# Claude Core Library - Foundation for all scripts
# PURPOSE: Provide core abstractions for configuration, logging, and error handling
# DEPENDENCIES: None (this is the base layer)

# Core paths
export CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
export CLAUDE_CONFIG="${CLAUDE_CONFIG:-$CLAUDE_HOME/config}"
export CLAUDE_SCRIPTS="${CLAUDE_SCRIPTS:-$CLAUDE_HOME/scripts}"
export CLAUDE_DATA="${CLAUDE_DATA:-$CLAUDE_HOME/data}"
export CLAUDE_RUNTIME="${CLAUDE_RUNTIME:-$CLAUDE_HOME/runtime}"
export CLAUDE_LOGS="${CLAUDE_LOGS:-$CLAUDE_HOME/logs}"

# Ensure directories exist
mkdir -p "$CLAUDE_CONFIG"/{system,user,project} "$CLAUDE_DATA"/{sessions,knowledge,state} "$CLAUDE_RUNTIME" "$CLAUDE_LOGS"

# Logging abstraction
claude_log() {
    local level="${2:-INFO}"
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_file="$CLAUDE_LOGS/claude.log"
    
    # Ensure log directory exists
    mkdir -p "$CLAUDE_LOGS"
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$log_file"
    
    # Log to console with colors
    case "$level" in
        ERROR)   echo -e "\033[0;31m❌ $message\033[0m" >&2 ;;
        WARN)    echo -e "\033[1;33m⚠️  $message\033[0m" ;;
        SUCCESS) echo -e "\033[0;32m✅ $message\033[0m" ;;
        DEBUG)   [ "${CLAUDE_DEBUG:-0}" = "1" ] && echo -e "\033[0;36m🔍 $message\033[0m" ;;
        *)       echo "ℹ️  $message" ;;
    esac
}

# Error handling abstraction
claude_error() {
    local code="${2:-1}"
    claude_log "$1" ERROR
    exit "$code"
}

# Configuration abstraction
claude_config() {
    local action="$1"
    local key="$2"
    local value="$3"
    local config_file="$CLAUDE_CONFIG/user/settings.conf"
    
    case "$action" in
        get)
            # Check environment first (highest priority)
            if [ -n "${!key}" ]; then
                echo "${!key}"
                return
            fi
            
            # Load configs in order
            [ -f "$CLAUDE_CONFIG/system/defaults.conf" ] && source "$CLAUDE_CONFIG/system/defaults.conf" 2>/dev/null
            [ -f "$CLAUDE_CONFIG/user/settings.conf" ] && source "$CLAUDE_CONFIG/user/settings.conf" 2>/dev/null
            
            # Get value with fallback
            echo "${!key:-$value}"
            ;;
            
        set)
            mkdir -p "$(dirname "$config_file")"
            
            # Update or add the key
            if grep -q "^export $key=" "$config_file" 2>/dev/null; then
                sed -i "s|^export $key=.*|export $key=\"$value\"|" "$config_file"
            else
                echo "export $key=\"$value\"" >> "$config_file"
            fi
            claude_log "Config updated: $key=$value" SUCCESS
            ;;
            
        list)
            echo "=== Claude Configuration ==="
            echo "System defaults:"
            [ -f "$CLAUDE_CONFIG/system/defaults.conf" ] && grep "^export" "$CLAUDE_CONFIG/system/defaults.conf" | sed 's/export /  /'
            echo -e "\nUser settings:"
            [ -f "$CLAUDE_CONFIG/user/settings.conf" ] && grep "^export" "$CLAUDE_CONFIG/user/settings.conf" | sed 's/export /  /'
            ;;
    esac
}

# Service abstraction
claude_service() {
    local service="$1"
    local action="${2:-status}"
    local service_script="$CLAUDE_SCRIPTS/claude-svc-$service.sh"
    
    if [ ! -f "$service_script" ]; then
        claude_error "Service not found: $service"
    fi
    
    case "$action" in
        start|stop|restart|status)
            "$service_script" "$action"
            ;;
        *)
            claude_error "Unknown action: $action"
            ;;
    esac
}

# Dependency check
claude_require() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        claude_error "Required command not found: $cmd"
    fi
}

# State management
claude_state() {
    local key="$1"
    local value="$2"
    local state_file="$CLAUDE_DATA/state/claude.state"
    
    mkdir -p "$(dirname "$state_file")"
    
    if [ -z "$value" ]; then
        # Get state
        grep "^$key=" "$state_file" 2>/dev/null | cut -d'=' -f2-
    else
        # Set state
        if grep -q "^$key=" "$state_file" 2>/dev/null; then
            sed -i "s|^$key=.*|$key=$value|" "$state_file"
        else
            echo "$key=$value" >> "$state_file"
        fi
    fi
}

# Lock management for preventing concurrent operations
claude_lock() {
    local name="$1"
    local lock_file="$CLAUDE_RUNTIME/$name.lock"
    
    mkdir -p "$CLAUDE_RUNTIME"
    
    if [ -f "$lock_file" ]; then
        local pid=$(cat "$lock_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 1  # Lock held by running process
        else
            rm -f "$lock_file"  # Stale lock
        fi
    fi
    
    echo $$ > "$lock_file"
    return 0
}

claude_unlock() {
    local name="$1"
    local lock_file="$CLAUDE_RUNTIME/$name.lock"
    rm -f "$lock_file"
}

# Export all functions
export -f claude_log
export -f claude_error
export -f claude_config
export -f claude_service
export -f claude_require
export -f claude_state
export -f claude_lock
export -f claude_unlock

# Create default configuration if not exists
if [ ! -f "$CLAUDE_CONFIG/system/defaults.conf" ]; then
    cat > "$CLAUDE_CONFIG/system/defaults.conf" << 'EOF'
# Claude System Defaults - DO NOT EDIT
export CLAUDE_SESSION_RETENTION=30
export CLAUDE_LOG_RETENTION=7
export CLAUDE_CACHE_SIZE=500
export CLAUDE_ENABLE_TELEMETRY=false
export CLAUDE_ENABLE_AUTO_UPDATE=true
EOF
fi

claude_log "Core library loaded" DEBUG