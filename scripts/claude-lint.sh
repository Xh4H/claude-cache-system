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
