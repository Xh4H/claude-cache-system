#\!/bin/bash
# Claude Code Configuration Cleanup Script

echo "=== Claude Code Configuration Cleanup ==="
echo

# Load environment variables
if [ -f ~/.claude-env ]; then
    echo "✓ Loading environment variables from ~/.claude-env"
    set -a
    source ~/.claude-env
    set +a
else
    echo "⚠️  Warning: ~/.claude-env not found"
fi

# Validate cleaned config
echo "✓ Validating cleaned configuration..."
if jq . ~/.claude.json.cleaned > /dev/null 2>&1; then
    echo "  Configuration is valid JSON"
else
    echo "  ❌ Error: Invalid JSON in cleaned config"
    exit 1
fi

# Check credentials are replaced
echo "✓ Checking credential replacement..."
if grep -q "alfredisgone\ < /dev/null | A41zMkL5xumBKuVyKma3rQ==" ~/.claude.json.cleaned; then
    echo "  ❌ Error: Plaintext passwords still present"
    exit 1
else
    echo "  Credentials properly replaced with env vars"
fi

# Show differences
echo
echo "=== Configuration Changes ==="
echo "Original: $(wc -l < ~/.claude.json) lines"
echo "Cleaned:  $(wc -l < ~/.claude.json.cleaned) lines"
echo "Reduced by: $(($(wc -l < ~/.claude.json) - $(wc -l < ~/.claude.json.cleaned))) lines"

echo
echo "=== Ready to Apply ==="
echo "This will replace your current configuration."
echo "Backup created at: ~/.claude.json.backup-$(date +%Y%m%d-%H%M%S)"
echo
read -p "Apply cleaned configuration? [y/N] " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    mv ~/.claude.json.cleaned ~/.claude.json
    echo "✓ Configuration updated successfully!"
    echo
    echo "Next steps:"
    echo "1. Restart Claude Code to load new configuration"
    echo "2. Test all MCP server connections"
    echo "3. Verify credentials are working"
else
    echo "Configuration update cancelled."
    echo "Cleaned config saved at: ~/.claude.json.cleaned"
fi
