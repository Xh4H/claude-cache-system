#!/bin/bash
# Claude Credentials Service - Secure credential management
# PURPOSE: Manage encrypted credentials with service interface
# DEPENDENCIES: claude-core-lib.sh, openssl

source "$(dirname "$0")/claude-core-lib.sh" || exit 1

CRED_DIR="$CLAUDE_HOME/.credentials"

# Service interface
case "${1:-status}" in
    start)
        claude_log "Starting credentials service"
        init_credentials
        ;;
        
    stop)
        claude_log "Credentials service doesn't run continuously"
        ;;
        
    status)
        if [ -f "$CRED_DIR/.master_key" ]; then
            local count=$(ls -1 "$CRED_DIR"/*.enc 2>/dev/null | wc -l)
            claude_log "Credentials service: Active ($count credentials stored)" SUCCESS
        else
            claude_log "Credentials service: Not initialized" WARN
        fi
        ;;
        
    restart)
        $0 stop
        $0 start
        ;;
        
    # Extended operations
    init)
        init_credentials
        ;;
        
    set)
        set_credential "$2" "$3"
        ;;
        
    get)
        get_credential "$2"
        ;;
        
    list)
        list_credentials
        ;;
        
    rotate)
        rotate_credentials
        ;;
        
    backup)
        backup_credentials
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|restart|init|set|get|list|rotate|backup}"
        exit 1
        ;;
esac

# Implementation functions
init_credentials() {
    mkdir -p "$CRED_DIR" && chmod 700 "$CRED_DIR"
    
    if [ ! -f "$CRED_DIR/.master_key" ]; then
        openssl rand -base64 32 > "$CRED_DIR/.master_key"
        chmod 600 "$CRED_DIR/.master_key"
        claude_log "Master key created - BACK THIS UP!" SUCCESS
        
        # Save master key hash for verification
        openssl dgst -sha256 "$CRED_DIR/.master_key" > "$CRED_DIR/.master_key.hash"
    else
        claude_log "Credentials already initialized"
    fi
}

set_credential() {
    local name="$1"
    local value="$2"
    
    if [ -z "$name" ] || [ -z "$value" ]; then
        claude_error "Usage: $0 set <name> <value>"
    fi
    
    [ ! -f "$CRED_DIR/.master_key" ] && init_credentials
    
    # Encrypt credential
    echo "$value" | openssl enc -aes-256-cbc -a -salt \
        -pass file:"$CRED_DIR/.master_key" \
        -out "$CRED_DIR/$name.enc" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        chmod 600 "$CRED_DIR/$name.enc"
        claude_log "Credential saved: $name" SUCCESS
        
        # Update state
        claude_state "credentials_updated" "$(date +%s)"
    else
        claude_error "Failed to encrypt credential"
    fi
}

get_credential() {
    local name="$1"
    
    if [ -z "$name" ]; then
        claude_error "Usage: $0 get <name>"
    fi
    
    if [ -f "$CRED_DIR/$name.enc" ]; then
        openssl enc -aes-256-cbc -d -a \
            -pass file:"$CRED_DIR/.master_key" \
            -in "$CRED_DIR/$name.enc" 2>/dev/null || \
            claude_error "Failed to decrypt credential"
    else
        claude_error "Credential not found: $name"
    fi
}

list_credentials() {
    claude_log "Stored credentials:"
    ls -1 "$CRED_DIR"/*.enc 2>/dev/null | while read enc; do
        local name=$(basename "$enc" .enc)
        local mtime=$(stat -c %y "$enc" 2>/dev/null | cut -d' ' -f1)
        echo "  - $name (modified: $mtime)"
    done
}

rotate_credentials() {
    claude_log "Rotating master key..."
    
    if ! claude_lock "credentials"; then
        claude_error "Another credential operation in progress"
    fi
    
    # Create new master key
    local new_key="$CRED_DIR/.master_key.new"
    openssl rand -base64 32 > "$new_key"
    chmod 600 "$new_key"
    
    # Re-encrypt all credentials
    ls -1 "$CRED_DIR"/*.enc 2>/dev/null | while read enc; do
        local name=$(basename "$enc" .enc)
        local value=$(get_credential "$name")
        
        # Encrypt with new key
        echo "$value" | openssl enc -aes-256-cbc -a -salt \
            -pass file:"$new_key" \
            -out "$enc.new" 2>/dev/null
            
        if [ $? -eq 0 ]; then
            mv "$enc.new" "$enc"
            claude_log "Rotated: $name" SUCCESS
        else
            claude_error "Failed to rotate: $name"
        fi
    done
    
    # Replace master key
    mv "$CRED_DIR/.master_key" "$CRED_DIR/.master_key.old"
    mv "$new_key" "$CRED_DIR/.master_key"
    
    claude_unlock "credentials"
    claude_log "Credential rotation complete" SUCCESS
}

backup_credentials() {
    local backup_file="$CLAUDE_HOME/backups/credentials-$(date +%Y%m%d-%H%M%S).tar.gz.enc"
    mkdir -p "$CLAUDE_HOME/backups"
    
    # Create encrypted backup
    tar -czf - -C "$CLAUDE_HOME" .credentials | \
        openssl enc -aes-256-cbc -a -salt \
        -pass file:"$CRED_DIR/.master_key" \
        -out "$backup_file"
        
    if [ $? -eq 0 ]; then
        chmod 600 "$backup_file"
        claude_log "Credentials backed up to: $backup_file" SUCCESS
    else
        claude_error "Backup failed"
    fi
}