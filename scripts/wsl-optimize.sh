#!/bin/bash
# WSL2 Optimization Script for Claude Performance
# PURPOSE: Configure WSL2 for optimal Claude Code performance
# DEPENDENCIES: Windows host access for .wslconfig

echo "🚀 WSL2 Optimization for Claude"
echo "==============================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running in WSL2
if ! grep -q WSL2 /proc/version; then
    echo -e "${RED}❌ This script is for WSL2 only${NC}"
    exit 1
fi

# Function to create Windows .wslconfig
create_wslconfig() {
    echo -e "${YELLOW}📝 Creating optimal .wslconfig...${NC}"
    
    # Get system info
    local total_ram=$(free -g | awk '/^Mem:/{print $2}')
    local cpu_count=$(nproc)
    
    # Calculate optimal settings (50% RAM, 75% CPUs)
    local wsl_ram=$((total_ram / 2))
    local wsl_cpus=$((cpu_count * 3 / 4))
    
    # Ensure minimum values
    [ $wsl_ram -lt 4 ] && wsl_ram=4
    [ $wsl_cpus -lt 2 ] && wsl_cpus=2
    
    # Create config content
    cat > /tmp/.wslconfig << EOF
[wsl2]
# Memory allocated to WSL2 VM
memory=${wsl_ram}GB

# Number of processors
processors=$wsl_cpus

# Swap space
swap=2GB

# localhost forwarding
localhostForwarding=true

[experimental]
# Automatically reclaim memory
autoMemoryReclaim=gradual

# Use sparse VHD to save disk space
sparseVhd=true

# DNS tunneling for better network performance
dnsTunneling=true

# Auto proxy for better network handling
autoProxy=true
EOF

    echo -e "${GREEN}✅ Created .wslconfig with:${NC}"
    echo "   - Memory: ${wsl_ram}GB"
    echo "   - Processors: $wsl_cpus"
    echo "   - Swap: 2GB"
    echo "   - Experimental features enabled"
}

# Function to apply WSL config
apply_wslconfig() {
    echo -e "${YELLOW}📋 Applying WSL configuration...${NC}"
    
    # Copy to Windows user directory
    local win_user=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r\n')
    local win_home="/mnt/c/Users/$win_user"
    
    if [ -d "$win_home" ]; then
        # Backup existing config
        if [ -f "$win_home/.wslconfig" ]; then
            cp "$win_home/.wslconfig" "$win_home/.wslconfig.backup-$(date +%Y%m%d)"
            echo "   ✓ Backed up existing .wslconfig"
        fi
        
        # Copy new config
        cp /tmp/.wslconfig "$win_home/.wslconfig"
        echo -e "${GREEN}✅ Applied .wslconfig to $win_home${NC}"
    else
        echo -e "${RED}❌ Could not find Windows home directory${NC}"
        echo "   Please manually copy /tmp/.wslconfig to C:\\Users\\YourUsername\\.wslconfig"
    fi
}

# Function to optimize WSL2 filesystem
optimize_filesystem() {
    echo -e "${YELLOW}🗂️  Optimizing filesystem...${NC}"
    
    # Create fstab entry for better performance
    if ! grep -q "claude-optimized" /etc/fstab; then
        echo "# claude-optimized" | sudo tee -a /etc/fstab
        echo "none /mnt/c fuse.drvfs rw,noatime,uid=1000,gid=1000,umask=22,fmask=11,metadata,case=off 0 0" | sudo tee -a /etc/fstab
        echo -e "${GREEN}✅ Optimized /etc/fstab for better performance${NC}"
    else
        echo "   ✓ Filesystem already optimized"
    fi
}

# Function to create performance monitoring
create_perf_monitor() {
    echo -e "${YELLOW}📊 Creating performance monitor...${NC}"
    
    cat > ~/.claude/scripts/wsl-perf.sh << 'PERF_SCRIPT'
#!/bin/bash
# WSL2 Performance Monitor

echo "=== WSL2 Performance Status ==="
echo ""
echo "Memory Usage:"
free -h | grep -E "^(Mem|Swap):"
echo ""
echo "CPU Info:"
nproc && grep "model name" /proc/cpuinfo | head -1
echo ""
echo "Disk I/O Performance:"
dd if=/dev/zero of=/tmp/test bs=1M count=100 2>&1 | grep -E "copied|MB/s"
rm -f /tmp/test
echo ""
echo "Network Performance:"
ping -c 3 8.8.8.8 | tail -1
echo ""
echo "Claude-specific paths:"
echo -n "  ~/projects: "
time -p ls ~/projects >/dev/null 2>&1 | grep real
echo -n "  /mnt/c: "
time -p ls /mnt/c >/dev/null 2>&1 | grep real
PERF_SCRIPT
    
    chmod +x ~/.claude/scripts/wsl-perf.sh
    echo -e "${GREEN}✅ Created performance monitor${NC}"
}

# Function to optimize Claude-specific settings
optimize_claude() {
    echo -e "${YELLOW}🤖 Optimizing Claude-specific settings...${NC}"
    
    # Move projects to native filesystem
    if [ ! -d ~/projects ]; then
        mkdir -p ~/projects
        echo "   ✓ Created ~/projects for better performance"
    fi
    
    # Create project mover script
    cat > ~/.claude/scripts/move-to-native.sh << 'MOVER_SCRIPT'
#!/bin/bash
# Move project from Windows to WSL native filesystem

PROJECT="${1:-$(basename $PWD)}"
WIN_PATH="${2:-$PWD}"

if [[ "$WIN_PATH" == /mnt/c/* ]]; then
    echo "Moving $PROJECT to native filesystem..."
    cp -r "$WIN_PATH" ~/projects/
    echo "✅ Moved to ~/projects/$PROJECT"
    echo "   Performance will be significantly better!"
    echo "   Windows symlink: mklink /D C:\\WSL-Projects\\$PROJECT \\\\wsl$\\Ubuntu\\home\\$USER\\projects\\$PROJECT"
else
    echo "Already on native filesystem"
fi
MOVER_SCRIPT
    
    chmod +x ~/.claude/scripts/move-to-native.sh
    
    # Add performance aliases
    cat >> ~/.bashrc << 'PERF_ALIASES'

# WSL2 Performance Aliases
alias wsl-perf='~/.claude/scripts/wsl-perf.sh'
alias move-to-native='~/.claude/scripts/move-to-native.sh'
alias claude-native='cd ~/projects'

# Faster file operations
alias cpn='cp --reflink=auto'  # Copy-on-write when possible
alias find-fast='find -printf ""'  # Faster find without stat

# Monitor WSL2 resources
wsl-stats() {
    echo "WSL2 Resource Usage:"
    echo "==================="
    cat /proc/meminfo | grep -E "^(MemTotal|MemFree|MemAvailable):"
    echo ""
    cat /proc/stat | grep "^cpu " | awk '{usage=100-($5*100)/($2+$3+$4+$5+$6+$7+$8)} END {printf "CPU Usage: %.1f%%\n", usage}'
}
PERF_ALIASES
    
    echo -e "${GREEN}✅ Added performance aliases${NC}"
}

# Function to create systemd service for performance
create_systemd_service() {
    echo -e "${YELLOW}🔧 Creating systemd optimization service...${NC}"
    
    if command -v systemctl &> /dev/null; then
        cat > /tmp/claude-wsl-optimize.service << 'SERVICE'
[Unit]
Description=Claude WSL2 Performance Optimizations
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo 1 > /proc/sys/vm/drop_caches'
ExecStart=/bin/bash -c 'echo madvise > /sys/kernel/mm/transparent_hugepage/enabled'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE
        
        sudo cp /tmp/claude-wsl-optimize.service /etc/systemd/system/
        sudo systemctl enable claude-wsl-optimize.service
        echo -e "${GREEN}✅ Created systemd optimization service${NC}"
    else
        echo "   ℹ️  Systemd not available, skipping service creation"
    fi
}

# Main execution
echo ""
create_wslconfig
apply_wslconfig
optimize_filesystem
create_perf_monitor
optimize_claude
create_systemd_service

echo ""
echo -e "${GREEN}🎉 WSL2 Optimization Complete!${NC}"
echo ""
echo "⚠️  IMPORTANT: You must restart WSL2 for changes to take effect:"
echo ""
echo "1. Exit all WSL terminals"
echo "2. In PowerShell (as admin): wsl --shutdown"
echo "3. Start WSL again"
echo ""
echo "📊 After restart, run 'wsl-perf' to check performance"
echo "🚀 Use 'move-to-native' to move projects for better speed"
echo ""
echo "💡 Tips:"
echo "- Work in ~/projects instead of /mnt/c for 10x better performance"
echo "- Use 'claude-native' to quickly go to native projects"
echo "- Run 'wsl-stats' to monitor resource usage"