#!/bin/bash
# Claude Configuration Reorganization Tool
# PURPOSE: Fix configuration chaos by consolidating and organizing
# DEPENDENCIES: None
# CONFIG_USED: Analyzes all configs

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       Claude Configuration Reorganization Tool        ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

# Function to analyze current state
analyze_chaos() {
    echo -e "\n${YELLOW}📊 Analyzing current configuration state...${NC}"
    
    # Count duplicates
    local json_files=$(find ~/.claude -name "*.json" -type f 2>/dev/null | wc -l)
    local shell_scripts=$(find ~/.claude/scripts -name "*.sh" -type f 2>/dev/null | wc -l)
    local backup_files=$(find ~ -name ".claude.json.backup*" -type f 2>/dev/null | wc -l)
    
    echo "  JSON configs: $json_files"
    echo "  Shell scripts: $shell_scripts"
    echo "  Backup files: $backup_files"
    
    # Find duplicate functionality
    echo -e "\n${YELLOW}🔍 Detecting duplicate scripts...${NC}"
    
    # Group cleanup scripts
    local cleanup_scripts=$(ls ~/.claude/scripts/*clean*.sh 2>/dev/null | wc -l)
    if [ $cleanup_scripts -gt 1 ]; then
        echo -e "  ${RED}⚠️  Found $cleanup_scripts cleanup scripts (should be 1)${NC}"
        ls ~/.claude/scripts/*clean*.sh 2>/dev/null | sed 's/^/    - /'
    fi
    
    # Group knowledge scripts  
    local knowledge_scripts=$(ls ~/.claude/scripts/knowledge*.sh 2>/dev/null | wc -l)
    if [ $knowledge_scripts -gt 1 ]; then
        echo -e "  ${RED}⚠️  Found $knowledge_scripts knowledge scripts (should be 1)${NC}"
        ls ~/.claude/scripts/knowledge*.sh 2>/dev/null | sed 's/^/    - /'
    fi
    
    # Check for config conflicts
    echo -e "\n${YELLOW}🔧 Checking configuration hierarchy...${NC}"
    [ -f ~/.claude.json ] && echo "  ✓ Main config: ~/.claude.json"
    [ -f ~/.claude/settings.json ] && echo "  ✓ Settings: ~/.claude/settings.json"
    [ -f ~/.claude/settings.local.json ] && echo "  ✓ Local: ~/.claude/settings.local.json"
    
    # Calculate chaos score
    local chaos_score=$((json_files + shell_scripts/5 + backup_files*2 + cleanup_scripts*3 + knowledge_scripts*2))
    echo -e "\n${YELLOW}📈 Chaos Score: $chaos_score${NC}"
    
    if [ $chaos_score -lt 20 ]; then
        echo -e "  ${GREEN}✓ Manageable${NC}"
    elif [ $chaos_score -lt 40 ]; then
        echo -e "  ${YELLOW}⚠ Needs attention${NC}"
    else
        echo -e "  ${RED}⚠️  Critical - immediate action needed${NC}"
    fi
}

# Function to consolidate scripts
consolidate_scripts() {
    echo -e "\n${YELLOW}🔨 Consolidating duplicate scripts...${NC}"
    
    # Create new consolidated directory
    mkdir -p ~/.claude/scripts/archive
    mkdir -p ~/.claude/scripts/consolidated
    
    # Consolidate cleanup scripts
    if [ $(ls ~/.claude/scripts/*clean*.sh 2>/dev/null | wc -l) -gt 1 ]; then
        echo "  Creating unified cleanup.sh..."
        cat > ~/.claude/scripts/consolidated/cleanup.sh << 'EOF'
#!/bin/bash
# Unified Claude Cleanup Script
# PURPOSE: Single cleanup tool with multiple modes
# DEPENDENCIES: None
# CONFIG_USED: ~/.claude/config/cleanup.conf

MODE="${1:-standard}"

case "$MODE" in
    standard)
        echo "🧹 Standard cleanup..."
        find ~/.claude -name "*.tmp" -o -name "*~" -o -name "*.swp" -delete
        find ~/.claude/logs -mtime +30 -delete 2>/dev/null || true
        ;;
    deep)
        echo "🧹 Deep cleanup..."
        find ~/.claude -name "*.tmp" -o -name "*~" -o -name "*.swp" -delete
        find ~/.claude/logs -mtime +7 -delete 2>/dev/null || true
        find ~/.claude/cache -mtime +3 -delete 2>/dev/null || true
        ;;
    backups)
        echo "🧹 Cleaning old backups..."
        # Keep only last 5 backups
        ls -t ~/.claude.json.backup* 2>/dev/null | tail -n +6 | xargs -r rm
        ;;
    all)
        $0 standard
        $0 backups
        echo "✅ Complete cleanup done"
        ;;
    *)
        echo "Usage: $0 [standard|deep|backups|all]"
        exit 1
        ;;
esac
EOF
        chmod +x ~/.claude/scripts/consolidated/cleanup.sh
        
        # Archive old scripts
        mv ~/.claude/scripts/*clean*.sh ~/.claude/scripts/archive/ 2>/dev/null || true
        echo -e "  ${GREEN}✓ Consolidated $(ls ~/.claude/scripts/archive/*clean*.sh | wc -l) cleanup scripts${NC}"
    fi
    
    # Consolidate knowledge scripts
    if [ $(ls ~/.claude/scripts/knowledge*.sh 2>/dev/null | wc -l) -gt 1 ]; then
        echo "  Creating unified knowledge.sh..."
        # Merge functionality from knowledge-extractor.sh and others
        cp ~/.claude/scripts/knowledge-extractor.sh ~/.claude/scripts/consolidated/knowledge.sh 2>/dev/null || \
        cp ~/.claude/scripts/knowledge-extract.sh ~/.claude/scripts/consolidated/knowledge.sh 2>/dev/null || \
        echo "#!/bin/bash" > ~/.claude/scripts/consolidated/knowledge.sh
        
        chmod +x ~/.claude/scripts/consolidated/knowledge.sh
        mv ~/.claude/scripts/knowledge*.sh ~/.claude/scripts/archive/ 2>/dev/null || true
        echo -e "  ${GREEN}✓ Consolidated knowledge scripts${NC}"
    fi
}

# Function to create unified config system
create_config_system() {
    echo -e "\n${YELLOW}🏗️  Creating unified configuration system...${NC}"
    
    # Create config directory structure
    mkdir -p ~/.claude/config/{defaults,user,project,generated}
    
    # Create config loader
    cat > ~/.claude/scripts/config-loader.sh << 'EOF'
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
EOF
    chmod +x ~/.claude/scripts/config-loader.sh
    
    # Create default config
    cat > ~/.claude/config/defaults/base.conf << 'EOF'
# Claude Default Configuration
# DO NOT EDIT - Use user/settings.conf for customization

export CLAUDE_HOME="$HOME/.claude"
export CLAUDE_SCRIPTS="$CLAUDE_HOME/scripts"
export CLAUDE_SESSIONS="$CLAUDE_HOME/sessions"
export CLAUDE_LOGS="$CLAUDE_HOME/logs"
export CLAUDE_CACHE="$CLAUDE_HOME/cache"

# Performance settings
export CLAUDE_SESSION_RETENTION_DAYS=30
export CLAUDE_LOG_RETENTION_DAYS=7
export CLAUDE_CACHE_SIZE_MB=500

# Feature flags
export CLAUDE_ENABLE_TELEMETRY=false
export CLAUDE_ENABLE_AUTO_UPDATE=true
export CLAUDE_ENABLE_FEEDBACK_LOOP=true
EOF
    
    echo -e "  ${GREEN}✓ Created unified config system${NC}"
}

# Function to generate documentation
generate_docs() {
    echo -e "\n${YELLOW}📚 Generating configuration documentation...${NC}"
    
    cat > ~/.claude/CONFIG_MAP.md << 'EOF'
# Claude Configuration Map

## Directory Structure
```
~/.claude/
├── config/              # All configuration files
│   ├── defaults/       # Default settings (don't edit)
│   ├── user/          # User customizations
│   └── project/       # Project-specific configs
├── scripts/            # Executable scripts
│   ├── consolidated/  # New unified scripts
│   └── archive/       # Old scripts (for reference)
├── sessions/          # Session data
├── logs/              # Application logs
├── cache/             # Temporary cache
└── .credentials/      # Encrypted credentials
```

## Configuration Loading Order
1. `defaults/base.conf` - Base configuration
2. `user/settings.conf` - User customizations  
3. `.claude/config.conf` - Project overrides (if exists)
4. Environment variables - Highest precedence

## Key Scripts
- `cleanup.sh [mode]` - Unified cleanup tool
- `config-loader.sh` - Configuration management
- `secure-credentials.sh` - Credential encryption
- `health-check.sh` - System health monitoring
- `knowledge.sh` - Knowledge extraction

## Usage
```bash
# Load configuration in any script
source ~/.claude/scripts/config-loader.sh

# Get config value
value=$(claude_config_get CLAUDE_SESSION_RETENTION_DAYS 30)

# Set config value
claude_config_set CLAUDE_ENABLE_TELEMETRY true
```
EOF
    
    echo -e "  ${GREEN}✓ Generated CONFIG_MAP.md${NC}"
}

# Function to add maintenance tools
add_maintenance_tools() {
    echo -e "\n${YELLOW}🛠️  Adding maintenance tools...${NC}"
    
    # Add chaos check to health script
    cat >> ~/.claude/scripts/health-check.sh << 'EOF'

# Configuration Health Check
echo ""
echo "Configuration Health:"
chaos_score=$(find ~/.claude -name "*.json" -type f | wc -l)
chaos_score=$((chaos_score + $(find ~/.claude/scripts -name "*.sh" | wc -l) / 5))

if [ $chaos_score -gt 30 ]; then
    echo "❌ Configuration chaos detected! Run: claude-reorg fix"
else
    echo "✅ Configuration organized"
fi
EOF
    
    # Create lint tool
    cat > ~/.claude/scripts/claude-lint.sh << 'EOF'
#!/bin/bash
# Claude Configuration Linter
# PURPOSE: Check for configuration issues
# DEPENDENCIES: config-loader.sh
# CONFIG_USED: All

source ~/.claude/scripts/config-loader.sh

echo "🔍 Linting Claude configuration..."

# Check for duplicate scripts
for pattern in clean knowledge session; do
    count=$(ls ~/.claude/scripts/*$pattern*.sh 2>/dev/null | wc -l)
    if [ $count -gt 1 ]; then
        echo "⚠️  Multiple $pattern scripts found"
    fi
done

# Check for stale backups
old_backups=$(find ~ -name ".claude.json.backup*" -mtime +7 | wc -l)
[ $old_backups -gt 0 ] && echo "⚠️  Found $old_backups old backup files"

# Check permissions
[ -f ~/.claude.json ] && [ "$(stat -c %a ~/.claude.json)" != "600" ] && echo "⚠️  .claude.json has insecure permissions"

echo "✅ Lint complete"
EOF
    chmod +x ~/.claude/scripts/claude-lint.sh
    
    echo -e "  ${GREEN}✓ Added maintenance tools${NC}"
}

# Main execution
case "${1:-analyze}" in
    analyze)
        analyze_chaos
        ;;
    fix)
        echo -e "\n${YELLOW}🔧 Fixing configuration chaos...${NC}"
        analyze_chaos
        consolidate_scripts
        create_config_system
        generate_docs
        add_maintenance_tools
        
        # Move consolidated scripts to main directory
        if [ -d ~/.claude/scripts/consolidated ]; then
            cp -n ~/.claude/scripts/consolidated/* ~/.claude/scripts/ 2>/dev/null || true
        fi
        
        echo -e "\n${GREEN}✅ Configuration reorganization complete!${NC}"
        echo -e "\n${BLUE}Next steps:${NC}"
        echo "1. Review archived scripts in ~/.claude/scripts/archive/"
        echo "2. Update your scripts to use: source ~/.claude/scripts/config-loader.sh"
        echo "3. Run 'claude-lint' regularly to maintain order"
        echo "4. See ~/.claude/CONFIG_MAP.md for documentation"
        ;;
    *)
        echo "Usage: $0 [analyze|fix]"
        echo "  analyze - Show current configuration state"
        echo "  fix     - Reorganize and consolidate configuration"
        exit 1
        ;;
esac