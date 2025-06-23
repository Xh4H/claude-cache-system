#!/bin/bash
KB_DIR="$HOME/.claude/knowledge-base"
mkdir -p "$KB_DIR"

case "$1" in
    extract)
        echo "Extracting knowledge..."
        find ~/.claude/sessions -name "*.md" -o -name "*.txt" | while read f; do
            grep -E "(^#|^\$|^```)" "$f" >> "$KB_DIR/extracted.md" 2>/dev/null || true
        done
        echo "✅ Knowledge extracted"
        ;;
    search)
        grep -i "$2" "$KB_DIR"/* 2>/dev/null | head -20
        ;;
esac
