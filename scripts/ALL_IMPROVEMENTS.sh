#!/bin/bash
# This file contains all improvement scripts

# 1. SECURE CREDENTIALS
cat > ~/.claude/scripts/secure-credentials.sh << 'SECURE_SCRIPT'
#!/bin/bash
CRED_DIR="$HOME/.claude/.credentials"

case "$1" in
    init)
        mkdir -p "$CRED_DIR" && chmod 700 "$CRED_DIR"
        if [ ! -f "$CRED_DIR/.master_key" ]; then
            openssl rand -base64 32 > "$CRED_DIR/.master_key"
            chmod 600 "$CRED_DIR/.master_key"
            echo "✅ Master key created - BACK THIS UP!"
        fi
        ;;
    set)
        [ ! -f "$CRED_DIR/.master_key" ] && $0 init
        echo "$3" | openssl enc -aes-256-cbc -a -salt -pass file:"$CRED_DIR/.master_key" -out "$CRED_DIR/$2.enc"
        chmod 600 "$CRED_DIR/$2.enc"
        echo "✅ Saved: $2"
        ;;
    get)
        [ -f "$CRED_DIR/$2.enc" ] && openssl enc -aes-256-cbc -d -a -pass file:"$CRED_DIR/.master_key" -in "$CRED_DIR/$2.enc"
        ;;
    list)
        ls -1 "$CRED_DIR"/*.enc 2>/dev/null | xargs -I{} basename {} .enc
        ;;
esac
SECURE_SCRIPT
chmod +x ~/.claude/scripts/secure-credentials.sh

# 2. HEALTH CHECK
cat > ~/.claude/scripts/health-check.sh << 'HEALTH_SCRIPT'
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
HEALTH_SCRIPT
chmod +x ~/.claude/scripts/health-check.sh

# 3. PERFORMANCE MONITOR
cat > ~/.claude/scripts/performance-monitor.sh << 'PERF_SCRIPT'
#!/bin/bash
echo "=== Performance Report ==="
echo "Cache: $(du -sh ~/.claude/.cache 2>/dev/null | cut -f1)"
echo "Sessions: $(ls -1 ~/.claude/sessions 2>/dev/null | wc -l)"
echo "Logs: $(find ~/.claude/logs -type f 2>/dev/null | wc -l)"
echo "Claude processes: $(pgrep -f claude | wc -l)"
PERF_SCRIPT
chmod +x ~/.claude/scripts/performance-monitor.sh

# 4. SESSION MANAGER
cat > ~/.claude/scripts/session-manager.sh << 'SESSION_SCRIPT'
#!/bin/bash
case "$1" in
    save)
        SESSION="session_$(date +%Y%m%d_%H%M%S)"
        mkdir -p ~/.claude/sessions/$SESSION
        echo "Topic: ${2:-Untitled}" > ~/.claude/sessions/$SESSION/info.txt
        echo "Created: $(date)" >> ~/.claude/sessions/$SESSION/info.txt
        pwd > ~/.claude/sessions/$SESSION/pwd.txt
        echo "✅ Saved: $SESSION"
        ;;
    list)
        find ~/.claude/sessions -name info.txt -exec grep -H "Topic:" {} \; 2>/dev/null
        ;;
esac
SESSION_SCRIPT
chmod +x ~/.claude/scripts/session-manager.sh

# 5. KNOWLEDGE EXTRACTOR
cat > ~/.claude/scripts/knowledge-extractor.sh << 'KNOWLEDGE_SCRIPT'
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
KNOWLEDGE_SCRIPT
chmod +x ~/.claude/scripts/knowledge-extractor.sh

echo "✅ All scripts created"
