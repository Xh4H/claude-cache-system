#!/usr/bin/env python3
"""
claude Security Daemon v3.0
High-performance daemon for enterprise security analysis
"""

import os
import sys
import json
import time
import socket
import threading
import signal
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import psutil
from claude_security_cache import claudeSecurityCache, FileType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - claude - %(levelname)s - %(message)s'
)
logger = logging.getLogger("claudeDaemon")

class claudeSecurityDaemon:
    """High-performance daemon for claude security cache operations"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 19848):
        self.host = host
        self.port = port
        self.cache = claudeSecurityCache()
        self.server_socket = None
        self.running = False
        self.stats = {
            'requests_handled': 0,
            'errors': 0,
            'start_time': time.time(),
            'vulnerabilities_detected': 0
        }
        
        # Command handlers
        self.handlers = {
            'cache': self._handle_cache,
            'warm': self._handle_warm,
            'get': self._handle_get,
            'stats': self._handle_stats,
            'security_report': self._handle_security_report,
            'git_update': self._handle_git_update,
            'scan': self._handle_scan,
            'check': self._handle_check,
            'metrics': self._handle_metrics,
            'health': self._handle_health,
            'set_repo': self._handle_set_repo,
            'vulnerabilities': self._handle_vulnerabilities,
            'clear': self._handle_clear,
            'optimize': self._handle_optimize,
            'claude_info': self._handle_claude_info
        }
        
        logger.info("claude Security Daemon initialized")
    
    def start(self):
        """Start the claude daemon server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            
            logger.info(f"🔒 claude Security Daemon started on {self.host}:{self.port}")
            logger.info("claude is ready for enterprise security analysis")
            
            # Start background monitoring
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
            
            # Accept connections
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except socket.error:
                    if self.running:
                        logger.error("Socket error in claude accept loop")
                        
        except Exception as e:
            logger.error(f"Failed to start claude daemon: {e}")
            sys.exit(1)
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle client connection"""
        try:
            # Receive command
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            try:
                request = json.loads(data)
                command = request.get('command')
                params = request.get('params', {})
                
                if command in self.handlers:
                    response = self.handlers[command](**params)
                else:
                    response = {'error': f'Unknown claude command: {command}'}
                
                self.stats['requests_handled'] += 1
                
            except json.JSONDecodeError:
                response = {'error': 'Invalid JSON request'}
                self.stats['errors'] += 1
            except Exception as e:
                response = {'error': str(e)}
                self.stats['errors'] += 1
                logger.error(f"claude error handling command: {e}")
            
            # Send response
            response_data = json.dumps(response).encode('utf-8')
            client_socket.sendall(response_data)
            
        except Exception as e:
            logger.error(f"claude client handling error: {e}")
        finally:
            client_socket.close()
    
    def _handle_cache(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Handle cache command"""
        start_time = time.time()
        
        entry = self.cache.cache_file_enhanced(file_path, force)
        
        if entry:
            self.stats['vulnerabilities_detected'] += len(entry.vulnerabilities)
            return {
                'status': 'success',
                'cached': True,
                'file': file_path,
                'size': entry.size,
                'security_score': entry.security_score,
                'vulnerabilities': len(entry.vulnerabilities),
                'response_time_ms': (time.time() - start_time) * 1000,
                'processed_by': 'claude Security Cache v3.0'
            }
        else:
            return {
                'status': 'error',
                'cached': False,
                'file': file_path,
                'error': 'Failed to cache file with claude'
            }
    
    def _handle_warm(self, patterns: List[str]) -> Dict[str, Any]:
        """Handle warm cache command"""
        start_time = time.time()
        
        result = self.cache.warm_cache_parallel(patterns)
        result['response_time_ms'] = (time.time() - start_time) * 1000
        result['claude_analysis'] = True
        
        self.stats['vulnerabilities_detected'] += result.get('vulnerabilities_detected', 0)
        
        return result
    
    def _handle_get(self, file_path: str) -> Dict[str, Any]:
        """Handle get cached content command"""
        start_time = time.time()
        
        content = self.cache.get_cached_content(file_path)
        
        if content:
            return {
                'status': 'success',
                'found': True,
                'file': file_path,
                'size': len(content),
                'content': content.decode('utf-8', errors='ignore')[:1000],  # First 1000 chars
                'response_time_ms': (time.time() - start_time) * 1000,
                'claude_cached': True
            }
        else:
            return {
                'status': 'miss',
                'found': False,
                'file': file_path
            }
    
    def _handle_stats(self) -> Dict[str, Any]:
        """Handle stats command"""
        metrics = self.cache.get_performance_metrics()
        
        # Add daemon stats
        uptime = time.time() - self.stats['start_time']
        metrics.update({
            'daemon_uptime_seconds': uptime,
            'daemon_requests_handled': self.stats['requests_handled'],
            'daemon_errors': self.stats['errors'],
            'daemon_requests_per_second': self.stats['requests_handled'] / uptime if uptime > 0 else 0,
            'total_vulnerabilities_detected': self.stats['vulnerabilities_detected'],
            'daemon_type': 'claude Security Daemon v3.0'
        })
        
        return metrics
    
    def _handle_security_report(self) -> Dict[str, Any]:
        """Handle claude security report command"""
        return self.cache.get_security_report()
    
    def _handle_git_update(self, base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> Dict[str, Any]:
        """Handle git update command"""
        try:
            self.cache.update_from_git(base_ref, target_ref)
            return {
                'status': 'success', 
                'message': 'claude git update completed',
                'claude_analysis': True
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_scan(self) -> Dict[str, Any]:
        """Handle vulnerability scan command"""
        try:
            self.cache.scan_all_vulnerabilities()
            return {
                'status': 'success', 
                'message': 'claude vulnerability scan completed',
                'claude_analysis': True
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_check(self, file_path: str) -> Dict[str, Any]:
        """Handle check if file is cached command"""
        entry = self.cache._get_cache_entry(file_path)
        
        if entry:
            return {
                'cached': True,
                'file': file_path,
                'size': entry.size,
                'security_score': entry.security_score,
                'vulnerabilities': len(entry.vulnerabilities),
                'last_accessed': entry.last_accessed,
                'access_count': entry.access_count,
                'claude_analyzed': True
            }
        else:
            return {
                'cached': False,
                'file': file_path
            }
    
    def _handle_metrics(self) -> Dict[str, Any]:
        """Handle detailed metrics command"""
        return self.cache.get_performance_metrics()
    
    def _handle_health(self) -> Dict[str, Any]:
        """Handle claude health check command"""
        try:
            # Check cache system
            metrics = self.cache.get_performance_metrics()
            
            # Check system resources
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Check database connections
            db_healthy = True
            try:
                with self.cache._get_db_connection() as conn:
                    conn.execute("SELECT 1")
            except:
                db_healthy = False
            
            health_status = {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'claude_version': '3.0',
                'cache_hit_rate': metrics.get('hit_rate_percent', 0),
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'cached_files': metrics.get('cached_files', 0),
                'daemon_uptime': time.time() - self.stats['start_time'],
                'database_healthy': db_healthy,
                'partitions': len(self.cache.partitions),
                'git_integration': self.cache.git_integration is not None,
                'avg_security_score': metrics.get('avg_security_score', 100),
                'active_vulnerabilities': metrics.get('active_vulnerabilities', 0),
                'enterprise_ready': True,
                'claude_security_analysis': True
            }
            
            return health_status
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'claude_version': '3.0'
            }
    
    def _handle_set_repo(self, repo_path: str) -> Dict[str, Any]:
        """Handle set git repository command"""
        try:
            self.cache.set_git_repo(repo_path)
            return {
                'status': 'success', 
                'message': f'claude git repo set to: {repo_path}',
                'claude_git_integration': True
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_vulnerabilities(self, severity: Optional[str] = None) -> Dict[str, Any]:
        """Handle get vulnerabilities command"""
        with self.cache._get_db_connection() as conn:
            if severity:
                cursor = conn.execute(
                    'SELECT * FROM claude_vulnerabilities WHERE severity = ? AND resolved = 0',
                    (severity,)
                )
            else:
                cursor = conn.execute(
                    'SELECT * FROM claude_vulnerabilities WHERE resolved = 0'
                )
            
            vulnerabilities = [dict(row) for row in cursor.fetchall()]
            
        return {
            'count': len(vulnerabilities),
            'vulnerabilities': vulnerabilities[:100],  # Limit to 100 for response size
            'analyzed_by': 'claude Security Analyzer'
        }
    
    def _handle_clear(self, confirm: bool = False) -> Dict[str, Any]:
        """Handle clear cache command"""
        if not confirm:
            return {'status': 'error', 'error': 'Clear requires confirmation'}
        
        try:
            # Clear all partitions
            for partition in self.cache.partitions.values():
                with self.cache._get_db_connection(partition.partition_id) as conn:
                    conn.execute('DELETE FROM claude_partition_cache')
                    conn.commit()
            
            # Clear main index
            with self.cache._get_db_connection() as conn:
                conn.execute('DELETE FROM claude_cache')
                conn.execute('DELETE FROM claude_vulnerabilities')
                conn.execute('DELETE FROM claude_git_commits')
                conn.commit()
            
            # Clear memory caches
            self.cache._memory_cache.clear()
            self.cache._ttl_cache.clear()
            
            return {
                'status': 'success', 
                'message': 'claude cache cleared',
                'claude_cleared': True
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_optimize(self) -> Dict[str, Any]:
        """Handle optimize command"""
        try:
            # Run VACUUM on all databases
            for partition in self.cache.partitions.values():
                with self.cache._get_db_connection(partition.partition_id) as conn:
                    conn.execute('VACUUM')
            
            with self.cache._get_db_connection() as conn:
                conn.execute('VACUUM')
                conn.execute('ANALYZE')
            
            # Force garbage collection
            import gc
            gc.collect()
            
            return {
                'status': 'success', 
                'message': 'claude optimization completed',
                'claude_optimized': True
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_claude_info(self) -> Dict[str, Any]:
        """Handle claude info command"""
        return {
            'name': 'claude Security Cache System',
            'version': '3.0',
            'description': 'Advanced security analysis for enterprise codebases',
            'features': [
                'Real-time vulnerability detection',
                'Git-based incremental updates',
                'Intelligent cache partitioning',
                'Security-focused warming strategies',
                'Comprehensive security reporting'
            ],
            'daemon_port': self.port,
            'daemon_uptime': time.time() - self.stats['start_time'],
            'enterprise_ready': True,
            'security_patterns': len(self.cache.security_analyzer.patterns)
        }
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Log metrics every 60 seconds
                time.sleep(60)
                metrics = self.cache.get_performance_metrics()
                logger.info(f"claude metrics: Hit rate: {metrics['hit_rate_percent']:.1f}%, "
                          f"Files: {metrics['cached_files']}, "
                          f"Memory: {metrics['memory_usage_mb']:.1f}MB, "
                          f"Security Score: {metrics['avg_security_score']:.1f}, "
                          f"Vulnerabilities: {metrics['active_vulnerabilities']}")
                
            except Exception as e:
                logger.error(f"claude monitor loop error: {e}")
    
    def stop(self):
        """Stop the claude daemon"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        # Cleanup cache resources
        self.cache.cleanup()
        
        logger.info("claude Security Daemon stopped")


class claudeDaemonClient:
    """Client for communicating with the claude cache daemon"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 19848):
        self.host = host
        self.port = port
    
    def send_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command to claude daemon"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(30)  # 30 second timeout
            client_socket.connect((self.host, self.port))
            
            request = {
                'command': command,
                'params': params or {},
                'client': 'claude CLI'
            }
            
            client_socket.sendall(json.dumps(request).encode('utf-8'))
            
            # Receive response
            response_data = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            client_socket.close()
            
            return json.loads(response_data.decode('utf-8'))
            
        except Exception as e:
            return {'error': f'Failed to communicate with claude daemon: {e}'}


def main():
    """Main entry point for claude daemon"""
    parser = argparse.ArgumentParser(description='claude Security Cache Daemon v3.0')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=19848, help='Port to bind to')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    # Client commands
    subparsers = parser.add_subparsers(dest='command', help='claude Commands')
    
    # Cache command
    cache_parser = subparsers.add_parser('cache', help='Cache a file with claude')
    cache_parser.add_argument('file', help='File to cache')
    cache_parser.add_argument('--force', action='store_true', help='Force recache')
    
    # Warm command
    warm_parser = subparsers.add_parser('warm', help='Warm cache with security analysis')
    warm_parser.add_argument('patterns', nargs='+', help='File patterns')
    
    # Stats command
    subparsers.add_parser('stats', help='Show claude cache statistics')
    
    # Security report command
    subparsers.add_parser('security-report', help='Generate claude security report')
    
    # Git update command
    git_parser = subparsers.add_parser('git-update', help='Update from git')
    git_parser.add_argument('--base', default='HEAD~1', help='Base reference')
    git_parser.add_argument('--target', default='HEAD', help='Target reference')
    
    # Scan command
    subparsers.add_parser('scan', help='Run claude vulnerability scan')
    
    # Health command
    subparsers.add_parser('health', help='Check claude daemon health')
    
    # Set repo command
    repo_parser = subparsers.add_parser('set-repo', help='Set git repository')
    repo_parser.add_argument('path', help='Repository path')
    
    # claude info command
    subparsers.add_parser('info', help='Show claude system information')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    if args.daemon:
        # Run as daemon
        daemon = claudeSecurityDaemon(args.host, args.port)
        
        # Handle signals
        def signal_handler(signum, frame):
            logger.info("Received signal, shutting down claude daemon...")
            daemon.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        daemon.start()
        
    elif args.command:
        # Run as client
        client = claudeDaemonClient(args.host, args.port)
        
        if args.command == 'cache':
            result = client.send_command('cache', {
                'file_path': args.file,
                'force': args.force
            })
        elif args.command == 'warm':
            result = client.send_command('warm', {
                'patterns': args.patterns
            })
        elif args.command == 'stats':
            result = client.send_command('stats')
        elif args.command == 'security-report':
            result = client.send_command('security_report')
        elif args.command == 'git-update':
            result = client.send_command('git_update', {
                'base_ref': args.base,
                'target_ref': args.target
            })
        elif args.command == 'scan':
            result = client.send_command('scan')
        elif args.command == 'health':
            result = client.send_command('health')
        elif args.command == 'set-repo':
            result = client.send_command('set_repo', {
                'repo_path': args.path
            })
        elif args.command == 'info':
            result = client.send_command('claude_info')
        else:
            result = {'error': f'Unknown claude command: {args.command}'}
        
        print(json.dumps(result, indent=2))
        
    else:
        print("🔒 claude Security Cache System v3.0")
        print("Advanced security analysis for enterprise codebases")
        print("")
        parser.print_help()


if __name__ == '__main__':
    main()