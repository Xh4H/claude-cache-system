#!/usr/bin/env python3
"""
MCP Server Integration for claude Security Cache
Provides Claude Code compatibility while maintaining claude branding
"""

import json
import asyncio
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

# Import claude cache system
from claude_security_cache import claudeSecurityCache

logger = logging.getLogger("claudeMCP")

class claudeMCPServer:
    """MCP Server for claude Security Cache - Claude Code Integration"""
    
    def __init__(self):
        self.cache = claudeSecurityCache()
        self.tools = {
            "cache_file": self._cache_file_tool,
            "warm_cache": self._warm_cache_tool,
            "get_cached_content": self._get_cached_content_tool,
            "security_report": self._security_report_tool,
            "health_check": self._health_check_tool
        }
    
    async def _cache_file_tool(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Cache a file with claude security analysis"""
        try:
            entry = self.cache.cache_file_enhanced(file_path, force)
            if entry:
                return {
                    "success": True,
                    "file": file_path,
                    "size": entry.size,
                    "security_score": entry.security_score,
                    "vulnerabilities": len(entry.vulnerabilities),
                    "claude_analyzed": True,
                    "cached_at": entry.cached_time
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to cache file",
                    "file": file_path
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file": file_path
            }
    
    async def _warm_cache_tool(self, patterns: List[str]) -> Dict[str, Any]:
        """Warm cache with security analysis"""
        try:
            result = self.cache.warm_cache_parallel(patterns)
            result["claude_analysis"] = True
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_cached_content_tool(self, file_path: str) -> Dict[str, Any]:
        """Get cached file content"""
        try:
            content = self.cache.get_cached_content(file_path)
            if content:
                return {
                    "success": True,
                    "file": file_path,
                    "content": content.decode('utf-8', errors='ignore'),
                    "size": len(content),
                    "claude_cached": True
                }
            else:
                return {
                    "success": False,
                    "error": "File not in cache",
                    "file": file_path
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file": file_path
            }
    
    async def _security_report_tool(self) -> Dict[str, Any]:
        """Generate claude security report"""
        try:
            report = self.cache.get_security_report()
            report["claude_generated"] = True
            return report
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _health_check_tool(self) -> Dict[str, Any]:
        """Check claude cache health"""
        try:
            metrics = self.cache.get_performance_metrics()
            return {
                "status": "healthy",
                "claude_version": "3.0",
                "cache_metrics": metrics,
                "enterprise_ready": True
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests from Claude Code"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "claude_cache_file",
                        "description": "Cache a file with claude security analysis",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Path to file to cache"},
                                "force": {"type": "boolean", "description": "Force recache", "default": False}
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "claude_warm_cache",
                        "description": "Warm cache with security analysis for multiple files",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "patterns": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "File patterns to cache"
                                }
                            },
                            "required": ["patterns"]
                        }
                    },
                    {
                        "name": "claude_get_content",
                        "description": "Get cached file content",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Path to cached file"}
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "claude_security_report",
                        "description": "Generate comprehensive security report",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "claude_health_check",
                        "description": "Check claude cache system health",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "claude_cache_file":
                result = await self._cache_file_tool(**arguments)
            elif tool_name == "claude_warm_cache":
                result = await self._warm_cache_tool(**arguments)
            elif tool_name == "claude_get_content":
                result = await self._get_cached_content_tool(**arguments)
            elif tool_name == "claude_security_report":
                result = await self._security_report_tool()
            elif tool_name == "claude_health_check":
                result = await self._health_check_tool()
            else:
                result = {"error": f"Unknown claude tool: {tool_name}"}
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        else:
            return {"error": f"Unknown method: {method}"}

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting claude MCP Server for Claude Code integration")
        
        # Read messages from stdin and write responses to stdout
        # This follows the MCP protocol for Claude Code integration
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                
                # Send response
                print(json.dumps(response), flush=True)
                
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                error_response = {"error": str(e)}
                print(json.dumps(error_response), flush=True)

def main():
    """Main entry point for claude MCP Server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - claudeMCP - %(levelname)s - %(message)s'
    )
    
    server = claudeMCPServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("claude MCP Server stopped")
    except Exception as e:
        logger.error(f"claude MCP Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()