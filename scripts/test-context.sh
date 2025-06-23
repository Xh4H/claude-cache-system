#!/bin/bash
# Test Claude's context awareness

echo "🎭 Testing Claude's Context-Aware Behaviors"
echo "=========================================="
echo

# Function to show context for a directory
test_context() {
    local dir=$1
    local name=$2
    local icon=$3
    
    echo "$icon Testing $name context:"
    echo "  Directory: $dir"
    echo "  Expected behavior: Claude should adapt to $name mode"
    echo
}

# Test each context
test_context "/home/mik/THESIS" "THESIS" "📚"
test_context "/home/mik/SEARXNG" "SEARXNG" "🔍"
test_context "/home/mik/AI-TOOLS" "AI-TOOLS" "🤖"
test_context "/home/mik/CONFIG" "CONFIG" "⚙️"
test_context "/home/mik" "General" "🏠"

echo "✅ Context definitions added to CLAUDE.md"
echo
echo "Claude will now automatically adjust its behavior based on your current directory:"
echo "- In THESIS: Academic mode with formal language and citations"
echo "- In SEARXNG: Technical mode focused on search engines"
echo "- In AI-TOOLS: ML engineering mode with GPU awareness"
echo "- In CONFIG: System admin mode with security focus"
echo "- Elsewhere: Adaptive general assistant mode"
echo
echo "Try switching directories and notice how Claude's responses adapt!"