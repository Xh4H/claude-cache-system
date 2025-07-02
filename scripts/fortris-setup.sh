#!/bin/bash
# Fortris Security Cache System - Enterprise Setup Script

set -e

echo "🔒 Fortris Security Cache System v3.0 - Enterprise Setup"
echo "======================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CLAUDE_DIR="$HOME/.claude"
CACHE_DIR="$CLAUDE_DIR/cache"
CONFIG_DIR="$CLAUDE_DIR/config"
LOGS_DIR="$CLAUDE_DIR/logs"
SCRIPTS_DIR="$CLAUDE_DIR/scripts"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Step 1: Create Fortris directory structure
setup_directories() {
    print_status "Creating Fortris directory structure in Claude folder..."
    
    mkdir -p "$CLAUDE_DIR"/{cache,config,logs,scripts,backups,reports}
    mkdir -p "$CACHE_DIR"/{files,partitions}
    chmod 700 "$CLAUDE_DIR"
    chmod 700 "$CONFIG_DIR"
    chmod 700 "$LOGS_DIR"
    
    print_success "Directory structure created in ~/.claude"
}

# Step 2: Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies for Fortris..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Install required packages
    pip3 install --user \
        aiohttp \
        psutil \
        jsonschema \
        pyyaml \
        croniter \
        crontab \
        GitPython \
        cachetools \
        numpy \
        2>/dev/null || {
        print_warning "Some packages may need manual installation"
        print_status "You may need to run: pip3 install aiohttp psutil jsonschema pyyaml croniter crontab GitPython cachetools numpy"
    }
    
    print_success "Dependencies installed"
}

# Step 3: Copy Fortris files
setup_fortris_files() {
    print_status "Setting up Fortris system files..."
    
    # Copy main cache files
    cp fortris_security_cache.py "$CACHE_DIR/"
    cp fortris_security_daemon.py "$CACHE_DIR/"
    cp fortris_config.json "$CONFIG_DIR/"
    
    # Copy scripts
    cp scripts/fortris "$SCRIPTS_DIR/"
    cp scripts/fortris-warm-strategies.sh "$SCRIPTS_DIR/"
    
    # Make scripts executable
    chmod +x "$SCRIPTS_DIR/fortris"
    chmod +x "$SCRIPTS_DIR/fortris-warm-strategies.sh"
    
    print_success "Fortris files installed"
}

# Step 4: Create configuration
setup_configuration() {
    print_status "Creating Fortris configuration..."
    
    # Create main config if it doesn't exist
    if [ ! -f "$CONFIG_DIR/fortris_security.json" ]; then
        cat > "$CONFIG_DIR/fortris_security.json" << 'EOF'
{
  "allowed_dirs": [
    "/home/$USER",
    "/workspace",
    "/opt/projects"
  ],
  "cache_size_limit_gb": 10.0,
  "max_file_size_mb": 50,
  "compression_threshold_kb": 100,
  "security_analysis": true,
  "git_integration": true,
  "parallel_workers": 8,
  "daemon_port": 19849,
  "log_level": "INFO",
  "fortris_enterprise": true
}
EOF
    fi
    
    print_success "Configuration created"
}

# Step 5: Setup shell integration
setup_shell_integration() {
    print_status "Setting up shell integration..."
    
    # Add to PATH
    if ! grep -q "CLAUDE_FORTRIS" ~/.bashrc; then
        cat >> ~/.bashrc << 'EOF'

# Fortris Security Cache System (Claude Integration)
export CLAUDE_HOME="$HOME/.claude"
export PATH="$CLAUDE_HOME/scripts:$PATH"

# Fortris aliases
alias fortris-start='fortris start'
alias fortris-stop='fortris stop'
alias fortris-status='fortris status'
alias fortris-scan='fortris scan'
alias fortris-report='fortris report'

# Auto-start Fortris daemon (optional)
# if ! pgrep -f "fortris_security_daemon.py" > /dev/null; then
#     fortris start > /dev/null 2>&1 &
# fi
EOF
    fi
    
    print_success "Shell integration added to ~/.bashrc"
}

# Step 6: Initialize security patterns
setup_security_patterns() {
    print_status "Setting up Fortris security patterns..."
    
    cat > "$CONFIG_DIR/fortris_patterns.json" << 'EOF'
{
  "version": "3.0",
  "patterns": [
    {
      "id": "hardcoded_password",
      "pattern": "(?:password|passwd|pwd)\\s*=\\s*[\"']([^\"']+)[\"']",
      "severity": "HIGH",
      "description": "Hardcoded password detected",
      "file_types": [".py", ".js", ".java", ".cs", ".go"]
    },
    {
      "id": "api_key",
      "pattern": "(?:api[_-]?key|apikey)\\s*=\\s*[\"']([^\"']+)[\"']",
      "severity": "HIGH", 
      "description": "Hardcoded API key detected",
      "file_types": [".py", ".js", ".java", ".cs", ".go", ".yml", ".yaml"]
    },
    {
      "id": "sql_injection",
      "pattern": "(?:execute|query)\\s*\\(\\s*[\"'].*?\\%s.*?[\"'].*?\\%.*?\\)",
      "severity": "HIGH",
      "description": "Potential SQL injection vulnerability",
      "file_types": [".py", ".php", ".java"]
    },
    {
      "id": "command_injection",
      "pattern": "os\\.system\\s*\\([^)]*\\+[^)]*\\)",
      "severity": "CRITICAL",
      "description": "Command injection vulnerability",
      "file_types": [".py"]
    }
  ]
}
EOF
    
    print_success "Security patterns configured"
}

# Step 7: Create logging configuration
setup_logging() {
    print_status "Setting up Fortris logging..."
    
    cat > "$CONFIG_DIR/logging.conf" << 'EOF'
[loggers]
keys=root,fortris

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_fortris]
level=INFO
handlers=consoleHandler,fileHandler
qualname=fortris
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('~/.claude/logs/fortris.log',)

[formatter_simpleFormatter]
format=%(asctime)s - Fortris - %(levelname)s - %(message)s
EOF
    
    print_success "Logging configuration created"
}

# Step 8: Verify installation
verify_installation() {
    print_status "Verifying Fortris installation..."
    
    # Check if all files exist
    local files=(
        "$CACHE_DIR/fortris_security_cache.py"
        "$CACHE_DIR/fortris_security_daemon.py"
        "$CONFIG_DIR/fortris_config.json"
        "$SCRIPTS_DIR/fortris"
    )
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Missing file: $file"
            exit 1
        fi
    done
    
    # Test Python imports
    if ! python3 -c "import aiohttp, psutil, git" 2>/dev/null; then
        print_warning "Some Python dependencies may be missing"
    fi
    
    print_success "Installation verified"
}

# Main installation process
main() {
    echo "Starting Fortris Security Cache System installation..."
    echo ""
    
    setup_directories
    install_dependencies
    setup_fortris_files
    setup_configuration
    setup_shell_integration
    setup_security_patterns
    setup_logging
    verify_installation
    
    echo ""
    echo -e "${GREEN}🔒 Fortris Security Cache System v3.0 installation complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Reload your shell: source ~/.bashrc"
    echo "2. Start Fortris: fortris start"
    echo "3. Check status: fortris status"
    echo "4. Warm cache: fortris warm \"**/*.py\""
    echo "5. Generate report: fortris report"
    echo ""
    echo "For interactive warming strategies: fortris-warm-strategies.sh"
    echo "For help: fortris help"
    echo ""
    echo -e "${BLUE}Fortris is ready for enterprise security analysis!${NC}"
}

# Run main installation
main "$@"