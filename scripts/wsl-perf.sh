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
