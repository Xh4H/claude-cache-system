#!/usr/bin/env python3
"""
Optimized MCP Server for Claude Cache
Phase 3: Enhanced protocol efficiency, connection pooling, and performance
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# Add cache directory to path
cache_dir = Path.home() / ".claude" / "cache"
sys.path.insert(0, str(cache_dir))

from claude_cache_optimized_async import OptimizedAsyncCache

logger = logging.getLogger(__name__)

@dataclass
class MCPResponse:
    """Standardized MCP response format"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cache_hit: bool = False

class OptimizedMCPServer:
    """High-performance MCP server with connection pooling and optimized protocols"""
    
    def __init__(self, max_connections: int = 10, connection_timeout: float = 30.0):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.active_connections = 0
        self.connection_semaphore = asyncio.Semaphore(max_connections)
        self.cache_pool = None
        self.stats = {
            'requests_served': 0,
            'cache_hits': 0,
            'errors': 0,
            'avg_response_time': 0.0
        }
        
    async def __aenter__(self):
        """Initialize server resources"""
        self.cache_pool = OptimizedAsyncCache()
        await self.cache_pool.__aenter__()
        logger.info(f"MCP Server initialized (max connections: {self.max_connections})")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup server resources"""
        if self.cache_pool:
            await self.cache_pool.__aexit__(exc_type, exc_val, exc_tb)
        logger.info("MCP Server shutdown complete")
    
    async def handle_request(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResponse:
        """Handle MCP tool request with connection pooling"""
        start_time = time.time()
        
        async with self.connection_semaphore:
            self.active_connections += 1
            try:
                response = await self._execute_tool(tool_name, parameters)
                response.execution_time = time.time() - start_time
                
                # Update statistics
                self.stats['requests_served'] += 1
                if response.cache_hit:
                    self.stats['cache_hits'] += 1
                if not response.success:
                    self.stats['errors'] += 1
                
                # Update rolling average response time
                current_avg = self.stats['avg_response_time']
                request_count = self.stats['requests_served']
                self.stats['avg_response_time'] = (
                    (current_avg * (request_count - 1) + response.execution_time) / request_count
                )
                
                return response
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error handling {tool_name}: {e}")
                return MCPResponse(
                    success=False,
                    error=str(e),
                    execution_time=time.time() - start_time
                )
            finally:
                self.active_connections -= 1
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResponse:
        """Execute specific cache tool with optimized routing"""
        
        # Optimized tool routing with direct method calls
        tool_map = {
            'cache_warm': self._handle_cache_warm,
            'cache_file': self._handle_cache_file,
            'cache_stats': self._handle_cache_stats,
            'cache_clear': self._handle_cache_clear,
            'cache_health': self._handle_cache_health
        }
        
        handler = tool_map.get(tool_name)
        if not handler:
            return MCPResponse(
                success=False,
                error=f"Unknown tool: {tool_name}"
            )
        
        return await handler(parameters)
    
    async def _handle_cache_warm(self, params: Dict[str, Any]) -> MCPResponse:
        """Optimized cache warming with progress tracking"""
        try:
            patterns = params.get('patterns', [])
            if not patterns:
                return MCPResponse(success=False, error="No patterns provided")
            
            # Use optimized async cache warming
            result = await self.cache_pool.warm_cache_optimized(patterns)
            
            return MCPResponse(
                success=True,
                data={
                    'files_processed': result['files_processed'],
                    'files_cached': result['files_cached'],
                    'execution_time': result['total_time'],
                    'speedup': result.get('speedup', 1.0),
                    'performance_tier': self._classify_performance(result.get('speedup', 1.0))
                }
            )
            
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def _handle_cache_file(self, params: Dict[str, Any]) -> MCPResponse:
        """Fast single file caching"""
        try:
            file_path = params.get('file_path')
            if not file_path:
                return MCPResponse(success=False, error="No file_path provided")
            
            # Direct file processing
            result = await self.cache_pool._process_file_fast(file_path)
            
            if result:
                # Insert to database
                await self.cache_pool._db_pool.execute(
                    'INSERT OR REPLACE INTO async_cache (path, cached_time, size) VALUES (?, ?, ?)',
                    result
                )
                await self.cache_pool._db_pool.commit()
                
                return MCPResponse(
                    success=True,
                    data={'file_path': file_path, 'cached': True},
                    cache_hit=False
                )
            else:
                return MCPResponse(success=False, error="Failed to cache file")
                
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def _handle_cache_stats(self, params: Dict[str, Any]) -> MCPResponse:
        """Get comprehensive cache and server statistics"""
        try:
            # Database stats
            cursor = await self.cache_pool._db_pool.execute(
                'SELECT COUNT(*) as total, SUM(size) as total_size FROM async_cache'
            )
            db_stats = await cursor.fetchone()
            
            server_stats = {
                'server': {
                    'active_connections': self.active_connections,
                    'max_connections': self.max_connections,
                    'requests_served': self.stats['requests_served'],
                    'cache_hits': self.stats['cache_hits'],
                    'hit_rate': self.stats['cache_hits'] / max(1, self.stats['requests_served']),
                    'errors': self.stats['errors'],
                    'avg_response_time': self.stats['avg_response_time']
                },
                'cache': {
                    'total_files': db_stats[0] if db_stats else 0,
                    'total_size_mb': (db_stats[1] / 1024 / 1024) if db_stats and db_stats[1] else 0,
                    'performance_tier': 'optimized_async'
                }
            }
            
            return MCPResponse(
                success=True,
                data=server_stats,
                cache_hit=True  # Stats are always "cached"
            )
            
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def _handle_cache_clear(self, params: Dict[str, Any]) -> MCPResponse:
        """Clear cache with confirmation"""
        try:
            confirm = params.get('confirm', False)
            if not confirm:
                return MCPResponse(success=False, error="Cache clear requires confirmation")
            
            # Clear database
            await self.cache_pool._db_pool.execute('DELETE FROM async_cache')
            await self.cache_pool._db_pool.commit()
            
            # Clear cache files
            cache_files_dir = self.cache_pool.cache_dir / "files"
            if cache_files_dir.exists():
                import shutil
                shutil.rmtree(cache_files_dir)
                cache_files_dir.mkdir(exist_ok=True)
            
            return MCPResponse(
                success=True,
                data={'message': 'Cache cleared successfully'}
            )
            
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def _handle_cache_health(self, params: Dict[str, Any]) -> MCPResponse:
        """Get comprehensive health check"""
        try:
            health_data = {
                'status': 'healthy',
                'server': {
                    'active_connections': self.active_connections,
                    'connection_utilization': self.active_connections / self.max_connections,
                    'avg_response_time': self.stats['avg_response_time'],
                    'uptime': time.time()  # Simplified uptime
                },
                'cache': {
                    'database_accessible': True,
                    'cache_directory_exists': self.cache_pool.cache_dir.exists(),
                    'performance_tier': 'phase3_optimized'
                },
                'recommendations': []
            }
            
            # Add performance recommendations
            if self.stats['avg_response_time'] > 0.1:
                health_data['recommendations'].append("Consider reducing cache size or optimizing queries")
            
            if self.active_connections / self.max_connections > 0.8:
                health_data['recommendations'].append("High connection utilization - consider increasing max_connections")
            
            return MCPResponse(
                success=True,
                data=health_data,
                cache_hit=True
            )
            
        except Exception as e:
            health_data = {
                'status': 'degraded',
                'error': str(e),
                'recommendations': ['Check cache system configuration', 'Verify database accessibility']
            }
            return MCPResponse(success=False, data=health_data, error=str(e))
    
    def _classify_performance(self, speedup: float) -> str:
        """Classify performance tier based on speedup"""
        if speedup >= 30:
            return "excellent"
        elif speedup >= 20:
            return "very_good"
        elif speedup >= 10:
            return "good"
        elif speedup >= 5:
            return "acceptable"
        else:
            return "needs_optimization"
    
    async def get_server_metrics(self) -> Dict[str, Any]:
        """Get detailed server performance metrics"""
        return {
            'performance': {
                'requests_per_second': self.stats['requests_served'] / max(1, time.time()),
                'avg_response_time': self.stats['avg_response_time'],
                'hit_rate': self.stats['cache_hits'] / max(1, self.stats['requests_served']),
                'error_rate': self.stats['errors'] / max(1, self.stats['requests_served'])
            },
            'resources': {
                'active_connections': self.active_connections,
                'connection_utilization': self.active_connections / self.max_connections,
                'max_connections': self.max_connections
            },
            'totals': self.stats.copy()
        }

# CLI interface for testing
async def test_mcp_server():
    """Test the optimized MCP server"""
    print("🚀 Testing Optimized MCP Server...")
    
    async with OptimizedMCPServer(max_connections=20) as server:
        # Test cache warming
        print("Testing cache warm...")
        warm_response = await server.handle_request('cache_warm', {'patterns': ['*.py']})
        print(f"Warm result: {warm_response.success}, Time: {warm_response.execution_time:.3f}s")
        
        # Test stats
        print("Testing cache stats...")
        stats_response = await server.handle_request('cache_stats', {})
        print(f"Stats: {stats_response.data}")
        
        # Test health check
        print("Testing health check...")
        health_response = await server.handle_request('cache_health', {})
        print(f"Health: {health_response.data['status']}")
        
        # Get server metrics
        metrics = await server.get_server_metrics()
        print(f"Server Performance: {metrics['performance']}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())