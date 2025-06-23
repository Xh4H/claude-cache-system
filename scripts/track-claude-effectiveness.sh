#!/bin/bash
# Claude Effectiveness Tracking Script

echo "=== Claude Effectiveness Report - Sun Jun 22 09:58:25 CEST 2025 ==="
echo ""
echo "1. Response Brevity (avg lines per response):"
if ls ~/.claude-conversations/*.md 2>/dev/null | head -1 > /dev/null; then
    tail -20 ~/.claude-conversations/*.md 2>/dev/null | grep "^>" | wc -l | 
        awk '{print "   Average: " /20 " lines"}'
else
    echo "   No conversation logs found"
fi

echo ""
echo "2. MCP Failures (last 7 days):"
if [ -d ~/.claude-server-commander-logs ]; then
    find ~/.claude-server-commander-logs -mtime -7 -exec grep -l "failed\|error" {} \; 2>/dev/null | 
        wc -l | awk '{print "   Total failures: " }'
else
    echo "   No MCP logs found"
fi

echo ""
echo "3. Clarification Requests:"
if ls ~/.claude-conversations/*.md 2>/dev/null | head -1 > /dev/null; then
    grep -h "?" ~/.claude-conversations/* 2>/dev/null | grep -E "(Should I|Which|Do you mean)" | 
        wc -l | awk '{print "   Total questions: " }'
else
    echo "   No conversation logs found"
fi

echo ""
echo "4. Most Used Tools:"
if ls ~/.claude-conversations/*.md 2>/dev/null | head -1 > /dev/null; then
    grep -hE "(Read|Write|Edit|Bash|execute_command|kh search)" ~/.claude-conversations/* 2>/dev/null | 
        sed 's/.*\(Read\|Write\|Edit\|Bash\|execute_command\|kh search\).*/\1/' | 
        sort | uniq -c | sort -rn | head -5
else
    echo "   No tool usage data found"
fi

echo ""
echo "5. Quick Effectiveness Checks:"
echo "   - Check for verbose responses"
echo "   - Verify WSL path handling" 
echo "   - Monitor Knowledge Hub usage"
echo "   - Track unauthorized commits"
echo ""
echo "Run weekly and update CLAUDE.md based on findings!"
