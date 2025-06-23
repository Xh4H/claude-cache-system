#!/usr/bin/env python3
"""
Claude Cache Daemon - High-performance CLI with persistent process
Phase 3: Eliminates Python startup overhead with background daemon
"""

import os
import sys
import json
import time
import socket
import asyncio
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import signal
import atexit

# Add cache directory to path
cache_dir = Path.home() / ".claude" / "cache"
sys.path.insert(0, str(cache_dir))

from mcp_server_optimized import OptimizedMCPServer

class CacheDaemon:
    """Background daemon for ultra-fast cache operations"""
    
    def __init__(self, socket_path: str = None, port: int = 19847):
        self.socket_path = socket_path or str(Path.home() / ".claude" / "cache_daemon.sock")
        self.port = port
        self.pid_file = Path.home() / ".claude" / "cache_daemon.pid"
        self.server = None
        self.running = False
        
    async def start_daemon(self):
        """Start the cache daemon"""
        print(f"🚀 Starting Claude Cache Daemon...")
        
        # Initialize MCP server
        self.server = OptimizedMCPServer(max_connections=50)
        await self.server.__aenter__()
        
        # Start TCP server for fast IPC
        server = await asyncio.start_server(
            self.handle_client, 
            '127.0.0.1', 
            self.port
        )
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        self.running = True
        print(f"✅ Cache daemon started on port {self.port} (PID: {os.getpid()})")
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self.cleanup)
        
        # Serve forever
        async with server:
            await server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """Handle client requests with minimal overhead"""
        try:
            # Read request (format: length_bytes + json_data)
            length_data = await reader.read(4)
            if not length_data:
                return
            
            length = int.from_bytes(length_data, byteorder='big')
            request_data = await reader.read(length)
            
            request = json.loads(request_data.decode('utf-8'))
            
            # Process request through optimized MCP server
            response = await self.server.handle_request(
                request.get('tool', ''),
                request.get('params', {})
            )
            
            # Send response
            response_data = json.dumps({
                'success': response.success,
                'data': response.data,
                'error': response.error,
                'execution_time': response.execution_time,
                'cache_hit': response.cache_hit
            }).encode('utf-8')
            
            response_length = len(response_data).to_bytes(4, byteorder='big')
            writer.write(response_length + response_data)
            await writer.drain()
            
        except Exception as e:
            # Send error response
            error_response = json.dumps({
                'success': False,
                'error': str(e),
                'execution_time': 0.0
            }).encode('utf-8')
            
            error_length = len(error_response).to_bytes(4, byteorder='big')
            writer.write(error_length + error_response)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n💀 Received signal {signum}, shutting down daemon...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup daemon resources"""
        if self.pid_file.exists():
            self.pid_file.unlink()
        
        if self.server:
            asyncio.create_task(self.server.__aexit__(None, None, None))

class CacheClient:
    """Ultra-fast client for daemon communication"""
    
    def __init__(self, port: int = 19847):
        self.port = port
        self.daemon_pid_file = Path.home() / ".claude" / "cache_daemon.pid"
    
    def is_daemon_running(self) -> bool:
        """Check if daemon is running"""
        if not self.daemon_pid_file.exists():
            return False
        
        try:
            with open(self.daemon_pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            return False
    
    async def send_request(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to daemon with minimal overhead"""
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
            
            # Prepare request
            request = json.dumps({'tool': tool, 'params': params}).encode('utf-8')
            request_length = len(request).to_bytes(4, byteorder='big')
            
            # Send request
            writer.write(request_length + request)
            await writer.drain()
            
            # Read response
            length_data = await reader.read(4)
            length = int.from_bytes(length_data, byteorder='big')
            response_data = await reader.read(length)
            
            writer.close()
            await writer.wait_closed()
            
            return json.loads(response_data.decode('utf-8'))
            
        except Exception as e:
            return {'success': False, 'error': f"Communication error: {e}"}
    
    def start_daemon_if_needed(self) -> bool:
        """Start daemon if not running"""
        if self.is_daemon_running():
            return True
        
        print("🔄 Starting cache daemon...")
        
        # Start daemon in background
        daemon_script = Path(__file__).resolve()
        process = subprocess.Popen([
            sys.executable, str(daemon_script), '--daemon'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for daemon to start
        for _ in range(10):  # Wait up to 5 seconds
            time.sleep(0.5)
            if self.is_daemon_running():
                print("✅ Cache daemon started")
                return True
        
        print("❌ Failed to start cache daemon")
        return False

async def fast_cache_command(command: str, *args) -> Dict[str, Any]:
    """Ultra-fast cache command execution"""
    client = CacheClient()
    
    # Ensure daemon is running
    if not client.start_daemon_if_needed():
        return {'success': False, 'error': 'Failed to start daemon'}
    
    # Map commands to tools
    command_map = {
        'warm': ('cache_warm', {'patterns': list(args)}),
        'stats': ('cache_stats', {}),
        'health': ('cache_health', {}),
        'clear': ('cache_clear', {'confirm': '--confirm' in args})
    }
    
    if command not in command_map:
        return {'success': False, 'error': f'Unknown command: {command}'}
    
    tool, params = command_map[command]
    return await client.send_request(tool, params)

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("""
🚀 Claude Cache Daemon CLI

USAGE:
    python claude_cache_daemon.py <command> [args]

COMMANDS:
    --daemon                Start daemon mode
    warm <patterns>         Warm cache with patterns
    stats                   Show cache statistics  
    health                  Health check
    clear --confirm         Clear cache
    stop                    Stop daemon

EXAMPLES:
    claude_cache_daemon.py warm "*.py" "*.js"
    claude_cache_daemon.py stats
    claude_cache_daemon.py health
""")
        return
    
    command = sys.argv[1]
    
    if command == '--daemon':
        # Run as daemon
        daemon = CacheDaemon()
        asyncio.run(daemon.start_daemon())
    
    elif command == 'stop':
        # Stop daemon
        client = CacheClient()
        if client.is_daemon_running():
            with open(client.daemon_pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print("💀 Cache daemon stopped")
        else:
            print("❌ Daemon not running")
    
    else:
        # Execute command via daemon
        start_time = time.time()
        result = asyncio.run(fast_cache_command(command, *sys.argv[2:]))
        total_time = time.time() - start_time
        
        if result['success']:
            print(f"✅ {command.upper()} completed in {total_time:.3f}s")
            if 'data' in result and result['data']:
                print(f"   Result: {result['data']}")
            if 'execution_time' in result:
                daemon_time = result['execution_time']
                overhead = total_time - daemon_time
                print(f"   Daemon time: {daemon_time:.3f}s")
                print(f"   IPC overhead: {overhead:.3f}s")
                speedup = 0.5 / total_time if total_time > 0 else 1  # vs 500ms cold start
                print(f"   vs Cold start: {speedup:.1f}x faster")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()