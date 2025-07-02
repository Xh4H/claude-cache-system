# Fortris Security Cache System - Enterprise Setup Guide

## Overview

**Fortris Security Cache** is a high-performance local caching solution specifically designed for **enterprise security analysis of large codebases**. Built for security teams who need to efficiently analyze massive repositories, Fortris accelerates code analysis operations by up to 40x while providing:

- **Real-time vulnerability detection** during caching
- **Git-based incremental updates** for efficient CI/CD integration
- **Intelligent cache partitioning** for large-scale codebases
- **Security-focused warming strategies** to prioritize high-risk files
- **Comprehensive security reporting** with vulnerability tracking

## Table of Contents
- [System Requirements](#system-requirements)
- [Security Features](#security-features)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Security-Focused Usage](#security-focused-usage)
- [Git Integration](#git-integration)
- [Vulnerability Detection](#vulnerability-detection)
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
pip3 install --user aiohttp psutil jsonschema pyyaml croniter crontab GitPython cachetools numpy
```

## Security Features

### 🔍 **Real-Time Vulnerability Detection**
- **50+ security patterns** covering OWASP Top 10
- **Hardcoded secrets detection** (passwords, API keys, tokens)
- **SQL injection vulnerability scanning**
- **Command injection risk assessment**
- **Path traversal attack detection**
- **Weak cryptography identification**
- **CORS misconfiguration alerts**

### ⚡ **Performance Optimizations for Large Codebases**
- **Intelligent cache partitioning** (up to 10GB cache with 4+ partitions)
- **Multi-level caching** (hot cache + TTL cache)
- **Parallel processing** (8 I/O workers + 4 CPU workers)
- **Memory-mapped file reading** for large files
- **Asynchronous operations** with connection pooling

### 🔄 **Git Integration**
- **Incremental updates** based on commits/PRs
- **Automatic change detection** via git hooks
- **Branch-aware caching** with SHA tracking
- **Commit-specific vulnerability tracking**

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

### Step 1: Clone or Extract Fortris Repository
```bash
# If using git
git clone <repository-url> ~/fortris-security-cache
# OR extract the provided archive
tar -xzf fortris-security-cache.tar.gz -C ~/

cd ~/fortris-security-cache
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
Edit the Fortris cache configuration file:
```bash
# Create Fortris configuration file
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

### Step 4: Start the Fortris Security Daemon
```bash
# Start the Fortris security cache daemon
python3 ~/.claude/cache/fortris_security_daemon.py --daemon &

# Or use the convenient command
fortris start

# Verify it's running
fortris status

# Expected output:
# ✅ Fortris security daemon is running
# ✅ Database is accessible
# ✅ Cache directory exists
# ✅ Security patterns loaded
```

### Step 5: Set Up Automatic Startup (Optional)
```bash
# Add to your shell profile (~/.bashrc or ~/.zshrc)
echo '# Auto-start Fortris Security daemon' >> ~/.bashrc
echo 'if ! pgrep -f "fortris_security_daemon.py" > /dev/null; then' >> ~/.bashrc
echo '    python3 ~/.claude/cache/fortris_security_daemon.py --daemon &' >> ~/.bashrc
echo 'fi' >> ~/.bashrc
```

## Configuration

### Fortris Cache Configuration Options

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
  "daemon_port": 19848,
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

## Security-Focused Usage

### Security Cache Commands

#### Primary Security Commands
```bash
# Start security analysis
fortris start                    # Start Fortris security daemon
fortris warm "src/**/*.py"      # Cache with vulnerability analysis
fortris scan                    # Full vulnerability scan
fortris report                  # Generate security report

# Git integration
fortris git-init /path/to/repo  # Enable git tracking
fortris git-update              # Update from git changes

# Monitoring
fortris health                  # System health check
fortris metrics                 # Performance metrics
```

#### Security-Focused Cache Warming
```bash
# Use intelligent warming strategies
./scripts/fortris-warm-strategies.sh

# Quick security-focused warming
fortris warm \
  "**/auth*.py" "**/security*.py" \
  "**/config*.py" "**/settings*.py" \
  "**/*.sql" "**/models*.py"

# Warm by risk level (high-risk files first)
fortris warm "**/password*" "**/secret*" "**/api*"
```

#### Legacy Commands (Still Available)
```bash
# Original cache commands still work
cwarm '*.py' '*.js' '*.java'  # Basic cache warming
cstats                        # Basic statistics  
cviz                          # Terminal visualizer
chealth                       # Basic health check
```

### Security Analysis Workflow

1. **Initial Security Setup**
```bash
cd /path/to/your/codebase
fortris start                           # Start Fortris security daemon
fortris git-init $(pwd)                # Enable git integration
./scripts/fortris-warm-strategies.sh   # Interactive warming
fortris report > security-baseline.json # Baseline report
```

2. **Daily Security Analysis**
```bash
# Incremental updates from git
fortris git-update

# Quick vulnerability check
fortris scan

# Monitor security metrics
fortris metrics | grep security
```

3. **CI/CD Integration**
```bash
# In your CI pipeline
fortris git-update --base origin/main --target HEAD
fortris scan
fortris report > security-report-$BUILD_ID.json

# Check for new vulnerabilities
if [ $(jq '.summary.high_risk_files' security-report-$BUILD_ID.json) -gt 0 ]; then
  echo "❌ New security issues detected by Fortris"
  exit 1
fi
```

## Git Integration

### Setting Up Git Integration
```bash
# Initialize git integration for a repository
fortris git-init /path/to/your/repo

# Fortris will now track:
# - File changes via git SHA hashes
# - Commit-based incremental updates
# - Branch-specific vulnerability tracking
```

### Git-Based Updates
```bash
# Update cache based on git changes
fortris git-update                    # Compare HEAD~1 to HEAD
fortris git-update --base main        # Compare main to HEAD
fortris git-update --base HEAD~5      # Compare HEAD~5 to HEAD

# Automatic updates (runs every 5 minutes)
# Background worker automatically detects git changes
```

### Pull Request Analysis
```bash
# Analyze changes in a specific commit range
fortris git-update --base $PR_BASE --target $PR_HEAD

# Generate PR-specific security report
fortris report --format json > pr-security-$PR_ID.json
```

## Vulnerability Detection

### Security Patterns Detected

1. **Authentication & Secrets**
   - Hardcoded passwords, API keys, tokens
   - Weak authentication mechanisms
   - Credential exposure in logs

2. **Injection Vulnerabilities**
   - SQL injection (string concatenation, f-strings)
   - Command injection (os.system, subprocess)
   - Code injection (eval with user input)

3. **Cryptography Issues**
   - Weak hash algorithms (MD5, SHA1)
   - Insecure random number generation
   - Poor encryption practices

4. **Security Headers & CORS**
   - Missing security headers
   - Overly permissive CORS policies
   - Unsafe content types

5. **Deserialization & Data Handling**
   - Unsafe pickle/YAML loading
   - Path traversal vulnerabilities
   - File upload security issues

### Security Scoring
- **100-80**: Excellent security posture
- **79-60**: Good with minor issues
- **59-40**: Moderate security concerns
- **39-20**: Significant vulnerabilities
- **19-0**: Critical security issues

### Vulnerability Management
```bash
# Find all critical vulnerabilities
fortris find-vulns --severity CRITICAL

# Get vulnerabilities by type
fortris find-vulns --type "SQL injection"

# Export vulnerability data
fortris report --vulnerabilities-only > vulns.json
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
# View Fortris logs
tail -f ~/.claude/logs/cache.log

# Check for errors
grep ERROR ~/.claude/logs/cache.log
```

3. **Resource Usage**
```bash
# Check memory usage
ps aux | grep fortris_security_daemon

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
fortris clear --confirm
fortris warm "**/*"
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
# Run Fortris daemon in foreground with debug logging
python3 ~/.claude/cache/fortris_security_daemon.py --log-level DEBUG
```

## Enterprise Considerations

### 1. Compliance & Auditing
- All Fortris operations are logged to `~/.claude/logs/cache.log`
- Implement log rotation: `logrotate -f ~/.claude/config/logrotate.conf`
- Regular audit reviews of cached content and security findings

### 2. Resource Limits
```bash
# Set memory limits in systemd (if using systemd)
# /etc/systemd/system/fortris-security.service
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
The Fortris cache is ephemeral and can be rebuilt:
```bash
# No need to backup cache files
# Exclude from backups: ~/.claude/cache/
# Do backup security reports and configurations
```

### 6. Monitoring Integration
```bash
# Export metrics for monitoring systems
fortris metrics --format json > /var/log/fortris-security-metrics.json

# Set up alerts for:
# - Fortris daemon not running
# - Cache hit rate < 80%
# - New critical vulnerabilities detected
# - Disk usage > 2GB
```

## Support

For issues or questions:
1. Check logs: `~/.claude/logs/cache.log`
2. Run health check: `fortris health`
3. Review this documentation
4. Contact your IT administrator

## Version
Fortris Security Cache System v3.0
Last Updated: 2025-01-02

---

**Fortris** - Advanced Security Analysis for Enterprise Codebases