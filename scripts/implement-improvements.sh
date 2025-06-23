#!/bin/bash
# Master script to implement Claude configuration improvements

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "=== Claude Configuration Improvements Implementation ==="
echo "Starting implementation of refactoring improvements..."
echo ""

# Function to backup current configuration
backup_current_config() {
    echo -e "Creating backup of current configuration..."
    local backup_dir="/home/mik/.claude-backup-20250622-173743"
    
    if [ -d "/home/mik/.claude" ]; then
        cp -r "/home/mik/.claude" ""
        tar -czf ".tar.gz" ""
        rm -rf ""
        echo -e "✓ Backup created: .tar.gz"
    fi
}

# Check and install dependencies
install_dependencies() {
    echo -e "Installing Python dependencies..."
    pip install --user croniter pyyaml crontab aiohttp psutil jsonschema 2>/dev/null || {
        pip3 install --user croniter pyyaml crontab aiohttp psutil jsonschema
    }
    echo -e "✓ Dependencies installed"
}

# Create directory structure
create_directories() {
    echo -e "Creating directory structure..."
    
    mkdir -p "/home/mik/.claude"/{scripts,logs,templates,workflows,dashboard,knowledge-base,venvs,backups,.cache,.credentials}
    chmod 700 "/home/mik/.claude/.credentials"
    
    echo -e "✓ Directory structure created"
}

# Implement security improvements
implement_security() {
    echo -e "Implementing security improvements..."
    
    # Create secure credentials script
    cat > "/home/mik/.claude/scripts/secure-credentials.sh" << 'SCRIPT'
#!/bin/bash
CRED_DIR="/home/mik/.claude/.credentials"

init_credential_store() {
    mkdir -p ""
    chmod 700 ""
    
    if [ ! -f "/.master_key" ]; then
        openssl rand -base64 32 > "/.master_key"
        chmod 600 "/.master_key"
        echo "✅ Master key created"
    fi
}

encrypt_credential() {
    echo "" | openssl enc -aes-256-cbc -a -salt         -pass file:"/.master_key"         -out "/.enc"
    chmod 600 "/.enc"
}

decrypt_credential() {
    [ -f "/.enc" ] &&     openssl enc -aes-256-cbc -d -a         -pass file:"/.master_key"         -in "/.enc"
}

case "" in
    init) init_credential_store ;;
    set) encrypt_credential "" "" ;;
    get) decrypt_credential "" ;;
esac
SCRIPT
    
    chmod +x "/home/mik/.claude/scripts/secure-credentials.sh"
    "/home/mik/.claude/scripts/secure-credentials.sh" init
    
    echo -e "✓ Security implemented"
}

# Quick implementation
echo "Starting quick implementation..."
backup_current_config
create_directories
install_dependencies
implement_security

echo -e "\n✅ Basic improvements implemented!"
echo "Run individual scripts to continue setup"
