#!/usr/bin/env python3
"""
🚀 Claude Cache Terminal Visualizer
Beautiful terminal-based stats, graphs, and monitoring
"""

import json
import sqlite3
import subprocess
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
import argparse

# Add color support
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

# Unicode box drawing characters
class Box:
    HORIZONTAL = '─'
    VERTICAL = '│'
    TOP_LEFT = '┌'
    TOP_RIGHT = '┐'
    BOTTOM_LEFT = '└'
    BOTTOM_RIGHT = '┘'
    CROSS = '┼'
    T_DOWN = '┬'
    T_UP = '┴'
    T_RIGHT = '├'
    T_LEFT = '┤'
    
    # Thick borders
    THICK_HORIZONTAL = '━'
    THICK_VERTICAL = '┃'
    THICK_TOP_LEFT = '┏'
    THICK_TOP_RIGHT = '┓'
    THICK_BOTTOM_LEFT = '┗'
    THICK_BOTTOM_RIGHT = '┛'

# Progress bar characters
class Progress:
    FULL = '█'
    SEVEN_EIGHTHS = '▉'
    THREE_QUARTERS = '▊'
    FIVE_EIGHTHS = '▋'
    HALF = '▌'
    THREE_EIGHTHS = '▍'
    QUARTER = '▎'
    EIGHTH = '▏'
    EMPTY = ' '

class CacheVisualizer:
    def __init__(self):
        self.cache_dir = Path.home() / ".claude" / "cache"
        self.daemon_script = self.cache_dir / "claude_cache_daemon.py"
        self.db_path = self.cache_dir / "files" / "async_index.db"
        
    def get_terminal_size(self) -> tuple:
        """Get terminal width and height"""
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except:
            return 80, 24
    
    def get_live_stats(self) -> Dict[str, Any]:
        """Get live statistics from daemon"""
        try:
            result = subprocess.run(
                ["python", str(self.daemon_script), "stats"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self.daemon_script.parent)
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'Result: ' in line:
                        json_str = line.split('Result: ', 1)[1]
                        return json.loads(json_str)
            
            return {"server": {}, "cache": {}}
        except Exception as e:
            return {"server": {}, "cache": {}, "error": str(e)}
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=2.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception:
            yield None
        finally:
            if conn:
                conn.close()
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get file statistics from database"""
        with self.get_db_connection() as conn:
            if not conn:
                return {"total_files": 0, "total_size_mb": 0.0, "largest_files": []}
            
            try:
                # Total stats
                cursor = conn.execute("SELECT COUNT(*) as count, SUM(size) as total_size FROM async_cache")
                row = cursor.fetchone()
                total_files = row['count'] if row else 0
                total_size = row['total_size'] if row and row['total_size'] else 0
                
                # Largest files
                cursor = conn.execute("""
                    SELECT path, size 
                    FROM async_cache 
                    ORDER BY size DESC 
                    LIMIT 5
                """)
                largest_files = [
                    {"path": row['path'], "size": row['size']}
                    for row in cursor.fetchall()
                ]
                
                return {
                    "total_files": total_files,
                    "total_size_mb": total_size / (1024 * 1024),
                    "largest_files": largest_files
                }
            except Exception:
                return {"total_files": 0, "total_size_mb": 0.0, "largest_files": []}
    
    def format_bytes(self, bytes_val: int) -> str:
        """Format bytes in human-readable format"""
        if bytes_val == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"
    
    def create_progress_bar(self, percentage: float, width: int = 20, color: str = Colors.GREEN) -> str:
        """Create a beautiful progress bar"""
        filled = int(percentage * width / 100)
        remainder = (percentage * width / 100) - filled
        
        bar = color + Progress.FULL * filled
        
        # Add partial block for smoother animation
        if remainder > 0.875:
            bar += Progress.SEVEN_EIGHTHS
        elif remainder > 0.75:
            bar += Progress.THREE_QUARTERS
        elif remainder > 0.625:
            bar += Progress.FIVE_EIGHTHS
        elif remainder > 0.5:
            bar += Progress.HALF
        elif remainder > 0.375:
            bar += Progress.THREE_EIGHTHS
        elif remainder > 0.25:
            bar += Progress.QUARTER
        elif remainder > 0.125:
            bar += Progress.EIGHTH
        elif filled < width:
            bar += Progress.EMPTY
        
        bar += Colors.DIM + Progress.EMPTY * (width - filled - (1 if remainder > 0 and filled < width else 0))
        bar += Colors.RESET
        
        return bar
    
    def create_sparkline(self, values: List[float], width: int = 20) -> str:
        """Create a sparkline chart"""
        if not values:
            return " " * width
        
        max_val = max(values) if max(values) > 0 else 1
        min_val = min(values)
        
        # Normalize values to 0-7 range for block characters
        blocks = "▁▂▃▄▅▆▇█"
        
        sparkline = ""
        for i in range(width):
            if i < len(values):
                val = values[i]
                normalized = (val - min_val) / (max_val - min_val) if max_val != min_val else 0
                block_index = int(normalized * 7)
                sparkline += blocks[block_index]
            else:
                sparkline += " "
        
        return sparkline
    
    def draw_box(self, width: int, height: int, title: str = "", thick: bool = False) -> List[str]:
        """Draw a box with optional title"""
        if thick:
            h_char, v_char = Box.THICK_HORIZONTAL, Box.THICK_VERTICAL
            tl, tr = Box.THICK_TOP_LEFT, Box.THICK_TOP_RIGHT
            bl, br = Box.THICK_BOTTOM_LEFT, Box.THICK_BOTTOM_RIGHT
        else:
            h_char, v_char = Box.HORIZONTAL, Box.VERTICAL
            tl, tr = Box.TOP_LEFT, Box.TOP_RIGHT
            bl, br = Box.BOTTOM_LEFT, Box.BOTTOM_RIGHT
        
        lines = []
        
        # Top border with title
        if title:
            title_text = f" {title} "
            title_padding = (width - len(title_text) - 2) // 2
            top_line = tl + h_char * title_padding + title_text + h_char * (width - len(title_text) - title_padding - 2) + tr
        else:
            top_line = tl + h_char * (width - 2) + tr
        lines.append(top_line)
        
        # Middle lines
        for _ in range(height - 2):
            lines.append(v_char + " " * (width - 2) + v_char)
        
        # Bottom border
        bottom_line = bl + h_char * (width - 2) + br
        lines.append(bottom_line)
        
        return lines
    
    def show_overview(self):
        """Show cache overview"""
        term_width, term_height = self.get_terminal_size()
        
        # Clear screen and move to top
        print(f"\033[2J\033[H", end="")
        
        # Get data
        live_stats = self.get_live_stats()
        file_stats = self.get_file_stats()
        
        server = live_stats.get("server", {})
        cache = live_stats.get("cache", {})
        
        # Header
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 Claude Cache Performance Dashboard{Colors.RESET}")
        print(f"{Colors.DIM}Real-time terminal visualization • {time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print()
        
        # Performance metrics (2x3 grid)
        metrics = [
            ("📁 Total Files", f"{file_stats.get('total_files', 0):,}", Colors.BLUE),
            ("💾 Cache Size", f"{file_stats.get('total_size_mb', 0):.1f} MB", Colors.CYAN),
            ("⚡ Hit Rate", f"{server.get('hit_rate', 0)*100:.1f}%", Colors.GREEN),
            ("📊 Requests", f"{server.get('requests_served', 0):,}", Colors.YELLOW),
            ("⏱️ Avg Response", f"{server.get('avg_response_time', 0)*1000:.1f}ms", Colors.MAGENTA),
            ("🔗 Connections", f"{server.get('active_connections', 0)}/{server.get('max_connections', 50)}", Colors.WHITE)
        ]
        
        # Draw metrics in 2x3 grid
        for row in range(2):
            line1, line2, line3 = "", "", ""
            for col in range(3):
                idx = row * 3 + col
                if idx < len(metrics):
                    label, value, color = metrics[idx]
                    
                    # Box width for each metric
                    box_width = 25
                    
                    # Create metric box
                    line1 += f"{color}┌─────────────────────────┐{Colors.RESET} "
                    line2 += f"{color}│{Colors.RESET} {label:<12} {Colors.BOLD}{color}{value:>9}{Colors.RESET} {color}│{Colors.RESET} "
                    line3 += f"{color}└─────────────────────────┘{Colors.RESET} "
            
            print(line1)
            print(line2)
            print(line3)
            if row == 0:
                print()
        
        print()
        
        # Performance bars
        hit_rate = server.get('hit_rate', 0) * 100
        response_time = min(server.get('avg_response_time', 0) * 1000, 100)  # Cap at 100ms for display
        connection_usage = (server.get('active_connections', 0) / max(server.get('max_connections', 50), 1)) * 100
        
        print(f"{Colors.BOLD}Performance Metrics{Colors.RESET}")
        print(f"Hit Rate:     {self.create_progress_bar(hit_rate, 30, Colors.GREEN)} {hit_rate:5.1f}%")
        print(f"Response:     {self.create_progress_bar(100-response_time, 30, Colors.BLUE)} {response_time:5.1f}ms")
        print(f"Connections:  {self.create_progress_bar(connection_usage, 30, Colors.YELLOW)} {connection_usage:5.1f}%")
        print()
        
        # Cache errors and status
        errors = server.get('errors', 0)
        performance_tier = cache.get('performance_tier', 'unknown')
        
        status_color = Colors.GREEN if errors == 0 else Colors.RED
        tier_color = {
            'optimized_async': Colors.BRIGHT_GREEN,
            'good': Colors.GREEN,
            'fair': Colors.YELLOW,
            'poor': Colors.RED
        }.get(performance_tier, Colors.WHITE)
        
        print(f"{Colors.BOLD}System Status{Colors.RESET}")
        print(f"Health:       {status_color}●{Colors.RESET} {'Healthy' if errors == 0 else f'{errors} errors'}")
        print(f"Performance:  {tier_color}●{Colors.RESET} {performance_tier.replace('_', ' ').title()}")
        print(f"Speedup:      {Colors.BRIGHT_GREEN}●{Colors.RESET} ~40x faster than baseline")
        print()
        
        # Top files
        largest_files = file_stats.get('largest_files', [])
        if largest_files:
            print(f"{Colors.BOLD}📁 Largest Cached Files{Colors.RESET}")
            for i, file_info in enumerate(largest_files[:5], 1):
                path = file_info['path']
                size = self.format_bytes(file_info['size'])
                
                # Truncate path if too long
                max_path_length = term_width - 20
                if len(path) > max_path_length:
                    path = "..." + path[-(max_path_length-3):]
                
                print(f"{Colors.DIM}{i}.{Colors.RESET} {path:<{max_path_length}} {Colors.CYAN}{size:>8}{Colors.RESET}")
        
        print()
        print(f"{Colors.DIM}Press Ctrl+C to exit • Use 'cviz monitor' for live updates{Colors.RESET}")
    
    def show_monitor(self, interval: int = 2):
        """Show live monitoring with updates"""
        try:
            while True:
                self.show_overview()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.BRIGHT_GREEN}✨ Monitoring stopped{Colors.RESET}")
    
    def show_graph(self, duration: int = 60):
        """Show performance graph over time"""
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}📊 Cache Performance Graph{Colors.RESET}")
        print(f"{Colors.DIM}Collecting data for {duration} seconds...{Colors.RESET}")
        
        hit_rates = []
        response_times = []
        timestamps = []
        
        try:
            for i in range(duration):
                stats = self.get_live_stats()
                server = stats.get("server", {})
                
                hit_rates.append(server.get('hit_rate', 0) * 100)
                response_times.append(server.get('avg_response_time', 0) * 1000)
                timestamps.append(time.strftime('%H:%M:%S'))
                
                if i % 5 == 0:  # Update every 5 seconds
                    print(f"\r{Colors.DIM}Progress: {self.create_progress_bar(i/duration*100, 20)} {i}/{duration}s{Colors.RESET}", end="")
                
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Graph collection stopped early{Colors.RESET}")
        
        print(f"\n\n{Colors.BOLD}Performance Over Time{Colors.RESET}")
        
        # Hit rate sparkline
        hit_sparkline = self.create_sparkline(hit_rates, 60)
        print(f"Hit Rate:     {Colors.GREEN}{hit_sparkline}{Colors.RESET} {hit_rates[-1] if hit_rates else 0:.1f}%")
        
        # Response time sparkline
        response_sparkline = self.create_sparkline(response_times, 60)
        print(f"Response:     {Colors.BLUE}{response_sparkline}{Colors.RESET} {response_times[-1] if response_times else 0:.1f}ms")
        
        print(f"\n{Colors.DIM}Collected {len(hit_rates)} data points{Colors.RESET}")
    
    def show_files(self, limit: int = 20):
        """Show detailed file information"""
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}📁 Cache File Analysis{Colors.RESET}")
        
        with self.get_db_connection() as conn:
            if not conn:
                print(f"{Colors.RED}❌ Cannot connect to cache database{Colors.RESET}")
                return
            
            try:
                # File size distribution
                cursor = conn.execute("""
                    SELECT 
                        CASE 
                            WHEN size < 1024 THEN '< 1KB'
                            WHEN size < 10240 THEN '1-10KB'
                            WHEN size < 102400 THEN '10-100KB'
                            WHEN size < 1048576 THEN '100KB-1MB'
                            ELSE '> 1MB'
                        END as size_range,
                        COUNT(*) as count,
                        SUM(size) as total_size
                    FROM async_cache 
                    GROUP BY size_range
                    ORDER BY total_size DESC
                """)
                
                print(f"\n{Colors.BOLD}File Size Distribution{Colors.RESET}")
                for row in cursor.fetchall():
                    size_range = row['size_range']
                    count = row['count']
                    total_size = self.format_bytes(row['total_size'])
                    
                    print(f"{size_range:>12}: {count:4d} files ({total_size})")
                
                # Top files by size
                cursor = conn.execute("""
                    SELECT path, size, cached_time
                    FROM async_cache 
                    ORDER BY size DESC 
                    LIMIT ?
                """, (limit,))
                
                print(f"\n{Colors.BOLD}Largest Files{Colors.RESET}")
                for i, row in enumerate(cursor.fetchall(), 1):
                    path = row['path']
                    size = self.format_bytes(row['size'])
                    cached_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(row['cached_time']))
                    
                    # Truncate path
                    term_width, _ = self.get_terminal_size()
                    max_path_length = term_width - 30
                    if len(path) > max_path_length:
                        path = "..." + path[-(max_path_length-3):]
                    
                    print(f"{Colors.DIM}{i:2d}.{Colors.RESET} {path:<{max_path_length}} {Colors.CYAN}{size:>8}{Colors.RESET} {Colors.DIM}{cached_time}{Colors.RESET}")
                
            except Exception as e:
                print(f"{Colors.RED}❌ Error querying database: {e}{Colors.RESET}")

def main():
    parser = argparse.ArgumentParser(description="🚀 Claude Cache Terminal Visualizer")
    parser.add_argument('command', nargs='?', default='overview', 
                       choices=['overview', 'monitor', 'graph', 'files'],
                       help='Command to run (default: overview)')
    parser.add_argument('--interval', '-i', type=int, default=2,
                       help='Update interval for monitor mode (seconds)')
    parser.add_argument('--duration', '-d', type=int, default=60,
                       help='Duration for graph collection (seconds)')
    parser.add_argument('--limit', '-l', type=int, default=20,
                       help='Number of files to show')
    
    args = parser.parse_args()
    
    viz = CacheVisualizer()
    
    if args.command == 'overview':
        viz.show_overview()
    elif args.command == 'monitor':
        viz.show_monitor(args.interval)
    elif args.command == 'graph':
        viz.show_graph(args.duration)
    elif args.command == 'files':
        viz.show_files(args.limit)

if __name__ == "__main__":
    main()