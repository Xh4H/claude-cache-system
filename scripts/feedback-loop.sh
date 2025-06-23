#!/bin/bash
# Claude Feedback Loop System - Learn from every command

# Command wrapper that tracks success/failure
cl() {
    local cmd="$*"
    local start_time=$(date +%s)
    
    # Query for similar past commands
    echo "🔍 Checking knowledge base..."
    local similar=$(claude-recall "$cmd" 2>/dev/null | head -3)
    if [ -n "$similar" ]; then
        echo "💡 Similar commands:"
        echo "$similar"
        echo ""
    fi
    
    # Execute command
    echo "🚀 Running: $cmd"
    eval "$cmd"
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Record result
    if [ $exit_code -eq 0 ]; then
        echo "✅ Success"
        claude-learn "$cmd" success $duration
    else
        echo "❌ Failed with code: $exit_code"
        claude-learn "$cmd" failure $exit_code
    fi
    
    return $exit_code
}

# Learn from command execution
claude-learn() {
    local command="$1"
    local result="$2"
    local metadata="$3"
    
    # Create observation for Memento
    local observation="Command: $command | Result: $result | Time: $(date) | Metadata: $metadata"
    
    # Store in Memento
    npx -y @gannonh/memento-mcp add_observations "{
        \"observations\": [{
            \"entityName\": \"command_history\",
            \"contents\": [\"$observation\"]
        }]
    }" 2>/dev/null || echo "[Stored locally]"
    
    # Also append to local log for quick access
    echo "$(date +%Y%m%d_%H%M%S)|$command|$result|$metadata" >> ~/.claude/knowledge/command_log.csv
}

# Recall similar commands and their success rates
claude-recall() {
    local query="$1"
    
    # Search in Memento
    local memento_results=$(npx -y @gannonh/memento-mcp semantic_search "{
        \"query\": \"$query\",
        \"limit\": 5
    }" 2>/dev/null)
    
    # Search in local log
    if [ -f ~/.claude/knowledge/command_log.csv ]; then
        echo "Recent similar commands:"
        grep -i "$query" ~/.claude/knowledge/command_log.csv | tail -5 | while IFS='|' read -r timestamp cmd result meta; do
            echo "  $cmd → $result"
        done
    fi
}

# Show learning progress
claude-insights() {
    echo "=== Claude Learning Insights ==="
    echo "Total commands tracked: $(wc -l < ~/.claude/knowledge/command_log.csv 2>/dev/null || echo 0)"
    
    if [ -f ~/.claude/knowledge/command_log.csv ]; then
        echo ""
        echo "Success rate by command:"
        awk -F'|' '{cmd=$2; result=$3} 
            {count[cmd]++; if(result=="success") success[cmd]++} 
            END {for(c in count) printf "  %-30s %.0f%% (%d/%d)\n", c, (success[c]/count[c])*100, success[c], count[c]}' \
            ~/.claude/knowledge/command_log.csv | sort -k2 -nr | head -10
            
        echo ""
        echo "Most used commands:"
        cut -d'|' -f2 ~/.claude/knowledge/command_log.csv | sort | uniq -c | sort -nr | head -5
    fi
}

# Auto-suggest based on context
claude-suggest() {
    local context="${1:-current task}"
    echo "🤔 Suggestions for: $context"
    
    # Query Memento for relevant patterns
    npx -y @gannonh/memento-mcp semantic_search "{
        \"query\": \"$context successful commands\",
        \"limit\": 3
    }" 2>/dev/null | grep -o '"content":"[^"]*"' | cut -d'"' -f4
}

# Initialize feedback loop
claude-feedback-init() {
    mkdir -p ~/.claude/knowledge
    
    # Create initial entity in Memento
    npx -y @gannonh/memento-mcp create_entities "{
        \"entities\": [{
            \"name\": \"command_history\",
            \"entityType\": \"knowledge_base\",
            \"observations\": [\"Claude feedback loop initialized\"]
        }]
    }" 2>/dev/null
    
    echo "✅ Feedback loop initialized!"
    echo "Usage:"
    echo "  cl <command>     - Run command with tracking"
    echo "  claude-recall    - Search for similar commands"
    echo "  claude-insights  - View learning progress"
    echo "  claude-suggest   - Get contextual suggestions"
}

# Export functions
export -f cl
export -f claude-learn
export -f claude-recall
export -f claude-insights
export -f claude-suggest