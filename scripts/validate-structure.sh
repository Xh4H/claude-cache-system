#!/bin/bash
# Validate Claude directory structure against maintenance policy

CLAUDE_DIR="$HOME/.claude"
ISSUES=0

echo "🔍 Validating Claude Directory Structure"
echo "========================================"

# Check for duplicate script names
echo -e "\n📜 Checking for duplicate scripts..."
DUPLICATES=$(find "$CLAUDE_DIR/scripts" -name "*.sh" -exec basename {} \; | sort | uniq -d)
if [ -n "$DUPLICATES" ]; then
    echo "❌ Found duplicate script names:"
    echo "$DUPLICATES" | sed 's/^/   /'
    ((ISSUES++))
else
    echo "✅ No duplicate scripts found"
fi

# Check naming convention
echo -e "\n🏷️  Checking script naming convention..."
BAD_NAMES=$(find "$CLAUDE_DIR/scripts" -name "*.sh" ! -name "claude-*.sh" ! -name "*.local.sh" -exec basename {} \; 2>/dev/null)
if [ -n "$BAD_NAMES" ]; then
    echo "⚠️  Scripts not following claude-*.sh convention:"
    echo "$BAD_NAMES" | sed 's/^/   /'
else
    echo "✅ All scripts follow naming convention"
fi

# Check for multiple env files
echo -e "\n🔧 Checking environment files..."
ENV_COUNT=$(find "$CLAUDE_DIR" -maxdepth 1 -name ".env*" | wc -l)
if [ $ENV_COUNT -gt 1 ]; then
    echo "❌ Multiple .env files found ($ENV_COUNT)"
    find "$CLAUDE_DIR" -maxdepth 1 -name ".env*" | sed 's/^/   /'
    ((ISSUES++))
else
    echo "✅ Single .env file"
fi

# Check for scattered config files
echo -e "\n⚙️  Checking configuration files..."
CONFIG_SCATTER=$(find "$CLAUDE_DIR" -name "*.json" -o -name "*.conf" | grep -v -E "(config/|archived/|.git/|todos/)" | wc -l)
if [ $CONFIG_SCATTER -gt 5 ]; then
    echo "⚠️  Config files outside config/ directory: $CONFIG_SCATTER"
    find "$CLAUDE_DIR" -name "*.json" -o -name "*.conf" | grep -v -E "(config/|archived/|.git/|todos/)" | head -5 | sed 's/^/   /'
fi

# Check directory structure
echo -e "\n📁 Checking directory structure..."
EXPECTED_DIRS=("scripts" "config" "logs" "sessions" "knowledge" "backups")
for dir in "${EXPECTED_DIRS[@]}"; do
    if [ ! -d "$CLAUDE_DIR/$dir" ]; then
        echo "❌ Missing directory: $dir"
        ((ISSUES++))
    fi
done

# Check for empty directories
echo -e "\n📂 Checking for empty directories..."
EMPTY_DIRS=$(find "$CLAUDE_DIR" -type d -empty -not -path "*/.git/*" | wc -l)
if [ $EMPTY_DIRS -gt 5 ]; then
    echo "⚠️  Too many empty directories: $EMPTY_DIRS"
    find "$CLAUDE_DIR" -type d -empty -not -path "*/.git/*" | head -5 | sed 's/^/   /'
fi

# Check file permissions
echo -e "\n🔒 Checking file permissions..."
BAD_PERMS=$(find "$CLAUDE_DIR/scripts" -name "*.sh" ! -perm -755 | wc -l)
if [ $BAD_PERMS -gt 0 ]; then
    echo "❌ Scripts without execute permissions: $BAD_PERMS"
    ((ISSUES++))
fi

# Summary
echo -e "\n📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━"
if [ $ISSUES -eq 0 ]; then
    echo "✅ All checks passed! Structure is compliant."
else
    echo "⚠️  Found $ISSUES issues that need attention."
    echo "   Run 'claude-cleanup deep' to fix most issues."
fi

exit $ISSUES