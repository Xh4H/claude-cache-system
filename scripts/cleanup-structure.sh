#!/bin/bash
# Clean up Claude directory structure

echo "=== Claude Directory Structure Cleanup ==="

# Archive old documentation
mkdir -p ~/.claude/docs/archive
mv ~/.claude/CLEANUP-*.md ~/.claude/docs/archive/ 2>/dev/null
mv ~/.claude/CONSOLIDATION-*.md ~/.claude/docs/archive/ 2>/dev/null
mv ~/.claude/DUPLICATE_*.md ~/.claude/docs/archive/ 2>/dev/null
mv ~/.claude/ORGANIZATION*.md ~/.claude/docs/archive/ 2>/dev/null
mv ~/.claude/STRUCTURE_*.md ~/.claude/docs/archive/ 2>/dev/null

# Keep only essential docs in root
# CLAUDE.md, USER_MEMORY.md, README.md stay in root

# Remove empty directories
echo "Removing empty directories..."
find ~/.claude -type d -empty -delete

# Consolidate settings files
if [ -f ~/.claude/settings-advanced.json ]; then
    echo "Backing up settings-advanced.json..."
    cp ~/.claude/settings-advanced.json ~/.claude/backups/archive/
fi

echo "✅ Cleanup complete"
echo ""
echo "Essential structure:"
echo "~/.claude/"
echo "├── .credentials/    # Encrypted secrets"
echo "├── scripts/         # All automation"
echo "├── sessions/        # Session data"
echo "├── logs/           # Logs"
echo "├── knowledge-base/ # Extracted knowledge"
echo "├── dashboard/      # Monitoring UI"
echo "├── backups/        # Backups"
echo "├── docs/           # Documentation"
echo "├── CLAUDE.md       # Main config"
echo "└── settings.json   # Claude settings"