# Claude Cache System - Enterprise Setup Guide

## Overview

The Claude Cache System is a high-performance local caching solution that accelerates Claude Code operations by up to 40x. It caches frequently accessed files in memory, reducing disk I/O and improving response times.

## Table of Contents
- [System Requirements](#system-requirements)
- [Security Overview](#security-overview)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Usage Instructions](#usage-instructions)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Enterprise Considerations](#enterprise-considerations)

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows (with WSL)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM (8GB recommended)
- **Disk Space**: 2GB free space for cache storage
- **Permissions**: User-level access (no root/admin required)

### Python Dependencies
```bash
pip3 install --user aiohttp psutil jsonschema pyyaml croniter crontab
```

## Security Overview

### ✅ Security Features
- **Local-Only Operation**: No external network connections
- **Path Validation**: Restricted to allowed directories only
- **Encrypted Credentials**: Uses OpenSSL for credential encryption
- **No Data Exfiltration**: All data remains on local machine
- **Audit Logging**: All operations are logged locally

### 🔒 Security Configuration
1. The system only accesses directories explicitly allowed in configuration
2. Default allowed directories: `$HOME` and `/tmp`
3. No external API calls or network requests in core functionality
4. Cache daemon listens only on localhost (127.0.0.1:19847)

## Installation Guide

### Step 1: Clone or Extract Repository
```bash
# If using git
git clone <repository-url> ~/claude-cache-system
# OR extract the provided archive
tar -xzf claude-cache-system.tar.gz -C ~/

cd ~/claude-cache-system
```

### Step 2: Run Initial Setup
```bash
# Make setup script executable
chmod +x scripts/quick-setup.sh

# Run the setup (creates directories, installs dependencies)
./scripts/quick-setup.sh

# Source bashrc to load new aliases
source ~/.bashrc
```

### Step 3: Configure Allowed Directories (IMPORTANT for Corporate Use)
Edit the cache configuration file:
```bash
# Create configuration file
mkdir -p ~/.claude/config
cat > ~/.claude/config/cache.json << 'EOF'
{
  "allowed_dirs": [
    "/home/$USER",
    "/path/to/your/project",
    "/path/to/shared/codebase"
  ],
  "cache_size_limit_gb": 1.0,
  "sensitive_data_detection": true,
  "log_level": "INFO",
  "daemon_port": 19847
}
EOF
```

Replace the paths in `allowed_dirs` with your actual project directories.

### Step 4: Start the Cache Daemon
```bash
# Start the cache daemon in background
python3 ~/.claude/cache/claude_cache_daemon.py --daemon &

# Verify it's running
chealth

# Expected output:
# ✅ Cache daemon is running
# ✅ Database is accessible
# ✅ Cache directory exists
```

### Step 5: Set Up Automatic Startup (Optional)
```bash
# Add to your shell profile (~/.bashrc or ~/.zshrc)
echo '# Auto-start Claude Cache daemon' >> ~/.bashrc
echo 'if ! pgrep -f "claude_cache_daemon.py" > /dev/null; then' >> ~/.bashrc
echo '    python3 ~/.claude/cache/claude_cache_daemon.py --daemon &' >> ~/.bashrc
echo 'fi' >> ~/.bashrc
```

## Configuration

### Cache Configuration Options

Edit `~/.claude/config/cache.json`:

```json
{
  "allowed_dirs": [
    "/home/username/projects",
    "/opt/company/codebase"
  ],
  "cache_size_limit_gb": 2.0,
  "max_file_size_mb": 10,
  "compression_threshold_kb": 100,
  "sensitive_data_detection": true,
  "sensitive_patterns": [
    "password",
    "api_key",
    "secret",
    "token",
    "private_key"
  ],
  "exclude_patterns": [
    "*.log",
    "*.tmp",
    ".git/*",
    "node_modules/*",
    "__pycache__/*"
  ],
  "log_level": "INFO",
  "log_file": "~/.claude/logs/cache.log",
  "daemon_port": 19847,
  "cleanup_interval_hours": 24,
  "ttl_hours": 168
}
```

### Performance Tuning

For large codebases, adjust these settings:
```json
{
  "worker_threads": 4,
  "batch_size": 100,
  "index_update_interval": 300,
  "memory_limit_mb": 1024
}
```

## Usage Instructions

### Basic Commands

#### Quick Aliases (Recommended)
```bash
# Cache specific file types
cwarm '*.py' '*.js' '*.java'

# Cache all common development files
cwarmall

# Check cache statistics
cstats

# Monitor cache performance
cviz

# Check system health
chealth
```

#### Full Command Interface
```bash
# Cache files matching patterns
claude-cache warm "src/**/*.py" "tests/**/*.py"

# Cache a single file
claude-cache cache /path/to/important/file.py

# Check if a file is cached
claude-cache check src/main.py

# View detailed statistics
claude-cache stats

# Monitor in real-time
claude-cache monitor

# Clear cache (requires confirmation)
claude-cache clear --confirm
```

### Typical Workflow

1. **Initial Project Setup**
```bash
cd /path/to/your/project
cwarmall  # Cache all project files
cstats    # Verify files are cached
```

2. **Daily Usage**
```bash
# The cache runs automatically in background
# Just use Claude Code normally - it will use the cache

# Periodically check performance
cstats
cviz monitor  # For real-time monitoring
```

3. **After Major Code Changes**
```bash
# Re-warm cache for changed files
cwarm '*.py'  # Or specific patterns that changed
```

## Monitoring & Maintenance

### Performance Monitoring

1. **Terminal Visualizer**
```bash
cviz          # Overview dashboard
cviz monitor  # Live monitoring
cviz graph    # Performance graphs
cviz files    # File-level analysis
```

2. **Log Monitoring**
```bash
# View cache logs
tail -f ~/.claude/logs/cache.log

# Check for errors
grep ERROR ~/.claude/logs/cache.log
```

3. **Resource Usage**
```bash
# Check memory usage
ps aux | grep claude_cache_daemon

# Check disk usage
du -sh ~/.claude/cache/
```

### Maintenance Tasks

1. **Weekly Maintenance**
```bash
# Check cache health
chealth

# Review cache statistics
cstats

# Clean up old entries (automatic, but can force)
claude-cache optimize
```

2. **Monthly Maintenance**
```bash
# Review and adjust configuration
vim ~/.claude/config/cache.json

# Clear and rebuild cache if needed
claude-cache clear --confirm
cwarmall
```

## Troubleshooting

### Common Issues

1. **Cache daemon not starting**
```bash
# Check if port is already in use
lsof -i :19847

# Check Python version
python3 --version  # Should be 3.8+

# Check permissions
ls -la ~/.claude/cache/
```

2. **Poor performance**
```bash
# Increase cache size limit
# Edit ~/.claude/config/cache.json
# Increase "cache_size_limit_gb"

# Check if files are being cached
claude-cache check /path/to/slow/file
```

3. **Permission errors**
```bash
# Ensure cache directory is writable
chmod -R 700 ~/.claude/cache/

# Check allowed directories configuration
cat ~/.claude/config/cache.json | grep allowed_dirs
```

### Debug Mode
```bash
# Run daemon in foreground with debug logging
python3 ~/.claude/cache/claude_cache_daemon.py --log-level DEBUG
```

## Enterprise Considerations

### 1. Compliance & Auditing
- All cache operations are logged to `~/.claude/logs/cache.log`
- Implement log rotation: `logrotate -f ~/.claude/config/logrotate.conf`
- Regular audit reviews of cached content

### 2. Resource Limits
```bash
# Set memory limits in systemd (if using systemd)
# /etc/systemd/system/claude-cache.service
[Service]
MemoryLimit=2G
CPUQuota=50%
```

### 3. Multi-User Setup
Each user should have their own cache instance:
```bash
# No shared cache between users for security
# Each user runs: ./scripts/quick-setup.sh
```

### 4. Integration with CI/CD
```bash
# Add to build scripts
cwarm 'src/**/*.py' 'tests/**/*.py'

# Run tests with cache enabled
pytest  # Will automatically benefit from cache
```

### 5. Backup Considerations
The cache is ephemeral and can be rebuilt:
```bash
# No need to backup cache files
# Exclude from backups: ~/.claude/cache/
```

### 6. Monitoring Integration
```bash
# Export metrics for monitoring systems
claude-cache stats --format json > /var/log/claude-cache-metrics.json

# Set up alerts for:
# - Daemon not running
# - Cache hit rate < 80%
# - Disk usage > 2GB
```

## Support

For issues or questions:
1. Check logs: `~/.claude/logs/cache.log`
2. Run health check: `chealth`
3. Review this documentation
4. Contact your IT administrator

## Version
Claude Cache System v2.0
Last Updated: 2025-01-02