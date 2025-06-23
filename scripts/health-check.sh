#!/bin/bash
echo "=== Claude Health Check ==="
echo "Time: $(date)"
echo ""
echo "Directories:"
for d in scripts logs .cache .credentials sessions; do
    [ -d ~/.claude/$d ] && echo "✅ $d" || echo "❌ $d"
done
echo ""
echo "Services:"
nc -zv localhost 7687 &>/dev/null && echo "✅ Neo4j" || echo "❌ Neo4j"
pg_isready -h localhost &>/dev/null && echo "✅ PostgreSQL" || echo "❌ PostgreSQL"
echo ""
echo "Resources:"
free -h | grep Mem | awk '{print "Memory: " $3 " / " $2}'
df -h /home | awk 'NR==2 {print "Disk: " $3 " / " $2}'
