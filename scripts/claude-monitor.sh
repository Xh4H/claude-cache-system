#!/bin/bash
# Claude Monitor - Unified performance and health monitoring
# Consolidates all monitoring functionality

CLAUDE_DIR="$HOME/.claude"
LOG_DIR="$CLAUDE_DIR/logs"
PERF_LOG="$LOG_DIR/performance.log"
STATS_DIR="$CLAUDE_DIR/stats"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$STATS_DIR"

# Main monitor command dispatcher
claude-monitor() {
    local cmd="${1:-status}"
    shift
    
    case "$cmd" in
        status|s)    monitor_status "$@" ;;
        live|l)      monitor_live "$@" ;;
        perf|p)      monitor_performance "$@" ;;
        health|h)    monitor_health "$@" ;;
        resources|r) monitor_resources "$@" ;;
        mcp|m)       monitor_mcp "$@" ;;
        report)      monitor_report "$@" ;;
        dashboard|d) monitor_dashboard "$@" ;;
        help)        monitor_help ;;
        *)           echo "Unknown command: $cmd"; monitor_help ;;
    esac
}

# Quick status overview
monitor_status() {
    echo "📊 Claude Environment Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # System info
    echo -e "\n🖥️  System:"
    echo "  OS: $(uname -s) $(uname -r)"
    echo "  Uptime: $(uptime -p 2>/dev/null || uptime | awk -F'up' '{print $2}' | awk -F',' '{print $1}')"
    echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
    
    # Claude directory
    echo -e "\n📁 Claude Directory:"
    echo "  Size: $(du -sh $CLAUDE_DIR 2>/dev/null | cut -f1)"
    echo "  Files: $(find $CLAUDE_DIR -type f 2>/dev/null | wc -l)"
    echo "  Sessions: $(find $CLAUDE_DIR/sessions -type f 2>/dev/null | wc -l)"
    
    # Resource usage
    echo -e "\n💾 Resources:"
    echo "  Memory: $(free -h | awk '/^Mem:/ {print $3 " / " $2 " (" int($3/$2 * 100) "%)"}')"
    echo "  Disk: $(df -h $HOME | awk 'NR==2 {print $3 " / " $2 " (" $5 ")"}')"
    
    # MCP servers
    echo -e "\n🔌 MCP Servers:"
    monitor_mcp quiet
}

# Live monitoring
monitor_live() {
    local interval="${1:-5}"
    
    echo "📊 Live Monitoring (Ctrl+C to stop)"
    echo "Updating every ${interval}s..."
    
    while true; do
        clear
        echo "📊 Claude Live Monitor - $(date)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # CPU and Memory
        echo -e "\n💻 System Resources:"
        echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% used"
        echo "  Memory: $(free | awk '/^Mem:/ {printf "%.1f%%", $3/$2 * 100}')"
        echo "  Load: $(cat /proc/loadavg | cut -d' ' -f1-3)"
        
        # Process info
        echo -e "\n🔄 Claude Processes:"
        ps aux | grep -E "(claude|mcp|memento)" | grep -v grep | \
            awk '{printf "  %-20s CPU:%-5s MEM:%-5s\n", substr($11,1,20), $3"%", $4"%"}' | head -5
        
        # Disk I/O
        echo -e "\n💾 Disk Activity:"
        iostat -x 1 2 | tail -n +7 | head -3 | \
            awk '{if(NR>1) printf "  %-10s Read:%-8s Write:%-8s\n", $1, $6"KB/s", $7"KB/s"}'
        
        # Network (if monitoring specific ports)
        echo -e "\n🌐 Network Connections:"
        ss -tan | grep -E "(7687|5432|8888)" | \
            awk '{printf "  %-20s %s\n", $4, $1}' | head -5
        
        sleep $interval
    done
}

# Performance analysis
monitor_performance() {
    local period="${1:-hour}"
    
    echo "⚡ Performance Analysis ($period)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Command execution times
    if [ -f "$PERF_LOG" ]; then
        echo -e "\n⏱️  Command Performance:"
        case "$period" in
            hour)  since=$(date -d "1 hour ago" +%s) ;;
            day)   since=$(date -d "1 day ago" +%s) ;;
            week)  since=$(date -d "1 week ago" +%s) ;;
            *)     since=0 ;;
        esac
        
        awk -v since=$since '
            {
                cmd_time = $1
                if (cmd_time > since) {
                    cmd = $3
                    time = $5
                    times[cmd] += time
                    counts[cmd]++
                }
            }
            END {
                for (cmd in times) {
                    avg = times[cmd] / counts[cmd]
                    printf "  %-30s Avg: %6.2fms Count: %d\n", cmd, avg, counts[cmd]
                }
            }
        ' "$PERF_LOG" | sort -k3 -nr | head -10
    fi
    
    # Session statistics
    echo -e "\n📈 Session Statistics:"
    local total_sessions=$(find $CLAUDE_DIR/sessions -type f 2>/dev/null | wc -l)
    local recent_sessions=$(find $CLAUDE_DIR/sessions -type f -mtime -1 2>/dev/null | wc -l)
    echo "  Total sessions: $total_sessions"
    echo "  Last 24h: $recent_sessions"
    
    # Cache hit rate
    if [ -d "$CLAUDE_DIR/.cache" ]; then
        local cache_files=$(find $CLAUDE_DIR/.cache -type f 2>/dev/null | wc -l)
        local cache_size=$(du -sh $CLAUDE_DIR/.cache 2>/dev/null | cut -f1)
        echo -e "\n💾 Cache Performance:"
        echo "  Files: $cache_files"
        echo "  Size: $cache_size"
    fi
}

# Health check
monitor_health() {
    echo "🏥 Claude Health Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━"
    
    local issues=0
    
    # Check critical directories
    echo -e "\n📁 Directory Health:"
    for dir in scripts sessions logs knowledge .credentials; do
        if [ -d "$CLAUDE_DIR/$dir" ]; then
            echo "  ✅ $dir"
        else
            echo "  ❌ $dir (missing)"
            ((issues++))
        fi
    done
    
    # Check critical files
    echo -e "\n📄 Configuration Files:"
    for file in .env CLAUDE.md settings.json; do
        if [ -f "$CLAUDE_DIR/$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ⚠️  $file (missing)"
        fi
    done
    
    # Check services
    echo -e "\n🔌 Service Health:"
    
    # Neo4j
    if nc -z localhost 7687 2>/dev/null; then
        echo "  ✅ Neo4j (port 7687)"
    else
        echo "  ❌ Neo4j (port 7687)"
        ((issues++))
    fi
    
    # PostgreSQL
    if nc -z localhost 5432 2>/dev/null; then
        echo "  ✅ PostgreSQL (port 5432)"
    else
        echo "  ⚠️  PostgreSQL (port 5432)"
    fi
    
    # Check disk space
    echo -e "\n💾 Disk Space:"
    local disk_usage=$(df -h $HOME | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -lt 80 ]; then
        echo "  ✅ Home directory: ${disk_usage}% used"
    elif [ $disk_usage -lt 90 ]; then
        echo "  ⚠️  Home directory: ${disk_usage}% used (getting full)"
    else
        echo "  ❌ Home directory: ${disk_usage}% used (critical)"
        ((issues++))
    fi
    
    # Summary
    echo -e "\n📊 Health Summary:"
    if [ $issues -eq 0 ]; then
        echo "  ✅ All systems healthy"
    else
        echo "  ⚠️  $issues issues found"
    fi
}

# Resource monitoring
monitor_resources() {
    echo "💻 Resource Usage Details"
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
    
    # CPU details
    echo -e "\n🔲 CPU:"
    lscpu | grep -E "(Model name|CPU\(s\)|Thread|Core)" | sed 's/^/  /'
    
    # Memory details
    echo -e "\n💾 Memory:"
    free -h | sed 's/^/  /'
    
    # Top Claude processes
    echo -e "\n📊 Top Claude Processes:"
    ps aux | grep -E "(claude|node|python)" | grep -v grep | \
        sort -k3 -nr | head -5 | \
        awk '{printf "  %-20s CPU:%-6s MEM:%-6s PID:%-8s\n", substr($11,1,20), $3"%", $4"%", $2}'
    
    # Disk usage by directory
    echo -e "\n📁 Claude Directory Usage:"
    du -sh $CLAUDE_DIR/* 2>/dev/null | sort -hr | head -10 | sed 's/^/  /'
}

# MCP server monitoring
monitor_mcp() {
    local quiet="${1:-}"
    
    [ -z "$quiet" ] && echo "🔌 MCP Server Status:"
    
    # Check known MCP servers
    local servers=("desktop-commander" "memento" "filesystem" "github")
    for server in "${servers[@]}"; do
        if pgrep -f "$server" > /dev/null 2>&1; then
            [ -z "$quiet" ] && echo "  ✅ $server"
        else
            echo "  ⚠️  $server (not running)"
        fi
    done
    
    # Check MCP ports
    [ -z "$quiet" ] && echo -e "\n🌐 MCP Connections:"
    ss -tan | grep LISTEN | grep -E "(7687|5432|6379)" | while read line; do
        port=$(echo $line | awk '{print $4}' | rev | cut -d: -f1 | rev)
        case $port in
            7687) service="Neo4j" ;;
            5432) service="PostgreSQL" ;;
            6379) service="Redis" ;;
            *) service="Unknown" ;;
        esac
        [ -z "$quiet" ] && echo "  ✅ $service (port $port)"
    done
}

# Generate comprehensive report
monitor_report() {
    local output="${1:-$CLAUDE_DIR/logs/monitoring-report-$(date +%Y%m%d-%H%M%S).txt}"
    
    echo "📊 Generating comprehensive report..."
    
    {
        echo "Claude Monitoring Report"
        echo "Generated: $(date)"
        echo "========================="
        echo
        
        monitor_status
        echo -e "\n\n"
        
        monitor_health
        echo -e "\n\n"
        
        monitor_performance day
        echo -e "\n\n"
        
        monitor_resources
        echo -e "\n\n"
        
        # Additional analytics
        echo "📊 Usage Analytics"
        echo "━━━━━━━━━━━━━━━━━"
        
        # Most used commands
        if [ -f "$CLAUDE_DIR/logs/commands.log" ]; then
            echo -e "\n🎯 Most Used Commands:"
            awk '{print $1}' "$CLAUDE_DIR/logs/commands.log" | \
                sort | uniq -c | sort -nr | head -10 | \
                awk '{printf "  %3d - %s\n", $1, $2}'
        fi
        
    } > "$output"
    
    echo "✅ Report saved to: $output"
}

# Web dashboard (simple HTTP server)
monitor_dashboard() {
    local port="${1:-8090}"
    
    echo "🌐 Starting monitoring dashboard on port $port..."
    echo "   Access at: http://localhost:$port"
    
    # Create simple HTML dashboard
    cat > "$CLAUDE_DIR/dashboard/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Claude Monitor Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .metric { background: #2d2d2d; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .status-ok { color: #4ec9b0; }
        .status-warn { color: #dcdcaa; }
        .status-error { color: #f44747; }
        h1 { color: #569cd6; }
        h2 { color: #4ec9b0; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Monitor Dashboard</h1>
        <p>Last updated: <span id="timestamp"></span></p>
        <div id="metrics"></div>
    </div>
    <script>
        function updateDashboard() {
            document.getElementById('timestamp').textContent = new Date().toLocaleString();
            // In real implementation, fetch metrics via API
        }
        setInterval(updateDashboard, 5000);
        updateDashboard();
    </script>
</body>
</html>
EOF
    
    # Start simple HTTP server
    cd "$CLAUDE_DIR/dashboard" && python3 -m http.server $port
}

# Help text
monitor_help() {
    cat << EOF
Claude Monitor - Unified Performance & Health Monitoring

Usage: claude-monitor <command> [options]

Commands:
  status          Quick status overview (default)
  live [interval] Live monitoring display (default: 5s)
  perf [period]   Performance analysis (hour|day|week)
  health          Comprehensive health check
  resources       Detailed resource usage
  mcp             MCP server status
  report [file]   Generate full report
  dashboard [port] Start web dashboard (default: 8090)
  help            Show this help

Shortcuts:
  cm    = claude-monitor
  cms   = claude-monitor status
  cml   = claude-monitor live
  cmh   = claude-monitor health

Examples:
  claude-monitor                # Quick status
  claude-monitor live 2         # Live updates every 2s
  claude-monitor perf week      # Week's performance
  claude-monitor report         # Generate report

Performance Logging:
  Commands are automatically logged to:
  $CLAUDE_DIR/logs/performance.log

EOF
}

# Performance logging wrapper
log_performance() {
    local cmd="$1"
    local start=$(date +%s%N)
    shift
    "$@"
    local end=$(date +%s%N)
    local duration=$(( (end - start) / 1000000 ))
    echo "$(date +%s) cmd:$cmd duration:${duration}ms" >> "$PERF_LOG"
}

# Aliases
alias cm='claude-monitor'
alias cms='claude-monitor status'
alias cml='claude-monitor live'
alias cmh='claude-monitor health'

# Export functions
export -f claude-monitor
export -f log_performance

# If called directly, run the command
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    claude-monitor "$@"
fi