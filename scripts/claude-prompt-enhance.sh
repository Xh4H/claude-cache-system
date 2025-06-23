#!/bin/bash
# Claude Code Prompt Enhancement Mode Toggle

CONFIG_FILE="$HOME/.claude/configs/prompt-enhancement-mode.json"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

show_status() {
    if grep -q '"enabled": true' "$CONFIG_FILE" 2>/dev/null; then
        LEVEL=$(jq -r '.settings.enhancement_level' "$CONFIG_FILE" 2>/dev/null || echo "smart")
        echo "✅ Prompt Enhancement: ON (Level: $LEVEL)"
    else
        echo "❌ Prompt Enhancement: OFF"
    fi
}

toggle_mode() {
    if grep -q '"enabled": true' "$CONFIG_FILE" 2>/dev/null; then
        # Turn off
        jq '.enabled = false' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        echo "❌ Prompt Enhancement Mode: DISABLED"
    else
        # Turn on
        jq '.enabled = true' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        echo "✅ Prompt Enhancement Mode: ENABLED"
    fi
}

set_level() {
    local LEVEL="$1"
    if [[ "$LEVEL" =~ ^(off|minimal|smart|aggressive)$ ]]; then
        jq --arg level "$LEVEL" '.settings.enhancement_level = $level' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        echo "✅ Enhancement level set to: $LEVEL"
    else
        echo "❌ Invalid level. Choose: off, minimal, smart, or aggressive"
        exit 1
    fi
}

case "$1" in
    "")
        show_status
        ;;
    "on")
        jq '.enabled = true' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        echo "✅ Prompt Enhancement Mode: ENABLED"
        ;;
    "off")
        jq '.enabled = false' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        echo "❌ Prompt Enhancement Mode: DISABLED"
        ;;
    "toggle")
        toggle_mode
        ;;
    "status")
        show_status
        echo ""
        echo "Current settings:"
        jq '.settings.enhancement_level, .settings.auto_detect' "$CONFIG_FILE" 2>/dev/null
        ;;
    "level")
        if [ -z "$2" ]; then
            echo "Current level: $(jq -r '.settings.enhancement_level' "$CONFIG_FILE" 2>/dev/null || echo "smart")"
            echo "Available: off, minimal, smart, aggressive"
        else
            set_level "$2"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Claude Code Prompt Enhancement Mode"
        echo ""
        echo "Usage:"
        echo "  claude-prompt-enhance         Show current status"
        echo "  claude-prompt-enhance on      Enable enhancement mode"
        echo "  claude-prompt-enhance off     Disable enhancement mode"
        echo "  claude-prompt-enhance toggle  Toggle on/off"
        echo "  claude-prompt-enhance status  Show detailed status"
        echo "  claude-prompt-enhance level [off|minimal|smart|aggressive]"
        echo ""
        echo "Levels:"
        echo "  off        - No enhancement"
        echo "  minimal    - Only fix critical issues"
        echo "  smart      - Intelligent enhancement (default)"
        echo "  aggressive - Always try to improve"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use 'claude-prompt-enhance help' for usage"
        exit 1
        ;;
esac