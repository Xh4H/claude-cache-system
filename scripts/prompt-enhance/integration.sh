#!/bin/bash
# Integration script for Claude Code prompt enhancement

# This would integrate with Claude Code's input processing
# Currently for demonstration/testing purposes

ENHANCER="$HOME/.claude/scripts/prompt-enhance/prompt-enhancer.py"

enhance_if_enabled() {
    local prompt="$1"
    local status=$(python3 "$ENHANCER" status | grep -o '"enabled": [^,]*' | cut -d' ' -f2)
    
    if [ "$status" = "true" ]; then
        python3 "$ENHANCER" enhance "$prompt"
    else
        echo "$prompt"
    fi
}

# Example integration point
if [ "$1" = "hook" ]; then
    # This would be called by Claude Code before processing
    enhance_if_enabled "$2"
fi