#!/bin/bash
# Quick status overview

echo "=== Claude Status ==="
echo ""
echo "📁 Storage:"
du -sh ~/.claude/* 2>/dev/null | grep -E "(sessions|logs|cache|data)" | head -5

echo ""
echo "🔐 Credentials:"
~/.claude/scripts/secure-credentials.sh list 2>/dev/null | wc -l | xargs -I{} echo "  {} stored"

echo ""
echo "📊 Recent Activity:"
find ~/.claude/sessions -type f -mtime -1 2>/dev/null | wc -l | xargs -I{} echo "  {} sessions today"
find ~/.claude/logs -type f -mtime -1 2>/dev/null | wc -l | xargs -I{} echo "  {} log files updated"

echo ""
echo "🔧 Services:"
for svc in credentials health performance; do
    echo -n "  $svc: "
    ~/.claude/scripts/service.sh $svc status 2>&1 | grep -q "Active\|OK" && echo "✓" || echo "✗"
done
